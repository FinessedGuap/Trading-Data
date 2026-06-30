import streamlit as st
import requests
import pandas as pd
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

def safe_parse_date(x):
    if pd.isna(x) or x is None or str(x).strip() == '':
        return pd.NaT
    try:
        from dateutil import parser as _dateutil_parser
        parsed = _dateutil_parser.isoparse(str(x))
        ts = pd.Timestamp(parsed)
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        return ts
    except Exception:
        try:
            from dateutil import parser as _dateutil_parser
            parsed = _dateutil_parser.parse(str(x))
            ts = pd.Timestamp(parsed)
            if ts.tzinfo is not None:
                ts = ts.tz_localize(None)
            return ts
        except Exception:
            return pd.NaT

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
    df['Date'] = df['Date'].apply(safe_parse_date)
    df['R_Result'] = df['R Result'].apply(parse_r_result)

    df_main = df.copy()
    df_main = df_main.sort_values('Date').reset_index(drop=True)

    main_stats = calc_stats(df_main)
    session_stats = calc_session_stats(df_main)
    daily_r = calc_daily_r(df_main)

max_abs_exp = max([abs(s['exp']) for s in session_stats]) if session_stats else 1
if max_abs_exp == 0:
    max_abs_exp = 1

css = """
<style>
  .stApp { background:#08090d; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }
  .header-title { font-size:1.6em; font-weight:700; color:#fff; }
  .section-label { font-size:0.7em; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; color:#6b7280; margin:32px 0 12px; }
  .kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:1px; background:#1a1c22; border:1px solid #1a1c22; border-radius:8px; overflow:hidden; margin-bottom:16px; }
  .kpi-tile { background:#0d0f14; padding:16px 14px; }
  .kpi-label { color:#6b7280; font-size:10px; letter-spacing:0.6px; text-transform:uppercase; margin-bottom:6px; }
  .kpi-value { color:#fff; font-size:20px; font-weight:600; }
  .panel { background:#0d0f14; border:1px solid #1a1c22; border-radius:8px; padding:18px; margin-bottom:16px; }
  .panel-title { color:#fff; font-size:13px; font-weight:600; margin-bottom:14px; }
  .session-row { display:grid; grid-template-columns:90px 1fr 60px 50px 36px; gap:12px; align-items:center; padding:9px 0; border-bottom:1px solid #15171d; }
  .session-row:last-child { border-bottom:none; }
  .session-header-row { display:grid; grid-template-columns:90px 1fr 60px 50px 36px; gap:12px; padding-bottom:10px; margin-bottom:4px; border-bottom:1px solid #1a1c22; }
  .session-bar-track { background:#15171d; border-radius:4px; height:10px; overflow:hidden; }
  .session-bar-fill { height:100%; border-radius:4px; }
  .cal-header { color:#6b7280; font-size:10px; text-align:center; text-transform:uppercase; padding:6px 0; }
  .cal-day-num { color:#6b7280; font-size:10px; text-align:center; }
  .cal-week-summary { background:#0d0f14; border:1px solid #1a1c22; border-radius:6px; padding:8px 4px; text-align:center; min-height:64px; }
  .cal-week-label { color:#6b7280; font-size:9px; font-weight:600; }
  .cal-week-r { font-size:13px; font-weight:700; margin-top:6px; }
  .cal-day-trades { color:#4b5360; font-size:9px; margin-top:2px; }
  div[data-testid="stButton"] button { width:100%; min-height:64px; border-radius:6px; white-space:pre-line; line-height:1.3; font-size:11px; }
  div[data-testid="stButton"] button[kind="primary"] { background:#0e2417 !important; border:1px solid #1a3a26 !important; color:#4ade80 !important; }
  div[data-testid="stButton"] button[kind="secondary"] { background:#2a1414 !important; border:1px solid #3a1a1a !important; color:#f87171 !important; }
  .trade-detail-card { background:#0d0f14; border:1px solid #1a1c22; border-radius:6px; padding:12px 16px; margin-bottom:8px; font-size:13px; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

st.markdown(f'<div class="header-title">Trading Data</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Performance Overview</div>', unsafe_allow_html=True)
stat_data = [
    ('Total R', main_stats.get('total_r','—'), '#fff'),
    ('Win Rate', f"{main_stats.get('win_rate','—')}%", '#fff'),
    ('Avg RR', main_stats.get('avg_r','—'), '#fff'),
    ('Max Losing Streak', main_stats.get('max_consec_losses','—'), '#fff'),
]
st.markdown(
    '<div class="kpi-grid">' +
    "".join([f'<div class="kpi-tile"><div class="kpi-label">{l}</div><div class="kpi-value" style="color:{c}">{v}</div></div>' for l,v,c in stat_data]) +
    '</div>',
    unsafe_allow_html=True
)
stat_data2 = [
    ('Wins', main_stats.get('wins','—'), '#4ade80'),
    ('Losses', main_stats.get('losses','—'), '#f87171'),
    ('Best Trade', main_stats.get('best_trade','—'), '#4ade80'),
    ('Max Drawdown', main_stats.get('max_drawdown','—'), '#f87171'),
]
st.markdown(
    '<div class="kpi-grid">' +
    "".join([f'<div class="kpi-tile"><div class="kpi-label">{l}</div><div class="kpi-value" style="color:{c}">{v}</div></div>' for l,v,c in stat_data2]) +
    '</div>',
    unsafe_allow_html=True
)

st.markdown('<div class="section-label">Equity Curve</div>', unsafe_allow_html=True)
eq_points = main_stats.get('equity_curve', [])
if eq_points:
    eq_max = max(eq_points)
    eq_min = min(min(eq_points), 0)
    eq_range = (eq_max - eq_min) if (eq_max - eq_min) != 0 else 1
    svg_w, svg_h = 800, 160
    n = len(eq_points)
    pts = []
    for i, v in enumerate(eq_points):
        x = (i / (n - 1)) * svg_w if n > 1 else 0
        y = svg_h - ((v - eq_min) / eq_range) * (svg_h - 20) - 10
        pts.append(f"{x:.1f},{y:.1f}")
    polyline = " ".join(pts)
    eq_svg = f"""
    <svg viewBox="0 0 {svg_w} {svg_h}" style="width:100%; height:160px; display:block;">
      <line x1="0" y1="40" x2="{svg_w}" y2="40" stroke="#1a1c22" stroke-width="1"/>
      <line x1="0" y1="80" x2="{svg_w}" y2="80" stroke="#1a1c22" stroke-width="1"/>
      <line x1="0" y1="120" x2="{svg_w}" y2="120" stroke="#1a1c22" stroke-width="1"/>
      <polyline points="{polyline}" fill="none" stroke="#5b9bf5" stroke-width="2"/>
    </svg>
    """
    st.markdown(f'<div class="panel">{eq_svg}</div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">3SL Window</div>', unsafe_allow_html=True)
session_rows_html = ""
for s in session_stats:
    bar_pct = round(abs(s['exp']) / max_abs_exp * 100, 1)
    bar_color = '#4ade80' if s['exp'] >= 0 else '#f87171'
    session_rows_html += (
        f'<div class="session-row">'
        f'<span style="color:#5b9bf5;font-weight:600;font-size:12px;">{s["session"]}</span>'
        f'<div class="session-bar-track"><div class="session-bar-fill" style="width:{bar_pct}%;background:{bar_color};"></div></div>'
        f'<span style="color:{bar_color};font-weight:600;font-size:12px;">{s["exp"]}</span>'
        f'<span style="color:#9ca3af;font-size:12px;">{s["wr"]}</span>'
        f'<span style="color:#6b7280;font-size:12px;">{s["n"]}</span>'
        f'</div>'
    )
st.markdown(
    f'<div class="panel">'
    f'<div class="session-header-row">'
    f'<span style="color:#6b7280;font-size:10px;text-transform:uppercase;">Value</span>'
    f'<span style="color:#6b7280;font-size:10px;text-transform:uppercase;">Chart</span>'
    f'<span style="color:#6b7280;font-size:10px;text-transform:uppercase;">Exp</span>'
    f'<span style="color:#6b7280;font-size:10px;text-transform:uppercase;">WR</span>'
    f'<span style="color:#6b7280;font-size:10px;text-transform:uppercase;">N</span>'
    f'</div>'
    f'{session_rows_html}'
    f'</div>',
    unsafe_allow_html=True
)

today = datetime.now()
month_total_r = sum(v['total_r'] for k, v in daily_r.items() if k.month == today.month and k.year == today.year)
month_color = '#4ade80' if month_total_r >= 0 else '#f87171'
month_sign = '+' if month_total_r > 0 else ''
st.markdown(
    f'<div class="panel" style="text-align:center;">'
    f'<span style="font-size:1.1em;font-weight:700;color:#fff;">Monthly Total R: <span style="color:{month_color};">{month_sign}{round(month_total_r,2)}</span></span>'
    f'</div>',
    unsafe_allow_html=True
)

cal_module.setfirstweekday(cal_module.MONDAY)
month_matrix = cal_module.monthcalendar(today.year, today.month)
day_header_cols = st.columns(8)
for i, d in enumerate(['Mo','Tu','We','Th','Fr','Sa','Su']):
    day_header_cols[i].markdown(f'<div class="cal-header">{d}</div>', unsafe_allow_html=True)
day_header_cols[7].markdown('<div class="cal-header">Week</div>', unsafe_allow_html=True)

if 'selected_day' not in st.session_state:
    st.session_state.selected_day = None

for week_num, week in enumerate(month_matrix):
    week_cols = st.columns(8)
    week_total = 0
    week_trades = 0
    for i, day_num in enumerate(week):
        if day_num == 0:
            week_cols[i].markdown('<div style="min-height:64px;"></div>', unsafe_allow_html=True)
        else:
            day_date = datetime(today.year, today.month, day_num).date()
            day_data = daily_r.get(day_date)
            if day_data:
                week_total += day_data['total_r']
                week_trades += day_data['trades']
                r_val = day_data['total_r']
                sign = '+' if r_val > 0 else ''
                btn_type = "primary" if r_val >= 0 else "secondary"
                if week_cols[i].button(f"{day_num}\n{sign}{r_val}R", key=f"day_{day_date}", use_container_width=True, type=btn_type):
                    st.session_state.selected_day = day_date
            else:
                week_cols[i].markdown(f'<div style="min-height:64px;display:flex;align-items:center;justify-content:center;"><div class="cal-day-num">{day_num}</div></div>', unsafe_allow_html=True)
    wk_color = '#4ade80' if week_total >= 0 else '#f87171'
    wk_sign = '+' if week_total > 0 else ''
    week_cols[7].markdown(
        f'<div class="cal-week-summary"><div class="cal-week-label">Week {week_num+1}</div>'
        f'<div class="cal-week-r" style="color:{wk_color}">{wk_sign}{round(week_total,2)}R</div>'
        f'<div class="cal-day-trades">{week_trades} trades</div></div>',
        unsafe_allow_html=True
    )

if st.session_state.selected_day:
    sel_day = st.session_state.selected_day
    df_temp = df_main.dropna(subset=['Date', 'R_Result']).copy()
    df_temp['day'] = df_temp['Date'].dt.date
    day_trades = df_temp[df_temp['day'] == sel_day]
    st.markdown(f'<div class="section-label">Trades on {sel_day.strftime("%B %d, %Y")}</div>', unsafe_allow_html=True)
    for _, trade in day_trades.iterrows():
        r_val = trade['R_Result']
        color = '#4ade80' if r_val > 0 else ('#f87171' if r_val < 0 else '#5b9bf5')
        label = 'Win' if r_val > 0 else ('Loss' if r_val < 0 else 'Breakeven')
        sign = '+' if r_val > 0 else ''
        pair = trade.get('Pair', '—')
        st.markdown(
            f'<div class="trade-detail-card"><span style="color:{color};font-weight:600;">{label}</span> '
            f'<span style="color:#6b7280;">· {pair}</span> '
            f'<span style="color:{color};font-weight:600;float:right;">{sign}{r_val}R</span></div>',
            unsafe_allow_html=True
        )
    if st.button("Close"):
        st.session_state.selected_day = None
        st.rerun()
