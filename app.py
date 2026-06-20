import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Trading Data", layout="wide", initial_sidebar_state="collapsed")

# ============================================================
# SETTINGS
# ============================================================

NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ============================================================
# DATA FUNCTIONS
# ============================================================

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

def calc_stats(df_in, label=""):
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

# ============================================================
# LOAD DATA
# ============================================================

st.title("📈 Trading Data")

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
    df['Type of Trade'] = df['Type of Trade'].astype(str).str.strip()
    df['Rules Followed? Y/N'] = df['Rules Followed? Y/N'].astype(str).str.strip()

    df_main = df.copy()
    df_forward = df[df['Type of Trade'].str.lower().str.contains('forward', na=False)].copy()
    df_rules_no = df[df['Rules Followed? Y/N'].str.lower().str.startswith('no', na=False)].copy()

    df_main = df_main.sort_values('Date').reset_index(drop=True)

    main_stats = calc_stats(df_main)
    session_stats = calc_session_stats(df_main)

st.caption(f"Generated {datetime.now().strftime('%B %d, %Y %I:%M %p')} · {main_stats.get('total_trades','—')} Trades")

# ============================================================
# PERFORMANCE OVERVIEW
# ============================================================

st.subheader("Performance Overview")
cols = st.columns(7)
cols[0].metric("Total Trades", main_stats.get('total_trades','—'))
cols[1].metric("Win Rate", f"{main_stats.get('win_rate','—')}%")
cols[2].metric("Total R", main_stats.get('total_r','—'))
cols[3].metric("Avg R/Trade", main_stats.get('avg_r','—'))
cols[4].metric("Expectancy", main_stats.get('expectancy','—'))
cols[5].metric("Avg Win", main_stats.get('avg_win','—'))
cols[6].metric("Avg Loss", main_stats.get('avg_loss','—'))

cols2 = st.columns(7)
cols2[0].metric("Best Trade", main_stats.get('best_trade','—'))
cols2[1].metric("Worst Trade", main_stats.get('worst_trade','—'))
cols2[2].metric("Max Drawdown", main_stats.get('max_drawdown','—'))
cols2[3].metric("Max Consec. Losses", main_stats.get('max_consec_losses','—'))
cols2[4].metric("Wins", main_stats.get('wins','—'))
cols2[5].metric("Losses", main_stats.get('losses','—'))
cols2[6].metric("Breakevens", main_stats.get('breakevens','—'))

# ============================================================
# CHARTS
# ============================================================

st.subheader("Charts")

if main_stats:
    eq_fig = go.Figure()
    eq_fig.add_trace(go.Scatter(
        y=main_stats['equity_curve'], mode='lines+markers',
        line=dict(color='#4ade80', width=2.5),
        fill='tozeroy', fillcolor='rgba(74,222,128,0.08)'))
    eq_fig.update_layout(template='plotly_dark', height=350, title="Equity Curve")
    st.plotly_chart(eq_fig, use_container_width=True)

    donut_labels = ['Win', 'Loss', 'Breakeven']
    donut_values = [main_stats.get('wins',0), main_stats.get('losses',0), main_stats.get('breakevens',0)]
    donut_fig = go.Figure(go.Pie(labels=donut_labels, values=donut_values, hole=0.65,
        marker=dict(colors=['#4ade80', '#f87171', '#60a5fa'])))
    donut_fig.update_layout(template='plotly_dark', height=350, title="Result Distribution")
    st.plotly_chart(donut_fig, use_container_width=True)

# ============================================================
# 3SL WINDOW
# ============================================================

st.subheader("3SL Window")
session_df = pd.DataFrame(session_stats)
if not session_df.empty:
    st.dataframe(session_df, use_container_width=True, hide_index=True)
