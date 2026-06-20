import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Trading Data", layout="wide", initial_sidebar_state="collapsed")

NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_all_trades():
    all_results = []
    has_more = True
    start_cursor = None
    while has_more:
        payload = {}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        response = requests.post(
            f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
            headers=headers, json=payload
        )
        data = response.json()
        if response.status_code != 200:
            st.error(f"Notion error: {data}")
            break
        all_results.extend(data['results'])
        has_more = data['has_more']
        start_cursor = data.get('next_cursor')
    return all_results

def extract_property(prop):
    if prop is None:
        return None
    ptype = prop['type']
    if ptype == 'title':
        items = prop['title']
        return items[0]['plain_text'] if items else None
    elif ptype == 'rich_text':
        items = prop['rich_text']
        return items[0]['plain_text'] if items else None
    elif ptype == 'number':
        return prop['number']
    elif ptype == 'select':
        return prop['select']['name'] if prop['select'] else None
    elif ptype == 'multi_select':
        return ', '.join([x['name'] for x in prop['multi_select']])
    elif ptype == 'date':
        return prop['date']['start'] if prop['date'] else None
    elif ptype == 'checkbox':
        return prop['checkbox']
    elif ptype == 'formula':
        f = prop['formula']
        return f.get(f['type'])
    elif ptype == 'status':
        return prop['status']['name'] if prop['status'] else None
    else:
        return str(prop.get(ptype, ''))

def parse_rr(value):
    if value is None or str(value).strip() == '' or str(value).lower() == 'nan':
        return None
    val = str(value).strip().upper().replace('RR', '').strip()
    if val.startswith('-'):
        try:
            return float(val)
        except:
            return None
    if '-' in val:
        parts = val.split('-')
        try:
            nums = [float(p.strip()) for p in parts if p.strip()]
            return sum(nums) / len(nums)
        except:
            return None
    try:
        return float(val)
    except:
        return None

def calc_r(row):
    result = str(row.get('Result', '') or '').strip().lower()
    if result == 'win':
        return row['RR_numeric'] if pd.notna(row['RR_numeric']) else None
    elif result == 'loss':
        return -1.0
    elif result == 'breakeven':
        return 0.0
    else:
        return None

def calc_stats(df_in):
    stats = {}
    r = df_in['R_Result'].dropna()
    if len(r) == 0:
        return stats
    stats['total_trades'] = len(r)
    stats['wins'] = int((r > 0).sum())
    stats['losses'] = int((r < 0).sum())
    stats['breakevens'] = int((r == 0).sum())
    non_breakeven = stats['wins'] + stats['losses']
    stats['win_rate'] = round(stats['wins'] / non_breakeven * 100, 1) if non_breakeven > 0 else 0
    stats['total_r'] = round(r.sum(), 2)
    stats['avg_r'] = round(r.mean(), 2)
    stats['avg_win'] = round(r[r > 0].mean(), 2) if stats['wins'] > 0 else 0
    stats['avg_loss'] = round(r[r < 0].mean(), 2) if stats['losses'] > 0 else 0
    stats['best_trade'] = round(r.max(), 2)
    stats['worst_trade'] = round(r.min(), 2)
    stats['expectancy'] = round(
        (stats['win_rate']/100 * stats['avg_win']) +
        ((1 - stats['win_rate']/100) * abs(stats['avg_loss'])) * -1, 2
    ) if stats['losses'] > 0 else round(stats['avg_win'], 2)
    equity = r.cumsum()
    peak = equity.cummax()
    drawdown = equity - peak
    stats['max_drawdown'] = round(drawdown.min(), 2)
    stats['equity_curve'] = equity.tolist()
    streak = 0
    max_streak = 0
    for val in r:
        if val < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    stats['max_consec_losses'] = max_streak
    return stats

def calc_period_summary(df_in, freq='W'):
    df_temp = df_in.dropna(subset=['Date', 'R_Result']).copy()
    if len(df_temp) == 0:
        return []
    df_temp['period'] = df_temp['Date'].dt.to_period(freq)
    grouped = df_temp.groupby('period')['R_Result'].agg(['count', 'sum'])
    grouped = grouped.sort_index(ascending=False)
    results = []
    for period, row in grouped.iterrows():
        if freq == 'W':
            label = f"{period.start_time.strftime('%b %d')} - {period.end_time.strftime('%b %d')}"
        else:
            label = period.strftime('%B %Y')
        results.append({'label': label, 'trades': int(row['count']), 'total_r': round(row['sum'], 2)})
    return results

def calc_session_stats(df_in, col='3SL Window'):
    if col not in df_in.columns:
        return []
    sessions = ['Asia', 'London', 'New York', 'No Window']
    df_temp = df_in.copy()
    df_temp[col] = df_temp[col].fillna('No Window').replace('', 'No Window')
    results = []
    for session in sessions:
        sub = df_temp[df_temp[col] == session]
        r = sub['R_Result'].dropna()
        n = len(r)
        if n == 0:
            results.append({'session': session, 'exp': 0, 'wr': 0, 'n': 0})
            continue
        wins = int((r > 0).sum())
        losses = int((r < 0).sum())
        non_be = wins + losses
        wr = round(wins / non_be, 2) if non_be > 0 else 0
        exp = round(r.mean(), 3)
        results.append({'session': session, 'exp': exp, 'wr': wr, 'n': n})
    return sorted(results, key=lambda x: x['exp'], reverse=True)

# Load data
with st.spinner("Pulling fresh data from Notion..."):
    raw_trades = get_all_trades()
    rows = []
    for trade in raw_trades:
        props = trade['properties']
        row = {}
        for col_name, col_data in props.items():
            row[col_name] = extract_property(col_data)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['RR_numeric'] = df['RR'].apply(parse_rr)
    df['R_Result'] = df.apply(calc_r, axis=1)

    df_main = df.copy()
    df_main = df_main.sort_values('Date').reset_index(drop=True)

    main_stats = calc_stats(df_main)
    session_stats = calc_session_stats(df_main)
    weekly_summary = calc_period_summary(df_main, freq='W')
    monthly_summary = calc_period_summary(df_main, freq='M')

now = datetime.now().strftime("%B %d, %Y %I:%M %p")

max_abs_exp = max([abs(s['exp']) for s in session_stats]) if session_stats else 1
if max_abs_exp == 0:
    max_abs_exp = 1

# ============ CSS ============
css = """
<style>
  .stApp {
    background:#0a0a0f;
    background-image: radial-gradient(circle at 20% 20%, rgba(74,222,128,0.04), transparent 40%),
                       radial-gradient(circle at 80% 0%, rgba(96,165,250,0.04), transparent 40%);
  }
  .header-title { font-size:1.7em; font-weight:600; color:#fff; letter-spacing:0.5px; }
  .header-sub { color:#666; margin-top:8px; font-size:0.85em; }
  .section-label { font-size:0.7em; font-weight:600; letter-spacing:3px; text-transform:uppercase; color:#555; margin:30px 0 16px; }
  .stat-card { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:16px; padding:22px 14px; text-align:center; }
  .stat-value { font-size:1.5em; font-weight:600; }
  .stat-label { color:#666; font-size:0.68em; margin-top:6px; letter-spacing:0.5px; }
  .divider-line { border:none; border-top:1px solid rgba(255,255,255,0.07); margin:30px 0; }
  .session-bar-track { background:rgba(255,255,255,0.06); border-radius:6px; height:14px; overflow:hidden; }
  .session-bar-fill { height:100%; border-radius:6px; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ============ HEADER ============
st.markdown(f'<div class="header-title">Trading Data</div>', unsafe_allow_html=True)
st.markdown(f'<div class="header-sub">Generated {now} &nbsp;·&nbsp; {main_stats.get("total_trades","—")} Trades</div>', unsafe_allow_html=True)

# ============ PERFORMANCE OVERVIEW ============
st.markdown('<div class="section-label">Performance Overview</div>', unsafe_allow_html=True)

stat_data = [
    ('Total Trades', main_stats.get('total_trades','—'), '#ffffff'),
    ('Win Rate', f"{main_stats.get('win_rate','—')}%", '#4ade80'),
    ('Total R', main_stats.get('total_r','—'), '#ffffff'),
    ('Avg R / Trade', main_stats.get('avg_r','—'), '#ffffff'),
    ('Expectancy', main_stats.get('expectancy','—'), '#ffffff'),
    ('Avg Win', main_stats.get('avg_win','—'), '#4ade80'),
    ('Avg Loss', main_stats.get('avg_loss','—'), '#f87171'),
    ('Best Trade', main_stats.get('best_trade','—'), '#4ade80'),
    ('Worst Trade', main_stats.get('worst_trade','—'), '#f87171'),
    ('Max Drawdown', main_stats.get('max_drawdown','—'), '#f87171'),
    ('Max Consec. Losses', main_stats.get('max_consec_losses','—'), '#f87171'),
    ('Wins', main_stats.get('wins','—'), '#4ade80'),
    ('Losses', main_stats.get('losses','—'), '#f87171'),
    ('Breakevens', main_stats.get('breakevens','—'), '#60a5fa'),
]

cols_per_row = 7
for i in range(0, len(stat_data), cols_per_row):
    row_data = stat_data[i:i+cols_per_row]
    cols = st.columns(len(row_data))
    for col, (label, value, color) in zip(cols, row_data):
        col.markdown(
            f'<div class="stat-card"><div class="stat-value" style="color:{color}">{value}</div><div class="stat-label">{label}</div></div>',
            unsafe_allow_html=True
        )

# ============ CHARTS ============
st.markdown('<div class="section-label">Charts</div>', unsafe_allow_html=True)

eq_fig = go.Figure()
eq_fig.add_trace(go.Scatter(y=main_stats['equity_curve'], mode='lines+markers',
    line=dict(color='#4ade80', width=2.5), marker=dict(size=5, color='#4ade80'),
    fill='tozeroy', fillcolor='rgba(74,222,128,0.08)'))
eq_fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    height=340, margin=dict(l=40, r=20, t=40, b=40), font=dict(color='#8a8a99', size=11), showlegend=False,
    xaxis=dict(gridcolor='rgba(255,255,255,0.05)', zeroline=False),
    yaxis=dict(gridcolor='rgba(255,255,255,0.05)', zeroline=False),
    title=dict(text='Equity Curve', font=dict(color='#eee', size=15)))
st.plotly_chart(eq_fig, use_container_width=True)

labels = ['Win', 'Loss', 'Breakeven']
values = [main_stats.get('wins',0), main_stats.get('losses',0), main_stats.get('breakevens',0)]
colors = ['#4ade80', '#f87171', '#60a5fa']
donut_fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.65,
    marker=dict(colors=colors), textinfo='label+percent', textfont=dict(size=11, color='#ccc')))
donut_fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    height=340, margin=dict(l=20, r=20, t=40, b=20), font=dict(color='#8a8a99', size=11), showlegend=False,
    title=dict(text='Result Distribution', font=dict(color='#eee', size=15)))
st.plotly_chart(donut_fig, use_container_width=True)

# ============ DIVIDER ============
st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

# ============ 3SL WINDOW ============
st.markdown('<div class="section-label">3SL Window</div>', unsafe_allow_html=True)

header_cols = st.columns([1, 3, 0.7, 0.6, 0.4])
header_cols[0].markdown('<span style="color:#666;font-size:0.75em;">Value</span>', unsafe_allow_html=True)
header_cols[1].markdown('<span style="color:#666;font-size:0.75em;">Chart</span>', unsafe_allow_html=True)
header_cols[2].markdown('<span style="color:#666;font-size:0.75em;">Exp</span>', unsafe_allow_html=True)
header_cols[3].markdown('<span style="color:#666;font-size:0.75em;">WR</span>', unsafe_allow_html=True)
header_cols[4].markdown('<span style="color:#666;font-size:0.75em;">N</span>', unsafe_allow_html=True)

for s in session_stats:
    bar_pct = round(abs(s['exp']) / max_abs_exp * 100, 1)
    bar_color = '#4ade80' if s['exp'] >= 0 else '#f87171'
    row_cols = st.columns([1, 3, 0.7, 0.6, 0.4])
    row_cols[0].markdown(f'<span style="color:#60a5fa;font-weight:500;">{s["session"]}</span>', unsafe_allow_html=True)
    row_cols[1].markdown(
        f'<div class="session-bar-track"><div class="session-bar-fill" style="width:{bar_pct}%;background:{bar_color};"></div></div>',
        unsafe_allow_html=True
    )
    row_cols[2].markdown(f'<span style="color:{bar_color};font-weight:600;">{s["exp"]}</span>', unsafe_allow_html=True)
    row_cols[3].markdown(f'<span style="color:#aaa;">{s["wr"]}</span>', unsafe_allow_html=True)
    row_cols[4].markdown(f'<span style="color:#666;">{s["n"]}</span>', unsafe_allow_html=True)

# ============ WEEKLY / MONTHLY SUMMARY ============
st.markdown('<hr class="divider-line">', unsafe_allow_html=True)
st.markdown('<div class="section-label">Monthly Summary</div>', unsafe_allow_html=True)

mh_cols = st.columns([2, 1, 1])
mh_cols[0].markdown('<span style="color:#666;font-size:0.75em;">Period</span>', unsafe_allow_html=True)
mh_cols[1].markdown('<span style="color:#666;font-size:0.75em;">Trades</span>', unsafe_allow_html=True)
mh_cols[2].markdown('<span style="color:#666;font-size:0.75em;">Total R</span>', unsafe_allow_html=True)

for m in monthly_summary:
    r_color = '#4ade80' if m['total_r'] >= 0 else '#f87171'
    row = st.columns([2, 1, 1])
    row[0].markdown(f'<span style="color:#ddd;">{m["label"]}</span>', unsafe_allow_html=True)
    row[1].markdown(f'<span style="color:#aaa;">{m["trades"]}</span>', unsafe_allow_html=True)
    row[2].markdown(f'<span style="color:{r_color};font-weight:600;">{m["total_r"]}</span>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Weekly Summary</div>', unsafe_allow_html=True)

wh_cols = st.columns([2, 1, 1])
wh_cols[0].markdown('<span style="color:#666;font-size:0.75em;">Period</span>', unsafe_allow_html=True)
wh_cols[1].markdown('<span style="color:#666;font-size:0.75em;">Trades</span>', unsafe_allow_html=True)
wh_cols[2].markdown('<span style="color:#666;font-size:0.75em;">Total R</span>', unsafe_allow_html=True)

for w in weekly_summary:
    r_color = '#4ade80' if w['total_r'] >= 0 else '#f87171'
    row = st.columns([2, 1, 1])
    row[0].markdown(f'<span style="color:#ddd;">{w["label"]}</span>', unsafe_allow_html=True)
    row[1].markdown(f'<span style="color:#aaa;">{w["trades"]}</span>', unsafe_allow_html=True)
    row[2].markdown(f'<span style="color:{r_color};font-weight:600;">{w["total_r"]}</span>', unsafe_allow_html=True)
