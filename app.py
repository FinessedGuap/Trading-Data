import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import calendar as cal_module

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

def parse_r_result(value):
    if value is None or str(value).strip() == '' or str(value).lower() == 'nan':
        return None
    val = str(value).strip().upper().replace('RR', '').replace('+', '').strip()
    try:
        return float(val)
    except:
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

def calc_daily_r(df_in):
    df_temp = df_in.dropna(subset=['Date', 'R_Result']).copy()
    df_temp['day'] = df_temp['Date'].dt.date
    grouped = df_temp.groupby('day')['R_Result'].agg(['count', 'sum'])
    daily = {}
    for day, row in grouped.iterrows():
        daily[day] = {'trades': int(row['count']), 'total_r': round(row['sum'], 2)}
    return daily

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
    df['R_Result'] = df['R Result'].apply(parse_r_result)

    df_main = df.copy()
    df_main = df_main.sort_values('Date').reset_index(drop=True)

    main_stats = calc_stats(df_main)
    session_stats = calc_session_stats(df_main)
    daily_r = calc_daily_r(df_main)

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
  .cal-header { color:#666; font-size:0.75em; text-align:center; letter-spacing:1px; text-transform:uppercase; padding:8px 0; }
  .cal-day { border-radius:10px; padding:10px 6px; text-align:center; min-height:80px; }
  .cal-day-num { color:#555; font-size:0.8em; }
  .cal-day-r { font-size:1.1em; font-weight:700; margin-top:8px; }
  .cal-day-trades { color:#666; font-size:0.65em; margin-top:2px; }
  .cal-day-empty { background:rgba(255,255,255,0.015); }
  .cal-day-win { background:rgba(74,222,128,0.12); border:1px solid rgba(74,222,128,0.25); }
  .cal-day-loss { background:rgba(248,113,113,0.12); border:1px solid rgba(248,113,113,0.25); }
  .cal-week-summary { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:10px 6px; text-align:center; min-height:80px; }
  .cal-week-label { color:#888; font-size:0.7em; font-weight:600; }
  .cal-week-r { font-size:1.2em; font-weight:700; margin-top:8px; }
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

# ============ MONTHLY CALENDAR ============
st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

today = datetime.now()
month_total_r = sum(v['total_r'] for k, v in daily_r.items() if k.month == today.month and k.year == today.year)
month_color = '#4ade80' if month_total_r >= 0 else '#f87171'
st.markdown(f'<div class="section-label">Calendar — {today.strftime("%B %Y")} &nbsp;·&nbsp; Total R: <span style="color:{month_color}">{round(month_total_r,2)}</span></div>', unsafe_allow_html=True)

cal_module.setfirstweekday(cal_module.MONDAY)
month_matrix = cal_module.monthcalendar(today.year, today.month)

day_header_cols = st.columns(8)
for i, d in enumerate(['Mo','Tu','We','Th','Fr','Sa','Su']):
    day_header_cols[i].markdown(f'<div class="cal-header">{d}</div>', unsafe_allow_html=True)
day_header_cols[7].markdown('<div class="cal-header">Week</div>', unsafe_allow_html=True)

for week_num, week in enumerate(month_matrix):
    week_cols = st.columns(8)
    week_total = 0
    week_trades = 0
    for i, day_num in enumerate(week):
        if day_num == 0:
            week_cols[i].markdown('<div class="cal-day cal-day-empty"></div>', unsafe_allow_html=True)
        else:
            day_date = datetime(today.year, today.month, day_num).date()
            day_data = daily_r.get(day_date)
            if day_data:
                week_total += day_data['total_r']
                week_trades += day_data['trades']
                r_val = day_data['total_r']
                css_class = 'cal-day-win' if r_val >= 0 else 'cal-day-loss'
                r_color = '#4ade80' if r_val >= 0 else '#f87171'
                sign = '+' if r_val > 0 else ''
                week_cols[i].markdown(
                    f'<div class="cal-day {css_class}"><div class="cal-day-num">{day_num}</div>'
                    f'<div class="cal-day-r" style="color:{r_color}">{sign}{r_val}R</div>'
                    f'<div class="cal-day-trades">{day_data["trades"]} trades</div></div>',
                    unsafe_allow_html=True
                )
            else:
                week_cols[i].markdown(
                    f'<div class="cal-day cal-day-empty"><div class="cal-day-num">{day_num}</div></div>',
                    unsafe_allow_html=True
                )
    wk_color = '#4ade80' if week_total >= 0 else '#f87171'
    wk_sign = '+' if week_total > 0 else ''
    week_cols[7].markdown(
        f'<div class="cal-week-summary"><div class="cal-week-label">Week {week_num+1}</div>'
        f'<div class="cal-week-r" style="color:{wk_color}">{wk_sign}{round(week_total,2)}R</div>'
        f'<div class="cal-day-trades">{week_trades} trades</div></div>',
        unsafe_allow_html=True
    )
