import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from datetime import datetime
import calendar as cal_module
import math

st.set_page_config(page_title="Trading Data", layout="wide", initial_sidebar_state="collapsed")

PASSWORD = st.secrets.get("DASHBOARD_PASSWORD", "trading123")
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp {
        background:#070b14;
        background-image: url('https://images.unsplash.com/photo-1592198084033-aade902d1aae?w=1600&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family:'Inter',sans-serif;
    }
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(7,11,20,0.82);
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
        z-index: 0;
    }
    .stApp > * { position: relative; z-index: 1; }
    div[data-testid="stForm"] { background:transparent; border:none; }
    div[data-testid="stFormSubmitButton"] button {
        background:linear-gradient(135deg, rgba(96,165,250,0.2), rgba(96,165,250,0.1)) !important;
        border:1px solid rgba(96,165,250,0.4) !important;
        color:#fff !important; border-radius:12px !important;
        min-height:48px !important; font-weight:600 !important;
        font-size:0.95em !important; letter-spacing:0.5px !important;
    }
    div[data-testid="stTextInput"] input {
        background:rgba(96,165,250,0.06) !important;
        border:1px solid rgba(96,165,250,0.2) !important;
        border-radius:12px !important; color:#fff !important;
        padding:12px 16px !important; font-size:0.95em !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color:rgba(96,165,250,0.5) !important;
        box-shadow:0 0 0 3px rgba(96,165,250,0.1) !important;
    }
    div[data-testid="stTextInput"] > div {
        border:none !important; background:transparent !important;
        box-shadow:none !important;
    }
    div[data-testid="stTextInput"] > div > div {
        border:none !important; background:transparent !important;
        box-shadow:none !important; padding:0 !important;
    }
    div[data-testid="stTextInput"] > div > div > div {
        border:none !important; background:transparent !important;
        box-shadow:none !important;
    }
    div[data-testid="stTextInput"] > label { display:none !important; }
    div[data-testid="stTextInput"] input::-webkit-credentials-auto-fill-button,
    div[data-testid="stTextInput"] input::-webkit-contacts-auto-fill-button { display:none !important; }
    input[type="password"]::-ms-reveal, input[type="password"]::-ms-clear { display:none !important; }
    </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:60px 0 36px;">
            <div style="font-size:2.2em;font-weight:800;color:#fff;letter-spacing:-0.5px;margin-bottom:8px;">Trading Data</div>
            <div style="width:40px;height:3px;background:linear-gradient(90deg,#60a5fa,#a78bfa);border-radius:2px;margin:0 auto 16px;"></div>
            <div style="color:#5a6a88;font-size:0.85em;">Your personal trading journal</div>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            pw = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter your password", autocomplete="off", help="")
            st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
            submitted = st.form_submit_button("Enter Dashboard", use_container_width=True)
            if submitted:
                if pw == PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password — try again")
        st.markdown('<div style="text-align:center;color:#3d4a63;font-size:0.72em;margin-top:20px;">Secured · Private · Your data only</div>', unsafe_allow_html=True)
    st.stop()

NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

if 'theme' not in st.session_state:
    st.session_state.theme = 'Blue'
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'account_size' not in st.session_state:
    st.session_state.account_size = 50000
if 'num_accounts' not in st.session_state:
    st.session_state.num_accounts = 1
if 'risk_per_trade' not in st.session_state:
    st.session_state.risk_per_trade = 500

themes = {
    'Blue':    {'ACCENT': '#60a5fa', 'ACCENT_SOFT': '#7fb2f5', 'BG_TINT': '96,165,250'},
    'Purple':  {'ACCENT': '#a78bfa', 'ACCENT_SOFT': '#c4b5fd', 'BG_TINT': '167,139,250'},
    'Green':   {'ACCENT': '#34d399', 'ACCENT_SOFT': '#6ee7b7', 'BG_TINT': '52,211,153'},
    'Red':     {'ACCENT': '#f87171', 'ACCENT_SOFT': '#fca5a5', 'BG_TINT': '248,113,113'},
    'Neutral': {'ACCENT': '#9ca3af', 'ACCENT_SOFT': '#d1d5db', 'BG_TINT': '156,163,175'},
}
active_theme = themes.get(st.session_state.theme, themes['Blue'])
ACCENT = active_theme['ACCENT']
ACCENT_SOFT = active_theme['ACCENT_SOFT']
BG_TINT = active_theme['BG_TINT']
GOLD = '#f59e0b'; GOLD_SOFT = '#fcd34d'
PURPLE = '#a78bfa'; PURPLE_SOFT = '#c4b5fd'
NAV_H = '56px'
RANK_COLORS = ['#fcd34d', '#7fb2f5', '#9ca3af']
IS_DARK = st.session_state.dark_mode

# ============ DARK/LIGHT COLOUR VARS ============
if IS_DARK:
    BG_BASE = '#070b14'
    BG_CARD = f'rgba({BG_TINT},0.06)'
    BG_GLASS = f'rgba({BG_TINT},0.05)'
    BG_GLASS2 = f'rgba({BG_TINT},0.08)'
    BORDER = f'rgba({BG_TINT},0.15)'
    BORDER2 = f'rgba({BG_TINT},0.2)'
    TEXT_PRIMARY = '#ffffff'
    TEXT_SECONDARY = '#5a6a88'
    TEXT_MUTED = '#3d4a63'
    SHADOW = f'rgba({BG_TINT},0.08)'
    SIDEBAR_BG = f'rgba({BG_TINT},0.03)'
    SIDEBAR_BORDER = f'rgba({BG_TINT},0.12)'
    CAL_EMPTY_NUM = '#3d4a63'
    BG_RADIAL1 = f'rgba({BG_TINT},0.08)'
    BG_RADIAL2 = f'rgba({BG_TINT},0.06)'
else:
    BG_BASE = '#f5f5f0'
    BG_CARD = '#ffffff'
    BG_GLASS = 'rgba(255,255,255,0.85)'
    BG_GLASS2 = 'rgba(255,255,255,0.9)'
    BORDER = f'rgba({BG_TINT},0.2)'
    BORDER2 = f'rgba({BG_TINT},0.25)'
    TEXT_PRIMARY = '#111827'
    TEXT_SECONDARY = '#6b7280'
    TEXT_MUTED = '#9ca3af'
    SHADOW = 'rgba(0,0,0,0.06)'
    SIDEBAR_BG = 'rgba(255,255,255,0.6)'
    SIDEBAR_BORDER = 'rgba(0,0,0,0.08)'
    CAL_EMPTY_NUM = '#9ca3af'
    BG_RADIAL1 = f'rgba({BG_TINT},0.05)'
    BG_RADIAL2 = f'rgba({BG_TINT},0.03)'

@st.cache_data(ttl=300)
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
        from dateutil import parser as _p
        parsed = _p.isoparse(str(x))
        ts = pd.Timestamp(parsed)
        if ts.tzinfo is not None:
            ts = ts.tz_convert('Australia/Sydney').tz_localize(None)
        return ts
    except:
        try:
            from dateutil import parser as _p
            parsed = _p.parse(str(x))
            ts = pd.Timestamp(parsed)
            if ts.tzinfo is not None:
                ts = ts.tz_convert('Australia/Sydney').tz_localize(None)
            return ts
        except:
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
    non_be = stats['wins'] + stats['losses']
    stats['win_rate'] = round(stats['wins'] / non_be * 100, 1) if non_be > 0 else 0
    stats['total_r'] = round(r.sum(), 2)
    stats['avg_r'] = round(r.mean(), 2)
    stats['avg_win'] = round(r[r > 0].mean(), 2) if stats['wins'] > 0 else 0
    stats['avg_loss'] = round(r[r < 0].mean(), 2) if stats['losses'] > 0 else 0
    stats['best_trade'] = round(r.max(), 2)
    stats['worst_trade'] = round(r.min(), 2)
    stats['expectancy'] = round(r.sum() / len(r), 2)
    equity = r.cumsum()
    peak = equity.cummax()
    stats['max_drawdown'] = round((equity - peak).min(), 2)
    stats['equity_curve'] = equity.tolist()
    streak = max_streak = 0
    for val in r:
        streak = streak + 1 if val < 0 else 0
        max_streak = max(max_streak, streak)
    stats['max_consec_losses'] = max_streak
    cur_streak = 0
    cur_type = None
    for val in reversed(r.tolist()):
        t = 'W' if val > 0 else ('L' if val < 0 else 'B')
        if cur_type is None:
            cur_type = t
        if t == cur_type:
            cur_streak += 1
        else:
            break
    stats['cur_streak'] = cur_streak
    stats['cur_streak_type'] = cur_type
    rolling = []
    vals = r.tolist()
    for i in range(len(vals)):
        window = vals[max(0, i-9):i+1]
        w = sum(1 for v in window if v > 0)
        l = sum(1 for v in window if v < 0)
        nb = w + l
        rolling.append(round(w / nb * 100, 1) if nb > 0 else 0)
    stats['rolling_wr'] = rolling
    stats['trade_results'] = ['W' if v > 0 else ('L' if v < 0 else 'B') for v in vals]
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
        exp = round(r.sum() / n, 3)
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

def calc_monthly_r(df_in):
    df_temp = df_in.dropna(subset=['Date', 'R_Result']).copy()
    df_temp['month'] = df_temp['Date'].dt.to_period('M')
    grouped = df_temp.groupby('month')['R_Result'].agg(['count', 'sum', lambda x: round(sum(1 for v in x if v > 0) / max(sum(1 for v in x if v != 0), 1) * 100, 1)])
    grouped.columns = ['trades', 'total_r', 'win_rate']
    monthly = {}
    for period, row in grouped.iterrows():
        monthly[str(period)] = {'trades': int(row['trades']), 'total_r': round(row['total_r'], 2), 'win_rate': round(row['win_rate'], 1)}
    return monthly

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
    return data[0] if data else None

def calc_consistency_score(df_in, session_stats):
    scores = []
    if 'Trade Quality Rating' in df_in.columns:
        temp = df_in.dropna(subset=['Trade Quality Rating'])
        a_plus = temp[temp['Trade Quality Rating'].str.contains('A\\+', na=False, regex=True)]
        if len(temp) > 0:
            scores.append(('A+ quality trades', round(len(a_plus) / len(temp) * 100)))
    if 'Rules Followed? Y/N' in df_in.columns:
        temp = df_in.dropna(subset=['Rules Followed? Y/N'])
        yes = temp[temp['Rules Followed? Y/N'].str.lower().str.startswith('yes', na=False)]
        if len(temp) > 0:
            scores.append(('Rules followed', round(len(yes) / len(temp) * 100)))
    if session_stats:
        best = max(session_stats, key=lambda x: x['exp'])
        if '3SL Window' in df_in.columns:
            temp = df_in.dropna(subset=['3SL Window', 'R_Result'])
            in_best = temp[temp['3SL Window'] == best['session']]
            if len(temp) > 0:
                scores.append((f"In {best['session']} session", round(len(in_best) / len(temp) * 100)))
    if 'Emotional State Before...' in df_in.columns:
        temp = df_in.dropna(subset=['Emotional State Before...'])
        conf = temp[temp['Emotional State Before...'].str.lower().str.contains('confident', na=False)]
        if len(temp) > 0:
            scores.append(('Confident entries', round(len(conf) / len(temp) * 100)))
    overall = round(sum(s[1] for s in scores) / len(scores)) if scores else 0
    return overall, scores

def find_best_setup(df_in):
    cols = ['3SL Window', 'Entry Confluences', 'Entry Model Timeframe', 'Double Confirmation', 'Target']
    available = [c for c in cols if c in df_in.columns]
    if not available:
        return None
    best_combos = []
    for col in available:
        data = breakdown_by_col(df_in, col, min_trades=2)
        if data and data[0]['exp'] > 0:
            best_combos.append({'col': col, 'label': data[0]['label'], 'wr': data[0]['wr'], 'exp': data[0]['exp'], 'n': data[0]['n']})
    if not best_combos:
        return None
    overall_wr = round(sum(b['wr'] for b in best_combos) / len(best_combos), 1)
    overall_exp = round(sum(b['exp'] for b in best_combos) / len(best_combos), 2)
    return {'combos': best_combos, 'overall_wr': overall_wr, 'overall_exp': overall_exp}

def generate_checklist(df_in, session_stats):
    green = []
    red = []
    analysis_cols = [
        ('Entry Model', 'entry model'), ('Entry Model Timeframe', 'timeframe'),
        ('Double Confirmation', 'double confirmation'), ('Target', 'target'),
        ('Stop Loss Logic', 'stop loss'), ('Entry + Confirmation', 'rejection candle'),
        ('Trade Quality Rating', 'trade quality'), ('Entry Confluences', 'entry confluence'),
        ('Conditions MTF/HTF', 'market conditions'),
    ]
    for col, label in analysis_cols:
        data = breakdown_by_col(df_in, col, min_trades=2)
        if not data:
            continue
        best = data[0]
        if best['exp'] > 0:
            green.append({'label': f"Use {best['label']} for {label}", 'detail': f"{best['exp']}R avg · {best['wr']}% WR · {best['n']} trades"})
    if session_stats:
        best_s = max(session_stats, key=lambda x: x['exp'])
        if best_s['exp'] > 0:
            green.append({'label': f"Trade {best_s['session']} session", 'detail': f"{best_s['exp']}R avg · {round(best_s['wr']*100)}% WR · {best_s['n']} trades"})
    if session_stats:
        for s in session_stats:
            if s['exp'] < 0 or s['wr'] < 0.4:
                red.append({'label': f"Avoid {s['session']} session", 'detail': f"{s['exp']}R avg · {round(s['wr']*100)}% WR · {s['n']} trades"})
    for col, check_exp, check_wr, tmpl in [
        ('Emotional State Before...', True, 45, "Avoid trading when {}"),
        ('Trade Quality Rating', True, 45, "Avoid {} quality trades"),
        ('News Proximity', True, 45, "Avoid trading {}"),
        ('Entry Model', True, 45, "Avoid {} entry model"),
        ('Conditions MTF/HTF', True, 45, "Avoid trading in {} conditions"),
        ('Stop Loss Logic', True, 45, "Avoid {} stop loss"),
        ('Target', True, 45, "Avoid {} as target"),
    ]:
        if col in df_in.columns:
            data = breakdown_by_col(df_in, col, min_trades=2)
            for d in data:
                if d['exp'] < 0 or d['wr'] < check_wr:
                    red.append({'label': tmpl.format(d['label']), 'detail': f"{d['exp']}R avg · {d['wr']}% WR · {d['n']} trades"})
    return green, red

def catmull(points):
    if len(points) < 2:
        return ""
    d = f"M{points[0][0]:.1f},{points[0][1]:.1f} "
    for i in range(len(points) - 1):
        p0 = points[i-1] if i > 0 else points[i]
        p1 = points[i]; p2 = points[i+1]
        p3 = points[i+2] if i+2 < len(points) else p2
        c1x = p1[0] + (p2[0] - p0[0]) / 6; c1y = p1[1] + (p2[1] - p0[1]) / 6
        c2x = p2[0] - (p3[0] - p1[0]) / 6; c2y = p2[1] - (p3[1] - p1[1]) / 6
        d += f"C{c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {p2[0]:.1f},{p2[1]:.1f} "
    return d

def make_curve(eq, svg_w, svg_h):
    if not eq:
        return "", ""
    mn = min(min(eq), 0); mx = max(eq)
    rng = (mx - mn) if (mx - mn) != 0 else 1
    n = len(eq)
    pts = [((i / (n-1)) * svg_w if n > 1 else 0, svg_h - ((v - mn) / rng) * (svg_h - 20) - 10) for i, v in enumerate(eq)]
    line = catmull(pts)
    return line, line + f"L{svg_w},{svg_h} L0,{svg_h} Z"

def build_donut(wins, losses, breakevens, colors, glow_color):
    total = wins + losses + breakevens if (wins + losses + breakevens) > 0 else 1
    segments = [('Win', wins, colors[0]), ('Loss', losses, colors[1]), ('Breakeven', breakevens, colors[2])]
    cx = cy = 110; r_outer = 95; r_inner = 60
    start_angle = -90; arcs = ""; legend = ""
    for label, val, color in segments:
        if val == 0:
            continue
        frac = val / total; sweep = frac * 360; end_angle = start_angle + sweep
        def polar(r, a):
            rad = math.radians(a)
            return cx + r * math.cos(rad), cy + r * math.sin(rad)
        x1o, y1o = polar(r_outer, start_angle); x2o, y2o = polar(r_outer, end_angle)
        x1i, y1i = polar(r_inner, end_angle); x2i, y2i = polar(r_inner, start_angle)
        large_arc = 1 if sweep > 180 else 0
        path_d = f"M{x1o:.1f},{y1o:.1f} A{r_outer},{r_outer} 0 {large_arc} 1 {x2o:.1f},{y2o:.1f} L{x1i:.1f},{y1i:.1f} A{r_inner},{r_inner} 0 {large_arc} 0 {x2i:.1f},{y2i:.1f} Z"
        arcs += f'<path d="{path_d}" fill="{color}" opacity="0.85" style="filter:drop-shadow(0 0 8px {glow_color});"/>'
        pct = round(frac * 100)
        legend += (f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
                   f'<div style="width:12px;height:12px;border-radius:50%;background:{color};box-shadow:0 0 8px {glow_color};"></div>'
                   f'<span style="color:{TEXT_SECONDARY};font-size:0.9em;">{label}</span>'
                   f'<span style="color:{color};font-weight:700;margin-left:auto;">{pct}%</span></div>')
        start_angle = end_angle
    fid = f"dg{colors[0].replace('#','')}"
    svg = f"""<svg viewBox="0 0 220 220" style="width:180px;height:180px;display:block;">
      <defs><filter id="{fid}" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="6" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      <g filter="url(#{fid})">{arcs}</g>
      <circle cx="{cx}" cy="{cy}" r="{r_inner-4}" fill="rgba(0,0,0,0.1)" stroke="{colors[0]}33" stroke-width="1"/></svg>"""
    return svg, legend

def render_breakdown(df_in, col, title):
    data = breakdown_by_col(df_in, col)
    if not data:
        return
    data = data[:3]
    st.markdown(f'<div style="color:{ACCENT_SOFT};font-size:0.7em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin:14px 0 8px;">{title}</div>', unsafe_allow_html=True)
    max_exp = max(abs(d['exp']) for d in data) if data else 1
    if max_exp == 0: max_exp = 1
    for rank, d in enumerate(data):
        bar_pct = round(abs(d['exp']) / max_exp * 100, 1)
        color = '#4ade80' if d['exp'] >= 0 else '#f87171'
        lbl = d['label'][:28] + '…' if len(d['label']) > 28 else d['label']
        rank_color = RANK_COLORS[rank] if rank < len(RANK_COLORS) else TEXT_MUTED
        st.markdown(
            f'<div style="display:grid;grid-template-columns:24px 150px 1fr 55px 55px 30px;gap:8px;align-items:center;padding:7px 0;border-bottom:1px solid rgba({BG_TINT},0.06);">'
            f'<span style="color:{rank_color};font-size:0.7em;font-weight:700;">#{rank+1}</span>'
            f'<span style="color:{TEXT_PRIMARY};font-size:0.82em;">{lbl}</span>'
            f'<div style="background:rgba({BG_TINT},0.08);border-radius:6px;height:10px;overflow:hidden;"><div style="width:{bar_pct}%;height:10px;background:linear-gradient(90deg,{color}66,{color});border-radius:6px;"></div></div>'
            f'<span style="color:{color};font-size:0.82em;font-weight:600;">{d["exp"]}R</span>'
            f'<span style="color:{ACCENT_SOFT};font-size:0.82em;">{d["wr"]}%</span>'
            f'<span style="color:{TEXT_MUTED};font-size:0.82em;">{d["n"]}</span>'
            f'</div>', unsafe_allow_html=True)

# ============ LOAD DATA ============
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
                if 'PM' in str(t).upper() and hour != 12: hour += 12
                if 'AM' in str(t).upper() and hour == 12: hour = 0
                return f"{hour:02d}:00"
        except: pass
        return None
    df['Hour'] = df['Time of Trade'].apply(parse_hour)

df_main = df.copy()
df_main = df_main.sort_values('Date').reset_index(drop=True)
if 'Pair' in df_main.columns:
    df_main['Pair'] = df_main['Pair'].str.strip()

df_xau = df_main[df_main['Pair'] == 'XAUUSD'].copy() if 'Pair' in df_main.columns else pd.DataFrame()
df_nas = df_main[df_main['Pair'] == 'NASDAQ'].copy() if 'Pair' in df_main.columns else pd.DataFrame()

if 'Type of Trade' in df_main.columns:
    df_funded = df_main[df_main['Type of Trade'].str.strip() == 'Funded'].copy()
else:
    df_funded = pd.DataFrame()

main_stats = calc_stats(df_main)
xau_stats = calc_stats(df_xau) if len(df_xau) > 0 else {}
nas_stats = calc_stats(df_nas) if len(df_nas) > 0 else {}
session_stats = calc_session_stats(df_main)
daily_r = calc_daily_r(df_main)
monthly_r = calc_monthly_r(df_main)
consistency_score, consistency_breakdown = calc_consistency_score(df_main, session_stats)
best_setup = find_best_setup(df_main)
green_checklist, red_checklist = generate_checklist(df_main, session_stats)

max_abs_exp = max([abs(s['exp']) for s in session_stats]) if session_stats else 1
if max_abs_exp == 0: max_abs_exp = 1
today = datetime.now()

for key, val in [
    ('selected_day', None), ('cal_month', today.month), ('cal_year', today.year),
    ('overview_idx', 0), ('active_page', 'Overview')
]:
    if key not in st.session_state:
        st.session_state[key] = val

css = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  .stApp {{
    background:{BG_BASE};
    background-image: radial-gradient(circle at 15% 10%, {BG_RADIAL1}, transparent 35%),
                       radial-gradient(circle at 85% 0%, {BG_RADIAL2}, transparent 35%);
    font-family:'Inter',sans-serif;
  }}
  @keyframes fadeUp {{
    from {{ opacity:0; transform:translateY(40px); }}
    to {{ opacity:1; transform:translateY(0); }}
  }}
  @keyframes slideIn {{
    from {{ opacity:0; transform:translateX(-20px); }}
    to {{ opacity:1; transform:translateX(0); }}
  }}
  @keyframes pulseGlow {{
    0%, 100% {{ box-shadow: 0 0 8px rgba(74,222,128,0.4); }}
    50% {{ box-shadow: 0 0 20px rgba(74,222,128,0.9), 0 0 40px rgba(74,222,128,0.3); }}
  }}
  @keyframes panelSweep {{
    from {{ left: -100%; }}
    to {{ left: 150%; }}
  }}
  @keyframes growBar {{
    from {{ width: 0; }}
    to {{ width: 100%; }}
  }}
  .main-content {{ animation: fadeUp 0.5s cubic-bezier(0.16,1,0.3,1); }}
  .glass-panel {{
    position: relative; overflow: hidden;
    animation: fadeUp 0.5s cubic-bezier(0.16,1,0.3,1);
    animation-fill-mode: both;
  }}
  .glass-panel::after {{
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba({BG_TINT},0.06), transparent);
    animation: panelSweep 1.5s ease-in-out 0.3s forwards;
    pointer-events: none;
  }}
  .stat-card {{
    animation: fadeUp 0.4s cubic-bezier(0.16,1,0.3,1);
    animation-fill-mode: both;
    position: relative; overflow: hidden;
    transition: all 0.25s ease; cursor: pointer;
  }}
  .stat-card:hover {{ transform:translateY(-2px); }}
  .pnl-card {{ animation: fadeUp 0.5s cubic-bezier(0.16,1,0.3,1); animation-fill-mode: both; }}
  .section-label {{
    animation: slideIn 0.4s cubic-bezier(0.16,1,0.3,1);
    animation-fill-mode: both;
    font-size:0.72em; font-weight:700; letter-spacing:2.5px; text-transform:uppercase;
    color:{ACCENT_SOFT}; margin:32px 0 16px; display:flex; align-items:center; gap:10px;
  }}
  .section-label::after {{ content:''; flex:1; height:1px; background:linear-gradient(90deg, rgba({BG_TINT},0.2), transparent); }}
  .streak-box {{ animation: fadeUp 0.4s cubic-bezier(0.16,1,0.3,1); animation-fill-mode: both; }}
  .streak-box.active-streak {{ animation: pulseGlow 2s ease-in-out infinite !important; }}
  .checklist-item {{ animation: slideIn 0.4s cubic-bezier(0.16,1,0.3,1); animation-fill-mode: both; }}
  .trade-detail-card {{ animation: fadeUp 0.4s cubic-bezier(0.16,1,0.3,1); animation-fill-mode: both; }}
  .cal-week-summary {{ animation: fadeUp 0.5s cubic-bezier(0.16,1,0.3,1); animation-fill-mode: both; }}
  .best-setup-row {{ display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom:1px solid rgba({BG_TINT},0.08); animation: fadeUp 0.4s cubic-bezier(0.16,1,0.3,1) both; }}
  section[data-testid="stSidebar"] {{
    background:{SIDEBAR_BG} !important;
    border-right:1px solid {SIDEBAR_BORDER} !important;
  }}
  section[data-testid="stSidebar"] > div {{ padding-top:0 !important; }}
  .stat-card {{
    background:{BG_CARD}; backdrop-filter:blur(20px);
    border:1px solid {BORDER2}; border-radius:18px; padding:20px 14px;
    text-align:center; box-shadow:0 4px 16px {SHADOW};
  }}
  .stat-value {{ font-size:1.55em; font-weight:700; color:{TEXT_PRIMARY}; }}
  .stat-label {{ color:{ACCENT_SOFT}; font-size:0.64em; margin-top:6px; letter-spacing:0.8px; font-weight:600; text-transform:uppercase; }}
  .glass-panel {{
    background:{BG_GLASS}; backdrop-filter:blur(24px);
    border:1px solid {BORDER}; border-radius:20px; padding:22px;
    box-shadow:0 12px 36px {SHADOW}; margin-bottom:14px;
  }}
  .nav-banner {{
    background:{BG_GLASS}; backdrop-filter:blur(24px);
    border:1px solid {BORDER}; border-radius:20px; padding:0 24px;
    text-align:center; display:flex; align-items:center; justify-content:center;
    min-height:{NAV_H}; box-sizing:border-box; margin-bottom:16px;
  }}
  .nav-label {{ font-size:1.2em; font-weight:800; color:{TEXT_PRIMARY}; }}
  .divider-line {{ border:none; border-top:1px solid {BORDER}; margin:32px 0; }}
  .cal-header {{ color:{ACCENT_SOFT}; font-size:0.72em; text-align:center; letter-spacing:1.5px; font-weight:600; text-transform:uppercase; padding:10px 0; }}
  .cal-day-num {{ color:{CAL_EMPTY_NUM}; font-size:0.78em; font-weight:600; text-align:center; }}
  .cal-week-summary {{ background:{BG_CARD}; border:1px solid {BORDER}; border-radius:16px; padding:12px 6px; text-align:center; min-height:88px; box-shadow:0 2px 8px {SHADOW}; }}
  .cal-week-label {{ color:{ACCENT_SOFT}; font-size:0.68em; font-weight:700; }}
  .cal-week-r {{ font-size:1.2em; font-weight:700; margin-top:10px; color:{TEXT_PRIMARY}; }}
  .cal-day-trades {{ color:{TEXT_SECONDARY}; font-size:0.64em; margin-top:3px; text-align:center; }}
  div[data-testid="stButton"] button {{
    width:100%; min-height:44px; border-radius:16px;
    font-family:'Inter',sans-serif; white-space:pre-line; line-height:1.4;
    transition:all 0.25s ease; font-weight:600;
    background:{BG_CARD} !important;
    border:1px solid {BORDER} !important; color:{TEXT_PRIMARY} !important;
    box-shadow:0 2px 8px {SHADOW} !important;
  }}
  div[data-testid="stButton"] button:hover {{ transform:translateY(-2px); border-color:{ACCENT} !important; }}
  div[data-testid="column"]:first-child div[data-testid="stButton"] button,
  div[data-testid="column"]:last-child div[data-testid="stButton"] button {{
    min-height:88px !important; border-radius:20px !important; font-size:1.1em !important;
  }}
  .trade-detail-card {{ background:{BG_CARD}; border:1px solid {BORDER}; border-radius:16px; padding:16px 20px; margin-bottom:10px; box-shadow:0 2px 8px {SHADOW}; }}
  .eq-legend {{ display:flex; gap:24px; margin-bottom:12px; flex-wrap:wrap; }}
  .eq-legend-item {{ display:flex; align-items:center; gap:8px; font-size:0.82em; font-weight:600; }}
  .eq-legend-dot {{ width:28px; height:3px; border-radius:2px; }}
  .streak-box {{ width:30px; height:30px; border-radius:7px; display:inline-flex; align-items:center; justify-content:center; font-size:11px; font-weight:700; margin:2px; }}
  .checklist-item {{ display:flex; align-items:flex-start; gap:12px; padding:10px 0; border-bottom:1px solid {BORDER}; }}
  .checklist-dot {{ width:8px; height:8px; border-radius:50%; margin-top:5px; flex-shrink:0; }}
  .glass-panel div::-webkit-scrollbar {{ display:none; }}
 section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
    min-height:40px !important; background:{BG_CARD} !important;
    border:1px solid {BORDER} !important; color:{TEXT_PRIMARY} !important;
    border-radius:10px !important; font-size:0.85em !important;
    box-shadow:0 1px 4px {SHADOW} !important;
    text-align:left !important; padding-left:14px !important;
    display:flex !important; align-items:center !important;
    justify-content:flex-start !important;
  }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] button * {{
    text-align:left !important;
    justify-content:flex-start !important;
  }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{
    border-color:{ACCENT} !important;
  }}
  section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {{
    margin:0 !important; padding:0 !important;
  }}
  section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {{
    margin:0 !important; padding:0 !important;
  }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] button[data-testid="baseButton-secondary"] {{
    min-height:6px !important; max-height:6px !important; height:6px !important;
    opacity:0 !important; padding:0 !important; margin:0 !important;
    border:none !important; background:transparent !important; overflow:hidden !important;
    box-shadow:none !important;
  }}
  #mode_toggle div[data-testid="stButton"] button,
  div[data-testid="stButton"] button[kind="secondary"][data-testid="mode_toggle"] {{
    border-radius:50% !important; width:40px !important; height:40px !important;
    min-height:40px !important; max-width:40px !important; padding:0 !important;
    font-size:1.1em !important;
  }}
  .cal-arrows div[data-testid="stButton"] button {{
    min-height:44px !important; max-height:44px !important; height:44px !important;
    border-radius:10px !important; font-size:1em !important;
    padding:0 !important; margin:0 !important;
  }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown(f'<div style="font-size:1.1em;font-weight:700;color:{TEXT_PRIMARY};padding:20px 16px 16px;border-bottom:1px solid {BORDER};margin-bottom:8px;">Trading Data</div>', unsafe_allow_html=True)
    svg_overview = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>'
    svg_pnl = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M14.8 9A2 2 0 0 0 13 8h-2a2 2 0 0 0 0 4h2a2 2 0 0 1 0 4h-2a2 2 0 0 1-1.8-1"/><path d="M12 7v1m0 8v1"/></svg>'
    svg_charts = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>'
    svg_calendar = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>'
    svg_edge = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
    svg_best = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
    pages = [(svg_overview, 'Overview'), (svg_pnl, 'P&L Tracker'), (svg_charts, 'Charts'), (svg_calendar, 'Calendar'), (svg_edge, 'Edge Analysis'), (svg_best, 'Best Setups')]
    for icon, page_name in pages:
        is_active = st.session_state.active_page == page_name
        if is_active:
            st.markdown(
                f'<div style="background:rgba({BG_TINT},0.1);border-left:3px solid {ACCENT};border-radius:8px;padding:9px 14px;margin:0;font-size:0.85em;font-weight:600;color:{ACCENT};line-height:1.6;">{page_name}</div>',
                unsafe_allow_html=True)
        else:
            if st.button(page_name, key=f"nav_{page_name}", use_container_width=True):
                st.session_state.active_page = page_name
                st.rerun()
    st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
    if st.button("↻ Refresh", key="refresh_btn", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.button("🔒 Logout", key="logout_btn", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    st.markdown(f'<div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:12px;"><div style="font-size:0.6em;color:{TEXT_MUTED};letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">Theme</div></div>', unsafe_allow_html=True)
    theme_options = {'Blue': '#60a5fa', 'Purple': '#a78bfa', 'Green': '#34d399', 'Red': '#f87171', 'Neutral': '#9ca3af'}
    theme_cols = st.columns(5)
    for i, (name, hex_color) in enumerate(theme_options.items()):
        is_active = st.session_state.theme == name
        border = '2px solid #fff' if is_active else '2px solid transparent'
        shadow = f'box-shadow:0 0 8px {hex_color};' if is_active else ''
        theme_cols[i].markdown(f'<div style="width:22px;height:22px;border-radius:50%;background:{hex_color};border:{border};{shadow}margin:auto;"></div>', unsafe_allow_html=True)
        if theme_cols[i].button(" ", key=f"theme_{name}", use_container_width=True):
            st.session_state.theme = name
            st.rerun()

    # Dark/Light toggle at bottom
    st.markdown('<div style="flex:1;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:16px;"></div>', unsafe_allow_html=True)
    mode_icon = "☀️" if IS_DARK else "🌙"
    col_gap, col_btn = st.columns([3, 1])
    col_gap.markdown(f'<div style="font-size:0.7em;color:{TEXT_MUTED};padding-top:10px;">{("Light Mode" if IS_DARK else "Dark Mode")}</div>', unsafe_allow_html=True)
    with col_btn:
        if st.button(mode_icon, key="mode_toggle", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

page = st.session_state.active_page
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.markdown('<a name="top"></a>', unsafe_allow_html=True)
components.html("""
<script>
(function() {
    function scroll() {
        try {
            var doc = window.parent.document;
            var el = doc.querySelector('section.stMain');
            if (el) el.scrollTop = 0;
        } catch(e) {}
    }
    setTimeout(scroll, 100);
    setTimeout(scroll, 400);
    setTimeout(scroll, 800);
    setTimeout(scroll, 1200);
})();
</script>
""", height=0)
# ============ PAGE: OVERVIEW ============
if page == 'Overview':
    st.markdown(f'<div style="font-size:1.6em;font-weight:700;color:{TEXT_PRIMARY};margin-bottom:4px;">Overview</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.75em;color:{TEXT_SECONDARY};margin-bottom:24px;">{main_stats.get("total_trades","—")} trades total</div>', unsafe_allow_html=True)

    cur = main_stats.get('cur_streak', 0)
    cur_type = main_stats.get('cur_streak_type', '—')
    cur_color = '#4ade80' if cur_type == 'W' else ('#f87171' if cur_type == 'L' else ACCENT)
    cur_label = 'Win Streak' if cur_type == 'W' else ('Loss Streak' if cur_type == 'L' else 'Streak')
    this_month_key = today.strftime('%Y-%m')
    this_month_r = monthly_r.get(this_month_key, {}).get('total_r', 0)
    last_month_key = (today.replace(day=1) - pd.Timedelta(days=1)).strftime('%Y-%m')
    last_month_r = monthly_r.get(last_month_key, {}).get('total_r', 0)
    diff = round(this_month_r - last_month_r, 2)
    diff_color = '#4ade80' if diff >= 0 else '#f87171'
    diff_sign = '+' if diff >= 0 else ''
    month_sign = '+' if this_month_r > 0 else ''

    st.markdown(
        f'<div class="glass-panel" style="display:flex;align-items:center;padding:18px 24px;">'
        f'<div style="text-align:center;flex:1;"><div style="font-size:1.6em;font-weight:700;color:{cur_color};">{cur}</div><div style="font-size:0.62em;color:{TEXT_SECONDARY};margin-top:3px;text-transform:uppercase;letter-spacing:0.5px;">{cur_label}</div></div>'
        f'<div style="width:1px;height:40px;background:{BORDER};"></div>'
        f'<div style="text-align:center;flex:1;"><div style="font-size:1.6em;font-weight:700;color:{ACCENT};" id="banner-consistency">0%</div><div style="font-size:0.62em;color:{TEXT_SECONDARY};margin-top:3px;text-transform:uppercase;letter-spacing:0.5px;">Consistency</div></div>'
        f'<div style="width:1px;height:40px;background:{BORDER};"></div>'
        f'<div style="text-align:center;flex:1;"><div style="font-size:1.6em;font-weight:700;color:{TEXT_PRIMARY};" id="banner-month">0R</div><div style="font-size:0.62em;color:{TEXT_SECONDARY};margin-top:3px;text-transform:uppercase;letter-spacing:0.5px;">This Month</div></div>'
        f'<div style="width:1px;height:40px;background:{BORDER};"></div>'
        f'<div style="text-align:center;flex:1;"><div style="font-size:1.6em;font-weight:700;color:{diff_color};" id="banner-diff">0R</div><div style="font-size:0.62em;color:{TEXT_SECONDARY};margin-top:3px;text-transform:uppercase;letter-spacing:0.5px;">vs Last Month</div></div>'
        f'</div>',
        unsafe_allow_html=True)

    components.html(f"""
<script>
function countUp(selector, target, decimals, suffix, finalText, duration) {{
    var el = window.parent.document.getElementById(selector);
    if (!el) return;
    var startTime = null;
    function step(ts) {{
        if (!startTime) startTime = ts;
        var progress = Math.min((ts - startTime) / duration, 1);
        var ease = 1 - Math.pow(1 - progress, 3);
        var val = target * ease;
        el.textContent = (decimals > 0 ? val.toFixed(decimals) : Math.round(val)) + suffix;
        if (progress < 1) requestAnimationFrame(step);
        else el.textContent = finalText;
    }}
    requestAnimationFrame(step);
}}
setTimeout(function() {{
    countUp('banner-consistency', {consistency_score}, 0, '%', '{consistency_score}%', 1000);
    countUp('banner-month', {abs(this_month_r)}, 2, 'R', '{month_sign}{this_month_r}R', 1000);
    countUp('banner-diff', {abs(diff)}, 2, 'R', '{diff_sign}{diff}R', 1000);
}}, 200);
setTimeout(function() {{
    var doc = window.parent.document;
    var targets = doc.querySelectorAll('.glass-panel, .stat-card, .checklist-item, .trade-detail-card, .cal-week-summary, .streak-box, .pnl-card');
    targets.forEach(function(el) {{
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'none';
        el.style.animationName = 'none';
    }});
    var observer = new IntersectionObserver(function(entries) {{
        entries.forEach(function(entry) {{
            if (entry.isIntersecting) {{
                var el = entry.target;
                var delay = parseInt(el.style.animationDelay) || 0;
                setTimeout(function() {{
                    el.style.transition = 'opacity 0.5s cubic-bezier(0.16,1,0.3,1), transform 0.5s cubic-bezier(0.16,1,0.3,1)';
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }}, delay);
                observer.unobserve(el);
            }}
        }});
    }}, {{ threshold: 0.1, rootMargin: '0px 0px -40px 0px' }});
    targets.forEach(function(el) {{ observer.observe(el); }});
    var bars = doc.querySelectorAll('.grow-bar');
    var barObserver = new IntersectionObserver(function(entries) {{
        entries.forEach(function(entry) {{
            if (entry.isIntersecting) {{
                entry.target.style.animationPlayState = 'running';
                barObserver.unobserve(entry.target);
            }}
        }});
    }}, {{ threshold: 0.1 }});
    bars.forEach(function(bar) {{
        var rect = bar.getBoundingClientRect();
        if (rect.top < window.parent.innerHeight) {{
            bar.style.animationPlayState = 'running';
        }} else {{
            barObserver.observe(bar);
        }}
    }});
}}, 400);
</script>
    """, height=0)

    st.markdown(f'<div class="section-label">Performance</div>', unsafe_allow_html=True)
    overviews = [
        {'label': 'Overall', 'stats': main_stats, 'color': ACCENT_SOFT},
        {'label': 'XAUUSD', 'stats': xau_stats, 'color': GOLD_SOFT},
        {'label': 'NASDAQ', 'stats': nas_stats, 'color': PURPLE_SOFT},
    ]
    idx = st.session_state.overview_idx
    current = overviews[idx]

    prev_col, next_col = st.columns(2)
    with prev_col:
        if st.button(f"← {overviews[(idx-1) % len(overviews)]['label']}", key="prev_ov", use_container_width=True):
            st.session_state.overview_idx = (idx - 1) % len(overviews)
            st.rerun()
    with next_col:
        if st.button(f"{overviews[(idx+1) % len(overviews)]['label']} →", key="next_ov", use_container_width=True):
            st.session_state.overview_idx = (idx + 1) % len(overviews)
            st.rerun()

    st.markdown(f'<div class="nav-banner"><span class="nav-label" style="color:{current["color"]};">{current["label"]} Performance</span></div>', unsafe_allow_html=True)

    stat_data = [
        ('Total Trades', current['stats'].get('total_trades', '—')),
        ('Win Rate', f"{current['stats'].get('win_rate', '—')}%"),
        ('Total R', current['stats'].get('total_r', '—')),
        ('Avg R / Trade', current['stats'].get('avg_r', '—')),
        ('Expectancy', current['stats'].get('expectancy', '—')),
        ('Avg Win', current['stats'].get('avg_win', '—')),
        ('Avg Loss', current['stats'].get('avg_loss', '—')),
        ('Best Trade', current['stats'].get('best_trade', '—')),
        ('Worst Trade', current['stats'].get('worst_trade', '—')),
        ('Max Drawdown', current['stats'].get('max_drawdown', '—')),
        ('Max Streak', current['stats'].get('max_consec_losses', '—')),
        ('Wins', current['stats'].get('wins', '—')),
        ('Losses', current['stats'].get('losses', '—')),
        ('Breakevens', current['stats'].get('breakevens', '—')),
    ]
    for i in range(0, len(stat_data), 7):
        row_data = stat_data[i:i+7]
        cols = st.columns(len(row_data))
        for j, (col, (label, value)) in enumerate(zip(cols, row_data)):
            delay = j * 25
            col.markdown(
                f'<div class="stat-card" style="border-color:{current["color"]}44;animation-delay:{delay}ms;">'
                f'<div class="stat-value">{value}</div>'
                f'<div class="stat-label" style="color:{current["color"]};">{label}</div>'
                f'</div>', unsafe_allow_html=True)
        st.write("")

    st.markdown('<div class="section-label">Recent Trades</div>', unsafe_allow_html=True)
    trade_results = main_stats.get('trade_results', [])
    streak_html = '<div style="display:flex;gap:4px;margin-bottom:8px;overflow-x:auto;padding-bottom:6px;scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;">'
    for idx_r, r in enumerate(trade_results):
        is_last = idx_r == len(trade_results) - 1
        color = 'rgba(74,222,128,0.8)' if r == 'W' else ('rgba(248,113,113,0.7)' if r == 'L' else f'rgba({BG_TINT},0.5)')
        text_color = '#000' if r == 'W' else '#fff'
        extra_class = 'active-streak' if is_last else ''
        streak_html += f'<div class="streak-box {extra_class}" style="background:{color};color:{text_color};animation-delay:{idx_r*30}ms;flex-shrink:0;">{r}</div>'
    streak_html += f'<div class="streak-box" style="border:1px dashed {BORDER};color:{TEXT_MUTED};flex-shrink:0;">?</div></div>'
    streak_html += f'<div style="font-size:0.72em;color:{TEXT_SECONDARY};"><span style="color:{cur_color};">Current streak: {cur} {cur_type}</span></div>'
    st.markdown(f'<div class="glass-panel">{streak_html}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Month vs Month</div>', unsafe_allow_html=True)
    months = sorted(monthly_r.keys())[-4:]
    if months:
        month_cols = st.columns(len(months))
        for i, (col, m) in enumerate(zip(month_cols, months)):
            data = monthly_r[m]
            sign = '+' if data['total_r'] > 0 else ''
            is_current = m == this_month_key
            current_lbl = f'<div style="color:{ACCENT_SOFT};font-size:0.65em;margin-top:4px;">Current</div>' if is_current else ''
            bg = BG_CARD if is_current else 'transparent'
            border_col = ACCENT if is_current else BORDER
            header_color = ACCENT_SOFT if is_current else TEXT_SECONDARY
            col.markdown(
                f'<div style="background:{bg};border:1px solid {border_col};border-radius:14px;padding:14px;text-align:center;animation:fadeUp 0.5s cubic-bezier(0.16,1,0.3,1) {i*80}ms both;box-shadow:{SHADOW} 0 2px 8px;">'
                f'<div style="color:{header_color};font-size:0.65em;margin-bottom:6px;text-transform:uppercase;">{m}</div>'
                f'<div style="color:{TEXT_PRIMARY};font-size:1.2em;font-weight:700;">{sign}{data["total_r"]}R</div>'
                f'<div style="color:{TEXT_SECONDARY};font-size:0.65em;margin-top:4px;">{data["win_rate"]}% WR · {data["trades"]} trades</div>'
                f'{current_lbl}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">3SL Window</div>', unsafe_allow_html=True)
    session_rows_html = ""
    for idx_s, s in enumerate(session_stats):
        bar_pct = round(abs(s['exp']) / max_abs_exp * 100, 1)
        bar_color = f'linear-gradient(90deg,rgba({BG_TINT},0.6),{ACCENT})' if s['exp'] >= 0 else 'linear-gradient(90deg,rgba(248,113,113,0.6),#f87171)'
        delay = idx_s * 400
        session_rows_html += (
            f'<div style="display:grid;grid-template-columns:100px 1fr 70px 60px 40px;gap:16px;align-items:center;padding:10px 0;">'
            f'<span style="color:{ACCENT_SOFT};font-weight:600;">{s["session"]}</span>'
            f'<div style="background:rgba({BG_TINT},0.1);border-radius:8px;height:14px;overflow:hidden;">'
            f'<div style="width:{bar_pct}%;height:14px;overflow:hidden;border-radius:8px;">'
            f'<div class="grow-bar" style="width:100%;height:14px;background:{bar_color};border-radius:8px;animation:growBar 1.5s cubic-bezier(0.16,1,0.3,1) {delay}ms both;animation-play-state:paused;"></div>'
            f'</div></div>'
            f'<span style="color:{TEXT_PRIMARY};font-weight:700;">{s["exp"]}</span>'
            f'<span style="color:{ACCENT_SOFT};">{s["wr"]}</span>'
            f'<span style="color:{TEXT_MUTED};">{s["n"]}</span>'
            f'</div>')
    st.markdown(
        f'<div class="glass-panel">'
        f'<div style="display:grid;grid-template-columns:100px 1fr 70px 60px 40px;gap:16px;padding-bottom:10px;margin-bottom:4px;border-bottom:1px solid {BORDER};">'
        f'<span style="color:{ACCENT_SOFT};font-size:0.7em;font-weight:600;">SESSION</span>'
        f'<span style="color:{ACCENT_SOFT};font-size:0.7em;font-weight:600;">CHART</span>'
        f'<span style="color:{ACCENT_SOFT};font-size:0.7em;font-weight:600;">EXP</span>'
        f'<span style="color:{ACCENT_SOFT};font-size:0.7em;font-weight:600;">WR</span>'
        f'<span style="color:{ACCENT_SOFT};font-size:0.7em;font-weight:600;">N</span>'
        f'</div>{session_rows_html}</div>', unsafe_allow_html=True)

# ============ PAGE: P&L TRACKER ============
elif page == 'P&L Tracker':
    st.markdown(f'<div style="font-size:1.6em;font-weight:700;color:{TEXT_PRIMARY};margin-bottom:24px;">P&L Tracker</div>', unsafe_allow_html=True)

    set_cols = st.columns(3)
    with set_cols[0]:
        account_size = st.number_input("Account Size ($)", min_value=1000, max_value=10000000, value=st.session_state.account_size, step=1000, format="%d")
        st.session_state.account_size = account_size
    with set_cols[1]:
        num_accounts = st.number_input("Number of Accounts", min_value=1, max_value=50, value=st.session_state.num_accounts, step=1)
        st.session_state.num_accounts = num_accounts
    with set_cols[2]:
        risk_per_trade = st.number_input("Risk Per Trade ($)", min_value=1, max_value=100000, value=st.session_state.risk_per_trade, step=50)
        st.session_state.risk_per_trade = risk_per_trade

    total_capital = account_size * num_accounts
    combined_risk = risk_per_trade * num_accounts

    if len(df_funded) > 0 and 'R_Result' in df_funded.columns:
        df_funded_clean = df_funded.dropna(subset=['R_Result', 'Date']).copy()
        month_funded = df_funded_clean[(df_funded_clean['Date'].dt.month == today.month) & (df_funded_clean['Date'].dt.year == today.year)]
        month_r = month_funded['R_Result'].sum()
        month_pnl = round(month_r * combined_risk, 2)
        month_pct = round(month_pnl / total_capital * 100, 2)
        week_start = today - pd.Timedelta(days=today.weekday())
        week_funded = df_funded_clean[df_funded_clean['Date'].dt.date >= week_start.date()]
        week_r = week_funded['R_Result'].sum()
        week_pnl = round(week_r * combined_risk, 2)
        week_pct = round(week_pnl / total_capital * 100, 2)
        today_funded = df_funded_clean[df_funded_clean['Date'].dt.date == today.date()]
        today_r = today_funded['R_Result'].sum()
        today_pnl = round(today_r * combined_risk, 2)
        today_pct = round(today_pnl / total_capital * 100, 2)

        def fmt_pnl(val): return f"+${val:,.2f}" if val >= 0 else f"-${abs(val):,.2f}"
        def fmt_pct(val): return f"+{val}%" if val >= 0 else f"{val}%"
        def pnl_color(val): return '#4ade80' if val >= 0 else '#f87171'

        st.markdown(f'<div style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:14px;">Performance</div>', unsafe_allow_html=True)
        pnl_data = [
            ('This Month', month_pnl, month_pct, f"{round(month_r,2)}R", len(month_funded)),
            ('This Week', week_pnl, week_pct, f"{round(week_r,2)}R", len(week_funded)),
            ('Today', today_pnl, today_pct, f"{round(today_r,2)}R", len(today_funded)),
        ]
        pnl_cols = st.columns(3)
        for i, (col, (period, pnl, pct, r_val, n_trades)) in enumerate(zip(pnl_cols, pnl_data)):
            color = pnl_color(pnl)
            col.markdown(
                f'<div class="pnl-card" style="background:{BG_CARD};border:1px solid {BORDER2};border-radius:18px;padding:20px 14px;text-align:center;animation-delay:{i*100}ms;box-shadow:0 4px 16px {SHADOW};">'
                f'<div style="font-size:0.62em;color:{TEXT_SECONDARY};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">{period}</div>'
                f'<div style="font-size:1.5em;font-weight:700;color:{color};" id="pnl-{i}">{fmt_pnl(pnl)}</div>'
                f'<div style="font-size:1em;font-weight:700;color:{color};margin-top:4px;" id="pct-{i}">{fmt_pct(pct)}</div>'
                f'<div style="font-size:0.65em;color:{TEXT_SECONDARY};margin-top:8px;border-top:1px solid {BORDER};padding-top:8px;">{r_val} &nbsp;·&nbsp; {n_trades} trades</div>'
                f'</div>', unsafe_allow_html=True)

        components.html(f"""
<script>
function countMoney(id, target, duration) {{
    var el = window.parent.document.getElementById(id);
    if (!el) return;
    var startTime = null;
    var prefix = target >= 0 ? '+$' : '-$';
    var absTarget = Math.abs(target);
    function step(ts) {{
        if (!startTime) startTime = ts;
        var progress = Math.min((ts - startTime) / duration, 1);
        var ease = 1 - Math.pow(1 - progress, 3);
        el.textContent = prefix + (absTarget * ease).toLocaleString('en-US', {{minimumFractionDigits:2, maximumFractionDigits:2}});
        if (progress < 1) requestAnimationFrame(step);
    }}
    requestAnimationFrame(step);
}}
function countPct(id, target, duration) {{
    var el = window.parent.document.getElementById(id);
    if (!el) return;
    var startTime = null;
    var prefix = target >= 0 ? '+' : '-';
    var absTarget = Math.abs(target);
    function step(ts) {{
        if (!startTime) startTime = ts;
        var progress = Math.min((ts - startTime) / duration, 1);
        var ease = 1 - Math.pow(1 - progress, 3);
        el.textContent = prefix + (absTarget * ease).toFixed(2) + '%';
        if (progress < 1) requestAnimationFrame(step);
    }}
    requestAnimationFrame(step);
}}
setTimeout(function() {{
    countMoney('pnl-0', {month_pnl}, 1000);
    countMoney('pnl-1', {week_pnl}, 1000);
    countMoney('pnl-2', {today_pnl}, 1000);
    countPct('pct-0', {month_pct}, 1000);
    countPct('pct-1', {week_pct}, 1000);
    countPct('pct-2', {today_pct}, 1000);
}}, 300);
</script>
        """, height=0)

        st.markdown(f'<div style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin:24px 0 14px;">All Time (Funded)</div>', unsafe_allow_html=True)
        total_r_funded = df_funded_clean['R_Result'].sum()
        total_pnl_funded = round(total_r_funded * combined_risk, 2)
        total_pct_funded = round(total_pnl_funded / total_capital * 100, 2)
        color_total = '#4ade80' if total_pnl_funded >= 0 else '#f87171'
        sign_total = '+' if total_pnl_funded >= 0 else ''
        at_cols = st.columns(4)
        at_cols[0].markdown(f'<div class="pnl-card" style="background:{BG_CARD};border:1px solid {BORDER2};border-radius:18px;padding:18px 14px;text-align:center;box-shadow:0 4px 16px {SHADOW};"><div style="font-size:0.6em;color:{TEXT_SECONDARY};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total P&L</div><div style="font-size:1.3em;font-weight:700;color:{color_total};">{sign_total}${abs(total_pnl_funded):,.2f}</div><div style="font-size:0.8em;color:{color_total};margin-top:3px;">{sign_total}{total_pct_funded}%</div></div>', unsafe_allow_html=True)
        at_cols[1].markdown(f'<div class="pnl-card" style="background:{BG_CARD};border:1px solid {BORDER2};border-radius:18px;padding:18px 14px;text-align:center;box-shadow:0 4px 16px {SHADOW};"><div style="font-size:0.6em;color:{TEXT_SECONDARY};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total R</div><div style="font-size:1.3em;font-weight:700;color:{TEXT_PRIMARY};">{sign_total}{round(total_r_funded,2)}R</div></div>', unsafe_allow_html=True)
        at_cols[2].markdown(f'<div class="pnl-card" style="background:{BG_CARD};border:1px solid {BORDER2};border-radius:18px;padding:18px 14px;text-align:center;box-shadow:0 4px 16px {SHADOW};"><div style="font-size:0.6em;color:{TEXT_SECONDARY};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Funded Trades</div><div style="font-size:1.3em;font-weight:700;color:{TEXT_PRIMARY};">{len(df_funded_clean)}</div></div>', unsafe_allow_html=True)
        at_cols[3].markdown(f'<div class="pnl-card" style="background:{BG_CARD};border:1px solid {BORDER2};border-radius:18px;padding:18px 14px;text-align:center;box-shadow:0 4px 16px {SHADOW};"><div style="font-size:0.6em;color:{TEXT_SECONDARY};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total Capital</div><div style="font-size:1.3em;font-weight:700;color:{ACCENT_SOFT};">${total_capital:,}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="glass-panel" style="text-align:center;padding:48px 24px;"><div style="font-size:1.4em;margin-bottom:12px;">💰</div><div style="color:{TEXT_PRIMARY};font-weight:600;margin-bottom:8px;">No trades yet</div></div>', unsafe_allow_html=True)

# ============ PAGE: CHARTS ============
elif page == 'Charts':
    st.markdown(f'<div style="font-size:1.6em;font-weight:700;color:{TEXT_PRIMARY};margin-bottom:24px;">Charts</div>', unsafe_allow_html=True)

    xau_eq = xau_stats.get('equity_curve', [])
    nas_eq = nas_stats.get('equity_curve', [])
    svg_w, svg_h = 800, 200
    xau_line, xau_fill = make_curve(xau_eq, svg_w, svg_h)
    nas_line, nas_fill = make_curve(nas_eq, svg_w, svg_h)
    xau_fill_path = f'<path d="{xau_fill}" fill="url(#xauFill)" opacity="0.5"/>' if xau_fill else ''
    xau_line_path = f'<path d="{xau_line}" fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round" filter="url(#xauGlow)" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2.5s" begin="0s" fill="freeze"/></path>' if xau_line else ''
    nas_line_path = f'<path d="{nas_line}" fill="none" stroke="{PURPLE}" stroke-width="3" stroke-linecap="round" filter="url(#nasGlow)" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2.5s" begin="0.4s" fill="freeze"/></path>' if nas_line else ''

    combined_svg = f"""<svg viewBox="0 0 {svg_w} {svg_h}" style="width:100%;height:280px;display:block;">
      <defs>
        <linearGradient id="xauFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba(245,158,11,0.3)"/><stop offset="100%" stop-color="rgba(245,158,11,0)"/></linearGradient>
        <filter id="xauGlow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        <filter id="nasGlow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      {xau_fill_path}{xau_line_path}{nas_line_path}
    </svg>"""

    st.markdown(
        f'<div class="glass-panel"><div style="color:{TEXT_PRIMARY};font-weight:600;font-size:1.05em;margin-bottom:8px;">Equity Curve</div>'
        f'<div class="eq-legend">'
        f'<div class="eq-legend-item"><div class="eq-legend-dot" style="background:{GOLD};box-shadow:0 0 6px {GOLD};"></div><span style="color:{GOLD_SOFT};">XAUUSD ({len(xau_eq)} trades)</span></div>'
        f'<div class="eq-legend-item"><div class="eq-legend-dot" style="background:{PURPLE};box-shadow:0 0 6px {PURPLE};"></div><span style="color:{PURPLE_SOFT};">NASDAQ ({len(nas_eq)} trades)</span></div>'
        f'</div>{combined_svg}</div>', unsafe_allow_html=True)

    rolling = main_stats.get('rolling_wr', [])
    if rolling:
        rsvg_w, rsvg_h = 800, 120
        n = len(rolling)
        pts = [((i / (n-1)) * rsvg_w if n > 1 else 0, rsvg_h - ((v / 100) * (rsvg_h - 20)) - 10) for i, v in enumerate(rolling)]
        rline = catmull(pts)
        rfill = rline + f"L{rsvg_w},{rsvg_h} L0,{rsvg_h} Z" if rline else ""
        baseline_y = rsvg_h - (0.5 * (rsvg_h - 20)) - 10
        trending = rolling[-1] > rolling[0] if len(rolling) > 1 else False
        trend_color = '#4ade80' if trending else '#f87171'
        trend_text = 'Trending up ↑' if trending else 'Trending down ↓'
        trend_bg = '74,222,128' if trending else '248,113,113'
        rsvg = f"""<svg viewBox="0 0 {rsvg_w} {rsvg_h}" style="width:100%;height:120px;display:block;">
          <defs><linearGradient id="rFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba({BG_TINT},0.25)"/><stop offset="100%" stop-color="rgba({BG_TINT},0)"/></linearGradient></defs>
          <line x1="0" y1="{baseline_y:.1f}" x2="{rsvg_w}" y2="{baseline_y:.1f}" stroke="rgba(0,0,0,0.08)" stroke-width="1" stroke-dasharray="4,4"/>
          {'<path d="' + rfill + '" fill="url(#rFill)"/>' if rfill else ''}
          {'<path d="' + rline + f'" fill="none" stroke="{ACCENT}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2s" begin="0s" fill="freeze"/></path>' if rline else ''}
        </svg>"""
        st.markdown(
            f'<div class="glass-panel"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
            f'<div><div style="color:{TEXT_PRIMARY};font-weight:600;font-size:1.05em;">Rolling Win Rate</div><div style="color:{TEXT_SECONDARY};font-size:0.72em;margin-top:2px;">Last 10 trades window</div></div>'
            f'<div style="background:rgba({trend_bg},0.1);border:1px solid rgba({trend_bg},0.2);border-radius:8px;padding:4px 10px;font-size:0.72em;color:{trend_color};">{trend_text}</div>'
            f'</div>{rsvg}</div>', unsafe_allow_html=True)

    donut_configs = [
        ('Overall', main_stats.get('wins',0), main_stats.get('losses',0), main_stats.get('breakevens',0), [ACCENT, f'{ACCENT}aa', f'{ACCENT}44'], f'rgba({BG_TINT},0.4)', ACCENT_SOFT),
        ('XAUUSD', xau_stats.get('wins',0), xau_stats.get('losses',0), xau_stats.get('breakevens',0), ['#b45309','#f59e0b','#fde68a'], 'rgba(245,158,11,0.4)', GOLD_SOFT),
        ('NASDAQ', nas_stats.get('wins',0), nas_stats.get('losses',0), nas_stats.get('breakevens',0), ['#6d28d9','#a78bfa','#ede9fe'], 'rgba(167,139,250,0.4)', PURPLE_SOFT),
    ]
    donut_cols = st.columns(3)
    for col, (label, w, l, b, colors, glow, title_color) in zip(donut_cols, donut_configs):
        svg, legend = build_donut(w, l, b, colors, glow)
        col.markdown(f'<div class="glass-panel" style="border-color:{colors[1]}44;"><div style="color:{title_color};font-weight:600;font-size:1em;margin-bottom:14px;">{label}</div><div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;"><div>{svg}</div><div style="flex:1;min-width:100px;">{legend}</div></div></div>', unsafe_allow_html=True)

# ============ PAGE: CALENDAR ============
elif page == 'Calendar':
    st.markdown(f'<div style="font-size:1.6em;font-weight:700;color:{TEXT_PRIMARY};margin-bottom:24px;">Calendar</div>', unsafe_allow_html=True)

    cal_month = st.session_state.cal_month
    cal_year = st.session_state.cal_year
    month_total_r = sum(v['total_r'] for k, v in daily_r.items() if k.month == cal_month and k.year == cal_year)
    month_sign2 = '+' if month_total_r > 0 else ''
    month_name = datetime(cal_year, cal_month, 1).strftime("%B %Y")

    nav_left, nav_right = st.columns([7, 2])
    nav_left.markdown(
        f'<div style="background:{BG_GLASS};border:1px solid {BORDER};border-radius:20px;height:44px;display:flex;align-items:center;padding:0 20px;margin-bottom:16px;box-shadow:0 2px 8px {SHADOW};">'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<div style="font-size:1.1em;font-weight:800;color:{TEXT_PRIMARY};">{month_name}</div>'
        f'<div style="font-size:0.75em;color:{ACCENT};font-weight:600;">{month_sign2}{round(month_total_r,2)}R</div>'
        f'</div></div>', unsafe_allow_html=True)
    with nav_right:
        st.markdown('<div class="cal-arrows">', unsafe_allow_html=True)
        arr_l, arr_r = st.columns(2)
        with arr_l:
            if st.button("‹", key="prev_month", use_container_width=True):
                if st.session_state.cal_month == 1:
                    st.session_state.cal_month = 12; st.session_state.cal_year -= 1
                else:
                    st.session_state.cal_month -= 1
                st.rerun()
        with arr_r:
            if st.button("›", key="next_month", use_container_width=True):
                if st.session_state.cal_month == 12:
                    st.session_state.cal_month = 1; st.session_state.cal_year += 1
                else:
                    st.session_state.cal_month += 1
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    cal_module.setfirstweekday(cal_module.MONDAY)
    month_matrix = cal_module.monthcalendar(cal_year, cal_month)
    day_header_cols = st.columns(8)
    for i, d in enumerate(['Mo','Tu','We','Th','Fr','Sa','Su']):
        day_header_cols[i].markdown(f'<div class="cal-header">{d}</div>', unsafe_allow_html=True)
    day_header_cols[7].markdown(f'<div class="cal-header">Week</div>', unsafe_allow_html=True)

    for week_num, week in enumerate(month_matrix):
        if week_num > 0: st.write("")
        week_cols = st.columns(8)
        week_total = week_trades = 0
        for i, day_num in enumerate(week):
            if day_num == 0:
                week_cols[i].markdown('<div style="min-height:88px;"></div>', unsafe_allow_html=True)
            else:
                day_date = datetime(cal_year, cal_month, day_num).date()
                day_data = daily_r.get(day_date)
                if day_data:
                    week_total += day_data['total_r']; week_trades += day_data['trades']
                    r_val = day_data['total_r']; sign = '+' if r_val > 0 else ''
                    if r_val >= 0:
                        day_style = "background:rgba(74,222,128,0.08);border:1px solid rgba(74,222,128,0.25);box-shadow:0 4px 12px rgba(74,222,128,0.08);"
                        r_color = '#16a34a' if not IS_DARK else '#4ade80'
                        num_color = '#14532d' if not IS_DARK else '#eafff0'
                    else:
                        day_style = "background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.25);box-shadow:0 4px 12px rgba(248,113,113,0.08);"
                        r_color = '#dc2626' if not IS_DARK else '#f87171'
                        num_color = '#7f1d1d' if not IS_DARK else '#ffeaea'
                    delay = (week_num * 7 + i) * 35
                    week_cols[i].markdown(
                        f'<div style="{day_style}backdrop-filter:blur(20px);border-radius:16px;min-height:88px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:8px;text-align:center;animation:fadeUp 0.5s cubic-bezier(0.16,1,0.3,1) {delay}ms both;">'
                        f'<div style="color:{num_color};font-size:0.82em;font-weight:600;">{day_num}</div>'
                        f'<div style="color:{r_color};font-size:0.9em;font-weight:700;margin-top:4px;">{sign}{r_val}R</div>'
                        f'<div style="color:{TEXT_SECONDARY};font-size:0.65em;margin-top:2px;">{day_data["trades"]} trades</div>'
                        f'</div>', unsafe_allow_html=True)
                else:
                    week_cols[i].markdown(f'<div style="min-height:88px;display:flex;align-items:center;justify-content:center;"><div class="cal-day-num">{day_num}</div></div>', unsafe_allow_html=True)
        wk_sign = '+' if week_total > 0 else ''
        week_cols[7].markdown(f'<div class="cal-week-summary" style="animation-delay:{week_num*80}ms;"><div class="cal-week-label">Week {week_num+1}</div><div class="cal-week-r">{wk_sign}{round(week_total,2)}R</div><div class="cal-day-trades">{week_trades} trades</div></div>', unsafe_allow_html=True)

    if st.session_state.selected_day:
        st.markdown('<hr class="divider-line">', unsafe_allow_html=True)
        sel_day = st.session_state.selected_day
        day_trades_df = get_day_trades(df_main, sel_day)
        st.markdown(f'<div class="section-label">Trades on {sel_day.strftime("%B %d, %Y")}</div>', unsafe_allow_html=True)
        for _, trade in day_trades_df.iterrows():
            r_val = trade['R_Result']
            label = 'Win' if r_val > 0 else ('Loss' if r_val < 0 else 'Breakeven')
            sign = '+' if r_val > 0 else ''
            pair = trade.get('Pair', '—'); trade_no = trade.get('Trade No.', '—')
            pair_color = GOLD_SOFT if pair == 'XAUUSD' else (PURPLE_SOFT if pair == 'NASDAQ' else ACCENT_SOFT)
            st.markdown(f'<div class="trade-detail-card"><span style="color:{pair_color};font-weight:700;font-size:1.1em;">{label}</span><span style="color:{TEXT_SECONDARY};"> &nbsp;·&nbsp; Trade #{trade_no} &nbsp;·&nbsp; <span style="color:{pair_color};">{pair}</span></span><span style="color:{TEXT_PRIMARY};font-weight:700;float:right;">{sign}{r_val}R</span></div>', unsafe_allow_html=True)
        if st.button("Close"):
            st.session_state.selected_day = None; st.rerun()

# ============ PAGE: EDGE ANALYSIS ============
elif page == 'Edge Analysis':
    st.markdown(f'<div style="font-size:1.6em;font-weight:700;color:{TEXT_PRIMARY};margin-bottom:4px;">Edge Analysis</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.75em;color:{TEXT_SECONDARY};margin-bottom:24px;">Top 3 per category · EXP = avg R · WR = win rate % · N = trades</div>', unsafe_allow_html=True)

    ea_cols = st.columns(2)
    with ea_cols[0]:
        render_breakdown(df_main, 'Entry Model', 'Entry Model')
        render_breakdown(df_main, 'Entry Model Timeframe', 'Entry Timeframe')
        render_breakdown(df_main, 'Double Confirmation', 'Double Confirmation')
        render_breakdown(df_main, 'Target', 'Target Used')
        render_breakdown(df_main, 'Entry + Confirmation', 'Rejection Candle')
        render_breakdown(df_main, 'News Proximity', 'News Proximity')
    with ea_cols[1]:
        render_breakdown(df_main, 'Entry Confluences', 'Entry Confluences')
        render_breakdown(df_main, 'Stop Loss Logic', 'Stop Loss Logic')
        render_breakdown(df_main, 'Hour', 'Time of Day')
        render_breakdown(df_main, 'Trade Quality Rating', 'Trade Quality')
        render_breakdown(df_main, 'Emotional State Before...', 'Emotional State')
        render_breakdown(df_main, 'Conditions MTF/HTF', 'Market Conditions')

    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:14px;">Next Trade Checklist</div>', unsafe_allow_html=True)

    if green_checklist or red_checklist:
        cl_cols = st.columns(2)
        with cl_cols[0]:
            st.markdown('<div style="color:#4ade80;font-size:0.7em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">✓ What\'s working — do more of this</div>', unsafe_allow_html=True)
            for idx_c, item in enumerate(green_checklist):
                st.markdown(f'<div class="checklist-item" style="animation-delay:{idx_c*50}ms;"><div class="checklist-dot" style="background:#4ade80;box-shadow:0 0 6px rgba(74,222,128,0.4);"></div><div><div style="color:{TEXT_PRIMARY};font-size:0.88em;font-weight:600;">{item["label"]}</div><div style="color:{TEXT_SECONDARY};font-size:0.76em;margin-top:2px;">{item["detail"]}</div></div></div>', unsafe_allow_html=True)
        with cl_cols[1]:
            st.markdown('<div style="color:#f87171;font-size:0.7em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">✗ What to avoid</div>', unsafe_allow_html=True)
            for idx_c, item in enumerate(red_checklist):
                st.markdown(f'<div class="checklist-item" style="animation-delay:{idx_c*50}ms;"><div class="checklist-dot" style="background:#f87171;box-shadow:0 0 6px rgba(248,113,113,0.4);"></div><div><div style="color:{TEXT_PRIMARY};font-size:0.88em;font-weight:600;">{item["label"]}</div><div style="color:{TEXT_SECONDARY};font-size:0.76em;margin-top:2px;">{item["detail"]}</div></div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="color:{TEXT_SECONDARY};font-size:0.85em;">Not enough data yet — keep logging trades and this will populate automatically.</div>', unsafe_allow_html=True)

    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:14px;">Consistency Score</div>', unsafe_allow_html=True)
    cs_cols = st.columns([1, 2])
    with cs_cols[0]:
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:center;padding:20px 0;">'
            f'<div style="position:relative;width:100px;height:100px;">'
            f'<svg viewBox="0 0 100 100" style="width:100px;height:100px;transform:rotate(-90deg);">'
            f'<circle cx="50" cy="50" r="40" fill="none" stroke="{BORDER}" stroke-width="10"/>'
            f'<circle cx="50" cy="50" r="40" fill="none" stroke="{ACCENT}" stroke-width="10" stroke-dasharray="251" stroke-dashoffset="251">'
            f'<animate attributeName="stroke-dashoffset" from="251" to="{round(251-(consistency_score/100)*251)}" dur="1s" begin="0.2s" fill="freeze"/>'
            f'</circle></svg>'
            f'<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;"><div style="font-size:1.3em;font-weight:700;color:{TEXT_PRIMARY};">{consistency_score}%</div></div>'
            f'</div></div>', unsafe_allow_html=True)
    with cs_cols[1]:
        for idx_c, (label, score) in enumerate(consistency_breakdown):
            color = '#4ade80' if score >= 70 else ('#f59e0b' if score >= 50 else '#f87171')
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid {BORDER};animation:slideIn 0.4s cubic-bezier(0.16,1,0.3,1) {idx_c*80}ms both;">'
                f'<span style="color:{ACCENT_SOFT};font-size:0.82em;">{label}</span>'
                f'<span style="color:{color};font-weight:700;font-size:0.82em;">{score}%</span>'
                f'</div>', unsafe_allow_html=True)

# ============ PAGE: BEST SETUPS ============
elif page == 'Best Setups':
    st.markdown(f'<div style="font-size:1.6em;font-weight:700;color:{TEXT_PRIMARY};margin-bottom:4px;">Best Setups</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.75em;color:{TEXT_SECONDARY};margin-bottom:24px;">Your highest probability combinations based on all logged trades</div>', unsafe_allow_html=True)

    if best_setup:
        st.markdown(f'<div style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:14px;">Top Setup Finder</div>', unsafe_allow_html=True)
        tags_html = ''.join([f'<span style="background:rgba({BG_TINT},0.15);border:1px solid rgba({BG_TINT},0.3);border-radius:6px;padding:4px 10px;font-size:0.75em;color:{ACCENT};margin:3px;animation:fadeUp 0.4s cubic-bezier(0.16,1,0.3,1) {i*60}ms both;display:inline-block;">{b["label"]}</span>' for i, b in enumerate(best_setup['combos'])])
        overall_color = '#4ade80' if best_setup['overall_wr'] >= 60 else ('#f59e0b' if best_setup['overall_wr'] >= 45 else '#f87171')
        st.markdown(
            f'<div class="glass-panel" style="border-color:rgba(74,222,128,0.2);">'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;">{tags_html}</div>'
            f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">'
            f'<div style="text-align:center;"><div style="font-size:1.4em;font-weight:700;color:{overall_color};">{best_setup["overall_wr"]}%</div><div style="font-size:0.65em;color:{TEXT_SECONDARY};margin-top:3px;">AVG WIN RATE</div></div>'
            f'<div style="text-align:center;"><div style="font-size:1.4em;font-weight:700;color:{TEXT_PRIMARY};">+{best_setup["overall_exp"]}R</div><div style="font-size:0.65em;color:{TEXT_SECONDARY};margin-top:3px;">AVG EXPECTANCY</div></div>'
            f'<div style="text-align:center;"><div style="font-size:1.4em;font-weight:700;color:{ACCENT_SOFT};">{len(best_setup["combos"])}</div><div style="font-size:0.65em;color:{TEXT_SECONDARY};margin-top:3px;">VARIABLES</div></div>'
            f'</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div style="color:{ACCENT_SOFT};font-size:0.72em;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin:24px 0 14px;">Best of each variable</div>', unsafe_allow_html=True)

    setup_cols_list = [
        ('Entry Model', 'Entry Model'), ('Entry Model Timeframe', 'Timeframe'),
        ('3SL Window', '3SL Window'), ('Target', 'Target'),
        ('Stop Loss Logic', 'Stop Loss'), ('Entry + Confirmation', 'Rejection Candle'),
        ('Double Confirmation', 'Double Confirmation'), ('Hour', 'Time of Day'),
        ('Trade Quality Rating', 'Trade Quality'), ('Emotional State Before...', 'Emotional State'),
        ('News Proximity', 'News Proximity'), ('Conditions MTF/HTF', 'Market Conditions'),
    ]
    rows_html = ''
    for i, (col_name, label) in enumerate(setup_cols_list):
        best = get_best(df_main, col_name)
        if not best:
            continue
        color = '#4ade80' if best['exp'] >= 0 else '#f87171'
        sign = '+' if best['exp'] >= 0 else ''
        rows_html += (
            f'<div class="best-setup-row" style="animation-delay:{i*40}ms;">'
            f'<span style="color:{TEXT_SECONDARY};font-size:0.72em;text-transform:uppercase;letter-spacing:0.5px;min-width:130px;">{label}</span>'
            f'<span style="color:{TEXT_PRIMARY};font-size:0.85em;font-weight:600;flex:1;">{best["label"]}</span>'
            f'<span style="color:{color};font-size:0.82em;font-weight:700;min-width:50px;text-align:right;">{sign}{best["exp"]}R</span>'
            f'<span style="color:{ACCENT_SOFT};font-size:0.78em;min-width:40px;text-align:right;">{best["wr"]}%</span>'
            f'<span style="color:{TEXT_MUTED};font-size:0.75em;min-width:30px;text-align:right;">{best["n"]}t</span>'
            f'</div>')

    if rows_html:
        st.markdown(
            f'<div class="glass-panel">'
            f'<div style="display:flex;gap:12px;padding-bottom:8px;margin-bottom:4px;border-bottom:1px solid {BORDER};">'
            f'<span style="color:{ACCENT_SOFT};font-size:0.65em;font-weight:600;text-transform:uppercase;min-width:130px;">Variable</span>'
            f'<span style="color:{ACCENT_SOFT};font-size:0.65em;font-weight:600;text-transform:uppercase;flex:1;">Best</span>'
            f'<span style="color:{ACCENT_SOFT};font-size:0.65em;font-weight:600;text-transform:uppercase;min-width:50px;text-align:right;">Avg R</span>'
            f'<span style="color:{ACCENT_SOFT};font-size:0.65em;font-weight:600;text-transform:uppercase;min-width:40px;text-align:right;">WR</span>'
            f'<span style="color:{ACCENT_SOFT};font-size:0.65em;font-weight:600;text-transform:uppercase;min-width:30px;text-align:right;">N</span>'
            f'</div>{rows_html}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
