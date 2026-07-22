import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from datetime import datetime
import calendar as cal_module
import math
import json

st.set_page_config(page_title="Trading Data", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

PASSWORD = st.secrets.get("DASHBOARD_PASSWORD", "trading123")
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp { background:#070b14; font-family:'Inter',sans-serif; }
    div[data-testid="stForm"] { background:transparent; border:none; }
    div[data-testid="stFormSubmitButton"] button {
        background:rgba(255,255,255,0.06) !important; border:1px solid rgba(255,255,255,0.1) !important;
        color:#fff !important; border-radius:10px !important; min-height:48px !important; font-weight:600 !important;
    }
    div[data-testid="stTextInput"] input {
        background:rgba(255,255,255,0.05) !important; border:1px solid rgba(255,255,255,0.08) !important;
        border-radius:10px !important; color:#fff !important; padding:12px 16px !important;
    }
    div[data-testid="stTextInput"] input:focus { border-color:rgba(255,255,255,0.2) !important; box-shadow:none !important; }
    div[data-testid="stTextInput"] > div, div[data-testid="stTextInput"] > div > div,
    div[data-testid="stTextInput"] > div > div > div { border:none !important; background:transparent !important; box-shadow:none !important; padding:0 !important; }
    div[data-testid="stTextInput"] > label { display:none !important; }
    </style>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.5, 2, 1.5])
    with c2:
        st.markdown('<div style="text-align:center;padding:80px 0 40px;"><div style="font-size:2em;font-weight:800;color:#fff;margin-bottom:6px;">Trading Data</div><div style="color:rgba(255,255,255,0.25);font-size:0.82em;margin-bottom:32px;">Your personal trading journal</div></div>', unsafe_allow_html=True)
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
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
COACH_MEMORY_PAGE_ID = "3a4c0c4c46ff8044b44ee780f7a0c6d8"
headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}

if 'theme' not in st.session_state: st.session_state.theme = 'Neutral'
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = True
if 'num_accounts' not in st.session_state: st.session_state.num_accounts = 1
if 'overview_idx' not in st.session_state: st.session_state.overview_idx = 0
if 'active_page' not in st.session_state: st.session_state.active_page = 'Overview'
if 'cal_month' not in st.session_state: st.session_state.cal_month = datetime.now().month
if 'cal_year' not in st.session_state: st.session_state.cal_year = datetime.now().year
if 'selected_day' not in st.session_state: st.session_state.selected_day = None
if 'coach_debrief' not in st.session_state: st.session_state.coach_debrief = None
if 'coach_profile' not in st.session_state: st.session_state.coach_profile = None
if 'coach_character' not in st.session_state: st.session_state.coach_character = None
if 'midweek_checkin' not in st.session_state: st.session_state.midweek_checkin = None
if 'coach_history' not in st.session_state: st.session_state.coach_history = []

ACCOUNT_SIZE = 50000
themes = {
    'Blue':    {'ACCENT':'#60a5fa','ACCENT_SOFT':'#93c5fd','RGB':'96,165,250'},
    'Purple':  {'ACCENT':'#a78bfa','ACCENT_SOFT':'#c4b5fd','RGB':'167,139,250'},
    'Green':   {'ACCENT':'#34d399','ACCENT_SOFT':'#6ee7b7','RGB':'52,211,153'},
    'Gold':    {'ACCENT':'#fcd34d','ACCENT_SOFT':'#fde68a','RGB':'252,211,77'},
    'Neutral': {'ACCENT':'#94a3b8','ACCENT_SOFT':'#cbd5e1','RGB':'148,163,184'},
}
T = themes.get(st.session_state.theme, themes['Neutral'])
ACCENT = T['ACCENT']; ACCENT_SOFT = T['ACCENT_SOFT']; RGB = T['RGB']
IS_DARK = st.session_state.dark_mode
GOLD = '#f59e0b'; GOLD_S = '#fcd34d'; PURPLE_C = '#a78bfa'; PURPLE_S = '#c4b5fd'
RANK_COLORS = ['#fcd34d','#94a3b8','#64748b']

if IS_DARK:
    BG='#070b14'; BG2='rgba(255,255,255,0.03)'; BG3='rgba(255,255,255,0.05)'
    TEXT='#ffffff'; TEXT2='rgba(255,255,255,0.45)'; TEXT3='rgba(255,255,255,0.2)'
    BORDER='rgba(255,255,255,0.06)'; BORDER2='rgba(255,255,255,0.08)'
    SIDEBAR='rgba(255,255,255,0.02)'; SIDEBAR_B='rgba(255,255,255,0.05)'; SHADOW='rgba(0,0,0,0.3)'
else:
    BG='#f8f9fa'; BG2='rgba(0,0,0,0.02)'; BG3='rgba(0,0,0,0.04)'
    TEXT='#0f172a'; TEXT2='rgba(0,0,0,0.4)'; TEXT3='rgba(0,0,0,0.15)'
    BORDER='rgba(0,0,0,0.05)'; BORDER2='rgba(0,0,0,0.08)'
    SIDEBAR='rgba(0,0,0,0.02)'; SIDEBAR_B='rgba(0,0,0,0.06)'; SHADOW='rgba(0,0,0,0.08)'

def save_coach_memory(profile, character, debrief=None, week_label=None):
    try:
        response = requests.get(f"https://api.notion.com/v1/blocks/{COACH_MEMORY_PAGE_ID}/children", headers=headers)
        existing_history = []
        if response.status_code == 200:
            blocks = response.json().get('results', [])
            for block in blocks:
                if block['type'] == 'code':
                    try:
                        text = block['code']['rich_text'][0]['text']['content']
                        existing = json.loads(text)
                        if 'history' in existing:
                            existing_history = existing['history']
                    except: pass
                requests.delete(f"https://api.notion.com/v1/blocks/{block['id']}", headers=headers)
        if debrief and week_label:
            history_entry = {
                'week': week_label,
                'grade': debrief.get('grade','—'),
                'grade_reason': debrief.get('grade_reason',''),
                'debrief': debrief.get('debrief',''),
                'focus_points': debrief.get('focus_points',[]),
                'action_plan': debrief.get('action_plan',''),
                'behavioral_patterns': debrief.get('behavioral_patterns',[]),
                'red_flags': debrief.get('red_flags',[]),
                'trader_character': debrief.get('trader_character',{}),
                'saved_at': datetime.now().isoformat()
            }
            existing_history = [h for h in existing_history if h.get('week') != week_label]
            existing_history.insert(0, history_entry)
            existing_history = existing_history[:12]
        memory = {'profile': profile, 'character': character, 'history': existing_history, 'updated': datetime.now().isoformat()}
        requests.patch(f"https://api.notion.com/v1/blocks/{COACH_MEMORY_PAGE_ID}/children", headers=headers,
            json={"children": [{"object": "block", "type": "code", "code": {"rich_text": [{"type": "text", "text": {"content": json.dumps(memory)}}], "language": "json"}}]})
        return True
    except: return False

def load_coach_memory():
    try:
        response = requests.get(f"https://api.notion.com/v1/blocks/{COACH_MEMORY_PAGE_ID}/children", headers=headers)
        if response.status_code != 200: return None, None, []
        blocks = response.json().get('results', [])
        for block in blocks:
            if block['type'] == 'code':
                text = block['code']['rich_text'][0]['text']['content']
                memory = json.loads(text)
                return memory.get('profile'), memory.get('character'), memory.get('history', [])
        return None, None, []
    except: return None, None, []

@st.cache_data(ttl=300)
def get_all_trades():
    all_results=[]; has_more=True; start_cursor=None
    while has_more:
        payload={}
        if start_cursor: payload["start_cursor"]=start_cursor
        try:
            r=requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",headers=headers,json=payload,timeout=10)
            data=r.json()
            if r.status_code==401: raise Exception("Invalid Notion token")
            if r.status_code==404: raise Exception("Database not found")
            if r.status_code!=200: raise Exception(f"Notion API error {r.status_code}")
            all_results.extend(data['results']); has_more=data['has_more']; start_cursor=data.get('next_cursor')
        except requests.exceptions.Timeout: raise Exception("Notion connection timed out")
        except requests.exceptions.ConnectionError: raise Exception("Can't reach Notion — check your internet connection")
    return all_results

def extract_property(prop):
    if prop is None: return None
    pt=prop['type']
    if pt=='title': return prop['title'][0]['plain_text'] if prop['title'] else None
    elif pt=='rich_text': return prop['rich_text'][0]['plain_text'] if prop['rich_text'] else None
    elif pt=='number': return prop['number']
    elif pt=='select': return prop['select']['name'] if prop['select'] else None
    elif pt=='multi_select': return [x['name'] for x in prop['multi_select']]
    elif pt=='date': return prop['date']['start'] if prop['date'] else None
    elif pt=='checkbox': return prop['checkbox']
    elif pt=='formula': f=prop['formula']; return f.get(f['type'])
    elif pt=='status': return prop['status']['name'] if prop['status'] else None
    else: return str(prop.get(pt,''))

def extract_str(prop):
    val=extract_property(prop)
    return ', '.join(val) if isinstance(val,list) else val

def parse_r(value):
    if value is None or str(value).strip() in ['','nan']: return None
    try: return float(str(value).strip().upper().replace('RR','').replace('+','').strip())
    except: return None

def parse_date(x):
    if pd.isna(x) or x is None or str(x).strip()=='': return pd.NaT
    try:
        from dateutil import parser as _p
        ts=pd.Timestamp(_p.isoparse(str(x)))
        return ts.tz_convert('Australia/Sydney').tz_localize(None) if ts.tzinfo else ts
    except:
        try:
            from dateutil import parser as _p
            ts=pd.Timestamp(_p.parse(str(x)))
            return ts.tz_convert('Australia/Sydney').tz_localize(None) if ts.tzinfo else ts
        except: return pd.NaT

def calc_stats(df_in):
    s={}; r=df_in['R_Result'].dropna()
    if len(r)==0: return s
    s['total_trades']=len(r); s['wins']=int((r>0).sum()); s['losses']=int((r<0).sum()); s['breakevens']=int((r==0).sum())
    nb=s['wins']+s['losses']; s['win_rate']=round(s['wins']/nb*100,1) if nb>0 else 0
    s['total_r']=round(r.sum(),2); s['avg_r']=round(r.mean(),2)
    s['avg_win']=round(r[r>0].mean(),2) if s['wins']>0 else 0
    s['avg_loss']=round(r[r<0].mean(),2) if s['losses']>0 else 0
    s['best_trade']=round(r.max(),2); s['worst_trade']=round(r.min(),2); s['expectancy']=round(r.sum()/len(r),2)
    eq=r.cumsum(); peak=eq.cummax(); s['max_drawdown']=round((eq-peak).min(),2); s['equity_curve']=eq.tolist()
    streak=ms=0
    for v in r:
        streak=streak+1 if v<0 else 0; ms=max(ms,streak)
    s['max_consec_losses']=ms; cur=0; ct=None
    for v in reversed(r.tolist()):
        t='W' if v>0 else ('L' if v<0 else 'B')
        if ct is None: ct=t
        if t==ct: cur+=1
        else: break
    s['cur_streak']=cur; s['cur_streak_type']=ct
    vals=r.tolist(); rolling=[]
    for i in range(len(vals)):
        w=vals[max(0,i-9):i+1]; ww=sum(1 for v in w if v>0); lw=sum(1 for v in w if v<0)
        rolling.append(round(ww/(ww+lw)*100,1) if (ww+lw)>0 else 0)
    s['rolling_wr']=rolling; s['trade_results']=['W' if v>0 else ('L' if v<0 else 'B') for v in vals]
    return s

def calc_session_stats(df_in):
    if '3SL Window' not in df_in.columns: return []
    df_t=df_in.copy(); df_t['3SL Window']=df_t['3SL Window'].fillna('No Window').replace('','No Window')
    results=[]
    for session in ['Asia','London','New York','No Window']:
        r=df_t[df_t['3SL Window']==session]['R_Result'].dropna(); n=len(r)
        if n==0: results.append({'session':session,'exp':0,'wr':0,'n':0}); continue
        w=int((r>0).sum()); l=int((r<0).sum()); nb=w+l
        results.append({'session':session,'exp':round(r.sum()/n,3),'wr':round(w/nb,2) if nb>0 else 0,'n':n})
    return sorted(results,key=lambda x:x['exp'],reverse=True)

def calc_daily_r(df_in):
    df_t=df_in.dropna(subset=['Date','R_Result']).copy(); df_t['day']=df_t['Date'].dt.date; daily={}
    for day,row in df_t.groupby('day')['R_Result'].agg(['count','sum']).iterrows():
        daily[day]={'trades':int(row['count']),'total_r':round(row['sum'],2)}
    return daily

def calc_monthly_r(df_in):
    df_t=df_in.dropna(subset=['Date','R_Result']).copy(); df_t['month']=df_t['Date'].dt.to_period('M'); monthly={}
    for period,grp in df_t.groupby('month')['R_Result']:
        r=grp; n=len(r); w=int((r>0).sum()); nb=w+int((r<0).sum())
        monthly[str(period)]={'trades':n,'total_r':round(r.sum(),2),'win_rate':round(w/nb*100,1) if nb>0 else 0}
    return monthly

def calc_dow_stats(df_in):
    df_t=df_in.dropna(subset=['Date','R_Result']).copy(); df_t['dow']=df_t['Date'].dt.day_name(); results=[]
    for day in ['Monday','Tuesday','Wednesday','Thursday','Friday']:
        r=df_t[df_t['dow']==day]['R_Result'].dropna(); n=len(r)
        if n==0: continue
        w=int((r>0).sum()); l=int((r<0).sum()); nb=w+l
        results.append({'day':day,'short':day[:3],'exp':round(r.sum()/n,2),'wr':round(w/nb*100,1) if nb>0 else 0,'n':n})
    return sorted(results,key=lambda x:x['exp'],reverse=True)

def breakdown_by_col(df_in,col,min_trades=2):
    if col not in df_in.columns: return []
    temp=df_in.dropna(subset=['R_Result',col]).copy()
    temp=temp[temp[col].notna()&(temp[col]!='')&(temp[col]!='NA')&(temp[col]!='N/A')]; results=[]
    for val,grp in temp.groupby(col):
        r=grp['R_Result'].dropna(); n=len(r)
        if n<min_trades: continue
        w=int((r>0).sum()); l=int((r<0).sum()); nb=w+l
        results.append({'label':str(val),'wr':round(w/nb*100,1) if nb>0 else 0,'exp':round(r.sum()/n,2),'n':n})
    return sorted(results,key=lambda x:x['exp'],reverse=True)

def get_best(df_in,col):
    data=breakdown_by_col(df_in,col,min_trades=2)
    return data[0] if data else None

def calc_consistency_score(df_in,session_stats):
    scores=[]
    if 'Trade Quality Rating' in df_in.columns:
        temp=df_in.dropna(subset=['Trade Quality Rating'])
        aplus=temp[temp['Trade Quality Rating'].str.contains('A\\+',na=False,regex=True)]
        if len(temp)>0: scores.append(('A+ quality trades',round(len(aplus)/len(temp)*100)))
    if 'Rules Followed? Y/N' in df_in.columns:
        temp=df_in.dropna(subset=['Rules Followed? Y/N'])
        yes=temp[temp['Rules Followed? Y/N'].str.lower().str.startswith('yes',na=False)]
        if len(temp)>0: scores.append(('Rules followed',round(len(yes)/len(temp)*100)))
    if session_stats:
        best=max(session_stats,key=lambda x:x['exp'])
        if '3SL Window' in df_in.columns:
            temp=df_in.dropna(subset=['3SL Window','R_Result'])
            in_best=temp[temp['3SL Window']==best['session']]
            if len(temp)>0: scores.append((f"In {best['session']} session",round(len(in_best)/len(temp)*100)))
    if 'Emotional State Before...' in df_in.columns:
        temp=df_in.dropna(subset=['Emotional State Before...'])
        conf=temp[temp['Emotional State Before...'].str.lower().str.contains('confident',na=False)]
        if len(temp)>0: scores.append(('Confident entries',round(len(conf)/len(temp)*100)))
    overall=round(sum(s[1] for s in scores)/len(scores)) if scores else 0
    return overall,scores

def find_best_setup(df_in):
    cols=['3SL Window','Entry Confluences','Entry Model Timeframe','Double Confirmation','Target']
    best_combos=[]
    for col in [c for c in cols if c in df_in.columns]:
        data=breakdown_by_col(df_in,col,min_trades=2)
        if data and data[0]['exp']>0: best_combos.append({'col':col,'label':data[0]['label'],'wr':data[0]['wr'],'exp':data[0]['exp'],'n':data[0]['n']})
    if not best_combos: return None
    return {'combos':best_combos,'overall_wr':round(sum(b['wr'] for b in best_combos)/len(best_combos),1),'overall_exp':round(sum(b['exp'] for b in best_combos)/len(best_combos),2)}

def generate_checklist(df_in,session_stats):
    green=[]; red=[]
    for col,label in [('Entry Model','entry model'),('Entry Model Timeframe','timeframe'),('Double Confirmation','double confirmation'),('Target','target'),('Stop Loss Logic','stop loss'),('Entry + Confirmation','rejection candle'),('Trade Quality Rating','trade quality'),('Entry Confluences','entry confluence'),('Conditions MTF/HTF','market conditions')]:
        data=breakdown_by_col(df_in,col,min_trades=2)
        if data and data[0]['exp']>0: green.append({'label':f"Use {data[0]['label']} for {label}",'detail':f"{data[0]['exp']}R avg · {data[0]['wr']}% WR · {data[0]['n']} trades"})
    if session_stats:
        best_s=max(session_stats,key=lambda x:x['exp'])
        if best_s['exp']>0: green.append({'label':f"Trade {best_s['session']} session",'detail':f"{best_s['exp']}R avg · {round(best_s['wr']*100)}% WR · {best_s['n']} trades"})
        for s in session_stats:
            if s['exp']<0 or s['wr']<0.4: red.append({'label':f"Avoid {s['session']} session",'detail':f"{s['exp']}R avg · {round(s['wr']*100)}% WR · {s['n']} trades"})
    for col,wr_thresh,tmpl in [('Emotional State Before...',45,"Avoid trading when {}"),('Trade Quality Rating',45,"Avoid {} quality trades"),('News Proximity',45,"Avoid trading {}"),('Entry Model',45,"Avoid {} entry model"),('Conditions MTF/HTF',45,"Avoid trading in {} conditions"),('Stop Loss Logic',45,"Avoid {} stop loss"),('Target',45,"Avoid {} as target")]:
        if col in df_in.columns:
            for d in breakdown_by_col(df_in,col,min_trades=2):
                if d['exp']<0 or d['wr']<wr_thresh: red.append({'label':tmpl.format(d['label']),'detail':f"{d['exp']}R avg · {d['wr']}% WR · {d['n']} trades"})
    return green,red

def catmull(pts):
    if len(pts)<2: return ""
    d=f"M{pts[0][0]:.1f},{pts[0][1]:.1f} "
    for i in range(len(pts)-1):
        p0=pts[i-1] if i>0 else pts[i]; p1=pts[i]; p2=pts[i+1]; p3=pts[i+2] if i+2<len(pts) else p2
        c1x=p1[0]+(p2[0]-p0[0])/6; c1y=p1[1]+(p2[1]-p0[1])/6
        c2x=p2[0]-(p3[0]-p1[0])/6; c2y=p2[1]-(p3[1]-p1[1])/6
        d+=f"C{c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {p2[0]:.1f},{p2[1]:.1f} "
    return d

def make_curve(eq,w,h):
    if not eq: return "",""
    mn=min(min(eq),0); mx=max(eq); rng=(mx-mn) if (mx-mn)!=0 else 1; n=len(eq)
    pts=[((i/(n-1))*w if n>1 else 0,h-((v-mn)/rng)*(h-20)-10) for i,v in enumerate(eq)]
    line=catmull(pts)
    return line,line+f"L{w},{h} L0,{h} Z"

def build_donut(wins,losses,bes,colors,glow):
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
    return svg,legend

def render_breakdown(df_in,col,title):
    data=breakdown_by_col(df_in,col)
    if not data: return
    data=data[:3]
    st.markdown(f'<div style="color:{TEXT2};font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin:20px 0 10px;">{title}</div>',unsafe_allow_html=True)
    max_exp=max(abs(d['exp']) for d in data) if data else 1
    if max_exp==0: max_exp=1
    for rank,d in enumerate(data):
        bar_pct=round(abs(d['exp'])/max_exp*100,1); color='#4ade80' if d['exp']>=0 else '#f87171'
        lbl=d['label'][:26]+'…' if len(d['label'])>26 else d['label']; rc=RANK_COLORS[rank] if rank<len(RANK_COLORS) else TEXT3
        st.markdown(
            f'<div style="display:grid;grid-template-columns:20px 140px 1fr 50px 50px 28px;gap:8px;align-items:center;padding:8px 0;border-bottom:1px solid {BORDER};">'
            f'<span style="color:{rc};font-size:0.68em;font-weight:700;">#{rank+1}</span>'
            f'<span style="color:{TEXT};font-size:0.82em;">{lbl}</span>'
            f'<div style="background:{BG3};border-radius:4px;height:4px;overflow:hidden;"><div style="width:{bar_pct}%;height:100%;background:{color};border-radius:4px;"></div></div>'
            f'<span style="color:{color};font-size:0.8em;font-weight:600;">{d["exp"]}R</span>'
            f'<span style="color:{TEXT2};font-size:0.8em;">{d["wr"]}%</span>'
            f'<span style="color:{TEXT3};font-size:0.78em;">{d["n"]}</span>'
            f'</div>',unsafe_allow_html=True)

def build_trade_summary(df_week,num_accounts):
    if len(df_week)==0: return "No trades logged this week."
    lines=[]
    for _,t in df_week.iterrows():
        pair=t.get('Pair','?'); r=t.get('R_Result','?')
        date=t['Date'].strftime('%a %b %d') if pd.notna(t['Date']) else '?'
        session=t.get('3SL Window','?'); model=t.get('Entry Model','?')
        quality=t.get('Trade Quality Rating','?'); rules=t.get('Rules Followed? Y/N','?')
        emotion=t.get('Emotional State Before...','?'); teaching=t.get('Teachings/Learning Curve','')
        line=f"- {date} | {pair} | {session} | {model} | R:{r} | Quality:{quality} | Rules:{rules} | Emotion:{emotion}"
        if teaching and str(teaching) not in ['nan','None','']: line+=f" | Notes:{teaching}"
        lines.append(line)
    return '\n'.join(lines)

def call_coach_api(df_week,profile,num_accounts,df_all=None):
    week_r=round(df_week['R_Result'].sum(),2) if len(df_week)>0 else 0
    wins=int((df_week['R_Result']>0).sum()) if len(df_week)>0 else 0
    losses=int((df_week['R_Result']<0).sum()) if len(df_week)>0 else 0
    total=len(df_week); wr=round(wins/(wins+losses)*100,1) if (wins+losses)>0 else 0
    avg_rr=round(df_week['R_Result'].mean(),2) if len(df_week)>0 else 0
    trade_summary=build_trade_summary(df_week,num_accounts)
    profile_ctx=f"EXISTING TRADER PROFILE:\n{profile}" if profile else "No prior profile. This is Kaea's first week of analysis."
    alltime_ctx=""
    if df_all is not None and len(df_all)>0:
        at_r=df_all['R_Result'].dropna()
        at_wins=int((at_r>0).sum()); at_losses=int((at_r<0).sum()); at_nb=at_wins+at_losses
        at_wr=round(at_wins/at_nb*100,1) if at_nb>0 else 0
        at_total_r=round(at_r.sum(),2); at_avg=round(at_r.mean(),2)
        at_best=round(at_r.max(),2); at_worst=round(at_r.min(),2)
        first_date=df_all['Date'].dropna().min().strftime('%b %d %Y') if len(df_all)>0 else '?'
        alltime_ctx=f"\nALL-TIME HISTORY (from {first_date}):\n- Total trades: {len(at_r)} | Win rate: {at_wr}% | Total R: {at_total_r}R | Avg R: {at_avg} | Best: {at_best}R | Worst: {at_worst}R\n"
    prompt=f"""You are Coach, a brutally honest AI trading coach. Your trader's name is Kaea.

{profile_ctx}
{alltime_ctx}
THIS WEEK'S TRADES:
{trade_summary}

WEEK STATS:
- Total trades: {total} | Win rate: {wr}% | Total R: {week_r}R | Avg RR: {avg_rr} | Wins: {wins} | Losses: {losses}

You are NOT generic. Reference specific trades, dates, patterns, language from notes. Brutally honest with tough love but genuine encouragement where earned.

Respond ONLY in this exact JSON format with no other text:
{{
  "debrief": "4-6 sentences. Specific, personal, brutally honest. Reference actual trades and numbers.",
  "focus_points": ["Focus point 1","Focus point 2","Focus point 3"],
  "behavioral_patterns": ["Pattern 1","Pattern 2"],
  "red_flags": ["Red flag 1"],
  "action_plan": "One specific concrete action Kaea must implement next week.",
  "updated_profile": "Updated 4-6 sentence trader profile of Kaea.",
  "grade": "A+/A/B+/B/C+/C/D/F",
  "grade_reason": "One honest sentence explaining the grade.",
  "trader_character": {{
    "title": "Pick ONE title from: The Phantom, The Oracle, The Legend (S), The Sniper, The Ghost, The Assassin, The Architect (A), The Strategist, The Commander, The Grinder, The Titan (B), The Maverick, The Prodigy, The Survivor (C), The Wild Card, The Apprentice, The Berserker (D), The Warmonger (F). Be honest.",
    "tier": "S, A, B, C, D, or F",
    "desc": "One punchy sentence max 12 words.",
    "stats": {{"patience": 0, "discipline": 0, "edge": 0}}
  }}
}}"""
    response=requests.post("https://api.anthropic.com/v1/messages",
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"},
        json={"model":"claude-sonnet-4-6","max_tokens":1500,"messages":[{"role":"user","content":prompt}]},timeout=60)
    if response.status_code!=200: return None
    data=response.json(); text=data['content'][0]['text'].strip()
    if '```' in text:
        parts=text.split('```'); text=parts[1] if len(parts)>1 else text
        if text.startswith('json'): text=text[4:]
    return json.loads(text.strip())

def call_midweek_api(df_tw,profile,num_accounts):
    if len(df_tw)==0: return None
    wins=int((df_tw['R_Result']>0).sum()); losses=int((df_tw['R_Result']<0).sum())
    total=len(df_tw); wr=round(wins/(wins+losses)*100,1) if (wins+losses)>0 else 0
    total_r=round(df_tw['R_Result'].sum(),2)
    trade_summary=build_trade_summary(df_tw,num_accounts)
    profile_ctx=f"TRADER PROFILE:\n{profile}" if profile else "No prior profile yet."
    prompt=f"""You are Coach, a brutally honest AI trading coach. Kaea's name is Kaea.

{profile_ctx}

TRADES SO FAR THIS WEEK:
{trade_summary}

WEEK SO FAR: {total} trades | {wr}% WR | {total_r}R total

Give Kaea a quick mid-week check-in. 2-3 sentences max. Be direct and specific. Reference actual trades. No fluff.

Respond in JSON:
{{"checkin": "2-3 sentence mid-week update.","focus": "One thing Kaea must focus on for the rest of the week."}}"""
    response=requests.post("https://api.anthropic.com/v1/messages",
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"},
        json={"model":"claude-sonnet-4-6","max_tokens":300,"messages":[{"role":"user","content":prompt}]},timeout=30)
    if response.status_code!=200: return None
    data=response.json(); text=data['content'][0]['text'].strip()
    if '```' in text:
        parts=text.split('```'); text=parts[1] if len(parts)>1 else text
        if text.startswith('json'): text=text[4:]
    return json.loads(text.strip())

@st.cache_data(ttl=300)
def compute_all_stats():
    try:
        raw=get_all_trades()
        if not raw: return None,"empty"
        rows=[]
        for trade in raw:
            props=trade['properties']; row={}
            for cn,cd in props.items():
                if cn=='Entry Confluences':
                    val=extract_property(cd); row[cn]=', '.join(val) if isinstance(val,list) else val
                else: row[cn]=extract_str(cd)
            rows.append(row)
        df=pd.DataFrame(rows); df.columns=df.columns.str.strip()
        df['Date']=df['Date'].apply(parse_date); df['Date']=pd.Series(df['Date'].tolist(),dtype='datetime64[ns]')
        df['R_Result']=df['R Result'].apply(parse_r)
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
            df['Hour']=df['Time of Trade'].apply(ph)
        df=df.sort_values('Date').reset_index(drop=True)
        if 'Pair' in df.columns: df['Pair']=df['Pair'].str.strip()
        df_x=df[df['Pair']=='XAUUSD'].copy() if 'Pair' in df.columns else pd.DataFrame()
        df_n=df[df['Pair']=='NASDAQ'].copy() if 'Pair' in df.columns else pd.DataFrame()
        df_f=df[df['Type of Trade'].str.strip()=='Funded'].copy() if 'Type of Trade' in df.columns else pd.DataFrame()
        ss=calc_session_stats(df); cs,cb=calc_consistency_score(df,ss); gc,rc=generate_checklist(df,ss)
        return {
            'df_main':df,'df_xau':df_x,'df_nas':df_n,'df_funded':df_f,
            'main_stats':calc_stats(df),
            'xau_stats':calc_stats(df_x) if len(df_x)>0 else {},
            'nas_stats':calc_stats(df_n) if len(df_n)>0 else {},
            'session_stats':ss,'daily_r':calc_daily_r(df),'monthly_r':calc_monthly_r(df),
            'dow_stats':calc_dow_stats(df),'consistency_score':cs,'consistency_breakdown':cb,
            'best_setup':find_best_setup(df),'green_checklist':gc,'red_checklist':rc,
        },"ok"
    except Exception as e: return None,f"error:{str(e)}"

data,data_status=compute_all_stats()

if data is None:
    if data_status=="empty":
        st.markdown('<div style="background:rgba(255,255,255,0.03);border-radius:16px;padding:40px 24px;text-align:center;margin:40px auto;max-width:480px;"><div style="font-size:2em;margin-bottom:12px;">📊</div><div style="font-size:0.92em;font-weight:600;color:#fff;margin-bottom:6px;">No trades logged yet</div><div style="font-size:0.72em;color:rgba(255,255,255,0.45);line-height:1.6;">Start logging trades in your Notion database and they\'ll appear here automatically.</div></div>',unsafe_allow_html=True)
    else:
        error_msg=data_status.replace("error:","") if data_status.startswith("error:") else "Unknown error"
        st.markdown(f'<div style="background:rgba(248,113,113,0.04);border:1px solid rgba(248,113,113,0.15);border-radius:16px;padding:24px;display:flex;align-items:flex-start;gap:16px;margin:40px auto;max-width:480px;"><div style="width:40px;height:40px;border-radius:10px;background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.15);display:flex;align-items:center;justify-content:center;font-size:1.1em;flex-shrink:0;">🔌</div><div><div style="font-size:0.88em;font-weight:600;color:#f87171;margin-bottom:4px;">Can\'t reach Notion</div><div style="font-size:0.72em;color:rgba(255,255,255,0.45);line-height:1.5;margin-bottom:10px;">{error_msg}</div></div></div>',unsafe_allow_html=True)
        if st.button("↻ Try again"): st.cache_data.clear(); st.rerun()
    st.stop()

df_main=data['df_main']; df_xau=data['df_xau']; df_nas=data['df_nas']; df_funded=data['df_funded']
main_stats=data['main_stats']; xau_stats=data['xau_stats']; nas_stats=data['nas_stats']
session_stats=data['session_stats']; daily_r=data['daily_r']; monthly_r=data['monthly_r']
dow_stats=data['dow_stats']; consistency_score=data['consistency_score']
consistency_breakdown=data['consistency_breakdown']; best_setup=data['best_setup']
green_checklist=data['green_checklist']; red_checklist=data['red_checklist']
today=datetime.now()
this_month_key=today.strftime('%Y-%m')
last_month_key=(today.replace(day=1)-pd.Timedelta(days=1)).strftime('%Y-%m')
this_month_r=monthly_r.get(this_month_key,{}).get('total_r',0)
last_month_r=monthly_r.get(last_month_key,{}).get('total_r',0)
diff=round(this_month_r-last_month_r,2)
max_abs_exp=max([abs(s['exp']) for s in session_stats]) if session_stats else 1
if max_abs_exp==0: max_abs_exp=1

css=f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
*{{box-sizing:border-box;}}
.stApp{{background:{BG};font-family:'Inter',sans-serif;}}
@keyframes pageIn{{from{{opacity:0;transform:translateY(8px);}}to{{opacity:1;transform:translateY(0);}}}}
@keyframes staggerIn{{from{{opacity:0;transform:translateY(12px) scale(0.98);}}to{{opacity:1;transform:translateY(0) scale(1);}}}}
@keyframes slideInLeft{{from{{opacity:0;transform:translateX(-16px);}}to{{opacity:1;transform:translateX(0);}}}}
@keyframes growBar{{from{{width:0;}}to{{width:100%;}}}}
@keyframes pulseGlow{{0%,100%{{box-shadow:0 0 0 rgba(74,222,128,0);}}50%{{box-shadow:0 0 20px rgba(74,222,128,0.4);}}}}
@keyframes coachGlow{{0%,100%{{box-shadow:0 0 0 rgba({RGB},0);}}50%{{box-shadow:0 0 24px rgba({RGB},0.15);}}}}
@keyframes fadeInUp{{from{{opacity:0;transform:translateY(16px);}}to{{opacity:1;transform:translateY(0);}}}}
.page-content{{animation:pageIn 0.35s cubic-bezier(0.16,1,0.3,1) both;}}
.v3-card{{background:{BG2};border-radius:16px;padding:20px 16px;text-align:center;transition:background 0.2s ease,transform 0.2s ease;cursor:pointer;animation:staggerIn 0.5s cubic-bezier(0.16,1,0.3,1) both;}}
.v3-card:hover{{background:{BG3};transform:translateY(-2px);}}
.v3-val{{font-size:1.5em;font-weight:700;color:{TEXT};}}
.v3-lbl{{font-size:0.6em;color:{TEXT2};margin-top:6px;text-transform:uppercase;letter-spacing:0.8px;font-weight:500;}}
.v3-panel{{background:{BG2};border-radius:20px;padding:24px;margin-bottom:16px;animation:staggerIn 0.5s cubic-bezier(0.16,1,0.3,1) both;}}
.v3-section{{font-size:0.65em;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:{TEXT3};margin:28px 0 14px;display:flex;align-items:center;gap:12px;}}
.v3-section::after{{content:'';flex:1;height:1px;background:{BORDER};}}
.v3-divider{{border:none;border-top:1px solid {BORDER};margin:28px 0;}}
.coach-card{{animation:fadeInUp 0.6s cubic-bezier(0.16,1,0.3,1) both;}}
.coach-avatar{{animation:coachGlow 3s ease-in-out infinite;}}
.coach-message{{animation:fadeInUp 0.8s cubic-bezier(0.16,1,0.3,1) 0.2s both;line-height:1.8;}}
.focus-item{{animation:fadeInUp 0.5s cubic-bezier(0.16,1,0.3,1) both;}}
.pattern-item{{animation:fadeInUp 0.5s cubic-bezier(0.16,1,0.3,1) both;}}
section[data-testid="stSidebar"]{{background:{SIDEBAR} !important;border-right:1px solid {SIDEBAR_B} !important;}}
section[data-testid="stSidebar"]>div{{padding-top:0 !important;}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button{{min-height:40px !important;background:transparent !important;border:none !important;color:{TEXT2} !important;border-radius:8px !important;font-size:0.85em !important;text-align:left !important;padding-left:12px !important;display:flex !important;align-items:center !important;justify-content:flex-start !important;box-shadow:none !important;transition:all 0.15s ease !important;}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover{{background:{BG2} !important;color:{TEXT} !important;}}
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"]{{margin:0 !important;padding:0 !important;}}
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p{{margin:0 !important;padding:0 !important;}}
div[data-testid="stButton"] button{{width:100%;min-height:44px;border-radius:10px;font-family:'Inter',sans-serif;transition:all 0.15s ease;font-weight:500;background:{BG2} !important;border:1px solid {BORDER2} !important;color:{TEXT} !important;box-shadow:none !important;}}
div[data-testid="stButton"] button:hover{{background:{BG3} !important;transform:translateY(-1px);}}
.cal-header{{color:{TEXT2};font-size:0.65em;text-align:center;letter-spacing:1px;font-weight:600;text-transform:uppercase;padding:8px 0;}}
.cal-day-num{{color:{TEXT3};font-size:0.72em;font-weight:600;text-align:center;}}
.streak-box{{width:28px;height:28px;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;margin:2px;animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) both;}}
.streak-box.active{{animation:pulseGlow 2s ease-in-out infinite !important;}}
.grow-bar{{animation:growBar 1.2s cubic-bezier(0.16,1,0.3,1) both;animation-play-state:paused;}}
.checklist-item{{display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-bottom:1px solid {BORDER};animation:slideInLeft 0.4s cubic-bezier(0.16,1,0.3,1) both;}}
.setup-row{{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid {BORDER};animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) both;}}
div[data-testid="stNumberInput"] input{{background:{BG2} !important;border:1px solid {BORDER2} !important;border-radius:8px !important;color:{TEXT} !important;}}
div[data-testid="stNumberInput"] button{{background:{BG2} !important;border:1px solid {BORDER2} !important;color:{TEXT} !important;box-shadow:none !important;}}
div[data-testid="stNumberInput"] button svg{{fill:{TEXT} !important;stroke:{TEXT} !important;}}
div[data-testid="stNumberInput"] button p{{color:{TEXT} !important;}}
div[data-testid="stNumberInput"] > label{{color:{TEXT} !important;}}
.cal-arrows div[data-testid="stButton"] button{{min-height:40px !important;max-height:40px !important;height:40px !important;border-radius:8px !important;padding:0 !important;margin:0 !important;}}
div[data-testid="stExpander"] div[data-testid="stExpanderDetails"]{{background:{BG3} !important;border-radius:0 0 10px 10px !important;}}
div[data-testid="stExpander"]{{border:1px solid {BORDER2} !important;border-radius:10px !important;}}
div[data-testid="stExpander"] summary{{color:{TEXT} !important;}}
div[data-testid="stExpander"] summary span{{color:{TEXT} !important;}}
div[data-testid="stExpander"] summary p{{color:{TEXT} !important;}}
</style>
"""
st.markdown(css,unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f'<div style="padding:20px 16px 16px;border-bottom:1px solid {BORDER};margin-bottom:8px;"><span style="font-size:1em;font-weight:700;color:{TEXT};">Trading Data</span></div>',unsafe_allow_html=True)
    pages=['Overview','P&L Tracker','Charts','Calendar','Edge Analysis','Best Setups','Coach']
    for p in pages:
        is_active=st.session_state.active_page==p
        icon='⚡ ' if p=='Coach' else ''
        if is_active:
            st.markdown(f'<div style="background:{BG2};border-left:2px solid {ACCENT};border-radius:8px;padding:9px 12px;margin:0;font-size:0.85em;font-weight:600;color:{ACCENT};line-height:1.6;">{icon}{p}</div>',unsafe_allow_html=True)
        else:
            if st.button(f"{icon}{p}",key=f"nav_{p}",use_container_width=True):
                st.session_state.active_page=p; st.rerun()
    st.markdown(f'<div style="margin-top:16px;"></div>',unsafe_allow_html=True)
    if st.button("↻  Refresh",key="refresh_btn",use_container_width=True):
        st.cache_data.clear(); st.rerun()
    if st.button("⎋  Logout",key="logout_btn",use_container_width=True):
        st.session_state.authenticated=False; st.rerun()
    st.markdown(f'<div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:16px;"><div style="font-size:0.58em;color:{TEXT3};letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;">Theme</div></div>',unsafe_allow_html=True)
    theme_opts={'Blue':'#60a5fa','Purple':'#a78bfa','Green':'#34d399','Gold':'#fcd34d','Neutral':'#94a3b8'}
    tcols=st.columns(5)
    for i,(name,hex_c) in enumerate(theme_opts.items()):
        active_t=st.session_state.theme==name; bdr='2px solid #fff' if active_t else '2px solid transparent'
        tcols[i].markdown(f'<div style="width:20px;height:20px;border-radius:50%;background:{hex_c};border:{bdr};margin:auto;"></div>',unsafe_allow_html=True)
        if tcols[i].button(" ",key=f"theme_{name}",use_container_width=True):
            st.session_state.theme=name; st.rerun()
    st.markdown(f'<div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:12px;"></div>',unsafe_allow_html=True)
    cg,cb=st.columns([3,1])
    cg.markdown(f'<div style="font-size:0.7em;color:{TEXT2};padding-top:8px;">{"Light" if IS_DARK else "Dark"} Mode</div>',unsafe_allow_html=True)
    with cb:
        if st.button("☀️" if IS_DARK else "🌙",key="mode_toggle",use_container_width=True):
            st.session_state.dark_mode=not IS_DARK; st.rerun()

page=st.session_state.active_page
st.markdown('<div class="page-content">',unsafe_allow_html=True)

# ============ OVERVIEW ============
if page=='Overview':
    cur=main_stats.get('cur_streak',0); cur_type=main_stats.get('cur_streak_type','—')
    cur_color='#4ade80' if cur_type=='W' else ('#f87171' if cur_type=='L' else ACCENT)
    cur_label='Win Streak' if cur_type=='W' else ('Loss Streak' if cur_type=='L' else 'Streak')
    diff_color='#4ade80' if diff>=0 else '#f87171'; diff_sign='+' if diff>=0 else ''; month_sign='+' if this_month_r>0 else ''
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:20px;">Overview</div>',unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:{BG2};border-radius:18px;padding:22px 28px;display:flex;align-items:center;margin-bottom:24px;">'
        f'<div style="flex:1;text-align:center;"><div style="font-size:1.8em;font-weight:800;color:{cur_color};">{cur}</div><div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">{cur_label}</div></div>'
        f'<div style="width:1px;height:36px;background:{BORDER};"></div>'
        f'<div style="flex:1;text-align:center;"><div style="font-size:1.8em;font-weight:800;color:{ACCENT};" id="b-cons">—</div><div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">Consistency</div></div>'
        f'<div style="width:1px;height:36px;background:{BORDER};"></div>'
        f'<div style="flex:1;text-align:center;"><div style="font-size:1.8em;font-weight:800;color:{TEXT};" id="b-month">—</div><div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">This Month</div></div>'
        f'<div style="width:1px;height:36px;background:{BORDER};"></div>'
        f'<div style="flex:1;text-align:center;"><div style="font-size:1.8em;font-weight:800;color:{diff_color};" id="b-diff">—</div><div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">vs Last Month</div></div>'
        f'</div>',unsafe_allow_html=True)
    components.html(f"""
<script>
function countUp(id,target,dec,suffix,final,dur){{
    var el=window.parent.document.getElementById(id);if(!el)return;
    var t0=null;
    function step(ts){{if(!t0)t0=ts;var p=Math.min((ts-t0)/dur,1),e=1-Math.pow(1-p,3);
    el.textContent=(dec>0?(target*e).toFixed(dec):Math.round(target*e))+suffix;
    if(p<1)requestAnimationFrame(step);else el.textContent=final;}}
    requestAnimationFrame(step);
}}
setTimeout(function(){{
    countUp('b-cons',{consistency_score},0,'%','{consistency_score}%',800);
    countUp('b-month',{abs(this_month_r)},2,'R','{month_sign}{this_month_r}R',800);
    countUp('b-diff',{abs(diff)},2,'R','{diff_sign}{diff}R',800);
    var bars=window.parent.document.querySelectorAll('.grow-bar');
    var obs=new IntersectionObserver(function(entries){{entries.forEach(function(e){{if(e.isIntersecting){{e.target.style.animationPlayState='running';obs.unobserve(e.target);}}}});}},{{threshold:0.1}});
    bars.forEach(function(b){{var r=b.getBoundingClientRect();if(r.top<window.parent.innerHeight)b.style.animationPlayState='running';else obs.observe(b);}});
}},150);
</script>
    """,height=0)
    st.markdown(f'<div class="v3-section">Performance</div>',unsafe_allow_html=True)
    overviews=[{'label':'Overall','stats':main_stats,'color':ACCENT_SOFT},{'label':'XAUUSD','stats':xau_stats,'color':GOLD_S},{'label':'NASDAQ','stats':nas_stats,'color':PURPLE_S}]
    idx=st.session_state.overview_idx; current=overviews[idx]
    pc,nc=st.columns(2)
    with pc:
        if st.button(f"← {overviews[(idx-1)%3]['label']}",key="prev_ov",use_container_width=True):
            st.session_state.overview_idx=(idx-1)%3; st.rerun()
    with nc:
        if st.button(f"{overviews[(idx+1)%3]['label']} →",key="next_ov",use_container_width=True):
            st.session_state.overview_idx=(idx+1)%3; st.rerun()
    st.markdown(f'<div style="background:{BG2};border-radius:14px;padding:14px 20px;text-align:center;margin-bottom:16px;font-size:1em;font-weight:700;color:{current["color"]};">{current["label"]} Performance</div>',unsafe_allow_html=True)
    stat_data=[('Total Trades',current['stats'].get('total_trades','—')),('Win Rate',f"{current['stats'].get('win_rate','—')}%"),('Total R',current['stats'].get('total_r','—')),('Avg R',current['stats'].get('avg_r','—')),('Expectancy',current['stats'].get('expectancy','—')),('Avg Win',current['stats'].get('avg_win','—')),('Avg Loss',current['stats'].get('avg_loss','—')),('Best Trade',current['stats'].get('best_trade','—')),('Worst Trade',current['stats'].get('worst_trade','—')),('Max DD',current['stats'].get('max_drawdown','—')),('Consec L',current['stats'].get('max_consec_losses','—')),('Wins',current['stats'].get('wins','—')),('Losses',current['stats'].get('losses','—')),('Breakevens',current['stats'].get('breakevens','—'))]
    for i in range(0,len(stat_data),7):
        row=stat_data[i:i+7]; cols=st.columns(len(row))
        for j,(col,(lbl,val)) in enumerate(zip(cols,row)):
            col.markdown(f'<div class="v3-card" style="animation-delay:{j*40}ms;"><div class="v3-val">{val}</div><div class="v3-lbl" style="color:{current["color"]};">{lbl}</div></div>',unsafe_allow_html=True)
        st.write("")
    # ===== STREAK TRACKER =====
    st.markdown(f'<div class="v3-section">Streak Tracker</div>',unsafe_allow_html=True)

    all_results=main_stats.get('trade_results',[])
    all_r=df_main['R_Result'].dropna().tolist()
    all_dates=df_main.dropna(subset=['R_Result','Date'])['Date'].tolist()

    # Find all streaks
    def find_all_streaks(results, dates, r_vals):
        streaks=[]
        if not results: return streaks
        cur_type=results[0]; cur_start=0; cur_r=r_vals[0]
        for i in range(1,len(results)):
            if results[i]==results[i-1]:
                cur_r+=r_vals[i]
            else:
                length=i-cur_start
                if cur_type in ['W','L']:
                    streaks.append({
                        'type':cur_type,'length':length,
                        'start_date':dates[cur_start],'end_date':dates[i-1],
                        'total_r':round(cur_r,2)
                    })
                cur_type=results[i]; cur_start=i; cur_r=r_vals[i]
        # last streak
        length=len(results)-cur_start
        if cur_type in ['W','L']:
            streaks.append({
                'type':cur_type,'length':length,
                'start_date':dates[cur_start],'end_date':dates[-1],
                'total_r':round(cur_r,2)
            })
        return streaks

    if all_results and all_dates:
        streaks=find_all_streaks(all_results,all_dates,all_r)
        win_streaks=sorted([s for s in streaks if s['type']=='W'],key=lambda x:x['length'],reverse=True)
        loss_streaks=sorted([s for s in streaks if s['type']=='L'],key=lambda x:x['length'],reverse=True)
        best_win=win_streaks[0] if win_streaks else None
        worst_loss=loss_streaks[0] if loss_streaks else None
        cur=main_stats.get('cur_streak',0); cur_type_s=main_stats.get('cur_streak_type','—')
        cur_color_s='#4ade80' if cur_type_s=='W' else ('#f87171' if cur_type_s=='L' else ACCENT)
        cur_label_s='Win Streak' if cur_type_s=='W' else ('Loss Streak' if cur_type_s=='L' else 'Streak')

        # Streak bar chart
        if all_results:
            bar_html='<div style="display:flex;gap:3px;align-items:flex-end;height:80px;margin-bottom:16px;overflow:hidden;">'
            max_len=max((s['length'] for s in streaks),default=1)
            for s in streaks[-30:]:
                color='rgba(74,222,128,0.7)' if s['type']=='W' else 'rgba(248,113,113,0.7)'
                height=max(8,round((s['length']/max_len)*76))
                bar_html+=f'<div style="flex:1;min-width:6px;height:{height}px;background:{color};border-radius:3px 3px 0 0;"></div>'
            bar_html+='</div>'
            st.markdown(f'<div class="v3-panel" style="padding:16px 20px;">'
                f'<div style="font-size:0.6em;color:{TEXT3};text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">Streak History</div>'
                f'{bar_html}</div>',unsafe_allow_html=True)
            
    else:
        st.markdown(f'<div style="color:{TEXT2};font-size:0.85em;padding:12px 0;">Not enough data yet.</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="v3-section">Recent Trades</div>',unsafe_allow_html=True)
    tr=main_stats.get('trade_results',[])
    streak_html=f'<div id="streak-container" style="display:flex;gap:3px;overflow-x:auto;padding-bottom:6px;scrollbar-width:none;margin-bottom:10px;">'
    for i,r in enumerate(tr):
        is_last=i==len(tr)-1
        bg='rgba(74,222,128,0.85)' if r=='W' else ('rgba(248,113,113,0.75)' if r=='L' else f'rgba({RGB},0.3)')
        tc='#000' if r=='W' else '#fff'
        cls='streak-box active' if is_last else 'streak-box'
        streak_html+=f'<div class="{cls}" style="background:{bg};color:{tc};animation-delay:{i*25}ms;animation-play-state:paused;flex-shrink:0;">{r}</div>'
    streak_html+=f'<div class="streak-box" style="background:{BG2};color:{TEXT3};border:1px dashed {BORDER2};flex-shrink:0;animation-play-state:paused;">?</div></div>'
    streak_html+=f'<div style="font-size:0.75em;color:{TEXT2};">Current streak: <span style="color:{cur_color};font-weight:600;">{cur} {cur_type}</span></div>'
    st.markdown(f'<div class="v3-panel">{streak_html}</div>',unsafe_allow_html=True)
    components.html(f"""
<script>
setTimeout(function(){{
    var container=window.parent.document.getElementById('streak-container');
    if(!container)return;
    var obs=new IntersectionObserver(function(entries){{
        entries.forEach(function(e){{
            if(e.isIntersecting){{
                var boxes=container.querySelectorAll('.streak-box');
                boxes.forEach(function(b){{b.style.animationPlayState='running';}});
                obs.unobserve(e.target);
            }}
        }});
    }},{{threshold:0.2}});
    obs.observe(container);
}},200);
</script>
    """,height=0)
    st.markdown(f'<div class="v3-section">Month vs Month</div>',unsafe_allow_html=True)
    months=sorted(monthly_r.keys())[-4:]
    if months:
        mcols=st.columns(len(months))
        for i,(col,m) in enumerate(zip(mcols,months)):
            d=monthly_r[m]; sign='+' if d['total_r']>0 else ''; is_cur=m==this_month_key
            current_badge=f'<div style="color:{ACCENT_SOFT};font-size:0.58em;margin-top:3px;">Current</div>' if is_cur else ''
            col.markdown(
                f'<div style="background:{"rgba("+RGB+",0.08)" if is_cur else BG2};border-radius:12px;padding:14px;text-align:center;{"border:1px solid rgba("+RGB+",0.2);" if is_cur else ""}animation:staggerIn 0.5s cubic-bezier(0.16,1,0.3,1) {i*60}ms both;">'
                f'<div style="color:{ACCENT_SOFT if is_cur else TEXT2};font-size:0.6em;margin-bottom:6px;text-transform:uppercase;">{m}</div>'
                f'<div style="color:{TEXT};font-size:1.15em;font-weight:700;">{sign}{d["total_r"]}R</div>'
                f'<div style="color:{TEXT2};font-size:0.6em;margin-top:4px;">{d["win_rate"]}% · {d["trades"]}t</div>'
                f'{current_badge}</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="v3-section">3SL Window</div>',unsafe_allow_html=True)
    rows_html=""
    for i,s in enumerate(session_stats):
        bar_pct=round(abs(s['exp'])/max_abs_exp*100,1)
        bar_color=f'linear-gradient(90deg,rgba({RGB},0.4),{ACCENT})' if s['exp']>=0 else 'linear-gradient(90deg,rgba(248,113,113,0.4),#f87171)'
        delay=i*300
        rows_html+=(f'<div style="display:grid;grid-template-columns:90px 1fr 60px 55px 35px;gap:14px;align-items:center;padding:10px 0;border-bottom:1px solid {BORDER};">'
            f'<span style="color:{TEXT};font-size:0.82em;font-weight:500;">{s["session"]}</span>'
            f'<div style="background:{BG3};border-radius:4px;height:6px;overflow:hidden;"><div style="width:{bar_pct}%;height:6px;overflow:hidden;border-radius:4px;"><div class="grow-bar" style="width:100%;height:6px;background:{bar_color};border-radius:4px;animation:growBar 1.2s cubic-bezier(0.16,1,0.3,1) {delay}ms both;animation-play-state:paused;"></div></div></div>'
            f'<span style="color:{TEXT};font-size:0.8em;font-weight:600;">{s["exp"]}R</span>'
            f'<span style="color:{TEXT2};font-size:0.8em;">{s["wr"]}</span>'
            f'<span style="color:{TEXT3};font-size:0.78em;">{s["n"]}</span>'
            f'</div>')
    st.markdown(
        f'<div class="v3-panel"><div style="display:grid;grid-template-columns:90px 1fr 60px 55px 35px;gap:14px;padding-bottom:8px;margin-bottom:2px;">'
        f'<span style="color:{TEXT3};font-size:0.62em;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Session</span>'
        f'<span style="color:{TEXT3};font-size:0.62em;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Chart</span>'
        f'<span style="color:{TEXT3};font-size:0.62em;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Exp</span>'
        f'<span style="color:{TEXT3};font-size:0.62em;font-weight:600;text-transform:uppercase;letter-spacing:1px;">WR</span>'
        f'<span style="color:{TEXT3};font-size:0.62em;font-weight:600;text-transform:uppercase;letter-spacing:1px;">N</span>'
        f'</div>{rows_html}</div>',unsafe_allow_html=True)

# ============ P&L TRACKER ============
elif page=='P&L Tracker':
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:20px;">P&L Tracker</div>',unsafe_allow_html=True)
    _,num_col,_=st.columns([2,1,2])
    with num_col:
        st.markdown(f'<div style="font-size:0.7em;color:{TEXT2};text-align:center;margin-bottom:6px;">Number of Accounts</div>',unsafe_allow_html=True)
        acol1,acol2,acol3=st.columns([1,1,1])
        with acol1:
            if st.button("−",key="acc_down",use_container_width=True):
                if st.session_state.num_accounts>1: st.session_state.num_accounts-=1; st.rerun()
        with acol2:
            st.markdown(f'<div style="text-align:center;font-size:1.4em;font-weight:700;color:{TEXT};padding:6px 0;">{st.session_state.num_accounts}</div>',unsafe_allow_html=True)
        with acol3:
            if st.button("+",key="acc_up",use_container_width=True):
                if st.session_state.num_accounts<50: st.session_state.num_accounts+=1; st.rerun()
        num_accounts=st.session_state.num_accounts
    total_capital=ACCOUNT_SIZE*num_accounts
    if len(df_funded)>0 and 'R_Result' in df_funded.columns:
        df_fc=df_funded.dropna(subset=['R_Result','Date']).copy().sort_values('Date').reset_index(drop=True)
        if 'Risk Management' in df_fc.columns:
            avg_risk_pct=pd.to_numeric(df_fc['Risk Management'].str.replace('%','').str.strip(),errors='coerce').mean()
            if pd.isna(avg_risk_pct): avg_risk_pct=1.0
        else: avg_risk_pct=1.0
        def calc_pnl(df_sub):
            if 'Risk Management' in df_sub.columns:
                rp=pd.to_numeric(df_sub['Risk Management'].str.replace('%','').str.strip(),errors='coerce').fillna(avg_risk_pct)
                return round((df_sub['R_Result'].values*rp.values/100*ACCOUNT_SIZE*num_accounts).sum(),2)
            return round(df_sub['R_Result'].sum()*avg_risk_pct/100*ACCOUNT_SIZE*num_accounts,2)
        month_funded=df_fc[(df_fc['Date'].dt.month==today.month)&(df_fc['Date'].dt.year==today.year)]
        month_pnl=calc_pnl(month_funded); month_pct=round(month_pnl/total_capital*100,2); month_r=round(month_funded['R_Result'].sum(),2)
        week_start=today-pd.Timedelta(days=today.weekday())
        week_funded=df_fc[df_fc['Date'].dt.date>=week_start.date()]
        week_pnl=calc_pnl(week_funded); week_pct=round(week_pnl/total_capital*100,2); week_r=round(week_funded['R_Result'].sum(),2)
        today_funded=df_fc[df_fc['Date'].dt.date==today.date()]
        today_pnl=calc_pnl(today_funded); today_pct=round(today_pnl/total_capital*100,2); today_r=round(today_funded['R_Result'].sum(),2)
        total_pnl=calc_pnl(df_fc); total_r=round(df_fc['R_Result'].sum(),2)
        def fmt(v): return f"+${v:,.2f}" if v>=0 else f"-${abs(v):,.2f}"
        def fmtp(v): return f"+{v}%" if v>=0 else f"{v}%"
        def pc(v): return '#4ade80' if v>=0 else '#f87171'
        st.markdown(f'<div class="v3-section">Performance</div>',unsafe_allow_html=True)
        pcols=st.columns(3)
        for i,(col,(period,pnl,pct,rv,nt)) in enumerate(zip(pcols,[('This Month',month_pnl,month_pct,f"{month_r}R",len(month_funded)),('This Week',week_pnl,week_pct,f"{week_r}R",len(week_funded)),('Today',today_pnl,today_pct,f"{today_r}R",len(today_funded))])):
            c=pc(pnl)
            col.markdown(f'<div class="v3-card" style="animation-delay:{i*60}ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">{period}</div><div style="font-size:1.5em;font-weight:700;color:{c};" id="pnl-{i}">{fmt(pnl)}</div><div style="font-size:0.9em;font-weight:600;color:{c};margin-top:3px;" id="pct-{i}">{fmtp(pct)}</div><div style="font-size:0.6em;color:{TEXT2};margin-top:10px;padding-top:10px;border-top:1px solid {BORDER};">{rv} · {nt} trades</div></div>',unsafe_allow_html=True)
        components.html(f"""
<script>
function cm(id,t,dur){{var el=window.parent.document.getElementById(id);if(!el)return;var t0=null,pfx=t>=0?'+$':'-$',at=Math.abs(t);function s(ts){{if(!t0)t0=ts;var p=Math.min((ts-t0)/dur,1),e=1-Math.pow(1-p,3);el.textContent=pfx+(at*e).toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});if(p<1)requestAnimationFrame(s);}}requestAnimationFrame(s);}}
function cp(id,t,dur){{var el=window.parent.document.getElementById(id);if(!el)return;var t0=null,pfx=t>=0?'+':'-',at=Math.abs(t);function s(ts){{if(!t0)t0=ts;var p=Math.min((ts-t0)/dur,1),e=1-Math.pow(1-p,3);el.textContent=pfx+(at*e).toFixed(2)+'%';if(p<1)requestAnimationFrame(s);}}requestAnimationFrame(s);}}
setTimeout(function(){{cm('pnl-0',{month_pnl},900);cm('pnl-1',{week_pnl},900);cm('pnl-2',{today_pnl},900);cp('pct-0',{month_pct},900);cp('pct-1',{week_pct},900);cp('pct-2',{today_pct},900);}},200);
</script>
        """,height=0)
        st.markdown(f'<div class="v3-section">All Time · Funded</div>',unsafe_allow_html=True)
        at_cols=st.columns(3); sign_t='+' if total_pnl>=0 else ''
        at_cols[0].markdown(f'<div class="v3-card" style="animation-delay:0ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total P&L</div><div style="font-size:1.3em;font-weight:700;color:{pc(total_pnl)};">{fmt(total_pnl)}</div><div style="font-size:0.72em;color:{pc(total_pnl)};margin-top:3px;">{sign_t}{round(total_pnl/total_capital*100,2)}%</div></div>',unsafe_allow_html=True)
        at_cols[1].markdown(f'<div class="v3-card" style="animation-delay:60ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total R</div><div style="font-size:1.3em;font-weight:700;color:{TEXT};">{sign_t}{total_r}R</div></div>',unsafe_allow_html=True)
        at_cols[2].markdown(f'<div class="v3-card" style="animation-delay:120ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total Capital</div><div style="font-size:1.3em;font-weight:700;color:{ACCENT_SOFT};">${total_capital:,}</div></div>',unsafe_allow_html=True)
        st.markdown(f'<div class="v3-section">Goals</div>',unsafe_allow_html=True)
        goal_pnl_target=10000; goal_wr=60
        funded_stats=calc_stats(df_fc); current_wr=funded_stats.get('win_rate',0)
        pnl_prog=min(round(max(total_pnl,0)/goal_pnl_target*100,1),100); wr_prog=min(round(current_wr/goal_wr*100,1),100)
        pnl_rem=round(max(goal_pnl_target-max(total_pnl,0),0),2)
        gcols=st.columns(2)
        gcols[0].markdown(f'<div class="v3-card" style="text-align:left;animation-delay:0ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">Monthly P&L Goal</div><div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:12px;"><span style="font-size:1.2em;font-weight:700;color:{TEXT};">${max(total_pnl,0):,.0f}</span><span style="font-size:0.72em;color:{TEXT2};">/ ${goal_pnl_target:,}</span></div><div style="background:{BG3};border-radius:4px;height:4px;overflow:hidden;margin-bottom:8px;"><div style="width:{pnl_prog}%;height:100%;background:{ACCENT};border-radius:4px;"></div></div><div style="font-size:0.62em;color:{TEXT2};">{pnl_prog}% · ${pnl_rem:,.0f} to go</div></div>',unsafe_allow_html=True)
        gcols[1].markdown(f'<div class="v3-card" style="text-align:left;animation-delay:60ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">Win Rate Goal</div><div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:12px;"><span style="font-size:1.2em;font-weight:700;color:{TEXT};">{current_wr}%</span><span style="font-size:0.72em;color:{TEXT2};">/ {goal_wr}%</span></div><div style="background:{BG3};border-radius:4px;height:4px;overflow:hidden;margin-bottom:8px;"><div style="width:{wr_prog}%;height:100%;background:{ACCENT};border-radius:4px;"></div></div><div style="font-size:0.62em;color:{TEXT2};">{wr_prog}% there</div></div>',unsafe_allow_html=True)
        pnl_dash=round(239-(pnl_prog/100)*239); wr_dash=round(239-(wr_prog/100)*239)
        st.markdown(
            f'<div class="v3-panel" style="display:flex;justify-content:space-around;align-items:center;padding:24px;margin-top:16px;">'
            f'<div style="text-align:center;"><div style="position:relative;width:88px;height:88px;margin:0 auto;"><svg viewBox="0 0 100 100" style="width:88px;height:88px;transform:rotate(-90deg);"><circle cx="50" cy="50" r="38" fill="none" stroke="{BG3}" stroke-width="8"/><circle cx="50" cy="50" r="38" fill="none" stroke="{ACCENT}" stroke-width="8" stroke-dasharray="239" stroke-dashoffset="{pnl_dash}" stroke-linecap="round"/></svg><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:0.82em;font-weight:700;color:{TEXT};">{pnl_prog}%</div></div><div style="font-size:0.7em;font-weight:600;color:{TEXT};margin-top:8px;">${max(total_pnl,0):,.0f}</div><div style="font-size:0.58em;color:{TEXT2};">of ${goal_pnl_target:,}</div></div>'
            f'<div style="text-align:center;"><div style="position:relative;width:88px;height:88px;margin:0 auto;"><svg viewBox="0 0 100 100" style="width:88px;height:88px;transform:rotate(-90deg);"><circle cx="50" cy="50" r="38" fill="none" stroke="{BG3}" stroke-width="8"/><circle cx="50" cy="50" r="38" fill="none" stroke="{ACCENT}" stroke-width="8" stroke-dasharray="239" stroke-dashoffset="{wr_dash}" stroke-linecap="round"/></svg><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:0.82em;font-weight:700;color:{TEXT};">{wr_prog}%</div></div><div style="font-size:0.7em;font-weight:600;color:{TEXT};margin-top:8px;">{current_wr}%</div><div style="font-size:0.58em;color:{TEXT2};">WR goal</div></div>'
            f'</div>',unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="v3-panel" style="text-align:center;padding:48px;"><div style="color:{TEXT2};">No trades yet</div></div>',unsafe_allow_html=True)

# ============ CHARTS ============
elif page=='Charts':
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:24px;">Charts</div>',unsafe_allow_html=True)
    xau_eq=xau_stats.get('equity_curve',[]); nas_eq=nas_stats.get('equity_curve',[])
    sw,sh=800,200; xl,xf=make_curve(xau_eq,sw,sh); nl,nf=make_curve(nas_eq,sw,sh)
    xfp=f'<path d="{xf}" fill="url(#xFill)" opacity="0.3"/>' if xf else ''
    xlp=f'<path d="{xl}" fill="none" stroke="{GOLD}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2.5s" begin="0s" fill="freeze"/></path>' if xl else ''
    nlp=f'<path d="{nl}" fill="none" stroke="{PURPLE_C}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2.5s" begin="0.3s" fill="freeze"/></path>' if nl else ''
    svg=f'<svg viewBox="0 0 {sw} {sh}" style="width:100%;height:260px;display:block;"><defs><linearGradient id="xFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba(245,158,11,0.2)"/><stop offset="100%" stop-color="rgba(245,158,11,0)"/></linearGradient></defs>{xfp}{xlp}{nlp}</svg>'
    st.markdown(f'<div class="v3-panel"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><div style="font-size:0.95em;font-weight:600;color:{TEXT};">Equity Curve</div><div style="display:flex;gap:16px;"><div style="display:flex;align-items:center;gap:6px;"><div style="width:20px;height:2px;background:{GOLD};border-radius:2px;"></div><span style="font-size:0.72em;color:{TEXT2};">XAUUSD</span></div><div style="display:flex;align-items:center;gap:6px;"><div style="width:20px;height:2px;background:{PURPLE_C};border-radius:2px;"></div><span style="font-size:0.72em;color:{TEXT2};">NASDAQ</span></div></div></div>{svg}</div>',unsafe_allow_html=True)
    rolling=main_stats.get('rolling_wr',[])
    if rolling:
        rw,rh=800,100; n=len(rolling)
        pts=[((i/(n-1))*rw if n>1 else 0,rh-((v/100)*(rh-16))-8) for i,v in enumerate(rolling)]
        rl=catmull(pts); rf=rl+f"L{rw},{rh} L0,{rh} Z" if rl else ""; by=rh-(0.5*(rh-16))-8
        trending=rolling[-1]>rolling[0] if len(rolling)>1 else False
        tc='#4ade80' if trending else '#f87171'; tt='Trending up ↑' if trending else 'Trending down ↓'
        rsvg=(f'<svg viewBox="0 0 {rw} {rh}" style="width:100%;height:100px;display:block;"><defs><linearGradient id="rFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba({RGB},0.15)"/><stop offset="100%" stop-color="rgba({RGB},0)"/></linearGradient></defs><line x1="0" y1="{by:.1f}" x2="{rw}" y2="{by:.1f}" stroke="{BORDER2}" stroke-width="1" stroke-dasharray="4,4"/>'+(f'<path d="{rf}" fill="url(#rFill)"/>' if rf else '')+(f'<path d="{rl}" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2s" begin="0s" fill="freeze"/></path>' if rl else '')+'</svg>')
        st.markdown(f'<div class="v3-panel"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;"><div><div style="font-size:0.95em;font-weight:600;color:{TEXT};">Rolling Win Rate</div><div style="font-size:0.68em;color:{TEXT2};margin-top:2px;">Last 10 trades window</div></div><div style="font-size:0.7em;color:{tc};font-weight:500;">{tt}</div></div>{rsvg}</div>',unsafe_allow_html=True)
    donut_configs=[('Overall',main_stats.get('wins',0),main_stats.get('losses',0),main_stats.get('breakevens',0),[ACCENT,f'{ACCENT}88',f'{ACCENT}33'],f'rgba({RGB},0.3)',ACCENT_SOFT),('XAUUSD',xau_stats.get('wins',0),xau_stats.get('losses',0),xau_stats.get('breakevens',0),['#b45309','#f59e0b','#fde68a33'],'rgba(245,158,11,0.3)',GOLD_S),('NASDAQ',nas_stats.get('wins',0),nas_stats.get('losses',0),nas_stats.get('breakevens',0),['#6d28d9','#a78bfa','#ede9fe33'],'rgba(167,139,250,0.3)',PURPLE_S)]
    dcols=st.columns(3)
    for col,(lbl,w,l,b,colors,glow,tc) in zip(dcols,donut_configs):
        svg,legend=build_donut(w,l,b,colors,glow)
        col.markdown(f'<div class="v3-panel"><div style="font-size:0.85em;font-weight:600;color:{tc};margin-bottom:14px;">{lbl}</div><div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;"><div>{svg}</div><div style="flex:1;min-width:90px;">{legend}</div></div></div>',unsafe_allow_html=True)

# ============ CALENDAR ============
elif page=='Calendar':
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:24px;">Calendar</div>',unsafe_allow_html=True)
    cm=st.session_state.cal_month; cy=st.session_state.cal_year
    mt_r=sum(v['total_r'] for k,v in daily_r.items() if k.month==cm and k.year==cy)
    ms2='+' if mt_r>0 else ''; mn=datetime(cy,cm,1).strftime("%B %Y")
    nl2,nr=st.columns([7,2])
    nl2.markdown(f'<div style="background:{BG2};border-radius:14px;height:40px;display:flex;align-items:center;padding:0 18px;margin-bottom:14px;"><span style="font-size:1em;font-weight:700;color:{TEXT};">{mn}</span><span style="font-size:0.72em;color:{ACCENT};font-weight:600;margin-left:10px;">{ms2}{round(mt_r,2)}R</span></div>',unsafe_allow_html=True)
    with nr:
        st.markdown('<div class="cal-arrows">',unsafe_allow_html=True)
        al,ar2=st.columns(2)
        with al:
            if st.button("‹",key="prev_m",use_container_width=True):
                if st.session_state.cal_month==1: st.session_state.cal_month=12; st.session_state.cal_year-=1
                else: st.session_state.cal_month-=1
                st.rerun()
        with ar2:
            if st.button("›",key="next_m",use_container_width=True):
                if st.session_state.cal_month==12: st.session_state.cal_month=1; st.session_state.cal_year+=1
                else: st.session_state.cal_month+=1
                st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)
    st.write("")
    cal_module.setfirstweekday(cal_module.MONDAY); mm=cal_module.monthcalendar(cy,cm)
    dhc=st.columns(8)
    for i,d in enumerate(['Mo','Tu','We','Th','Fr','Sa','Su']): dhc[i].markdown(f'<div class="cal-header">{d}</div>',unsafe_allow_html=True)
    dhc[7].markdown(f'<div class="cal-header">Wk</div>',unsafe_allow_html=True)
    for wn,week in enumerate(mm):
        if wn>0: st.write("")
        wc=st.columns(8); wt=wtr=0
        for i,dn in enumerate(week):
            if dn==0: wc[i].markdown('<div style="min-height:72px;"></div>',unsafe_allow_html=True)
            else:
                dd=datetime(cy,cm,dn).date(); dd_data=daily_r.get(dd)
                if dd_data:
                    wt+=dd_data['total_r']; wtr+=dd_data['trades']; rv=dd_data['total_r']; sg='+' if rv>0 else ''
                    if rv>=0: ds="background:rgba(74,222,128,0.06);border:1px solid rgba(74,222,128,0.15);"; rc='#4ade80' if IS_DARK else '#16a34a'; nc='rgba(74,222,128,0.9)' if IS_DARK else '#14532d'
                    else: ds="background:rgba(248,113,113,0.06);border:1px solid rgba(248,113,113,0.15);"; rc='#f87171' if IS_DARK else '#dc2626'; nc='rgba(248,113,113,0.9)' if IS_DARK else '#7f1d1d'
                    delay=(wn*7+i)*30
                    wc[i].markdown(f'<div style="{ds}border-radius:10px;min-height:72px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:6px;text-align:center;animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) {delay}ms both;"><div style="color:{nc};font-size:0.7em;font-weight:600;">{dn}</div><div style="color:{rc};font-size:0.82em;font-weight:700;margin-top:3px;">{sg}{rv}R</div><div style="color:{TEXT2};font-size:0.58em;margin-top:2px;">{dd_data["trades"]}t</div></div>',unsafe_allow_html=True)
                else: wc[i].markdown(f'<div style="min-height:72px;display:flex;align-items:center;justify-content:center;"><div class="cal-day-num">{dn}</div></div>',unsafe_allow_html=True)
        ws='+' if wt>0 else ''
        wc[7].markdown(f'<div style="background:{BG2};border-radius:10px;min-height:72px;padding:8px 4px;text-align:center;animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) {wn*60}ms both;"><div style="color:{TEXT2};font-size:0.58em;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">W{wn+1}</div><div style="font-size:0.92em;font-weight:700;color:{TEXT};margin-top:8px;">{ws}{round(wt,2)}R</div><div style="color:{TEXT2};font-size:0.55em;margin-top:2px;">{wtr}t</div></div>',unsafe_allow_html=True)
    st.markdown(f'<hr class="v3-divider">',unsafe_allow_html=True)
    st.markdown(f'<div class="v3-section">Best Day of the Week</div>',unsafe_allow_html=True)
    if dow_stats:
        best_day=dow_stats[0]; bc='#4ade80' if best_day['exp']>=0 else '#f87171'; bs='+' if best_day['exp']>=0 else ''
        dow_cols=st.columns([1,2])
        with dow_cols[0]:
            st.markdown(f'<div class="v3-panel" style="text-align:center;padding:24px 16px;"><div style="font-size:0.58em;color:{TEXT2};text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Best Day</div><div style="font-size:1.5em;font-weight:800;color:{TEXT};margin-bottom:6px;">{best_day["day"]}</div><div style="font-size:0.95em;font-weight:700;color:{bc};">{bs}{best_day["exp"]}R avg</div><div style="font-size:0.62em;color:{TEXT2};margin-top:6px;">{best_day["wr"]}% WR · {best_day["n"]} trades</div></div>',unsafe_allow_html=True)
        with dow_cols[1]:
            rows=''
            for i,d in enumerate(dow_stats):
                c='#4ade80' if d['exp']>=0 else '#f87171'; s='+' if d['exp']>=0 else ''; rc=RANK_COLORS[i] if i<len(RANK_COLORS) else TEXT3
                rows+=(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid {BORDER};"><span style="color:{rc};font-size:0.68em;font-weight:700;min-width:20px;">#{i+1}</span><span style="color:{TEXT};font-size:0.82em;font-weight:500;flex:1;margin-left:8px;">{d["day"]}</span><span style="color:{c};font-size:0.82em;font-weight:700;min-width:46px;text-align:right;">{s}{d["exp"]}R</span><span style="color:{TEXT2};font-size:0.78em;min-width:38px;text-align:right;">{d["wr"]}%</span><span style="color:{TEXT3};font-size:0.72em;min-width:24px;text-align:right;">{d["n"]}t</span></div>')
            st.markdown(f'<div class="v3-panel">{rows}</div>',unsafe_allow_html=True)

# ============ EDGE ANALYSIS ============
elif page=='Edge Analysis':
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:20px;">Edge Analysis</div>',unsafe_allow_html=True)
    ea1,ea2=st.columns(2)
    with ea1:
        for col,title in [('Entry Model','Entry Model'),('Entry Model Timeframe','Entry Timeframe'),('Double Confirmation','Double Confirmation'),('Target','Target'),('Entry + Confirmation','Rejection Candle'),('News Proximity','News Proximity')]:
            render_breakdown(df_main,col,title)
    with ea2:
        for col,title in [('Entry Confluences','Entry Confluences'),('Stop Loss Logic','Stop Loss'),('Hour','Time of Day'),('Trade Quality Rating','Trade Quality'),('Emotional State Before...','Emotional State'),('Conditions MTF/HTF','Market Conditions')]:
            render_breakdown(df_main,col,title)
    st.markdown(f'<hr class="v3-divider">',unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin-bottom:14px;">Next Trade Checklist</div>',unsafe_allow_html=True)
    if green_checklist or red_checklist:
        cl1,cl2=st.columns(2)
        with cl1:
            st.markdown(f'<div style="font-size:0.62em;color:#4ade80;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">✓ Do more of this</div>',unsafe_allow_html=True)
            for i,item in enumerate(green_checklist):
                st.markdown(f'<div class="checklist-item" style="animation-delay:{i*40}ms;"><div style="width:6px;height:6px;border-radius:50%;background:#4ade80;margin-top:5px;flex-shrink:0;"></div><div><div style="color:{TEXT};font-size:0.85em;font-weight:500;">{item["label"]}</div><div style="color:{TEXT2};font-size:0.72em;margin-top:2px;">{item["detail"]}</div></div></div>',unsafe_allow_html=True)
        with cl2:
            st.markdown(f'<div style="font-size:0.62em;color:#f87171;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">✗ Avoid this</div>',unsafe_allow_html=True)
            for i,item in enumerate(red_checklist):
                st.markdown(f'<div class="checklist-item" style="animation-delay:{i*40}ms;"><div style="width:6px;height:6px;border-radius:50%;background:#f87171;margin-top:5px;flex-shrink:0;"></div><div><div style="color:{TEXT};font-size:0.85em;font-weight:500;">{item["label"]}</div><div style="color:{TEXT2};font-size:0.72em;margin-top:2px;">{item["detail"]}</div></div></div>',unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="color:{TEXT2};font-size:0.85em;">Not enough data yet.</div>',unsafe_allow_html=True)
    st.markdown(f'<hr class="v3-divider">',unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin-bottom:14px;">Consistency Score</div>',unsafe_allow_html=True)
    csc1,csc2=st.columns([1,2])
    with csc1:
        st.markdown(f'<div style="display:flex;align-items:center;justify-content:center;padding:16px 0;"><div style="position:relative;width:90px;height:90px;"><svg viewBox="0 0 100 100" style="width:90px;height:90px;transform:rotate(-90deg);"><circle cx="50" cy="50" r="38" fill="none" stroke="{BG3}" stroke-width="8"/><circle cx="50" cy="50" r="38" fill="none" stroke="{ACCENT}" stroke-width="8" stroke-dasharray="239" stroke-dashoffset="239"><animate attributeName="stroke-dashoffset" from="239" to="{round(239-(consistency_score/100)*239)}" dur="1s" begin="0.2s" fill="freeze"/></circle></svg><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:1.1em;font-weight:700;color:{TEXT};">{consistency_score}%</div></div></div>',unsafe_allow_html=True)
    with csc2:
        for i,(lbl,score) in enumerate(consistency_breakdown):
            c='#4ade80' if score>=70 else ('#f59e0b' if score>=50 else '#f87171')
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid {BORDER};animation:slideInLeft 0.4s cubic-bezier(0.16,1,0.3,1) {i*70}ms both;"><span style="color:{TEXT2};font-size:0.82em;">{lbl}</span><span style="color:{c};font-weight:600;font-size:0.82em;">{score}%</span></div>',unsafe_allow_html=True)

# ============ BEST SETUPS ============
elif page=='Best Setups':
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:20px;">Best Setups</div>',unsafe_allow_html=True)
    if best_setup:
        st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin-bottom:12px;">Top Setup Finder</div>',unsafe_allow_html=True)
        tags=''.join([f'<span style="background:rgba({RGB},0.1);border-radius:6px;padding:4px 10px;font-size:0.75em;color:{ACCENT};margin:3px;display:inline-block;animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) {i*50}ms both;">{b["label"]}</span>' for i,b in enumerate(best_setup['combos'])])
        oc='#4ade80' if best_setup['overall_wr']>=60 else ('#f59e0b' if best_setup['overall_wr']>=45 else '#f87171')
        st.markdown(f'<div class="v3-panel"><div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:18px;">{tags}</div><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;"><div style="text-align:center;"><div style="font-size:1.3em;font-weight:700;color:{oc};">{best_setup["overall_wr"]}%</div><div style="font-size:0.58em;color:{TEXT2};margin-top:3px;text-transform:uppercase;letter-spacing:0.5px;">Avg Win Rate</div></div><div style="text-align:center;"><div style="font-size:1.3em;font-weight:700;color:{TEXT};">+{best_setup["overall_exp"]}R</div><div style="font-size:0.58em;color:{TEXT2};margin-top:3px;text-transform:uppercase;letter-spacing:0.5px;">Avg Expectancy</div></div></div></div>',unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:24px 0 12px;">Best of Each Variable</div>',unsafe_allow_html=True)
    setup_cols=[('Entry Model','Entry Model'),('Entry Model Timeframe','Timeframe'),('3SL Window','3SL Window'),('Target','Target'),('Stop Loss Logic','Stop Loss'),('Entry + Confirmation','Rejection Candle'),('Double Confirmation','Double Confirmation'),('Hour','Time of Day'),('Trade Quality Rating','Trade Quality'),('Emotional State Before...','Emotional State'),('News Proximity','News Proximity'),('Conditions MTF/HTF','Market Conditions')]
    rows=''
    for i,(cn,lbl) in enumerate(setup_cols):
        best=get_best(df_main,cn)
        if not best: continue
        c='#4ade80' if best['exp']>=0 else '#f87171'; s='+' if best['exp']>=0 else ''
        rows+=(f'<div class="setup-row" style="animation-delay:{i*35}ms;"><span style="color:{TEXT2};font-size:0.68em;text-transform:uppercase;letter-spacing:0.5px;min-width:110px;">{lbl}</span><span style="color:{TEXT};font-size:0.85em;font-weight:500;flex:1;">{best["label"]}</span><span style="color:{c};font-size:0.82em;font-weight:700;min-width:46px;text-align:right;">{s}{best["exp"]}R</span><span style="color:{TEXT2};font-size:0.78em;min-width:36px;text-align:right;">{best["wr"]}%</span><span style="color:{TEXT3};font-size:0.72em;min-width:24px;text-align:right;">{best["n"]}t</span></div>')
    if rows:
        st.markdown(f'<div class="v3-panel"><div style="display:flex;gap:12px;padding-bottom:8px;margin-bottom:2px;border-bottom:1px solid {BORDER};"><span style="color:{TEXT3};font-size:0.6em;font-weight:600;text-transform:uppercase;min-width:110px;">Variable</span><span style="color:{TEXT3};font-size:0.6em;font-weight:600;text-transform:uppercase;flex:1;">Best</span><span style="color:{TEXT3};font-size:0.6em;font-weight:600;text-transform:uppercase;min-width:46px;text-align:right;">Avg R</span><span style="color:{TEXT3};font-size:0.6em;font-weight:600;text-transform:uppercase;min-width:36px;text-align:right;">WR</span><span style="color:{TEXT3};font-size:0.6em;font-weight:600;text-transform:uppercase;min-width:24px;text-align:right;">N</span></div>{rows}</div>',unsafe_allow_html=True)

# ============ COACH ============
elif page=='Coach':
    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:20px;">Coach</div>',unsafe_allow_html=True)
    num_accounts=st.session_state.num_accounts

    # Load persistent memory
    saved_profile,saved_character,saved_history=load_coach_memory()
    if saved_profile: st.session_state.coach_profile=saved_profile
    if saved_character: st.session_state.coach_character=saved_character
    if saved_history: st.session_state.coach_history=saved_history

    # ===== COACH HEADER =====
    st.markdown(
        f'<div style="background:{BG2};border-radius:16px;padding:18px 22px;margin-bottom:24px;display:flex;align-items:center;gap:16px;">'
        f'<div style="width:44px;height:44px;border-radius:50%;background:rgba({RGB},0.08);border:1px solid rgba({RGB},0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:1.2em;">⚡</div>'
        f'<div><div style="font-size:0.95em;font-weight:700;color:{TEXT};">Your AI Trading Coach</div>'
        f'<div style="font-size:0.7em;color:{TEXT2};margin-top:2px;">Brutally honest · Tracks your patterns · Gets smarter every week</div></div>'
        f'</div>',unsafe_allow_html=True)

    # ===== TRADER CHARACTER HERO =====
    character=st.session_state.coach_character
    if character and isinstance(character,dict):
        title=character.get('title','—'); tier=character.get('tier','B'); desc=character.get('desc','')
        stats=character.get('stats',{'patience':50,'discipline':50,'edge':50})
        patience=stats.get('patience',50); discipline=stats.get('discipline',50); edge=stats.get('edge',50)
        tier_colors={'S':'#fcd34d','A':'#a78bfa','B':'#60a5fa','C':'#4ade80','D':'#f59e0b','F':'#f87171'}
        tier_labels={'S':'S Tier · Elite','A':'A Tier · Disciplined','B':'B Tier · Developing','C':'C Tier · Potential','D':'D Tier · Struggling','F':'F Tier · Reset Required'}
        char_color=tier_colors.get(tier,'#94a3b8'); tier_label=tier_labels.get(tier,'Unknown')
        char_html=(
            "<!DOCTYPE html><html><head><style>"
            "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');"
            "@keyframes revealTitle{0%{opacity:0;letter-spacing:20px;transform:scale(0.88);}60%{opacity:1;letter-spacing:6px;transform:scale(1.04);}100%{opacity:1;letter-spacing:4px;transform:scale(1);}}"
            "@keyframes scanLine{from{top:0;opacity:0.8;}to{top:100%;opacity:0;}}"
            "@keyframes tierBadge{from{opacity:0;transform:scale(0.7);}to{opacity:1;transform:scale(1);}}"
            "@keyframes charFadeUp{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}"
            f"@keyframes charGlow{{0%,100%{{box-shadow:0 0 0 rgba(0,0,0,0);}}50%{{box-shadow:0 0 30px {char_color}33;}}}}"
            "body{margin:0;padding:0;background:transparent;font-family:'Inter',sans-serif;}"
            f".char-card{{position:relative;overflow:hidden;background:{'rgba(255,255,255,0.02)' if IS_DARK else 'rgba(0,0,0,0.03)'};border:1px solid {char_color}40;border-radius:20px;padding:32px 28px;text-align:center;animation:charGlow 3s ease-in-out infinite;}}"
            f".char-scan{{position:absolute;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,{char_color},transparent);animation:none;}}"
            f".char-tier-badge{{display:inline-flex;align-items:center;gap:6px;background:{'rgba(255,255,255,0.03)' if IS_DARK else 'rgba(0,0,0,0.04)'};border:1px solid {char_color}40;border-radius:6px;padding:4px 12px;font-size:0.55em;font-weight:700;color:{char_color};letter-spacing:2px;text-transform:uppercase;animation:tierBadge 0.6s cubic-bezier(0.16,1,0.3,1) 0.1s both;animation-play-state:paused;margin-bottom:16px;}}"
            f".char-title{{font-size:2.4em;font-weight:900;background:linear-gradient(135deg,{'#fff' if IS_DARK else '#111'} 30%,{char_color});-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px;text-transform:uppercase;animation:revealTitle 1.4s cubic-bezier(0.16,1,0.3,1) 0.3s both;animation-play-state:paused;}}"
            f".char-divider{{width:48px;height:2px;background:{char_color};margin:16px auto;opacity:0.4;animation:charFadeUp 0.5s ease 1.2s both;animation-play-state:paused;}}"
            f".char-desc{{font-size:0.82em;color:{'rgba(255,255,255,0.4)' if IS_DARK else 'rgba(0,0,0,0.5)'};font-style:italic;line-height:1.7;animation:charFadeUp 0.8s ease 1.3s both;animation-play-state:paused;max-width:340px;margin:0 auto;}}"
            f".char-stats{{display:flex;justify-content:center;gap:24px;margin-top:20px;animation:charFadeUp 0.6s ease 1.6s both;animation-play-state:paused;}}"
            f".char-stat{{text-align:center;}}.char-stat-label{{font-size:0.48em;color:{'rgba(255,255,255,0.2)' if IS_DARK else 'rgba(0,0,0,0.35)'};text-transform:uppercase;letter-spacing:1px;margin-bottom:5px;}}"
            f".char-stat-bar-bg{{width:64px;height:3px;background:{'rgba(255,255,255,0.06)' if IS_DARK else 'rgba(0,0,0,0.08)'};border-radius:2px;}}"
            f".char-stat-bar-fill{{height:3px;background:{char_color};border-radius:2px;}}"
            "</style></head><body><div class='char-card'><div class='char-scan'></div>"
            f"<div class='char-tier-badge'>&#x2B23; {tier_label}</div>"
            f"<div class='char-title'>{title}</div><div class='char-divider'></div>"
            f"<div class='char-desc'>{desc}</div><div class='char-stats'>"
            f"<div class='char-stat'><div class='char-stat-label'>Patience</div><div class='char-stat-bar-bg'><div class='char-stat-bar-fill' style='width:{patience}%;'></div></div></div>"
            f"<div class='char-stat'><div class='char-stat-label'>Discipline</div><div class='char-stat-bar-bg'><div class='char-stat-bar-fill' style='width:{discipline}%;'></div></div></div>"
            f"<div class='char-stat'><div class='char-stat-label'>Edge</div><div class='char-stat-bar-bg'><div class='char-stat-bar-fill' style='width:{edge}%;'></div></div></div>"
            "</div></div><script>setTimeout(function(){var card=document.querySelector('.char-card');if(!card)return;"
            "var obs=new IntersectionObserver(function(entries){entries.forEach(function(e){if(e.isIntersecting){"
            "var scan=card.querySelector('.char-scan');if(scan)scan.style.animation='scanLine 1.5s ease 0.2s forwards';"
            "var animated=card.querySelectorAll('.char-tier-badge,.char-title,.char-divider,.char-desc,.char-stats');"
            "animated.forEach(function(el){el.style.animationPlayState='running';});obs.unobserve(e.target);}});},{threshold:0.3});"
            "obs.observe(card);},300);</script></body></html>"
        )
        components.html(char_html,height=280)

        # Tier rankings + profile side by side
        tc1,tc2=st.columns(2)
        with tc1:
            with st.expander("Tier Rankings"):
                tier_data=[
                    ('S','#fcd34d','Elite · Rare unlock',['The Phantom','The Oracle','The Legend']),
                    ('A','#a78bfa','Disciplined · Precise',['The Sniper','The Ghost','The Assassin','The Architect']),
                    ('B','#60a5fa','Developing · Solid',['The Maverick','The Commander','The Grinder','The Titan']),
                    ('C','#4ade80','Potential · Inconsistent',['The Prodigy','The Survivor']),
                    ('D','#f59e0b','Struggling',['The Wild Card','The Apprentice','The Berserker']),
                    ('F','#f87171','Reset required',['The Warmonger']),
                ]
                st.markdown(f'<div style="background:{BG3};border-radius:10px;padding:8px 12px;">',unsafe_allow_html=True)
                for t_tier,t_color,t_desc,t_names in tier_data:
                    is_active=t_tier==tier
                    names_html=''
                    for n in t_names:
                        if n==title: names_html+=f'<span style="color:{t_color};font-weight:700;">{n}</span>'
                        else: names_html+=f'<span style="color:{"rgba(255,255,255,0.3)" if IS_DARK else "rgba(0,0,0,0.5)"};">{n}</span>'
                        names_html+=' · '
                    names_html=names_html.rstrip(' · ')
                    you_badge=f'<span style="font-size:0.5em;color:{t_color};font-weight:700;background:rgba(255,255,255,0.06);border-radius:4px;padding:2px 6px;margin-left:8px;">You</span>' if is_active else ''
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid {BORDER};{"background:rgba(255,255,255,0.02);border-radius:6px;padding:8px;" if (is_active and IS_DARK) else ("background:rgba(0,0,0,0.04);border-radius:6px;padding:8px;" if is_active else "")}">'
                        f'<div style="width:3px;height:20px;border-radius:2px;background:{t_color};flex-shrink:0;"></div>'
                        f'<div style="font-size:0.72em;font-weight:800;color:{t_color};min-width:16px;">{t_tier}</div>'
                        f'<div style="font-size:0.58em;flex:1;">{names_html}</div>'
                        f'{you_badge}</div>',unsafe_allow_html=True)
                st.markdown('</div>',unsafe_allow_html=True)
        with tc2:
            profile=st.session_state.coach_profile
            if profile:
                with st.expander("Your Trader Profile"):
                    st.markdown(f'<div style="font-size:0.82em;color:{TEXT};line-height:1.85;">{profile}</div>',unsafe_allow_html=True)

    # ===== DATE RANGES =====
    st.markdown(f'<hr class="v3-divider">',unsafe_allow_html=True)
    today_date=today.date()
    days_since_sunday=(today_date.weekday()+1)%7
    last_sunday_date=today_date-pd.Timedelta(days=days_since_sunday)
    last_monday_date=last_sunday_date-pd.Timedelta(days=6)
    week_start=today_date-pd.Timedelta(days=today_date.weekday())

    df_lw=df_main.dropna(subset=['Date','R_Result']).copy()
    df_lw=df_lw[(df_lw['Date'].dt.date>=last_monday_date)&(df_lw['Date'].dt.date<=last_sunday_date)]
    df_tw=df_main.dropna(subset=['Date','R_Result']).copy()
    df_tw=df_tw[df_tw['Date'].dt.date>=week_start]

    total_v=len(df_lw)
    wins_v=int((df_lw['R_Result']>0).sum()) if total_v>0 else 0
    losses_v=int((df_lw['R_Result']<0).sum()) if total_v>0 else 0
    wr_v=round(wins_v/(wins_v+losses_v)*100,1) if (wins_v+losses_v)>0 else 0
    avg_rr_v=round(df_lw['R_Result'].mean(),2) if total_v>0 else 0

    # ===== ACTIONS ROW =====
    st.markdown(f'<div class="v3-section">This Week</div>',unsafe_allow_html=True)
    btn_col1,btn_col2,_=st.columns([1,1,2])
    with btn_col1:
        run_btn=st.button("⚡  Run Weekly Debrief",key="run_debrief",use_container_width=True)
    with btn_col2:
        if len(df_tw)>0:
            midweek_btn=st.button("💬  Mid-Week Check-in",key="midweek_btn",use_container_width=True)
        else:
            midweek_btn=False

    if run_btn:
        if total_v==0:
            st.markdown(f'<div style="background:{BG2};border-radius:14px;padding:20px;color:{TEXT2};font-size:0.88em;margin-top:12px;">No trades found for last week ({last_monday_date.strftime("%b %d")} – {last_sunday_date.strftime("%b %d")}). Log some trades and come back!</div>',unsafe_allow_html=True)
        elif not ANTHROPIC_API_KEY:
            st.error("Add your ANTHROPIC_API_KEY to Streamlit secrets.")
        else:
            with st.spinner("Coach is reviewing your week..."):
                try:
                    result=call_coach_api(df_lw,st.session_state.coach_profile,num_accounts,df_main)
                    if result:
                        st.session_state.coach_debrief=result
                        if result.get('updated_profile'): st.session_state.coach_profile=result['updated_profile']
                        if result.get('trader_character'): st.session_state.coach_character=result['trader_character']
                        week_label=f"{last_monday_date.strftime('%b %d')} – {last_sunday_date.strftime('%b %d %Y')}"
                        save_coach_memory(st.session_state.coach_profile,st.session_state.coach_character,result,week_label)
                        st.rerun()
                    else:
                        st.markdown(f'<div style="background:rgba(167,139,250,0.04);border:1px solid rgba(167,139,250,0.15);border-radius:14px;padding:20px;text-align:center;margin-top:12px;"><div style="font-size:1.2em;margin-bottom:8px;">⚡</div><div style="font-size:0.88em;font-weight:600;color:rgba(167,139,250,0.9);margin-bottom:6px;">Coach is unavailable right now</div><div style="font-size:0.7em;color:{TEXT2};">Check your ANTHROPIC_API_KEY in Streamlit secrets.</div></div>',unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div style="background:rgba(248,113,113,0.04);border:1px solid rgba(248,113,113,0.15);border-radius:14px;padding:20px;text-align:center;margin-top:12px;"><div style="font-size:0.88em;font-weight:600;color:#f87171;margin-bottom:6px;">Something went wrong</div><div style="font-size:0.7em;color:{TEXT2};">{str(e)}</div></div>',unsafe_allow_html=True)

    if midweek_btn:
        if not ANTHROPIC_API_KEY:
            st.error("Add your ANTHROPIC_API_KEY to Streamlit secrets.")
        else:
            with st.spinner("Coach is checking in..."):
                try:
                    result=call_midweek_api(df_tw,st.session_state.coach_profile,num_accounts)
                    if result: st.session_state.midweek_checkin=result; st.rerun()
                except Exception as e:
                    st.markdown(f'<div style="background:rgba(248,113,113,0.04);border:1px solid rgba(248,113,113,0.15);border-radius:14px;padding:16px;margin-top:12px;"><div style="font-size:0.85em;color:#f87171;">Coach unavailable — try again in a moment.</div></div>',unsafe_allow_html=True)

    if st.session_state.get('midweek_checkin'):
        mc=st.session_state.midweek_checkin
        st.markdown(
            f'<div style="background:{BG2};border-radius:14px;padding:20px;border-left:3px solid {ACCENT};margin-top:12px;">'
            f'<div style="font-size:0.58em;color:{TEXT2};font-weight:600;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Coach · Mid-Week · {len(df_tw)} trades so far</div>'
            f'<div style="font-size:0.88em;color:{TEXT};line-height:1.8;">{mc.get("checkin","")}</div>'
            f'<div style="margin-top:12px;padding-top:12px;border-top:1px solid {BORDER};font-size:0.82em;color:{ACCENT};">→ {mc.get("focus","")}</div>'
            f'</div>',unsafe_allow_html=True)

    # ===== DEBRIEF RESULTS =====
    cached=st.session_state.coach_debrief
    if cached:
        grade=cached.get('grade','—'); grade_reason=cached.get('grade_reason','')
        grade_color='#4ade80' if grade in ['A+','A'] else ('#fcd34d' if grade in ['B+','B'] else ('#f59e0b' if grade in ['C+','C'] else '#f87171'))
        st.markdown(f'<div class="v3-section">Last Debrief · {last_monday_date.strftime("%b %d")} – {last_sunday_date.strftime("%b %d")}</div>',unsafe_allow_html=True)
        st.markdown(
            f'<div style="background:{BG2};border-radius:16px;padding:20px 24px;margin-bottom:14px;display:flex;align-items:center;gap:16px;">'
            f'<div style="font-size:2em;font-weight:800;color:{grade_color};min-width:52px;">{grade}</div>'
            f'<div style="width:1px;height:36px;background:{BORDER};"></div>'
            f'<div style="font-size:0.85em;color:{TEXT2};font-style:italic;line-height:1.5;">{grade_reason}</div>'
            f'</div>',unsafe_allow_html=True)
        debrief_text=cached.get('debrief','')
        st.markdown(
            f'<div style="background:{BG2};border-radius:16px;padding:24px;margin-bottom:14px;border-left:3px solid {ACCENT};">'
            f'<div style="color:{TEXT};line-height:1.85;font-size:0.92em;">{debrief_text}</div>'
            f'</div>',unsafe_allow_html=True)
        fps=cached.get('focus_points',[])
        if fps:
            st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:20px 0 10px;">Focus Points</div>',unsafe_allow_html=True)
            for i,fp in enumerate(fps):
                st.markdown(f'<div style="background:{BG2};border-radius:12px;padding:14px 16px;margin-bottom:8px;display:flex;gap:14px;align-items:flex-start;"><div style="width:26px;height:26px;border-radius:50%;background:rgba({RGB},0.08);border:1px solid rgba({RGB},0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:0.72em;font-weight:700;color:{ACCENT};">{i+1}</div><div style="font-size:0.85em;color:{TEXT};line-height:1.7;">{fp}</div></div>',unsafe_allow_html=True)
        action=cached.get('action_plan','')
        if action:
            st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:20px 0 10px;">Action Plan</div>',unsafe_allow_html=True)
            st.markdown(f'<div style="background:rgba({RGB},0.04);border:1px solid rgba({RGB},0.1);border-radius:12px;padding:16px;margin-bottom:8px;"><div style="font-size:0.88em;color:{TEXT};line-height:1.7;">→ {action}</div></div>',unsafe_allow_html=True)
        patterns=[p for p in cached.get('behavioral_patterns',[]) if p]
        if patterns:
            st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:20px 0 10px;">Behavioral Patterns</div>',unsafe_allow_html=True)
            for i,p in enumerate(patterns):
                st.markdown(f'<div style="background:rgba(252,211,77,0.03);border:1px solid rgba(252,211,77,0.1);border-radius:12px;padding:14px 16px;margin-bottom:8px;"><div style="font-size:0.85em;color:{TEXT};line-height:1.7;">{p}</div></div>',unsafe_allow_html=True)
        red_flags=[r for r in cached.get('red_flags',[]) if r]
        if red_flags:
            st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:20px 0 10px;">Red Flags</div>',unsafe_allow_html=True)
            for i,rf in enumerate(red_flags):
                st.markdown(f'<div style="background:rgba(248,113,113,0.03);border:1px solid rgba(248,113,113,0.1);border-radius:12px;padding:14px 16px;margin-bottom:8px;"><div style="font-size:0.85em;color:{TEXT};line-height:1.7;">⚠ {rf}</div></div>',unsafe_allow_html=True)
        st.markdown(f'<div style="margin-top:16px;"></div>',unsafe_allow_html=True)
        if st.button("↺  Clear & Re-run",key="clear_debrief",use_container_width=False):
            st.session_state.coach_debrief=None; st.rerun()
    elif total_v==0:
        st.markdown(
            f'<div style="background:{BG2};border-radius:14px;padding:32px;text-align:center;margin-top:12px;">'
            f'<div style="font-size:1.2em;margin-bottom:10px;">⚡</div>'
            f'<div style="font-size:0.92em;color:{TEXT};font-weight:600;margin-bottom:6px;">No trades last week</div>'
            f'<div style="font-size:0.75em;color:{TEXT2};">Keep logging trades in Notion — Coach will analyse them every Sunday</div>'
            f'</div>',unsafe_allow_html=True)

    # ===== COACH HISTORY =====
    history=st.session_state.coach_history
    if history:
        st.markdown(f'<div class="v3-section">Debrief History</div>',unsafe_allow_html=True)
        for i,h in enumerate(history):
            h_grade=h.get('grade','—')
            h_grade_color='#4ade80' if h_grade in ['A+','A'] else ('#fcd34d' if h_grade in ['B+','B'] else ('#f59e0b' if h_grade in ['C+','C'] else '#f87171'))
            h_char=h.get('trader_character',{})
            h_tier=h_char.get('tier','—') if h_char else '—'
            h_title=h_char.get('title','—') if h_char else '—'
            h_tier_colors={'S':'#fcd34d','A':'#a78bfa','B':'#60a5fa','C':'#4ade80','D':'#f59e0b','F':'#f87171'}
            h_color=h_tier_colors.get(h_tier,'#94a3b8')
            h_week=h.get('week','—')
            h_debrief=h.get('debrief','')[:160]+'…' if len(h.get('debrief',''))>160 else h.get('debrief','')
            h_fps=h.get('focus_points',[])
            h_action=h.get('action_plan','')
            connector=f'<div style="width:1px;height:12px;background:{BORDER};margin-left:19px;"></div>' if i<len(history)-1 else ''
            st.markdown(
                f'<div style="display:flex;gap:14px;align-items:flex-start;">'
                f'<div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;">'
                f'<div style="width:10px;height:10px;border-radius:50%;background:{h_color};margin-top:18px;{"box-shadow:0 0 8px "+h_color+"66;" if i==0 else ""}"></div>'
                f'{"<div style=\'width:1px;height:20px;background:"+BORDER+";margin-top:4px;\'></div>" if i<len(history)-1 else ""}'
                f'<div style="flex:1;background:{BG2};border-radius:14px;padding:16px 18px;margin-bottom:10px;">'
                f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">'
                f'<div>'
                f'<div style="font-size:0.62em;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{h_color};">{h_tier} · {h_title}</div>'
                f'<div style="font-size:0.6em;color:{TEXT3};margin-top:2px;">{h_week}</div>'
                f'</div>'
                f'<div style="font-size:1.4em;font-weight:800;color:{h_grade_color};">{h_grade}</div>'
                f'</div>'
                f'<div style="font-size:0.8em;color:{TEXT2};line-height:1.7;margin-bottom:10px;">{h_debrief}</div>'
                f'{"<div style=\'font-size:0.72em;color:"+ACCENT+"\'>→ "+h_action+"</div>" if h_action else ""}'
                f'</div></div>',unsafe_allow_html=True)

st.markdown('</div>',unsafe_allow_html=True)
