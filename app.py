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
        background: #070b14;
        background-image: url('https://images.unsplash.com/photo-1592198084033-aade902d1aae?w=1600&q=80');
        background-size: cover; background-position: center; background-attachment: fixed;
        font-family: 'Inter', sans-serif;
    }
    .stApp::before {
        content: ''; position: fixed; inset: 0;
        background: rgba(7,11,20,0.85);
        backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
        z-index: 0;
    }
    .stApp > * { position: relative; z-index: 1; }
    div[data-testid="stForm"] { background: transparent; border: none; }
    div[data-testid="stFormSubmitButton"] button {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #fff !important; border-radius: 10px !important;
        min-height: 48px !important; font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        background: rgba(255,255,255,0.1) !important;
    }
    div[data-testid="stTextInput"] input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important; color: #fff !important;
        padding: 12px 16px !important; font-size: 0.95em !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: rgba(255,255,255,0.2) !important;
        box-shadow: none !important;
    }
    div[data-testid="stTextInput"] > div { border: none !important; background: transparent !important; box-shadow: none !important; }
    div[data-testid="stTextInput"] > div > div { border: none !important; background: transparent !important; box-shadow: none !important; padding: 0 !important; }
    div[data-testid="stTextInput"] > div > div > div { border: none !important; background: transparent !important; box-shadow: none !important; }
    div[data-testid="stTextInput"] > label { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.5, 2, 1.5])
    with c2:
        st.markdown("""
        <div style="text-align:center;padding:80px 0 40px;">
            <div style="font-size:2em;font-weight:800;color:#fff;letter-spacing:-0.5px;margin-bottom:6px;">Trading Data</div>
            <div style="color:rgba(255,255,255,0.25);font-size:0.82em;margin-bottom:32px;">Your personal trading journal</div>
        </div>
        """, unsafe_allow_html=True)
       pw = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Password", autocomplete="off", help="")
        st.markdown('<div style="margin-top:8px;"></div>', unsafe_allow_html=True)
        if st.button("Enter", use_container_width=True):
            if pw == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
    st.stop()

NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}

if 'theme' not in st.session_state: st.session_state.theme = 'Neutral'
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = True
if 'num_accounts' not in st.session_state: st.session_state.num_accounts = 1
if 'overview_idx' not in st.session_state: st.session_state.overview_idx = 0
if 'active_page' not in st.session_state: st.session_state.active_page = 'Overview'
if 'cal_month' not in st.session_state: st.session_state.cal_month = datetime.now().month
if 'cal_year' not in st.session_state: st.session_state.cal_year = datetime.now().year
if 'selected_day' not in st.session_state: st.session_state.selected_day = None

ACCOUNT_SIZE = 50000

themes = {
    'Blue':    {'ACCENT': '#60a5fa', 'ACCENT_SOFT': '#93c5fd', 'RGB': '96,165,250'},
    'Purple':  {'ACCENT': '#a78bfa', 'ACCENT_SOFT': '#c4b5fd', 'RGB': '167,139,250'},
    'Green':   {'ACCENT': '#34d399', 'ACCENT_SOFT': '#6ee7b7', 'RGB': '52,211,153'},
    'Gold':    {'ACCENT': '#fcd34d', 'ACCENT_SOFT': '#fde68a', 'RGB': '252,211,77'},
    'Neutral': {'ACCENT': '#94a3b8', 'ACCENT_SOFT': '#cbd5e1', 'RGB': '148,163,184'},
}
T = themes.get(st.session_state.theme, themes['Neutral'])
ACCENT = T['ACCENT']
ACCENT_SOFT = T['ACCENT_SOFT']
RGB = T['RGB']
IS_DARK = st.session_state.dark_mode
GOLD = '#f59e0b'; GOLD_S = '#fcd34d'
PURPLE_C = '#a78bfa'; PURPLE_S = '#c4b5fd'
RANK_COLORS = ['#fcd34d', '#94a3b8', '#64748b']

if IS_DARK:
    BG = '#070b14'; BG2 = 'rgba(255,255,255,0.03)'; BG3 = 'rgba(255,255,255,0.05)'
    TEXT = '#ffffff'; TEXT2 = 'rgba(255,255,255,0.45)'; TEXT3 = 'rgba(255,255,255,0.2)'
    BORDER = 'rgba(255,255,255,0.06)'; BORDER2 = 'rgba(255,255,255,0.08)'
    SIDEBAR = 'rgba(255,255,255,0.02)'; SIDEBAR_B = 'rgba(255,255,255,0.05)'
    SHADOW = 'rgba(0,0,0,0.3)'
else:
    BG = '#f8f9fa'; BG2 = 'rgba(0,0,0,0.02)'; BG3 = 'rgba(0,0,0,0.04)'
    TEXT = '#0f172a'; TEXT2 = 'rgba(0,0,0,0.4)'; TEXT3 = 'rgba(0,0,0,0.15)'
    BORDER = 'rgba(0,0,0,0.05)'; BORDER2 = 'rgba(0,0,0,0.08)'
    SIDEBAR = 'rgba(0,0,0,0.02)'; SIDEBAR_B = 'rgba(0,0,0,0.06)'
    SHADOW = 'rgba(0,0,0,0.08)'

@st.cache_data(ttl=300)
def get_all_trades():
    all_results = []
    has_more = True
    start_cursor = None
    while has_more:
        payload = {}
        if start_cursor: payload["start_cursor"] = start_cursor
        r = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=payload)
        data = r.json()
        if r.status_code != 200: break
        all_results.extend(data['results'])
        has_more = data['has_more']
        start_cursor = data.get('next_cursor')
    return all_results

def extract_property(prop):
    if prop is None: return None
    pt = prop['type']
    if pt == 'title': return prop['title'][0]['plain_text'] if prop['title'] else None
    elif pt == 'rich_text': return prop['rich_text'][0]['plain_text'] if prop['rich_text'] else None
    elif pt == 'number': return prop['number']
    elif pt == 'select': return prop['select']['name'] if prop['select'] else None
    elif pt == 'multi_select': return [x['name'] for x in prop['multi_select']]
    elif pt == 'date': return prop['date']['start'] if prop['date'] else None
    elif pt == 'checkbox': return prop['checkbox']
    elif pt == 'formula': f = prop['formula']; return f.get(f['type'])
    elif pt == 'status': return prop['status']['name'] if prop['status'] else None
    else: return str(prop.get(pt, ''))

def extract_str(prop):
    val = extract_property(prop)
    return ', '.join(val) if isinstance(val, list) else val

def parse_r(value):
    if value is None or str(value).strip() in ['', 'nan']: return None
    try: return float(str(value).strip().upper().replace('RR','').replace('+','').strip())
    except: return None

def parse_date(x):
    if pd.isna(x) or x is None or str(x).strip() == '': return pd.NaT
    try:
        from dateutil import parser as _p
        ts = pd.Timestamp(_p.isoparse(str(x)))
        return ts.tz_convert('Australia/Sydney').tz_localize(None) if ts.tzinfo else ts
    except:
        try:
            from dateutil import parser as _p
            ts = pd.Timestamp(_p.parse(str(x)))
            return ts.tz_convert('Australia/Sydney').tz_localize(None) if ts.tzinfo else ts
        except: return pd.NaT

def calc_stats(df_in):
    s = {}
    r = df_in['R_Result'].dropna()
    if len(r) == 0: return s
    s['total_trades'] = len(r)
    s['wins'] = int((r > 0).sum())
    s['losses'] = int((r < 0).sum())
    s['breakevens'] = int((r == 0).sum())
    nb = s['wins'] + s['losses']
    s['win_rate'] = round(s['wins'] / nb * 100, 1) if nb > 0 else 0
    s['total_r'] = round(r.sum(), 2)
    s['avg_r'] = round(r.mean(), 2)
    s['avg_win'] = round(r[r > 0].mean(), 2) if s['wins'] > 0 else 0
    s['avg_loss'] = round(r[r < 0].mean(), 2) if s['losses'] > 0 else 0
    s['best_trade'] = round(r.max(), 2)
    s['worst_trade'] = round(r.min(), 2)
    s['expectancy'] = round(r.sum() / len(r), 2)
    eq = r.cumsum(); peak = eq.cummax()
    s['max_drawdown'] = round((eq - peak).min(), 2)
    s['equity_curve'] = eq.tolist()
    streak = ms = 0
    for v in r:
        streak = streak + 1 if v < 0 else 0
        ms = max(ms, streak)
    s['max_consec_losses'] = ms
    cur = 0; ct = None
    for v in reversed(r.tolist()):
        t = 'W' if v > 0 else ('L' if v < 0 else 'B')
        if ct is None: ct = t
        if t == ct: cur += 1
        else: break
    s['cur_streak'] = cur; s['cur_streak_type'] = ct
    vals = r.tolist(); rolling = []
    for i in range(len(vals)):
        w = vals[max(0,i-9):i+1]
        ww = sum(1 for v in w if v > 0); lw = sum(1 for v in w if v < 0)
        rolling.append(round(ww/(ww+lw)*100,1) if (ww+lw) > 0 else 0)
    s['rolling_wr'] = rolling
    s['trade_results'] = ['W' if v > 0 else ('L' if v < 0 else 'B') for v in vals]
    return s

def calc_session_stats(df_in):
    if '3SL Window' not in df_in.columns: return []
    df_t = df_in.copy(); df_t['3SL Window'] = df_t['3SL Window'].fillna('No Window').replace('','No Window')
    results = []
    for session in ['Asia','London','New York','No Window']:
        r = df_t[df_t['3SL Window']==session]['R_Result'].dropna()
        n = len(r)
        if n == 0: results.append({'session':session,'exp':0,'wr':0,'n':0}); continue
        w = int((r>0).sum()); l = int((r<0).sum()); nb = w+l
        results.append({'session':session,'exp':round(r.sum()/n,3),'wr':round(w/nb,2) if nb>0 else 0,'n':n})
    return sorted(results, key=lambda x: x['exp'], reverse=True)

def calc_daily_r(df_in):
    df_t = df_in.dropna(subset=['Date','R_Result']).copy()
    df_t['day'] = df_t['Date'].dt.date
    daily = {}
    for day, row in df_t.groupby('day')['R_Result'].agg(['count','sum']).iterrows():
        daily[day] = {'trades': int(row['count']), 'total_r': round(row['sum'],2)}
    return daily

def calc_monthly_r(df_in):
    df_t = df_in.dropna(subset=['Date','R_Result']).copy()
    df_t['month'] = df_t['Date'].dt.to_period('M')
    monthly = {}
    for period, grp in df_t.groupby('month')['R_Result']:
        r = grp; n = len(r); w = int((r>0).sum()); nb = w+int((r<0).sum())
        monthly[str(period)] = {'trades':n,'total_r':round(r.sum(),2),'win_rate':round(w/nb*100,1) if nb>0 else 0}
    return monthly

def calc_dow_stats(df_in):
    df_t = df_in.dropna(subset=['Date','R_Result']).copy()
    df_t['dow'] = df_t['Date'].dt.day_name()
    results = []
    for day in ['Monday','Tuesday','Wednesday','Thursday','Friday']:
        r = df_t[df_t['dow']==day]['R_Result'].dropna()
        n = len(r)
        if n == 0: continue
        w = int((r>0).sum()); l = int((r<0).sum()); nb = w+l
        results.append({'day':day,'short':day[:3],'exp':round(r.sum()/n,2),'wr':round(w/nb*100,1) if nb>0 else 0,'n':n})
    return sorted(results, key=lambda x: x['exp'], reverse=True)

def breakdown_by_col(df_in, col, min_trades=2):
    if col not in df_in.columns: return []
    temp = df_in.dropna(subset=['R_Result',col]).copy()
    temp = temp[temp[col].notna() & (temp[col]!='') & (temp[col]!='NA') & (temp[col]!='N/A')]
    results = []
    for val, grp in temp.groupby(col):
        r = grp['R_Result'].dropna(); n = len(r)
        if n < min_trades: continue
        w = int((r>0).sum()); l = int((r<0).sum()); nb = w+l
        results.append({'label':str(val),'wr':round(w/nb*100,1) if nb>0 else 0,'exp':round(r.sum()/n,2),'n':n})
    return sorted(results, key=lambda x: x['exp'], reverse=True)

def get_best(df_in, col):
    data = breakdown_by_col(df_in, col, min_trades=2)
    return data[0] if data else None

def calc_consistency_score(df_in, session_stats):
    scores = []
    if 'Trade Quality Rating' in df_in.columns:
        temp = df_in.dropna(subset=['Trade Quality Rating'])
        aplus = temp[temp['Trade Quality Rating'].str.contains('A\\+',na=False,regex=True)]
        if len(temp) > 0: scores.append(('A+ quality trades', round(len(aplus)/len(temp)*100)))
    if 'Rules Followed? Y/N' in df_in.columns:
        temp = df_in.dropna(subset=['Rules Followed? Y/N'])
        yes = temp[temp['Rules Followed? Y/N'].str.lower().str.startswith('yes',na=False)]
        if len(temp) > 0: scores.append(('Rules followed', round(len(yes)/len(temp)*100)))
    if session_stats:
        best = max(session_stats, key=lambda x: x['exp'])
        if '3SL Window' in df_in.columns:
            temp = df_in.dropna(subset=['3SL Window','R_Result'])
            in_best = temp[temp['3SL Window']==best['session']]
            if len(temp) > 0: scores.append((f"In {best['session']} session", round(len(in_best)/len(temp)*100)))
    if 'Emotional State Before...' in df_in.columns:
        temp = df_in.dropna(subset=['Emotional State Before...'])
        conf = temp[temp['Emotional State Before...'].str.lower().str.contains('confident',na=False)]
        if len(temp) > 0: scores.append(('Confident entries', round(len(conf)/len(temp)*100)))
    overall = round(sum(s[1] for s in scores)/len(scores)) if scores else 0
    return overall, scores

def find_best_setup(df_in):
    cols = ['3SL Window','Entry Confluences','Entry Model Timeframe','Double Confirmation','Target']
    best_combos = []
    for col in [c for c in cols if c in df_in.columns]:
        data = breakdown_by_col(df_in, col, min_trades=2)
        if data and data[0]['exp'] > 0:
            best_combos.append({'col':col,'label':data[0]['label'],'wr':data[0]['wr'],'exp':data[0]['exp'],'n':data[0]['n']})
    if not best_combos: return None
    return {'combos':best_combos,'overall_wr':round(sum(b['wr'] for b in best_combos)/len(best_combos),1),'overall_exp':round(sum(b['exp'] for b in best_combos)/len(best_combos),2)}

def generate_checklist(df_in, session_stats):
    green = []; red = []
    for col, label in [('Entry Model','entry model'),('Entry Model Timeframe','timeframe'),('Double Confirmation','double confirmation'),('Target','target'),('Stop Loss Logic','stop loss'),('Entry + Confirmation','rejection candle'),('Trade Quality Rating','trade quality'),('Entry Confluences','entry confluence'),('Conditions MTF/HTF','market conditions')]:
        data = breakdown_by_col(df_in, col, min_trades=2)
        if data and data[0]['exp'] > 0:
            green.append({'label':f"Use {data[0]['label']} for {label}",'detail':f"{data[0]['exp']}R avg · {data[0]['wr']}% WR · {data[0]['n']} trades"})
    if session_stats:
        best_s = max(session_stats, key=lambda x: x['exp'])
        if best_s['exp'] > 0: green.append({'label':f"Trade {best_s['session']} session",'detail':f"{best_s['exp']}R avg · {round(best_s['wr']*100)}% WR · {best_s['n']} trades"})
        for s in session_stats:
            if s['exp'] < 0 or s['wr'] < 0.4: red.append({'label':f"Avoid {s['session']} session",'detail':f"{s['exp']}R avg · {round(s['wr']*100)}% WR · {s['n']} trades"})
    for col, wr_thresh, tmpl in [('Emotional State Before...',45,"Avoid trading when {}"),('Trade Quality Rating',45,"Avoid {} quality trades"),('News Proximity',45,"Avoid trading {}"),('Entry Model',45,"Avoid {} entry model"),('Conditions MTF/HTF',45,"Avoid trading in {} conditions"),('Stop Loss Logic',45,"Avoid {} stop loss"),('Target',45,"Avoid {} as target")]:
        if col in df_in.columns:
            for d in breakdown_by_col(df_in, col, min_trades=2):
                if d['exp'] < 0 or d['wr'] < wr_thresh: red.append({'label':tmpl.format(d['label']),'detail':f"{d['exp']}R avg · {d['wr']}% WR · {d['n']} trades"})
    return green, red

def catmull(pts):
    if len(pts) < 2: return ""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f} "
    for i in range(len(pts)-1):
        p0=pts[i-1] if i>0 else pts[i]; p1=pts[i]; p2=pts[i+1]; p3=pts[i+2] if i+2<len(pts) else p2
        c1x=p1[0]+(p2[0]-p0[0])/6; c1y=p1[1]+(p2[1]-p0[1])/6
        c2x=p2[0]-(p3[0]-p1[0])/6; c2y=p2[1]-(p3[1]-p1[1])/6
        d += f"C{c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {p2[0]:.1f},{p2[1]:.1f} "
    return d

def make_curve(eq, w, h):
    if not eq: return "", ""
    mn=min(min(eq),0); mx=max(eq); rng=(mx-mn) if (mx-mn)!=0 else 1; n=len(eq)
    pts=[((i/(n-1))*w if n>1 else 0, h-((v-mn)/rng)*(h-20)-10) for i,v in enumerate(eq)]
    line=catmull(pts)
    return line, line+f"L{w},{h} L0,{h} Z"

def build_donut(wins, losses, bes, colors, glow):
    total=wins+losses+bes if wins+losses+bes>0 else 1
    cx=cy=110; ro=95; ri=60; sa=-90; arcs=""; legend=""
    for label,val,color in [('Win',wins,colors[0]),('Loss',losses,colors[1]),('BE',bes,colors[2])]:
        if val==0: continue
        frac=val/total; sw=frac*360; ea=sa+sw
        def polar(r,a): rad=math.radians(a); return cx+r*math.cos(rad),cy+r*math.sin(rad)
        x1o,y1o=polar(ro,sa); x2o,y2o=polar(ro,ea); x1i,y1i=polar(ri,ea); x2i,y2i=polar(ri,sa)
        la=1 if sw>180 else 0
        arcs+=f'<path d="M{x1o:.1f},{y1o:.1f} A{ro},{ro} 0 {la} 1 {x2o:.1f},{y2o:.1f} L{x1i:.1f},{y1i:.1f} A{ri},{ri} 0 {la} 0 {x2i:.1f},{y2i:.1f} Z" fill="{color}" opacity="0.9"/>'
        legend+=f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><div style="width:8px;height:8px;border-radius:50%;background:{color};"></div><span style="color:{TEXT2};font-size:0.82em;">{label}</span><span style="color:{color};font-weight:700;margin-left:auto;">{round(frac*100)}%</span></div>'
        sa=ea
    fid=f"dg{colors[0].replace('#','')}"
    svg=f'<svg viewBox="0 0 220 220" style="width:160px;height:160px;display:block;"><defs><filter id="{fid}"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><g filter="url(#{fid})">{arcs}</g><circle cx="{cx}" cy="{cy}" r="{ri-4}" fill="{BG2}"/></svg>'
    return svg, legend

def render_breakdown(df_in, col, title):
    data = breakdown_by_col(df_in, col)
    if not data: return
    data = data[:3]
    st.markdown(f'<div style="color:{TEXT2};font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin:20px 0 10px;">{title}</div>', unsafe_allow_html=True)
    max_exp = max(abs(d['exp']) for d in data) if data else 1
    if max_exp == 0: max_exp = 1
    for rank, d in enumerate(data):
        bar_pct = round(abs(d['exp'])/max_exp*100,1)
        color = '#4ade80' if d['exp'] >= 0 else '#f87171'
        lbl = d['label'][:26]+'…' if len(d['label'])>26 else d['label']
        rc = RANK_COLORS[rank] if rank < len(RANK_COLORS) else TEXT3
        st.markdown(
            f'<div style="display:grid;grid-template-columns:20px 140px 1fr 50px 50px 28px;gap:8px;align-items:center;padding:8px 0;border-bottom:1px solid {BORDER};">'
            f'<span style="color:{rc};font-size:0.68em;font-weight:700;">#{rank+1}</span>'
            f'<span style="color:{TEXT};font-size:0.82em;">{lbl}</span>'
            f'<div style="background:{BG3};border-radius:4px;height:4px;overflow:hidden;"><div style="width:{bar_pct}%;height:100%;background:{color};border-radius:4px;"></div></div>'
            f'<span style="color:{color};font-size:0.8em;font-weight:600;">{d["exp"]}R</span>'
            f'<span style="color:{TEXT2};font-size:0.8em;">{d["wr"]}%</span>'
            f'<span style="color:{TEXT3};font-size:0.78em;">{d["n"]}</span>'
            f'</div>', unsafe_allow_html=True)

# ============ LOAD & CACHE DATA ============
@st.cache_data(ttl=300)
def load_and_process():
    raw = get_all_trades()
    rows = []
    for trade in raw:
        props = trade['properties']; row = {}
        for cn, cd in props.items():
            if cn == 'Entry Confluences':
                val = extract_property(cd)
                row[cn] = ', '.join(val) if isinstance(val, list) else val
            else:
                row[cn] = extract_str(cd)
        rows.append(row)
    df = pd.DataFrame(rows)
    df.columns = df.columns.str.strip()
    df['Date'] = df['Date'].apply(parse_date)
    df['Date'] = pd.Series(df['Date'].tolist(), dtype='datetime64[ns]')
    df['R_Result'] = df['R Result'].apply(parse_r)
    if 'Time of Trade' in df.columns:
        def ph(t):
            try:
                t=str(t).strip()
                if ':' in t:
                    h=int(t.split(':')[0])
                    if 'PM' in t.upper() and h!=12: h+=12
                    if 'AM' in t.upper() and h==12: h=0
                    return f"{h:02d}:00"
            except: pass
            return None
        df['Hour'] = df['Time of Trade'].apply(ph)
    df = df.sort_values('Date').reset_index(drop=True)
    if 'Pair' in df.columns: df['Pair'] = df['Pair'].str.strip()
    return df

df_main = load_and_process()
df_xau = df_main[df_main['Pair']=='XAUUSD'].copy() if 'Pair' in df_main.columns else pd.DataFrame()
df_nas = df_main[df_main['Pair']=='NASDAQ'].copy() if 'Pair' in df_main.columns else pd.DataFrame()
df_funded = df_main[df_main['Type of Trade'].str.strip()=='Funded'].copy() if 'Type of Trade' in df_main.columns else pd.DataFrame()

# Calculate all stats once
main_stats = calc_stats(df_main)
xau_stats = calc_stats(df_xau) if len(df_xau) > 0 else {}
nas_stats = calc_stats(df_nas) if len(df_nas) > 0 else {}
session_stats = calc_session_stats(df_main)
daily_r = calc_daily_r(df_main)
monthly_r = calc_monthly_r(df_main)
dow_stats = calc_dow_stats(df_main)
consistency_score, consistency_breakdown = calc_consistency_score(df_main, session_stats)
best_setup = find_best_setup(df_main)
green_checklist, red_checklist = generate_checklist(df_main, session_stats)
max_abs_exp = max([abs(s['exp']) for s in session_stats]) if session_stats else 1
if max_abs_exp == 0: max_abs_exp = 1
today = datetime.now()
this_month_key = today.strftime('%Y-%m')
last_month_key = (today.replace(day=1)-pd.Timedelta(days=1)).strftime('%Y-%m')
this_month_r = monthly_r.get(this_month_key,{}).get('total_r',0)
last_month_r = monthly_r.get(last_month_key,{}).get('total_r',0)
diff = round(this_month_r - last_month_r, 2)

css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {{ box-sizing: border-box; }}

.stApp {{
    background: {BG};
    font-family: 'Inter', sans-serif;
}}

/* ===== PAGE TRANSITION ===== */
@keyframes pageIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes staggerIn {{
    from {{ opacity: 0; transform: translateY(12px) scale(0.98); }}
    to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
@keyframes slideInLeft {{
    from {{ opacity: 0; transform: translateX(-16px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes growBar {{
    from {{ width: 0; }}
    to {{ width: 100%; }}
}}
@keyframes pulseGlow {{
    0%, 100% {{ box-shadow: 0 0 0 rgba(74,222,128,0); }}
    50% {{ box-shadow: 0 0 20px rgba(74,222,128,0.4); }}
}}
@keyframes drawLine {{
    to {{ stroke-dashoffset: 0; }}
}}

.page-content {{ animation: pageIn 0.35s cubic-bezier(0.16,1,0.3,1) both; }}

/* ===== CARDS ===== */
.v3-card {{
    background: {BG2};
    border-radius: 16px;
    padding: 20px 16px;
    text-align: center;
    transition: background 0.2s ease, transform 0.2s ease;
    cursor: pointer;
    animation: staggerIn 0.5s cubic-bezier(0.16,1,0.3,1) both;
}}
.v3-card:hover {{
    background: {BG3};
    transform: translateY(-2px);
}}
.v3-val {{ font-size: 1.5em; font-weight: 700; color: {TEXT}; }}
.v3-lbl {{ font-size: 0.6em; color: {TEXT2}; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 500; }}

/* ===== GLASS PANEL ===== */
.v3-panel {{
    background: {BG2};
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 16px;
    animation: staggerIn 0.5s cubic-bezier(0.16,1,0.3,1) both;
}}

/* ===== SECTION LABEL ===== */
.v3-section {{
    font-size: 0.65em;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: {TEXT3};
    margin: 28px 0 14px;
    display: flex;
    align-items: center;
    gap: 12px;
}}
.v3-section::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: {BORDER};
}}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {{
    background: {SIDEBAR} !important;
    border-right: 1px solid {SIDEBAR_B} !important;
}}
section[data-testid="stSidebar"] > div {{ padding-top: 0 !important; }}

section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
    min-height: 40px !important;
    background: transparent !important;
    border: none !important;
    color: {TEXT2} !important;
    border-radius: 8px !important;
    font-size: 0.85em !important;
    text-align: left !important;
    padding-left: 12px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button * {{
    text-align: left !important;
    justify-content: flex-start !important;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{
    background: {BG2} !important;
    color: {TEXT} !important;
}}
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {{
    margin: 0 !important; padding: 0 !important;
}}
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {{
    margin: 0 !important; padding: 0 !important;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[data-testid="baseButton-secondary"] {{
    min-height: 4px !important; max-height: 4px !important;
    opacity: 0 !important; overflow: hidden !important;
    box-shadow: none !important; border: none !important;
    background: transparent !important; padding: 0 !important; margin: 0 !important;
}}

/* ===== MAIN BUTTONS ===== */
div[data-testid="stButton"] button {{
    width: 100%;
    min-height: 44px;
    border-radius: 10px;
    font-family: 'Inter', sans-serif;
    transition: all 0.15s ease;
    font-weight: 500;
    background: {BG2} !important;
    border: 1px solid {BORDER2} !important;
    color: {TEXT} !important;
    box-shadow: none !important;
}}
div[data-testid="stButton"] button:hover {{
    background: {BG3} !important;
    transform: translateY(-1px);
}}
div[data-testid="column"]:first-child div[data-testid="stButton"] button,
div[data-testid="column"]:last-child div[data-testid="stButton"] button {{
    min-height: 52px !important;
    border-radius: 12px !important;
}}

/* ===== MODE TOGGLE ===== */
div[data-testid="stButton"] button[data-testid="mode_toggle"] {{
    border-radius: 50% !important;
    width: 36px !important; height: 36px !important;
    min-height: 36px !important; max-width: 36px !important;
    padding: 0 !important; font-size: 1em !important;
}}

/* ===== CAL ===== */
.cal-arrows div[data-testid="stButton"] button {{
    min-height: 40px !important; max-height: 40px !important;
    height: 40px !important; border-radius: 8px !important;
    padding: 0 !important; margin: 0 !important;
}}
.cal-header {{ color: {TEXT2}; font-size: 0.65em; text-align: center; letter-spacing: 1px; font-weight: 600; text-transform: uppercase; padding: 8px 0; }}
.cal-day-num {{ color: {TEXT3}; font-size: 0.72em; font-weight: 600; text-align: center; }}

/* ===== STREAK ===== */
.streak-box {{
    width: 28px; height: 28px; border-radius: 6px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 700; margin: 2px;
    animation: staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
}}
.streak-box.active {{ animation: pulseGlow 2s ease-in-out infinite !important; }}

/* ===== GROW BAR ===== */
.grow-bar {{
    animation: growBar 1.2s cubic-bezier(0.16,1,0.3,1) both;
    animation-play-state: paused;
}}

/* ===== CHECKLIST ===== */
.checklist-item {{
    display: flex; align-items: flex-start; gap: 12px;
    padding: 10px 0; border-bottom: 1px solid {BORDER};
    animation: slideInLeft 0.4s cubic-bezier(0.16,1,0.3,1) both;
}}

/* ===== BEST SETUP ROW ===== */
.setup-row {{
    display: flex; align-items: center; gap: 12px;
    padding: 10px 0; border-bottom: 1px solid {BORDER};
    animation: staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
}}

/* ===== DIVIDER ===== */
.v3-divider {{ border: none; border-top: 1px solid {BORDER}; margin: 28px 0; }}

/* ===== INPUTS ===== */
div[data-testid="stNumberInput"] input {{
    background: {BG2} !important; border: 1px solid {BORDER2} !important;
    border-radius: 8px !important; color: {TEXT} !important;
}}
div[data-testid="stNumberInput"] label {{ color: {TEXT2} !important; font-size: 0.82em !important; }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown(f'<div style="padding:20px 16px 16px;border-bottom:1px solid {BORDER};margin-bottom:8px;"><span style="font-size:1em;font-weight:700;color:{TEXT};">Trading Data</span></div>', unsafe_allow_html=True)

    pages = ['Overview','P&L Tracker','Charts','Calendar','Edge Analysis','Best Setups']
    for p in pages:
        is_active = st.session_state.active_page == p
        if is_active:
            st.markdown(f'<div style="background:{BG2};border-left:2px solid {ACCENT};border-radius:8px;padding:9px 12px;margin:0;font-size:0.85em;font-weight:600;color:{ACCENT};line-height:1.6;">{p}</div>', unsafe_allow_html=True)
        else:
            if st.button(p, key=f"nav_{p}", use_container_width=True):
                st.session_state.active_page = p
                st.rerun()

    st.markdown(f'<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    if st.button("↻  Refresh", key="refresh_btn", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    if st.button("⎋  Logout", key="logout_btn", use_container_width=True):
        st.session_state.authenticated = False; st.rerun()

    st.markdown(f'<div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:16px;"><div style="font-size:0.58em;color:{TEXT3};letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;">Theme</div></div>', unsafe_allow_html=True)
    theme_opts = {'Blue':'#60a5fa','Purple':'#a78bfa','Green':'#34d399','Gold':'#fcd34d','Neutral':'#94a3b8'}
    tcols = st.columns(5)
    for i,(name,hex_c) in enumerate(theme_opts.items()):
        active_t = st.session_state.theme == name
        bdr = '2px solid #fff' if active_t else f'2px solid transparent'
        tcols[i].markdown(f'<div style="width:20px;height:20px;border-radius:50%;background:{hex_c};border:{bdr};margin:auto;"></div>', unsafe_allow_html=True)
        if tcols[i].button(" ", key=f"theme_{name}", use_container_width=True):
            st.session_state.theme = name; st.rerun()

    st.markdown(f'<div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:12px;"></div>', unsafe_allow_html=True)
    cg, cb = st.columns([3,1])
    cg.markdown(f'<div style="font-size:0.7em;color:{TEXT2};padding-top:8px;">{"Light" if IS_DARK else "Dark"} Mode</div>', unsafe_allow_html=True)
    with cb:
        if st.button("☀️" if IS_DARK else "🌙", key="mode_toggle", use_container_width=True):
            st.session_state.dark_mode = not IS_DARK; st.rerun()

page = st.session_state.active_page
st.markdown('<div class="page-content">', unsafe_allow_html=True)

# ============ OVERVIEW ============
if page == 'Overview':
    cur = main_stats.get('cur_streak',0)
    cur_type = main_stats.get('cur_streak_type','—')
    cur_color = '#4ade80' if cur_type=='W' else ('#f87171' if cur_type=='L' else ACCENT)
    cur_label = 'Win Streak' if cur_type=='W' else ('Loss Streak' if cur_type=='L' else 'Streak')
    diff_color = '#4ade80' if diff >= 0 else '#f87171'
    diff_sign = '+' if diff >= 0 else ''
    month_sign = '+' if this_month_r > 0 else ''

    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:20px;">Overview</div>', unsafe_allow_html=True)

    # Clean banner — no borders
    st.markdown(
        f'<div style="background:{BG2};border-radius:18px;padding:22px 28px;display:flex;align-items:center;margin-bottom:24px;">'
        f'<div style="flex:1;text-align:center;">'
        f'<div style="font-size:1.8em;font-weight:800;color:{cur_color};">{cur}</div>'
        f'<div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">{cur_label}</div>'
        f'</div>'
        f'<div style="width:1px;height:36px;background:{BORDER};"></div>'
        f'<div style="flex:1;text-align:center;">'
        f'<div style="font-size:1.8em;font-weight:800;color:{ACCENT};" id="b-cons">—</div>'
        f'<div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">Consistency</div>'
        f'</div>'
        f'<div style="width:1px;height:36px;background:{BORDER};"></div>'
        f'<div style="flex:1;text-align:center;">'
        f'<div style="font-size:1.8em;font-weight:800;color:{TEXT};" id="b-month">—</div>'
        f'<div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">This Month</div>'
        f'</div>'
        f'<div style="width:1px;height:36px;background:{BORDER};"></div>'
        f'<div style="flex:1;text-align:center;">'
        f'<div style="font-size:1.8em;font-weight:800;color:{diff_color};" id="b-diff">—</div>'
        f'<div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">vs Last Month</div>'
        f'</div>'
        f'</div>', unsafe_allow_html=True)

    components.html(f"""
<script>
function countUp(id, target, dec, suffix, final, dur) {{
    var el = window.parent.document.getElementById(id);
    if (!el) return;
    var t0 = null;
    function step(ts) {{
        if (!t0) t0 = ts;
        var p = Math.min((ts-t0)/dur, 1);
        var e = 1-Math.pow(1-p,3);
        el.textContent = (dec>0 ? (target*e).toFixed(dec) : Math.round(target*e)) + suffix;
        if (p<1) requestAnimationFrame(step);
        else el.textContent = final;
    }}
    requestAnimationFrame(step);
}}
setTimeout(function() {{
    countUp('b-cons', {consistency_score}, 0, '%', '{consistency_score}%', 800);
    countUp('b-month', {abs(this_month_r)}, 2, 'R', '{month_sign}{this_month_r}R', 800);
    countUp('b-diff', {abs(diff)}, 2, 'R', '{diff_sign}{diff}R', 800);
    // Trigger grow bars
    var bars = window.parent.document.querySelectorAll('.grow-bar');
    var obs = new IntersectionObserver(function(entries) {{
        entries.forEach(function(e) {{
            if (e.isIntersecting) {{ e.target.style.animationPlayState='running'; obs.unobserve(e.target); }}
        }});
    }}, {{threshold:0.1}});
    bars.forEach(function(b) {{
        var r = b.getBoundingClientRect();
        if (r.top < window.parent.innerHeight) b.style.animationPlayState='running';
        else obs.observe(b);
    }});
}}, 150);
</script>
    """, height=0)

    # Performance nav
    st.markdown(f'<div class="v3-section">Performance</div>', unsafe_allow_html=True)
    overviews = [
        {'label':'Overall','stats':main_stats,'color':ACCENT_SOFT},
        {'label':'XAUUSD','stats':xau_stats,'color':GOLD_S},
        {'label':'NASDAQ','stats':nas_stats,'color':PURPLE_S},
    ]
    idx = st.session_state.overview_idx
    current = overviews[idx]

    pc, nc = st.columns(2)
    with pc:
        if st.button(f"← {overviews[(idx-1)%3]['label']}", key="prev_ov", use_container_width=True):
            st.session_state.overview_idx = (idx-1)%3; st.rerun()
    with nc:
        if st.button(f"{overviews[(idx+1)%3]['label']} →", key="next_ov", use_container_width=True):
            st.session_state.overview_idx = (idx+1)%3; st.rerun()

    st.markdown(f'<div style="background:{BG2};border-radius:14px;padding:14px 20px;text-align:center;margin-bottom:16px;font-size:1em;font-weight:700;color:{current["color"]};">{current["label"]} Performance</div>', unsafe_allow_html=True)

    stat_data = [
        ('Total Trades', current['stats'].get('total_trades','—')),
        ('Win Rate', f"{current['stats'].get('win_rate','—')}%"),
        ('Total R', current['stats'].get('total_r','—')),
        ('Avg R', current['stats'].get('avg_r','—')),
        ('Expectancy', current['stats'].get('expectancy','—')),
        ('Avg Win', current['stats'].get('avg_win','—')),
        ('Avg Loss', current['stats'].get('avg_loss','—')),
        ('Best Trade', current['stats'].get('best_trade','—')),
        ('Worst Trade', current['stats'].get('worst_trade','—')),
        ('Max DD', current['stats'].get('max_drawdown','—')),
        ('Consec L', current['stats'].get('max_consec_losses','—')),
        ('Wins', current['stats'].get('wins','—')),
        ('Losses', current['stats'].get('losses','—')),
        ('Breakevens', current['stats'].get('breakevens','—')),
    ]
    for i in range(0, len(stat_data), 7):
        row = stat_data[i:i+7]
        cols = st.columns(len(row))
        for j,(col,(lbl,val)) in enumerate(zip(cols,row)):
            col.markdown(
                f'<div class="v3-card" style="animation-delay:{j*40}ms;">'
                f'<div class="v3-val">{val}</div>'
                f'<div class="v3-lbl" style="color:{current["color"]};">{lbl}</div>'
                f'</div>', unsafe_allow_html=True)
        st.write("")

    # Recent trades — improved streak viz
    st.markdown(f'<div class="v3-section">Recent Trades</div>', unsafe_allow_html=True)
    tr = main_stats.get('trade_results',[])
    streak_html = f'<div style="display:flex;gap:3px;overflow-x:auto;padding-bottom:6px;scrollbar-width:none;margin-bottom:10px;">'
    for i,r in enumerate(tr):
        is_last = i == len(tr)-1
        bg = 'rgba(74,222,128,0.85)' if r=='W' else ('rgba(248,113,113,0.75)' if r=='L' else f'rgba({RGB},0.3)')
        tc = '#000' if r=='W' else '#fff'
        cls = 'streak-box active' if is_last else 'streak-box'
        streak_html += f'<div class="{cls}" style="background:{bg};color:{tc};animation-delay:{i*25}ms;flex-shrink:0;">{r}</div>'
    streak_html += f'<div class="streak-box" style="background:{BG2};color:{TEXT3};border:1px dashed {BORDER2};flex-shrink:0;">?</div></div>'
    streak_html += f'<div style="font-size:0.75em;color:{TEXT2};">Current streak: <span style="color:{cur_color};font-weight:600;">{cur} {cur_type}</span></div>'
    st.markdown(f'<div class="v3-panel">{streak_html}</div>', unsafe_allow_html=True)

    # Month vs month
    st.markdown(f'<div class="v3-section">Month vs Month</div>', unsafe_allow_html=True)
    months = sorted(monthly_r.keys())[-4:]
    if months:
        mcols = st.columns(len(months))
        for i,(col,m) in enumerate(zip(mcols,months)):
            d = monthly_r[m]; sign = '+' if d['total_r']>0 else ''
            is_cur = m==this_month_key
            current_badge = f'<div style="color:{ACCENT_SOFT};font-size:0.58em;margin-top:3px;">Current</div>' if is_cur else ''
            col.markdown(
                f'<div style="background:{"rgba("+RGB+",0.08)" if is_cur else BG2};border-radius:12px;padding:14px;text-align:center;{"border:1px solid rgba("+RGB+",0.2);" if is_cur else ""}animation:staggerIn 0.5s cubic-bezier(0.16,1,0.3,1) {i*60}ms both;">'
                f'<div style="color:{ACCENT_SOFT if is_cur else TEXT2};font-size:0.6em;margin-bottom:6px;text-transform:uppercase;">{m}</div>'
                f'<div style="color:{TEXT};font-size:1.15em;font-weight:700;">{sign}{d["total_r"]}R</div>'
                f'<div style="color:{TEXT2};font-size:0.6em;margin-top:4px;">{d["win_rate"]}% · {d["trades"]}t</div>'
                f'{current_badge}'
                f'</div>', unsafe_allow_html=True)

    # 3SL Window
    st.markdown(f'<div class="v3-section">3SL Window</div>', unsafe_allow_html=True)
    rows_html = ""
    for i,s in enumerate(session_stats):
        bar_pct = round(abs(s['exp'])/max_abs_exp*100,1)
        bar_color = f'linear-gradient(90deg,rgba({RGB},0.4),{ACCENT})' if s['exp']>=0 else 'linear-gradient(90deg,rgba(248,113,113,0.4),#f87171)'
        delay = i*300
        rows_html += (
            f'<div style="display:grid;grid-template-columns:90px 1fr 60px 55px 35px;gap:14px;align-items:center;padding:10px 0;border-bottom:1px solid {BORDER};">'
            f'<span style="color:{TEXT};font-size:0.82em;font-weight:500;">{s["session"]}</span>'
            f'<div style="background:{BG3};border-radius:4px;height:6px;overflow:hidden;">'
            f'<div style="width:{bar_pct}%;height:6px;overflow:hidden;border-radius:4px;">'
            f'<div class="grow-bar" style="width:100%;height:6px;background:{bar_color};border-radius:4px;animation:growBar 1.2s cubic-bezier(0.16,1,0.3,1) {delay}ms both;animation-play-state:paused;"></div>'
            f'</div></div>'
            f'<span style="color:{TEXT};font-size:0.8em;font-weight:600;">{s["exp"]}R</span>'
            f'<span style="color:{TEXT2};font-size:0.8em;">{s["wr"]}</span>'
            f'<span style="color:{TEXT3};font-size:0.78em;">{s["n"]}</span>'
            f'</div>')
    st.markdown(
        f'<div class="v3-panel">'
        f'<div style="display:grid;grid-template-columns:90px 1fr 60px 55px 35px;gap:14px;padding-bottom:8px;margin-bottom:2px;">'
        f'<span style="color:{TEXT3};font-size:0.62em;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Session</span>'
        f'<span style="color:{TEXT3};font-size:0.62em;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Chart</span>'
        f'<span style="color:{TEXT3};font-size:0.62em;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Exp</span>'
        f'<span style="color:{TEXT3};font-size:0.62em;font-weight:600;text-transform:uppercase;letter-spacing:1px;">WR</span>'
        f'<span style="color:{TEXT3};font-size:0.62em;font-weight:600;text-transform:uppercase;letter-spacing:1px;">N</span>'
        f'</div>{rows_html}</div>', unsafe_allow_html=True)

# ============ P&L TRACKER ============
elif page == 'P&L Tracker':
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:2px;">P&L Tracker</div>', unsafe_allow_html=True)

    _, num_col, _ = st.columns([2,1,2])
    with num_col:
        num_accounts = st.number_input("Accounts", min_value=1, max_value=50, value=st.session_state.num_accounts, step=1)
        st.session_state.num_accounts = num_accounts

    total_capital = ACCOUNT_SIZE * num_accounts

    if len(df_funded) > 0 and 'R_Result' in df_funded.columns:
        df_fc = df_funded.dropna(subset=['R_Result','Date']).copy().sort_values('Date').reset_index(drop=True)

        if 'Risk Management' in df_fc.columns:
            avg_risk_pct = pd.to_numeric(df_fc['Risk Management'].str.replace('%','').str.strip(), errors='coerce').mean()
            if pd.isna(avg_risk_pct): avg_risk_pct = 1.0
        else:
            avg_risk_pct = 1.0

        def calc_pnl(df_sub):
            if 'Risk Management' in df_sub.columns:
                rp = pd.to_numeric(df_sub['Risk Management'].str.replace('%','').str.strip(), errors='coerce').fillna(avg_risk_pct)
                return round((df_sub['R_Result'].values * rp.values / 100 * ACCOUNT_SIZE * num_accounts).sum(), 2)
            return round(df_sub['R_Result'].sum() * avg_risk_pct/100 * ACCOUNT_SIZE * num_accounts, 2)

        month_funded = df_fc[(df_fc['Date'].dt.month==today.month)&(df_fc['Date'].dt.year==today.year)]
        month_pnl = calc_pnl(month_funded)
        month_pct = round(month_pnl/total_capital*100,2)
        month_r = round(month_funded['R_Result'].sum(),2)

        week_start = today - pd.Timedelta(days=today.weekday())
        week_funded = df_fc[df_fc['Date'].dt.date >= week_start.date()]
        week_pnl = calc_pnl(week_funded)
        week_pct = round(week_pnl/total_capital*100,2)
        week_r = round(week_funded['R_Result'].sum(),2)

        today_funded = df_fc[df_fc['Date'].dt.date == today.date()]
        today_pnl = calc_pnl(today_funded)
        today_pct = round(today_pnl/total_capital*100,2)
        today_r = round(today_funded['R_Result'].sum(),2)

        total_pnl = calc_pnl(df_fc)
        total_r = round(df_fc['R_Result'].sum(),2)

        def fmt(v): return f"+${v:,.2f}" if v>=0 else f"-${abs(v):,.2f}"
        def fmtp(v): return f"+{v}%" if v>=0 else f"{v}%"
        def pc(v): return '#4ade80' if v>=0 else '#f87171'

        st.markdown(f'<div class="v3-section">Performance</div>', unsafe_allow_html=True)
        pcols = st.columns(3)
        for i,(col,(period,pnl,pct,rv,nt)) in enumerate(zip(pcols,[
            ('This Month',month_pnl,month_pct,f"{month_r}R",len(month_funded)),
            ('This Week',week_pnl,week_pct,f"{week_r}R",len(week_funded)),
            ('Today',today_pnl,today_pct,f"{today_r}R",len(today_funded)),
        ])):
            c = pc(pnl)
            col.markdown(
                f'<div class="v3-card" style="animation-delay:{i*60}ms;">'
                f'<div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">{period}</div>'
                f'<div style="font-size:1.5em;font-weight:700;color:{c};" id="pnl-{i}">{fmt(pnl)}</div>'
                f'<div style="font-size:0.9em;font-weight:600;color:{c};margin-top:3px;" id="pct-{i}">{fmtp(pct)}</div>'
                f'<div style="font-size:0.6em;color:{TEXT2};margin-top:10px;padding-top:10px;border-top:1px solid {BORDER};">{rv} · {nt} trades</div>'
                f'</div>', unsafe_allow_html=True)

        components.html(f"""
<script>
function cm(id,t,dur){{var el=window.parent.document.getElementById(id);if(!el)return;var t0=null,pfx=t>=0?'+$':'-$',at=Math.abs(t);function s(ts){{if(!t0)t0=ts;var p=Math.min((ts-t0)/dur,1),e=1-Math.pow(1-p,3);el.textContent=pfx+(at*e).toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});if(p<1)requestAnimationFrame(s);}}requestAnimationFrame(s);}}
function cp(id,t,dur){{var el=window.parent.document.getElementById(id);if(!el)return;var t0=null,pfx=t>=0?'+':'-',at=Math.abs(t);function s(ts){{if(!t0)t0=ts;var p=Math.min((ts-t0)/dur,1),e=1-Math.pow(1-p,3);el.textContent=pfx+(at*e).toFixed(2)+'%';if(p<1)requestAnimationFrame(s);}}requestAnimationFrame(s);}}
setTimeout(function(){{
    cm('pnl-0',{month_pnl},900);cm('pnl-1',{week_pnl},900);cm('pnl-2',{today_pnl},900);
    cp('pct-0',{month_pct},900);cp('pct-1',{week_pct},900);cp('pct-2',{today_pct},900);
}},200);
</script>
        """, height=0)

        st.markdown(f'<div class="v3-section">All Time · Funded</div>', unsafe_allow_html=True)
        at_cols = st.columns(3)
        sign_t = '+' if total_pnl>=0 else ''
        at_cols[0].markdown(f'<div class="v3-card" style="animation-delay:0ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total P&L</div><div style="font-size:1.3em;font-weight:700;color:{pc(total_pnl)};">{fmt(total_pnl)}</div><div style="font-size:0.72em;color:{pc(total_pnl)};margin-top:3px;">{sign_t}{round(total_pnl/total_capital*100,2)}%</div></div>', unsafe_allow_html=True)
        at_cols[1].markdown(f'<div class="v3-card" style="animation-delay:60ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total R</div><div style="font-size:1.3em;font-weight:700;color:{TEXT};">{sign_t}{total_r}R</div></div>', unsafe_allow_html=True)
        at_cols[2].markdown(f'<div class="v3-card" style="animation-delay:120ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total Capital</div><div style="font-size:1.3em;font-weight:700;color:{ACCENT_SOFT};">${total_capital:,}</div></div>', unsafe_allow_html=True)

        # Goals
        st.markdown(f'<div class="v3-section">Goals</div>', unsafe_allow_html=True)
        goal_pnl = 10000; goal_wr = 60
        funded_stats = calc_stats(df_fc)
        current_wr = funded_stats.get('win_rate',0)
        pnl_prog = min(round(max(total_pnl,0)/goal_pnl*100,1),100)
        wr_prog = min(round(current_wr/goal_wr*100,1),100)
        pnl_rem = round(max(goal_pnl-max(total_pnl,0),0),2)

        gcols = st.columns(2)
        gcols[0].markdown(
            f'<div class="v3-card" style="text-align:left;animation-delay:0ms;">'
            f'<div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">Monthly P&L Goal</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:12px;">'
            f'<span style="font-size:1.2em;font-weight:700;color:{TEXT};">${max(total_pnl,0):,.0f}</span>'
            f'<span style="font-size:0.72em;color:{TEXT2};">/ ${goal_pnl:,}</span></div>'
            f'<div style="background:{BG3};border-radius:4px;height:4px;overflow:hidden;margin-bottom:8px;">'
            f'<div style="width:{pnl_prog}%;height:100%;background:{ACCENT};border-radius:4px;"></div></div>'
            f'<div style="font-size:0.62em;color:{TEXT2};">{pnl_prog}% · ${pnl_rem:,.0f} to go</div>'
            f'</div>', unsafe_allow_html=True)
        gcols[1].markdown(
            f'<div class="v3-card" style="text-align:left;animation-delay:60ms;">'
            f'<div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">Win Rate Goal</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:12px;">'
            f'<span style="font-size:1.2em;font-weight:700;color:{TEXT};">{current_wr}%</span>'
            f'<span style="font-size:0.72em;color:{TEXT2};">/ {goal_wr}%</span></div>'
            f'<div style="background:{BG3};border-radius:4px;height:4px;overflow:hidden;margin-bottom:8px;">'
            f'<div style="width:{wr_prog}%;height:100%;background:{ACCENT};border-radius:4px;"></div></div>'
            f'<div style="font-size:0.62em;color:{TEXT2};">{wr_prog}% there</div>'
            f'</div>', unsafe_allow_html=True)

        # Goal rings
        pnl_dash = round(239-(pnl_prog/100)*239)
        wr_dash = round(239-(wr_prog/100)*239)
        st.markdown(
            f'<div class="v3-panel" style="display:flex;justify-content:space-around;align-items:center;padding:24px;">'
            f'<div style="text-align:center;"><div style="position:relative;width:88px;height:88px;margin:0 auto;">'
            f'<svg viewBox="0 0 100 100" style="width:88px;height:88px;transform:rotate(-90deg);">'
            f'<circle cx="50" cy="50" r="38" fill="none" stroke="{BG3}" stroke-width="8"/>'
            f'<circle cx="50" cy="50" r="38" fill="none" stroke="{ACCENT}" stroke-width="8" stroke-dasharray="239" stroke-dashoffset="{pnl_dash}" stroke-linecap="round"/></svg>'
            f'<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:0.82em;font-weight:700;color:{TEXT};">{pnl_prog}%</div>'
            f'</div><div style="font-size:0.7em;font-weight:600;color:{TEXT};margin-top:8px;">${max(total_pnl,0):,.0f}</div>'
            f'<div style="font-size:0.58em;color:{TEXT2};">of ${goal_pnl:,}</div></div>'
            f'<div style="text-align:center;"><div style="position:relative;width:88px;height:88px;margin:0 auto;">'
            f'<svg viewBox="0 0 100 100" style="width:88px;height:88px;transform:rotate(-90deg);">'
            f'<circle cx="50" cy="50" r="38" fill="none" stroke="{BG3}" stroke-width="8"/>'
            f'<circle cx="50" cy="50" r="38" fill="none" stroke="{ACCENT}" stroke-width="8" stroke-dasharray="239" stroke-dashoffset="{wr_dash}" stroke-linecap="round"/></svg>'
            f'<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:0.82em;font-weight:700;color:{TEXT};">{wr_prog}%</div>'
            f'</div><div style="font-size:0.7em;font-weight:600;color:{TEXT};margin-top:8px;">{current_wr}%</div>'
            f'<div style="font-size:0.58em;color:{TEXT2};">WR goal</div></div>'
            f'</div>', unsafe_allow_html=True)

    else:
       st.markdown(f'<div class="v3-panel" style="text-align:center;padding:48px;"><div style="color:{TEXT2};">No trades yet</div></div>', unsafe_allow_html=True)

# ============ CHARTS ============
elif page == 'Charts':
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:24px;">Charts</div>', unsafe_allow_html=True)

    xau_eq = xau_stats.get('equity_curve',[])
    nas_eq = nas_stats.get('equity_curve',[])
    sw,sh = 800,200
    xl,xf = make_curve(xau_eq,sw,sh)
    nl,nf = make_curve(nas_eq,sw,sh)

    xfp = f'<path d="{xf}" fill="url(#xFill)" opacity="0.3"/>' if xf else ''
    xlp = f'<path d="{xl}" fill="none" stroke="{GOLD}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2.5s" begin="0s" fill="freeze"/></path>' if xl else ''
    nlp = f'<path d="{nl}" fill="none" stroke="{PURPLE_C}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2.5s" begin="0.3s" fill="freeze"/></path>' if nl else ''

    svg = f"""<svg viewBox="0 0 {sw} {sh}" style="width:100%;height:260px;display:block;">
      <defs>
        <linearGradient id="xFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba(245,158,11,0.2)"/><stop offset="100%" stop-color="rgba(245,158,11,0)"/></linearGradient>
      </defs>
      {xfp}{xlp}{nlp}
    </svg>"""

    st.markdown(
        f'<div class="v3-panel">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">'
        f'<div style="font-size:0.95em;font-weight:600;color:{TEXT};">Equity Curve</div>'
        f'<div style="display:flex;gap:16px;">'
        f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:20px;height:2px;background:{GOLD};border-radius:2px;"></div><span style="font-size:0.72em;color:{TEXT2};">XAUUSD</span></div>'
        f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:20px;height:2px;background:{PURPLE_C};border-radius:2px;"></div><span style="font-size:0.72em;color:{TEXT2};">NASDAQ</span></div>'
        f'</div></div>{svg}</div>', unsafe_allow_html=True)

    rolling = main_stats.get('rolling_wr',[])
    if rolling:
        rw,rh = 800,100
        n = len(rolling)
        pts = [((i/(n-1))*rw if n>1 else 0, rh-((v/100)*(rh-16))-8) for i,v in enumerate(rolling)]
        rl = catmull(pts)
        rf = rl+f"L{rw},{rh} L0,{rh} Z" if rl else ""
        by = rh-(0.5*(rh-16))-8
        trending = rolling[-1]>rolling[0] if len(rolling)>1 else False
        tc = '#4ade80' if trending else '#f87171'
        tt = 'Trending up ↑' if trending else 'Trending down ↓'
        rsvg = f"""<svg viewBox="0 0 {rw} {rh}" style="width:100%;height:100px;display:block;">
          <defs><linearGradient id="rFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba({RGB},0.15)"/><stop offset="100%" stop-color="rgba({RGB},0)"/></linearGradient></defs>
          <line x1="0" y1="{by:.1f}" x2="{rw}" y2="{by:.1f}" stroke="{BORDER2}" stroke-width="1" stroke-dasharray="4,4"/>
          {'<path d="'+rf+'" fill="url(#rFill)"/>' if rf else ''}
          {'<path d="'+rl+f'" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2s" begin="0s" fill="freeze"/></path>' if rl else ''}
        </svg>"""
        st.markdown(
            f'<div class="v3-panel"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
            f'<div><div style="font-size:0.95em;font-weight:600;color:{TEXT};">Rolling Win Rate</div><div style="font-size:0.68em;color:{TEXT2};margin-top:2px;">Last 10 trades window</div></div>'
            f'<div style="font-size:0.7em;color:{tc};font-weight:500;">{tt}</div>'
            f'</div>{rsvg}</div>', unsafe_allow_html=True)

    donut_configs = [
        ('Overall',main_stats.get('wins',0),main_stats.get('losses',0),main_stats.get('breakevens',0),[ACCENT,f'{ACCENT}88',f'{ACCENT}33'],f'rgba({RGB},0.3)',ACCENT_SOFT),
        ('XAUUSD',xau_stats.get('wins',0),xau_stats.get('losses',0),xau_stats.get('breakevens',0),['#b45309','#f59e0b','#fde68a33'],'rgba(245,158,11,0.3)',GOLD_S),
        ('NASDAQ',nas_stats.get('wins',0),nas_stats.get('losses',0),nas_stats.get('breakevens',0),['#6d28d9','#a78bfa','#ede9fe33'],'rgba(167,139,250,0.3)',PURPLE_S),
    ]
    dcols = st.columns(3)
    for col,(lbl,w,l,b,colors,glow,tc) in zip(dcols,donut_configs):
        svg,legend = build_donut(w,l,b,colors,glow)
        col.markdown(f'<div class="v3-panel"><div style="font-size:0.85em;font-weight:600;color:{tc};margin-bottom:14px;">{lbl}</div><div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;"><div>{svg}</div><div style="flex:1;min-width:90px;">{legend}</div></div></div>', unsafe_allow_html=True)

# ============ CALENDAR ============
elif page == 'Calendar':
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:24px;">Calendar</div>', unsafe_allow_html=True)

    cm = st.session_state.cal_month; cy = st.session_state.cal_year
    mt_r = sum(v['total_r'] for k,v in daily_r.items() if k.month==cm and k.year==cy)
    ms2 = '+' if mt_r>0 else ''
    mn = datetime(cy,cm,1).strftime("%B %Y")

    nl2, nr = st.columns([7,2])
    nl2.markdown(
        f'<div style="background:{BG2};border-radius:14px;height:40px;display:flex;align-items:center;padding:0 18px;margin-bottom:14px;">'
        f'<span style="font-size:1em;font-weight:700;color:{TEXT};">{mn}</span>'
        f'<span style="font-size:0.72em;color:{ACCENT};font-weight:600;margin-left:10px;">{ms2}{round(mt_r,2)}R</span>'
        f'</div>', unsafe_allow_html=True)
    with nr:
        st.markdown('<div class="cal-arrows">', unsafe_allow_html=True)
        al,ar2 = st.columns(2)
        with al:
            if st.button("‹", key="prev_m", use_container_width=True):
                if st.session_state.cal_month==1: st.session_state.cal_month=12; st.session_state.cal_year-=1
                else: st.session_state.cal_month-=1
                st.rerun()
        with ar2:
            if st.button("›", key="next_m", use_container_width=True):
                if st.session_state.cal_month==12: st.session_state.cal_month=1; st.session_state.cal_year+=1
                else: st.session_state.cal_month+=1
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    cal_module.setfirstweekday(cal_module.MONDAY)
    mm = cal_module.monthcalendar(cy,cm)
    dhc = st.columns(8)
    for i,d in enumerate(['Mo','Tu','We','Th','Fr','Sa','Su']):
        dhc[i].markdown(f'<div class="cal-header">{d}</div>', unsafe_allow_html=True)
    dhc[7].markdown(f'<div class="cal-header">Wk</div>', unsafe_allow_html=True)

    for wn,week in enumerate(mm):
        if wn>0: st.write("")
        wc = st.columns(8); wt = wtr = 0
        for i,dn in enumerate(week):
            if dn==0:
                wc[i].markdown('<div style="min-height:72px;"></div>', unsafe_allow_html=True)
            else:
                dd = datetime(cy,cm,dn).date()
                dd_data = daily_r.get(dd)
                if dd_data:
                    wt+=dd_data['total_r']; wtr+=dd_data['trades']
                    rv=dd_data['total_r']; sg='+' if rv>0 else ''
                    if rv>=0:
                        ds="background:rgba(74,222,128,0.06);border:1px solid rgba(74,222,128,0.15);"
                        rc='#4ade80' if IS_DARK else '#16a34a'
                        nc='rgba(74,222,128,0.9)' if IS_DARK else '#14532d'
                    else:
                        ds="background:rgba(248,113,113,0.06);border:1px solid rgba(248,113,113,0.15);"
                        rc='#f87171' if IS_DARK else '#dc2626'
                        nc='rgba(248,113,113,0.9)' if IS_DARK else '#7f1d1d'
                    delay=(wn*7+i)*30
                    wc[i].markdown(
                        f'<div style="{ds}border-radius:10px;min-height:72px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:6px;text-align:center;animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) {delay}ms both;">'
                        f'<div style="color:{nc};font-size:0.7em;font-weight:600;">{dn}</div>'
                        f'<div style="color:{rc};font-size:0.82em;font-weight:700;margin-top:3px;">{sg}{rv}R</div>'
                        f'<div style="color:{TEXT2};font-size:0.58em;margin-top:2px;">{dd_data["trades"]}t</div>'
                        f'</div>', unsafe_allow_html=True)
                else:
                    wc[i].markdown(f'<div style="min-height:72px;display:flex;align-items:center;justify-content:center;"><div class="cal-day-num">{dn}</div></div>', unsafe_allow_html=True)
        ws = '+' if wt>0 else ''
        wc[7].markdown(
            f'<div style="background:{BG2};border-radius:10px;min-height:72px;padding:8px 4px;text-align:center;animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) {wn*60}ms both;">'
            f'<div style="color:{TEXT2};font-size:0.58em;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">W{wn+1}</div>'
            f'<div style="font-size:0.92em;font-weight:700;color:{TEXT};margin-top:8px;">{ws}{round(wt,2)}R</div>'
            f'<div style="color:{TEXT2};font-size:0.55em;margin-top:2px;">{wtr}t</div>'
            f'</div>', unsafe_allow_html=True)

    if st.session_state.selected_day:
        st.markdown(f'<hr class="v3-divider">', unsafe_allow_html=True)
        sd = st.session_state.selected_day
        dtdf = df_main.dropna(subset=['Date','R_Result']).copy()
        dtdf['day'] = dtdf['Date'].dt.date
        dtdf = dtdf[dtdf['day']==sd]
        st.markdown(f'<div style="font-size:0.85em;font-weight:600;color:{TEXT};margin-bottom:12px;">Trades on {sd.strftime("%B %d, %Y")}</div>', unsafe_allow_html=True)
        for _,trade in dtdf.iterrows():
            rv=trade['R_Result']; lbl='Win' if rv>0 else ('Loss' if rv<0 else 'BE')
            sg='+' if rv>0 else ''; pair=trade.get('Pair','—'); tno=trade.get('Trade No.','—')
            pc2=GOLD_S if pair=='XAUUSD' else (PURPLE_S if pair=='NASDAQ' else ACCENT_SOFT)
            st.markdown(f'<div style="background:{BG2};border-radius:10px;padding:12px 16px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><span style="color:{pc2};font-weight:600;font-size:0.88em;">{lbl} · {pair}</span><span style="color:{TEXT};font-weight:700;">{sg}{rv}R</span></div>', unsafe_allow_html=True)
        if st.button("Close"): st.session_state.selected_day = None; st.rerun()

    # Best day of week
    st.markdown(f'<hr class="v3-divider">', unsafe_allow_html=True)
    st.markdown(f'<div class="v3-section">Best Day of the Week</div>', unsafe_allow_html=True)
    if dow_stats:
        best_day = dow_stats[0]
        bc = '#4ade80' if best_day['exp']>=0 else '#f87171'
        bs = '+' if best_day['exp']>=0 else ''
        dow_cols = st.columns([1,2])
        with dow_cols[0]:
            st.markdown(
                f'<div class="v3-panel" style="text-align:center;padding:24px 16px;">'
                f'<div style="font-size:0.58em;color:{TEXT2};text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Best Day</div>'
                f'<div style="font-size:1.5em;font-weight:800;color:{TEXT};margin-bottom:6px;">{best_day["day"]}</div>'
                f'<div style="font-size:0.95em;font-weight:700;color:{bc};">{bs}{best_day["exp"]}R avg</div>'
                f'<div style="font-size:0.62em;color:{TEXT2};margin-top:6px;">{best_day["wr"]}% WR · {best_day["n"]} trades</div>'
                f'</div>', unsafe_allow_html=True)
        with dow_cols[1]:
            rows = ''
            for i,d in enumerate(dow_stats):
                c = '#4ade80' if d['exp']>=0 else '#f87171'
                s = '+' if d['exp']>=0 else ''
                rc = RANK_COLORS[i] if i<len(RANK_COLORS) else TEXT3
                rows += (
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid {BORDER};">'
                    f'<span style="color:{rc};font-size:0.68em;font-weight:700;min-width:20px;">#{i+1}</span>'
                    f'<span style="color:{TEXT};font-size:0.82em;font-weight:500;flex:1;margin-left:8px;">{d["day"]}</span>'
                    f'<span style="color:{c};font-size:0.82em;font-weight:700;min-width:46px;text-align:right;">{s}{d["exp"]}R</span>'
                    f'<span style="color:{TEXT2};font-size:0.78em;min-width:38px;text-align:right;">{d["wr"]}%</span>'
                    f'<span style="color:{TEXT3};font-size:0.72em;min-width:24px;text-align:right;">{d["n"]}t</span>'
                    f'</div>')
            st.markdown(f'<div class="v3-panel">{rows}</div>', unsafe_allow_html=True)

# ============ EDGE ANALYSIS ============
elif page == 'Edge Analysis':
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:4px;">Edge Analysis</div>', unsafe_allow_html=True)

    ea1, ea2 = st.columns(2)
    with ea1:
        for col,title in [('Entry Model','Entry Model'),('Entry Model Timeframe','Entry Timeframe'),('Double Confirmation','Double Confirmation'),('Target','Target'),('Entry + Confirmation','Rejection Candle'),('News Proximity','News Proximity')]:
            render_breakdown(df_main,col,title)
    with ea2:
        for col,title in [('Entry Confluences','Entry Confluences'),('Stop Loss Logic','Stop Loss'),('Hour','Time of Day'),('Trade Quality Rating','Trade Quality'),('Emotional State Before...','Emotional State'),('Conditions MTF/HTF','Market Conditions')]:
            render_breakdown(df_main,col,title)

    st.markdown(f'<hr class="v3-divider">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin-bottom:14px;">Next Trade Checklist</div>', unsafe_allow_html=True)

    if green_checklist or red_checklist:
        cl1,cl2 = st.columns(2)
        with cl1:
            st.markdown(f'<div style="font-size:0.62em;color:#4ade80;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">✓ Do more of this</div>', unsafe_allow_html=True)
            for i,item in enumerate(green_checklist):
                st.markdown(f'<div class="checklist-item" style="animation-delay:{i*40}ms;"><div style="width:6px;height:6px;border-radius:50%;background:#4ade80;margin-top:5px;flex-shrink:0;"></div><div><div style="color:{TEXT};font-size:0.85em;font-weight:500;">{item["label"]}</div><div style="color:{TEXT2};font-size:0.72em;margin-top:2px;">{item["detail"]}</div></div></div>', unsafe_allow_html=True)
        with cl2:
            st.markdown(f'<div style="font-size:0.62em;color:#f87171;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">✗ Avoid this</div>', unsafe_allow_html=True)
            for i,item in enumerate(red_checklist):
                st.markdown(f'<div class="checklist-item" style="animation-delay:{i*40}ms;"><div style="width:6px;height:6px;border-radius:50%;background:#f87171;margin-top:5px;flex-shrink:0;"></div><div><div style="color:{TEXT};font-size:0.85em;font-weight:500;">{item["label"]}</div><div style="color:{TEXT2};font-size:0.72em;margin-top:2px;">{item["detail"]}</div></div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="color:{TEXT2};font-size:0.85em;">Not enough data yet.</div>', unsafe_allow_html=True)

    st.markdown(f'<hr class="v3-divider">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin-bottom:14px;">Consistency Score</div>', unsafe_allow_html=True)
    csc1,csc2 = st.columns([1,2])
    with csc1:
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:center;padding:16px 0;">'
            f'<div style="position:relative;width:90px;height:90px;">'
            f'<svg viewBox="0 0 100 100" style="width:90px;height:90px;transform:rotate(-90deg);">'
            f'<circle cx="50" cy="50" r="38" fill="none" stroke="{BG3}" stroke-width="8"/>'
            f'<circle cx="50" cy="50" r="38" fill="none" stroke="{ACCENT}" stroke-width="8" stroke-dasharray="239" stroke-dashoffset="239">'
            f'<animate attributeName="stroke-dashoffset" from="239" to="{round(239-(consistency_score/100)*239)}" dur="1s" begin="0.2s" fill="freeze"/>'
            f'</circle></svg>'
            f'<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:1.1em;font-weight:700;color:{TEXT};">{consistency_score}%</div>'
            f'</div></div>', unsafe_allow_html=True)
    with csc2:
        for i,(lbl,score) in enumerate(consistency_breakdown):
            c = '#4ade80' if score>=70 else ('#f59e0b' if score>=50 else '#f87171')
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid {BORDER};animation:slideInLeft 0.4s cubic-bezier(0.16,1,0.3,1) {i*70}ms both;">'
                f'<span style="color:{TEXT2};font-size:0.82em;">{lbl}</span>'
                f'<span style="color:{c};font-weight:600;font-size:0.82em;">{score}%</span>'
                f'</div>', unsafe_allow_html=True)

# ============ BEST SETUPS ============
elif page == 'Best Setups':
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:4px;">Best Setups</div>', unsafe_allow_html=True)
 
    if best_setup:
        st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin-bottom:12px;">Top Setup Finder</div>', unsafe_allow_html=True)
        tags = ''.join([f'<span style="background:rgba({RGB},0.1);border-radius:6px;padding:4px 10px;font-size:0.75em;color:{ACCENT};margin:3px;display:inline-block;animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) {i*50}ms both;">{b["label"]}</span>' for i,b in enumerate(best_setup['combos'])])
        oc = '#4ade80' if best_setup['overall_wr']>=60 else ('#f59e0b' if best_setup['overall_wr']>=45 else '#f87171')
        st.markdown(
            f'<div class="v3-panel">'
            f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:18px;">{tags}</div>'
            f'<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">'
            f'<div style="text-align:center;"><div style="font-size:1.3em;font-weight:700;color:{oc};">{best_setup["overall_wr"]}%</div><div style="font-size:0.58em;color:{TEXT2};margin-top:3px;text-transform:uppercase;letter-spacing:0.5px;">Avg Win Rate</div></div>'
            f'<div style="text-align:center;"><div style="font-size:1.3em;font-weight:700;color:{TEXT};">+{best_setup["overall_exp"]}R</div><div style="font-size:0.58em;color:{TEXT2};margin-top:3px;text-transform:uppercase;letter-spacing:0.5px;">Avg Expectancy</div></div>'
            f'</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:24px 0 12px;">Best of Each Variable</div>', unsafe_allow_html=True)

    setup_cols = [('Entry Model','Entry Model'),('Entry Model Timeframe','Timeframe'),('3SL Window','3SL Window'),('Target','Target'),('Stop Loss Logic','Stop Loss'),('Entry + Confirmation','Rejection Candle'),('Double Confirmation','Double Confirmation'),('Hour','Time of Day'),('Trade Quality Rating','Trade Quality'),('Emotional State Before...','Emotional State'),('News Proximity','News Proximity'),('Conditions MTF/HTF','Market Conditions')]
    rows = ''
    for i,(cn,lbl) in enumerate(setup_cols):
        best = get_best(df_main,cn)
        if not best: continue
        c = '#4ade80' if best['exp']>=0 else '#f87171'
        s = '+' if best['exp']>=0 else ''
        rows += (
            f'<div class="setup-row" style="animation-delay:{i*35}ms;">'
            f'<span style="color:{TEXT2};font-size:0.68em;text-transform:uppercase;letter-spacing:0.5px;min-width:110px;">{lbl}</span>'
            f'<span style="color:{TEXT};font-size:0.85em;font-weight:500;flex:1;">{best["label"]}</span>'
            f'<span style="color:{c};font-size:0.82em;font-weight:700;min-width:46px;text-align:right;">{s}{best["exp"]}R</span>'
            f'<span style="color:{TEXT2};font-size:0.78em;min-width:36px;text-align:right;">{best["wr"]}%</span>'
            f'<span style="color:{TEXT3};font-size:0.72em;min-width:24px;text-align:right;">{best["n"]}t</span>'
            f'</div>')

    if rows:
        st.markdown(
            f'<div class="v3-panel">'
            f'<div style="display:flex;gap:12px;padding-bottom:8px;margin-bottom:2px;border-bottom:1px solid {BORDER};">'
            f'<span style="color:{TEXT3};font-size:0.6em;font-weight:600;text-transform:uppercase;min-width:110px;">Variable</span>'
            f'<span style="color:{TEXT3};font-size:0.6em;font-weight:600;text-transform:uppercase;flex:1;">Best</span>'
            f'<span style="color:{TEXT3};font-size:0.6em;font-weight:600;text-transform:uppercase;min-width:46px;text-align:right;">Avg R</span>'
            f'<span style="color:{TEXT3};font-size:0.6em;font-weight:600;text-transform:uppercase;min-width:36px;text-align:right;">WR</span>'
            f'<span style="color:{TEXT3};font-size:0.6em;font-weight:600;text-transform:uppercase;min-width:24px;text-align:right;">N</span>'
            f'</div>{rows}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
