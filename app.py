import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Trading Data", layout="wide", initial_sidebar_state="collapsed")
st.markdown("<style>.element-container{overflow:visible;}</style>", unsafe_allow_html=True)
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

def stat_card(label, value, color="#ffffff"):
    return f"""
    <div class="stat-card">
        <div class="stat-value" style="color:{color}">{value}</div>
        <div class="stat-label">{label}</div>
    </div>"""

def make_chart(fig, title, subtitle=""):
    fig.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=340, margin=dict(l=40, r=20, t=20, b=40),
        font=dict(color='#8a8a99', size=11), showlegend=False,
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', zeroline=False),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', zeroline=False),
    )
    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    subtitle_html = f'<p class="chart-subtitle">{subtitle}</p>' if subtitle else ''
    return f"""
    <div class="chart-card">
        <div class="chart-title">{title}</div>
        {subtitle_html}
        {chart_html}
    </div>"""

def make_donut(stats):
    if not stats:
        return ""
    labels = ['Win', 'Loss', 'Breakeven']
    values = [stats.get('wins',0), stats.get('losses',0), stats.get('breakevens',0)]
    colors = ['#4ade80', '#f87171', '#60a5fa']
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.65,
        marker=dict(colors=colors), textinfo='label+percent', textfont=dict(size=11, color='#ccc')))
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=340, margin=dict(l=20, r=20, t=20, b=20), font=dict(color='#8a8a99', size=11), showlegend=False)
    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    return f"""
    <div class="chart-card">
        <div class="chart-title">Result Distribution</div>
        <p class="chart-subtitle">Win / Loss / Breakeven breakdown</p>
        {chart_html}
    </div>"""

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

eq_fig = go.Figure()
eq_fig.add_trace(go.Scatter(y=main_stats['equity_curve'], mode='lines+markers',
    line=dict(color='#4ade80', width=2.5), marker=dict(size=5, color='#4ade80'),
    fill='tozeroy', fillcolor='rgba(74,222,128,0.08)'))
eq_html = make_chart(eq_fig, 'Equity Curve', f'Cumulative R across {main_stats["total_trades"]} trades')
donut_html = make_donut(main_stats)

now = datetime.now().strftime("%B %d, %Y %I:%M %p")

max_abs_exp = max([abs(s['exp']) for s in session_stats]) if session_stats else 1
if max_abs_exp == 0:
    max_abs_exp = 1

session_rows_html = ""
for s in session_stats:
    bar_pct = round(abs(s['exp']) / max_abs_exp * 100, 1)
    bar_color = '#4ade80' if s['exp'] >= 0 else '#f87171'
    session_rows_html += f"""
    <div class="session-row">
        <div class="session-value">{s['session']}</div>
        <div class="session-bar-track"><div class="session-bar-fill" style="width:{bar_pct}%; background:{bar_color}"></div></div>
        <div class="session-exp" style="color:{bar_color}">{s['exp']}</div>
        <div class="session-wr">{s['wr']}</div>
        <div class="session-n">{s['n']}</div>
    </div>"""

full_html = f"""
<style>
  .stApp {{
    background:#0a0a0f;
    background-image: radial-gradient(circle at 20% 20%, rgba(74,222,128,0.04), transparent 40%),
                       radial-gradient(circle at 80% 0%, rgba(96,165,250,0.04), transparent 40%);
  }}
  * {{ box-sizing:border-box; }}
  .report-wrap {{ color:#d4d4dc; font-family:'Segoe UI',system-ui,sans-serif; max-width:1300px; margin:0 auto; }}
  .header {{ padding:20px 0 30px; margin-bottom:20px; }}
  .header h1 {{ font-size:1.7em; font-weight:600; color:#fff; letter-spacing:0.5px; }}
  .header p {{ color:#666; margin-top:8px; font-size:0.85em; }}
  .section-label {{ font-size:0.7em; font-weight:600; letter-spacing:3px; text-transform:uppercase; color:#555; margin:30px 0 16px; }}
  .stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:14px; margin-bottom:30px; }}
  .stat-card {{ background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:16px; padding:22px 14px; text-align:center; }}
  .stat-value {{ font-size:1.5em; font-weight:600; }}
  .stat-label {{ color:#666; font-size:0.68em; margin-top:6px; letter-spacing:0.5px; }}
  .chart-card {{ background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:18px; padding:26px; margin-bottom:16px; }}
  .chart-title {{ font-size:1.05em; font-weight:600; color:#eee; margin-bottom:4px; }}
  .chart-subtitle {{ font-size:0.8em; color:#666; margin-bottom:14px; }}
  .divider {{ border:none; border-top:1px solid rgba(255,255,255,0.07); margin:30px 0; }}
  .session-card {{ background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:18px; padding:8px 22px; }}
  .session-header {{ display:grid; grid-template-columns: 100px 1fr 70px 60px 40px; gap:16px; padding:14px 0 10px; color:#666; font-size:0.75em; letter-spacing:0.5px; border-bottom:1px solid rgba(255,255,255,0.07); }}
  .session-row {{ display:grid; grid-template-columns: 100px 1fr 70px 60px 40px; gap:16px; padding:14px 0; align-items:center; border-bottom:1px solid rgba(255,255,255,0.04); }}
  .session-row:last-child {{ border-bottom:none; }}
  .session-value {{ color:#60a5fa; font-size:0.9em; font-weight:500; }}
  .session-bar-track {{ background:rgba(255,255,255,0.06); border-radius:6px; height:14px; overflow:hidden; }}
  .session-bar-fill {{ height:100%; border-radius:6px; }}
  .session-exp {{ font-size:0.9em; font-weight:600; text-align:right; }}
  .session-wr {{ font-size:0.85em; color:#aaa; text-align:right; }}
  .session-n {{ font-size:0.85em; color:#666; text-align:right; }}
</style>

<div class="report-wrap">
<div class="header">
  <h1>Trading Data</h1>
  <p>Generated {now} &nbsp;·&nbsp; {main_stats.get('total_trades','—')} Trades</p>
</div>

<div class="section-label">Performance Overview</div>
<div class="stats-grid">
  {stat_card('Total Trades', main_stats.get('total_trades','—'))}
  {stat_card('Win Rate', f"{main_stats.get('win_rate','—')}%", '#4ade80')}
  {stat_card('Total R', main_stats.get('total_r','—'))}
  {stat_card('Avg R / Trade', main_stats.get('avg_r','—'))}
  {stat_card('Expectancy', main_stats.get('expectancy','—'))}
  {stat_card('Avg Win', main_stats.get('avg_win','—'), '#4ade80')}
  {stat_card('Avg Loss', main_stats.get('avg_loss','—'), '#f87171')}
  {stat_card('Best Trade', main_stats.get('best_trade','—'), '#4ade80')}
  {stat_card('Worst Trade', main_stats.get('worst_trade','—'), '#f87171')}
  {stat_card('Max Drawdown', main_stats.get('max_drawdown','—'), '#f87171')}
  {stat_card('Max Consec. Losses', main_stats.get('max_consec_losses','—'), '#f87171')}
  {stat_card('Wins', main_stats.get('wins','—'), '#4ade80')}
  {stat_card('Losses', main_stats.get('losses','—'), '#f87171')}
  {stat_card('Breakevens', main_stats.get('breakevens','—'), '#60a5fa')}
</div>

<div class="section-label">Charts</div>
{eq_html}
{donut_html}

<hr class="divider">

<div class="section-label">3SL Window</div>
<div class="session-card">
    <div class="session-header">
        <div class="session-value">Value</div>
        <div>Chart</div>
        <div class="session-exp">Exp</div>
        <div class="session-wr">WR</div>
        <div class="session-n">N</div>
    </div>
    {session_rows_html}
</div>
</div>
"""

st.markdown(full_html, unsafe_allow_html=True)
