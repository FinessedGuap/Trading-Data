import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar as cal_module
import math

st.set_page_config(page_title="Overall Data", layout="wide", initial_sidebar_state="collapsed")

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
        return [x['name'] for x in prop['multi_select']]
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

def extract_property_str(prop):
    val = extract_property(prop)
    if isinstance(val, list):
        return ', '.join(val) if val else None
    return val

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
            ts = ts.tz_convert('Australia/Sydney').tz_localize(None)
        return ts
    except Exception:
        try:
            from dateutil import parser as _dateutil_parser
            parsed = _dateutil_parser.parse(str(x))
            ts = pd.Timestamp(parsed)
            if ts.tzinfo is not None:
                ts = ts.tz_convert('Australia/Sydney').tz_localize(None)
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
    stats['expectancy'] = round(r.sum() / len(r), 2)
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
        exp = round(r.sum() / len(r), 3)
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

def get_day_trades(df_in, day_date):
    df_temp = df_in.dropna(subset=['Date', 'R_Result']).copy()
    df_temp['day'] = df_temp['Date'].dt.date
    return df_temp[df_temp['day'] == day_date]

def breakdown_by_col(df_in, col, min_trades=2):
    if col not in df_in.columns:
        return []
    temp = df_in.dropna(subset=['R_Result', col]).copy()
    temp = temp[temp[col].notna() & (temp[col] != '') & (temp[col] != 'NA') & (temp[col] != 'N/A')]
    results = []
    for val, grp in temp.groupby(col):
        r = grp['R_Result'].dropna()
        n = len(r)
        if n < min_trades:
            continue
        wins = int((r > 0).sum())
        losses = int((r < 0).sum())
        non_be = wins + losses
        wr = round(wins / non_be * 100, 1) if non_be > 0 else 0
        exp = round(r.sum() / n, 2)
        results.append({'label': str(val), 'wr': wr, 'exp': exp, 'n': n})
    return sorted(results, key=lambda x: x['exp'], reverse=True)

def get_best(df_in, col):
    data = breakdown_by_col(df_in, col, min_trades=2)
    if not data:
        return None
    return data[0]

def generate_checklist(df_in, session_stats):
    items = []
    col_map = {
        'Entry Model': 'entry model',
        'Entry Model Timeframe': 'timeframe',
        'Double Confirmation': 'double confirmation',
        'Target': 'target',
        'Stop Loss Logic': 'stop loss',
        'Entry + Confirmation': 'rejection candle',
        'Trade Quality Rating': 'trade quality',
    }
    for col, label in col_map.items():
        best = get_best(df_in, col)
        if best and best['exp'] > 0:
            items.append({
                'label': f"Use {best['label']} for {label}",
                'detail': f"{best['exp']}R avg · {best['wr']}% WR · {best['n']} trades",
                'type': 'green'
            })
    if session_stats:
        best_s = max(session_stats, key=lambda x: x['exp'])
        worst_s = min(session_stats, key=lambda x: x['exp'])
        if best_s['exp'] > 0:
            items.append({
                'label': f"Trade {best_s['session']} session",
                'detail': f"{best_s['exp']}R avg · {round(best_s['wr']*100)}% WR · {best_s['n']} trades",
                'type': 'green'
            })
        if worst_s['exp'] < 0 or worst_s['wr'] < 0.35:
            items.append({
                'label': f"Avoid {worst_s['session']} session",
                'detail': f"{worst_s['exp']}R avg · {round(worst_s['wr']*100)}% WR · {worst_s['n']} trades",
                'type': 'red'
            })
    if 'Hour' in df_in.columns:
        best_h = get_best(df_in, 'Hour')
        if best_h and best_h['exp'] > 0:
            items.append({
                'label': f"Best time to trade: {best_h['label']}",
                'detail': f"{best_h['exp']}R avg · {best_h['wr']}% WR · {best_h['n']} trades",
                'type': 'green'
            })
    avoid_cols = ['Entry Model', 'Stop Loss Logic', 'Target']
    for col in avoid_cols:
        data = breakdown_by_col(df_in, col, min_trades=2)
        if data:
            worst = data[-1]
            if worst['exp'] < 0:
                label_short = worst['label'][:25] + '…' if len(worst['label']) > 25 else worst['label']
                items.append({
                    'label': f"Avoid: {label_short}",
                    'detail': f"{worst['exp']}R avg · {worst['wr']}% WR · {worst['n']} trades",
                    'type': 'red'
                })
    return items

def catmull(points):
    if len(points) < 2:
        return ""
    d = f"M{points[0][0]:.1f},{points[0][1]:.1f} "
    for i in range(len(points) - 1):
        p0 = points[i-1] if i > 0 else points[i]
        p1 = points[i]
        p2 = points[i+1]
        p3 = points[i+2] if i+2 < len(points) else p2
        c1x = p1[0] + (p2[0] - p0[0]) / 6
        c1y = p1[1] + (p2[1] - p0[1]) / 6
        c2x = p2[0] - (p3[0] - p1[0]) / 6
        c2y = p2[1] - (p3[1] - p1[1]) / 6
        d += f"C{c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {p2[0]:.1f},{p2[1]:.1f} "
    return d

def make_curve(eq, svg_w, svg_h):
    if not eq:
        return "", ""
    mn = min(min(eq), 0)
    mx = max(eq)
    rng = (mx - mn) if (mx - mn) != 0 else 1
    n = len(eq)
    pts = [((i / (n-1)) * svg_w if n > 1 else 0,
             svg_h - ((v - mn) / rng) * (svg_h - 20) - 10)
            for i, v in enumerate(eq)]
    line = catmull(pts)
    fill = line + f"L{svg_w},{svg_h} L0,{svg_h} Z"
    return line, fill

def build_donut(wins, losses, breakevens, colors, glow_color):
    total = wins + losses + breakevens if (wins + losses + breakevens) > 0 else 1
    segments = [('Win', wins, colors[0]), ('Loss', losses, colors[1]), ('Breakeven', breakevens, colors[2])]
    cx, cy, r_outer, r_inner = 110, 110, 95, 60
    start_angle = -90
    arcs = ""
    legend = ""
    for label, val, color in segments:
        if val == 0:
            continue
        frac = val / total
        sweep = frac * 360
        end_angle = start_angle + sweep
        def polar(r, a):
            rad = math.radians(a)
            return cx + r * math.cos(rad), cy + r * math.sin(rad)
        x1o, y1o = polar(r_outer, start_angle)
        x2o, y2o = polar(r_outer, end_angle)
        x1i, y1i = polar(r_inner, end_angle)
        x2i, y2i = polar(r_inner, start_angle)
        large_arc = 1 if sweep > 180 else 0
        path_d = f"M{x1o:.1f},{y1o:.1f} A{r_outer},{r_outer} 0 {large_arc} 1 {x2o:.1f},{y2o:.1f} L{x1i:.1f},{y1i:.1f} A{r_inner},{r_inner} 0 {large_arc} 0 {x2i:.1f},{y2i:.1f} Z"
        arcs += f'<path d="{path_d}" fill="{color}" opacity="0.85" style="filter:drop-shadow(0 0 8px {glow_color});"/>'
        pct = round(frac * 100)
        legend += (
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
            f'<div style="width:12px;height:12px;border-radius:50%;background:{color};box-shadow:0 0 8px {glow_color};"></div>'
            f'<span style="color:#ccc;font-size:0.9em;">{label}</span>'
            f'<span style="color:{color};font-weight:700;margin-left:auto;">{pct}%</span>'
            f'</div>'
        )
        start_angle = end_angle
    filter_id = f"dg{colors[0].replace('#','')}"
    svg = f"""<svg viewBox="0 0 220 220" style="width:180px;height:180px;display:block;">
      <defs>
        <filter id="{filter_id}" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="6" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <g filter="url(#{filter_id})">{arcs}</g>
      <circle cx="{cx}" cy="{cy}" r="{r_inner-4}" fill="rgba(0,0,0,0.2)" stroke="{colors[0]}33" stroke-width="1"/>
    </svg>"""
    return svg, legend

def render_stats_panel(stats, label_color):
    stat_data = [
        ('Total Trades', stats.get('total_trades','—')),
        ('Win Rate', f"{stats.get('win_rate','—')}%"),
        ('Total R', stats.get('total_r','—')),
        ('Avg R / Trade', stats.get('avg_r','—')),
        ('Expectancy', stats.get('expectancy','—')),
        ('Avg Win', stats.get('avg_win','—')),
        ('Avg Loss', stats.get('avg_loss','—')),
        ('Best Trade', stats.get('best_trade','—')),
        ('Worst Trade', stats.get('worst_trade','—')),
        ('Max Drawdown', stats.get('max_drawdown','—')),
        ('Max Streak', stats.get('max_consec_losses','—')),
        ('Wins', stats.get('wins','—')),
        ('Losses', stats.get('losses','—')),
        ('Breakevens', stats.get('breakevens','—')),
    ]
    cols_per_row = 7
    for i in range(0, len(stat_data), cols_per_row):
        row_data = stat_data[i:i+cols_per_row]
        cols = st.columns(len(row_data))
        for col, (label, value) in zip(cols, row_data):
            col.markdown(
                f'<div class="stat-card" style="border-color:{label_color}44;">'
                f'<div class="stat-value">{value}</div>'
                f'<div class="stat-label" style="color:{label_color};">{label}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.write("")

def render_breakdown(df_in, col, title, ACCENT_SOFT, ACCENT):
    data = breakdown_by_col(df_in, col)
    if not data:
        return
    st.markdown(f'<div style="color:{ACCENT_SOFT};font-size:0.7em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin:14px 0 8px;">{title}</div>', unsafe_allow_html=True)
    max_exp = max(abs(d['exp']) for d in data) if data else 1
    if max_exp == 0: max_exp = 1
    for d in data:
        bar_pct = round(abs(d['exp']) / max_exp * 100, 1)
        color = '#4ade80' if d['exp'] >= 0 else '#f87171'
        label_short = d['label'][:30] + '…' if len(d['label']) > 30 else d['label']
        st.markdown(
            f'<div style="display:grid;grid-template-columns:180px 1fr 55px 55px 30px;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid rgba(96,165,250,0.06);">'
            f'<span style="color:#ccc;font-size:0.82em;">{label_short}</span>'
            f'<div style="background:rgba(96,165,250,0.08);border-radius:6px;height:10px;overflow:hidden;">'
            f'<div style="width:{bar_pct}%;height:100%;background:linear-gradient(90deg,{color}66,{color});border-radius:6px;"></div>'
            f'</div>'
            f'<span style="color:{color};font-size:0.82em;font-weight:600;">{d["exp"]}R</span>'
            f'<span style="color:#9ab4dd;font-size:0.82em;">{d["wr"]}%</span>'
            f'<span style="color:#5a6a88;font-size:0.82em;">{d["n"]}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

# ============ LOAD DATA ============
with st.spinner("Pulling fresh data from Notion..."):
    raw_trades = get_all_trades()
    rows = []
    for trade in raw_trades:
        props = trade['properties']
        row = {}
        for col_name, col_data in props.items():
            if col_name == 'Entry Confluences':
                val = extract_property(col_data)
                row[col_name] = ', '.join(val) if isinstance(val, list) else val
            else:
                row[col_name] = extract_property_str(col_data)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.columns = df.columns.str.strip()
    df['Date'] = df['Date'].apply(safe_parse_date)
    df['Date'] = pd.Series(df['Date'].tolist(), dtype='datetime64[ns]')
    df['R_Result'] = df['R Result'].apply(parse_r_result)

    if 'Time of Trade' in df.columns:
        def parse_hour(t):
            try:
                t = str(t).strip()
                if ':' in t:
                    h = t.split(':')[0]
                    hour = int(h)
                    if 'PM' in str(t).upper() and hour != 12:
                        hour += 12
                    if 'AM' in str(t).upper() and hour == 12:
                        hour = 0
                    return f"{hour:02d}:00"
            except:
                pass
            return None
        df['Hour'] = df['Time of Trade'].apply(parse_hour)

    df_main = df.copy()
    df_main = df_main.sort_values('Date').reset_index(drop=True)
    df_main['Pair'] = df_main['Pair'].str.strip()

    df_xau = df_main[df_main['Pair'] == 'XAUUSD'].copy()
    df_nas = df_main[df_main['Pair'] == 'NASDAQ'].copy()

    main_stats = calc_stats(df_main)
    xau_stats = calc_stats(df_xau)
    nas_stats = calc_stats(df_nas)
    session_stats = calc_session_stats(df_main)
    daily_r = calc_daily_r(df_main)

max_abs_exp = max([abs(s['exp']) for s in session_stats]) if session_stats else 1
if max_abs_exp == 0:
    max_abs_exp = 1

today = datetime.now()

if 'selected_day' not in st.session_state:
    st.session_state.selected_day = None
if 'cal_month' not in st.session_state:
    st.session_state.cal_month = today.month
if 'cal_year' not in st.session_state:
    st.session_state.cal_year = today.year
if 'overview_idx' not in st.session_state:
    st.session_state.overview_idx = 0
if 'show_edge_analysis' not in st.session_state:
    st.session_state.show_edge_analysis = False

ACCENT = '#60a5fa'
ACCENT_SOFT = '#7fb2f5'
GOLD = '#f59e0b'
GOLD_SOFT = '#fcd34d'
PURPLE = '#a78bfa'
PURPLE_SOFT = '#c4b5fd'
NAV_H = '62px'

css = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  .stApp {{
    background:#070b14;
    background-image: radial-gradient(circle at 15% 10%, rgba(96,165,250,0.08), transparent 35%),
                       radial-gradient(circle at 85% 0%, rgba(96,165,250,0.06), transparent 35%);
    font-family: 'Inter', sans-serif;
  }}
  .header-title {{
    font-size:2.1em; font-weight:700;
    background: linear-gradient(135deg, #fff 30%, #999 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .section-label {{
    font-size:0.72em; font-weight:700; letter-spacing:2.5px; text-transform:uppercase;
    color:{ACCENT_SOFT}; margin:42px 0 18px; display:flex; align-items:center; gap:10px;
  }}
  .section-label::after {{ content:''; flex:1; height:1px; background:linear-gradient(90deg, rgba(96,165,250,0.2), transparent); }}
  .stat-card {{
    background: rgba(96,165,250,0.06);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border:1px solid rgba(96,165,250,0.2);
    border-radius:18px; padding:24px 14px; text-align:center;
    transition: all 0.25s ease;
    box-shadow: 0 8px 28px rgba(96,165,250,0.06);
  }}
  .stat-card:hover {{ transform: translateY(-2px); }}
  .stat-value {{ font-size:1.65em; font-weight:700; letter-spacing:-0.3px; color:#fff; }}
  .stat-label {{ font-size:0.66em; margin-top:7px; letter-spacing:0.8px; font-weight:600; text-transform:uppercase; }}
  .divider-line {{ border:none; border-top:1px solid rgba(96,165,250,0.12); margin:42px 0; }}
  .glass-panel {{
    background: rgba(96,165,250,0.05);
    backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
    border:1px solid rgba(96,165,250,0.15);
    border-radius:20px; padding:24px;
    box-shadow: 0 12px 36px rgba(96,165,250,0.08);
    margin-bottom:16px;
  }}
  .nav-banner {{
    background: rgba(96,165,250,0.05);
    backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
    border:1px solid rgba(96,165,250,0.15);
    border-radius:20px; padding:0 24px;
    text-align:center; display:flex; align-items:center; justify-content:center;
    min-height:{NAV_H}; box-sizing:border-box;
  }}
  .nav-label {{ font-size:1.3em; font-weight:800; color:#fff; letter-spacing:-0.3px; }}
  .collapse-bar {{
    background:rgba(96,165,250,0.06);
    border:1px solid rgba(96,165,250,0.2);
    border-radius:14px;
    padding:14px 18px;
    display:flex;
    align-items:center;
    gap:12px;
  }}
  .cal-header {{ color:{ACCENT_SOFT}; font-size:0.72em; text-align:center; letter-spacing:1.5px; font-weight:600; text-transform:uppercase; padding:10px 0; }}
  .cal-day-num {{ color:#3d4a63; font-size:0.78em; font-weight:600; text-align:center; }}
  .cal-week-summary {{
    background: rgba(96,165,250,0.06);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border:1px solid rgba(96,165,250,0.18); border-radius:16px; padding:12px 6px;
    text-align:center; min-height:88px;
  }}
  .cal-week-label {{ color:{ACCENT_SOFT}; font-size:0.68em; font-weight:700; letter-spacing:0.5px; }}
  .cal-week-r {{ font-size:1.25em; font-weight:700; margin-top:10px; color:#fff; }}
  .cal-day-trades {{ color:#5a6a88; font-size:0.64em; margin-top:3px; font-weight:500; text-align:center; }}
  div[data-testid="stButton"] button {{
    width:100%; min-height:88px; border-radius:16px;
    font-family:'Inter', sans-serif; white-space:pre-line; line-height:1.4;
    transition: all 0.25s ease; font-weight:600;
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    background: rgba(96,165,250,0.06) !important;
    border:1px solid rgba(96,165,250,0.18) !important;
    color:#fff !important;
  }}
  div[data-testid="stButton"] button:hover {{ transform: translateY(-2px); border-color: rgba(96,165,250,0.4) !important; }}
  div[data-testid="column"]:first-child div[data-testid="stButton"] button,
  div[data-testid="column"]:last-child div[data-testid="stButton"] button {{
    min-height:{NAV_H} !important;
    border-radius:20px !important;
    font-size:1.2em !important;
  }}
  .trade-detail-card {{
    background: rgba(96,165,250,0.05);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border:1px solid rgba(96,165,250,0.15); border-radius:16px; padding:16px 20px; margin-bottom:10px;
  }}
  .eq-legend {{ display:flex; gap:24px; margin-bottom:12px; flex-wrap:wrap; }}
  .eq-legend-item {{ display:flex; align-items:center; gap:8px; font-size:0.82em; font-weight:600; }}
  .eq-legend-dot {{ width:28px; height:3px; border-radius:2px; }}
  .checklist-item {{
    display:flex; align-items:flex-start; gap:12px;
    padding:10px 0; border-bottom:1px solid rgba(96,165,250,0.08);
  }}
  .checklist-dot {{
    width:8px; height:8px; border-radius:50%; margin-top:5px; flex-shrink:0;
  }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ============ HEADER ============
st.markdown('<div class="header-title">Overall Data</div>', unsafe_allow_html=True)

# ============ PERFORMANCE OVERVIEW ============
st.markdown('<div class="section-label">Performance Overview</div>', unsafe_allow_html=True)

overviews = [
    {'label': 'Overall', 'stats': main_stats, 'color': ACCENT_SOFT},
    {'label': 'XAUUSD', 'stats': xau_stats, 'color': GOLD_SOFT},
    {'label': 'NASDAQ', 'stats': nas_stats, 'color': PURPLE_SOFT},
]

idx = st.session_state.overview_idx
current = overviews[idx]

nav_l, nav_mid, nav_r = st.columns([1, 8, 1])
if nav_l.button("←", key="prev_overview", use_container_width=True):
    st.session_state.overview_idx = (idx - 1) % len(overviews)
    st.rerun()
nav_mid.markdown(f'<div class="nav-banner"><span class="nav-label" style="color:{current["color"]};">{current["label"]} Performance</span></div>', unsafe_allow_html=True)
if nav_r.button("→", key="next_overview", use_container_width=True):
    st.session_state.overview_idx = (idx + 1) % len(overviews)
    st.rerun()

st.write("")
render_stats_panel(current['stats'], current['color'])

# ============ CHARTS ============
st.markdown('<div class="section-label">Charts</div>', unsafe_allow_html=True)

xau_eq = xau_stats.get('equity_curve', [])
nas_eq = nas_stats.get('equity_curve', [])
svg_w, svg_h = 800, 200

xau_line, xau_fill = make_curve(xau_eq, svg_w, svg_h)
nas_line, nas_fill = make_curve(nas_eq, svg_w, svg_h)

xau_fill_path = f'<path d="{xau_fill}" fill="url(#xauFill)" opacity="0.5"/>' if xau_fill else ''
nas_fill_path = f'<path d="{nas_fill}" fill="url(#nasFill)" opacity="0.4"/>' if nas_fill else ''
xau_line_path = f'<path d="{xau_line}" fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round" filter="url(#xauGlow)"/>' if xau_line else ''
nas_line_path = f'<path d="{nas_line}" fill="none" stroke="{PURPLE}" stroke-width="3" stroke-linecap="round" filter="url(#nasGlow)"/>' if nas_line else ''

combined_svg = f"""<svg viewBox="0 0 {svg_w} {svg_h}" style="width:100%; height:280px; display:block;">
  <defs>
    <linearGradient id="xauFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="rgba(245,158,11,0.3)"/>
      <stop offset="100%" stop-color="rgba(245,158,11,0)"/>
    </linearGradient>
    <linearGradient id="nasFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="rgba(167,139,250,0.3)"/>
      <stop offset="100%" stop-color="rgba(167,139,250,0)"/>
    </linearGradient>
    <filter id="xauGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="nasGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  {xau_fill_path}
  {nas_fill_path}
  {xau_line_path}
  {nas_line_path}
</svg>"""

legend_html = f"""<div class="eq-legend">
  <div class="eq-legend-item"><div class="eq-legend-dot" style="background:{GOLD};box-shadow:0 0 6px {GOLD};"></div><span style="color:{GOLD_SOFT};">XAUUSD ({len(xau_eq)} trades)</span></div>
  <div class="eq-legend-item"><div class="eq-legend-dot" style="background:{PURPLE};box-shadow:0 0 6px {PURPLE};"></div><span style="color:{PURPLE_SOFT};">NASDAQ ({len(nas_eq)} trades)</span></div>
</div>"""

st.markdown(f'<div class="glass-panel"><div style="color:#cfe0fb;font-weight:600;font-size:1.05em;margin-bottom:8px;">Equity Curve</div>{legend_html}{combined_svg}</div>', unsafe_allow_html=True)

donut_configs = [
    ('Overall', main_stats.get('wins',0), main_stats.get('losses',0), main_stats.get('breakevens',0), ['#1d4ed8','#3b82f6','#93c5fd'], 'rgba(96,165,250,0.4)', ACCENT_SOFT),
    ('XAUUSD', xau_stats.get('wins',0), xau_stats.get('losses',0), xau_stats.get('breakevens',0), ['#b45309','#f59e0b','#fde68a'], 'rgba(245,158,11,0.4)', GOLD_SOFT),
    ('NASDAQ', nas_stats.get('wins',0), nas_stats.get('losses',0), nas_stats.get('breakevens',0), ['#6d28d9','#a78bfa','#ede9fe'], 'rgba(167,139,250,0.4)', PURPLE_SOFT),
]

donut_cols = st.columns(3)
for col, (label, w, l, b, colors, glow, title_color) in zip(donut_cols, donut_configs):
    svg, legend = build_donut(w, l, b, colors, glow)
    col.markdown(
        f'<div class="glass-panel" style="border-color:{colors[1]}44;"><div style="color:{title_color};font-weight:600;font-size:1em;margin-bottom:14px;">{label}</div>'
        f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;"><div>{svg}</div><div style="flex:1;min-width:100px;">{legend}</div></div></div>',
        unsafe_allow_html=True
    )

st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

# ============ 3SL WINDOW ============
st.markdown('<div class="section-label">3SL Window</div>', unsafe_allow_html=True)

session_rows_html = ""
for s in session_stats:
    bar_pct = round(abs(s['exp']) / max_abs_exp * 100, 1)
    session_rows_html += (
        f'<div style="display:grid;grid-template-columns:100px 1fr 70px 60px 40px;gap:16px;align-items:center;padding:12px 0;">'
        f'<span style="color:{ACCENT_SOFT};font-weight:600;">{s["session"]}</span>'
        f'<div style="background:rgba(96,165,250,0.1);border-radius:8px;height:16px;overflow:hidden;">'
        f'<div style="width:{bar_pct}%;height:100%;background:linear-gradient(90deg,rgba(59,130,246,0.6),{ACCENT});border-radius:8px;"></div>'
        f'</div>'
        f'<span style="color:#fff;font-weight:700;">{s["exp"]}</span>'
        f'<span style="color:#9ab4dd;font-weight:500;">{s["wr"]}</span>'
        f'<span style="color:#5a6a88;font-weight:500;">{s["n"]}</span>'
        f'</div>'
    )

st.markdown(
    f'<div class="glass-panel">'
    f'<div style="display:grid;grid-template-columns:100px 1fr 70px 60px 40px;gap:16px;padding-bottom:14px;margin-bottom:8px;border-bottom:1px solid rgba(96,165,250,0.12);">'
    f'<span style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:600;letter-spacing:0.5px;">VALUE</span>'
    f'<span style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:600;letter-spacing:0.5px;">CHART</span>'
    f'<span style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:600;letter-spacing:0.5px;">EXP</span>'
    f'<span style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:600;letter-spacing:0.5px;">WR</span>'
    f'<span style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:600;letter-spacing:0.5px;">N</span>'
    f'</div>'
    f'{session_rows_html}</div>',
    unsafe_allow_html=True
)

# ============ MONTHLY CALENDAR ============
st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

cal_month = st.session_state.cal_month
cal_year = st.session_state.cal_year
month_total_r = sum(v['total_r'] for k, v in daily_r.items() if k.month == cal_month and k.year == cal_year)
month_sign = '+' if month_total_r > 0 else ''
month_name = datetime(cal_year, cal_month, 1).strftime("%B %Y")

nav_col_left, nav_col_mid, nav_col_right = st.columns([1, 8, 1])
if nav_col_left.button("←", key="prev_month", use_container_width=True):
    if st.session_state.cal_month == 1:
        st.session_state.cal_month = 12
        st.session_state.cal_year -= 1
    else:
        st.session_state.cal_month -= 1
    st.rerun()
nav_col_mid.markdown(f'<div class="nav-banner"><span class="nav-label">{month_name} &nbsp;·&nbsp; Total R: <span style="color:{ACCENT};">{month_sign}{round(month_total_r,2)}</span></span></div>', unsafe_allow_html=True)
if nav_col_right.button("→", key="next_month", use_container_width=True):
    if st.session_state.cal_month == 12:
        st.session_state.cal_month = 1
        st.session_state.cal_year += 1
    else:
        st.session_state.cal_month += 1
    st.rerun()

st.write("")

cal_module.setfirstweekday(cal_module.MONDAY)
month_matrix = cal_module.monthcalendar(cal_year, cal_month)

day_header_cols = st.columns(8)
for i, d in enumerate(['Mo','Tu','We','Th','Fr','Sa','Su']):
    day_header_cols[i].markdown(f'<div class="cal-header">{d}</div>', unsafe_allow_html=True)
day_header_cols[7].markdown('<div class="cal-header">Week</div>', unsafe_allow_html=True)

for week_num, week in enumerate(month_matrix):
    if week_num > 0:
        st.write("")
    week_cols = st.columns(8)
    week_total = 0
    week_trades = 0
    for i, day_num in enumerate(week):
        if day_num == 0:
            week_cols[i].markdown('<div style="min-height:88px;"></div>', unsafe_allow_html=True)
        else:
            day_date = datetime(cal_year, cal_month, day_num).date()
            day_data = daily_r.get(day_date)
            if day_data:
                week_total += day_data['total_r']
                week_trades += day_data['trades']
                r_val = day_data['total_r']
                sign = '+' if r_val > 0 else ''
                button_label = f"{day_num}\n{sign}{r_val}R\n{day_data['trades']} trades"
                if week_cols[i].button(button_label, key=f"day_{day_date}", use_container_width=True):
                    st.session_state.selected_day = day_date
            else:
                week_cols[i].markdown(
                    f'<div style="min-height:88px;display:flex;align-items:center;justify-content:center;">'
                    f'<div class="cal-day-num">{day_num}</div></div>',
                    unsafe_allow_html=True
                )
    wk_sign = '+' if week_total > 0 else ''
    week_cols[7].markdown(
        f'<div class="cal-week-summary"><div class="cal-week-label">Week {week_num+1}</div>'
        f'<div class="cal-week-r">{wk_sign}{round(week_total,2)}R</div>'
        f'<div class="cal-day-trades">{week_trades} trades</div></div>',
        unsafe_allow_html=True
    )

# ============ SELECTED DAY DETAIL ============
if st.session_state.selected_day:
    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)
    sel_day = st.session_state.selected_day
    day_trades = get_day_trades(df_main, sel_day)
    st.markdown(f'<div class="section-label">Trades on {sel_day.strftime("%B %d, %Y")}</div>', unsafe_allow_html=True)
    for _, trade in day_trades.iterrows():
        r_val = trade['R_Result']
        label = 'Win' if r_val > 0 else ('Loss' if r_val < 0 else 'Breakeven')
        sign = '+' if r_val > 0 else ''
        pair = trade.get('Pair', '—')
        trade_no = trade.get('Trade No.', '—')
        pair_color = GOLD_SOFT if pair == 'XAUUSD' else (PURPLE_SOFT if pair == 'NASDAQ' else ACCENT_SOFT)
        st.markdown(
            f'<div class="trade-detail-card">'
            f'<span style="color:{pair_color};font-weight:700;font-size:1.1em;">{label}</span>'
            f'<span style="color:#888;"> &nbsp;·&nbsp; Trade #{trade_no} &nbsp;·&nbsp; <span style="color:{pair_color};">{pair}</span></span>'
            f'<span style="color:#fff;font-weight:700;float:right;">{sign}{r_val}R</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    if st.button("Close"):
        st.session_state.selected_day = None
        st.rerun()

# ============ EDGE ANALYSIS (bottom, collapsible) ============
st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

ea_col1, ea_col2 = st.columns([9, 1])
ea_col1.markdown(f'<div class="collapse-bar"><span style="font-size:0.8em;font-weight:700;letter-spacing:1px;color:{ACCENT_SOFT};text-transform:uppercase;">Edge Analysis</span><span style="color:#5a6a88;font-size:0.8em;">— what\'s working, what to avoid</span></div>', unsafe_allow_html=True)
if ea_col2.button("▼" if not st.session_state.show_edge_analysis else "▲", key="toggle_ea", use_container_width=True):
    st.session_state.show_edge_analysis = not st.session_state.show_edge_analysis
    st.rerun()

if st.session_state.show_edge_analysis:
    st.markdown(f'<div style="color:#5a6a88;font-size:0.75em;margin-bottom:6px;padding-top:4px;">EXP = avg R · WR = win rate % · N = trades. Min 2 trades to appear.</div>', unsafe_allow_html=True)

    ea_cols = st.columns(2)
    with ea_cols[0]:
        render_breakdown(df_main, 'Entry Model', 'Entry Model', ACCENT_SOFT, ACCENT)
        render_breakdown(df_main, 'Entry Model Timeframe', 'Entry Timeframe', ACCENT_SOFT, ACCENT)
        render_breakdown(df_main, 'Double Confirmation', 'Double Confirmation', ACCENT_SOFT, ACCENT)
        render_breakdown(df_main, 'Target', 'Target Used', ACCENT_SOFT, ACCENT)
        render_breakdown(df_main, 'Entry + Confirmation', 'Rejection Candle', ACCENT_SOFT, ACCENT)
    with ea_cols[1]:
        render_breakdown(df_main, 'Entry Confluences', 'Entry Confluences', ACCENT_SOFT, ACCENT)
        render_breakdown(df_main, 'Stop Loss Logic', 'Stop Loss Logic', ACCENT_SOFT, ACCENT)
        render_breakdown(df_main, 'Hour', 'Time of Day', ACCENT_SOFT, ACCENT)
        render_breakdown(df_main, 'Trade Quality Rating', 'Trade Quality', ACCENT_SOFT, ACCENT)
        render_breakdown(df_main, 'Emotional State Before...', 'Emotional State', ACCENT_SOFT, ACCENT)

    # ============ NEXT TRADE CHECKLIST ============
    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:14px;">Next Trade Checklist — based on your data</div>', unsafe_allow_html=True)

    checklist = generate_checklist(df_main, session_stats)
    if checklist:
        cl_cols = st.columns(2)
        green_items = [c for c in checklist if c['type'] == 'green']
        red_items = [c for c in checklist if c['type'] == 'red']
        with cl_cols[0]:
            st.markdown(f'<div style="color:#4ade80;font-size:0.7em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">✓ What\'s working — do more of this</div>', unsafe_allow_html=True)
            for item in green_items:
                st.markdown(
                    f'<div class="checklist-item">'
                    f'<div class="checklist-dot" style="background:#4ade80;box-shadow:0 0 6px rgba(74,222,128,0.4);"></div>'
                    f'<div><div style="color:#ddd;font-size:0.88em;font-weight:600;">{item["label"]}</div>'
                    f'<div style="color:#5a6a88;font-size:0.76em;margin-top:2px;">{item["detail"]}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        with cl_cols[1]:
            st.markdown(f'<div style="color:#f87171;font-size:0.7em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">✗ What to avoid</div>', unsafe_allow_html=True)
            for item in red_items:
                st.markdown(
                    f'<div class="checklist-item">'
                    f'<div class="checklist-dot" style="background:#f87171;box-shadow:0 0 6px rgba(248,113,113,0.4);"></div>'
                    f'<div><div style="color:#ddd;font-size:0.88em;font-weight:600;">{item["label"]}</div>'
                    f'<div style="color:#5a6a88;font-size:0.76em;margin-top:2px;">{item["detail"]}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
    else:
        st.markdown('<div style="color:#5a6a88;font-size:0.85em;">Not enough data yet — keep logging trades and this will populate automatically.</div>', unsafe_allow_html=True)
