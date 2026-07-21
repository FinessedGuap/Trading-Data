import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(page_title="Trading Data", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# ============ AUTH ============
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

# ============ IMPORTS ============
from utils.config import get_colors, ACCOUNT_SIZE, COACH_MEMORY_PAGE_ID
from utils.data import load_and_process
from utils.calculations import (
    calc_stats, calc_session_stats, calc_daily_r,
    calc_monthly_r, calc_dow_stats, calc_consistency_score,
    find_best_setup, generate_checklist
)
from utils.css import get_css
import pages.overview as pg_overview
import pages.pnl_tracker as pg_pnl
import pages.charts as pg_charts
import pages.calendar as pg_calendar
import pages.edge_analysis as pg_edge
import pages.best_setups as pg_setups
import pages.coach as pg_coach

# ============ SECRETS ============
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")

# ============ SESSION STATE ============
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

# ============ THEME ============
c = get_colors(st.session_state.theme, st.session_state.dark_mode)
c['IS_DARK'] = st.session_state.dark_mode

# ============ LOAD DATA ============
today = datetime.now()
df_main = load_and_process(NOTION_TOKEN, DATABASE_ID)

import pandas as pd

# ============ CALCULATE ALL STATS ONCE & CACHE ============
@st.cache_data(ttl=300)
def compute_all_stats(notion_token, database_id):
    df = load_and_process(notion_token, database_id)
    df_x = df[df['Pair'] == 'XAUUSD'].copy() if 'Pair' in df.columns else pd.DataFrame()
    df_n = df[df['Pair'] == 'NASDAQ'].copy() if 'Pair' in df.columns else pd.DataFrame()
    df_f = df[df['Type of Trade'].str.strip() == 'Funded'].copy() if 'Type of Trade' in df.columns else pd.DataFrame()
    ss = calc_session_stats(df)
    return {
        'df_main': df,
        'df_xau': df_x,
        'df_nas': df_n,
        'df_funded': df_f,
        'main_stats': calc_stats(df),
        'xau_stats': calc_stats(df_x) if len(df_x) > 0 else {},
        'nas_stats': calc_stats(df_n) if len(df_n) > 0 else {},
        'session_stats': ss,
        'daily_r': calc_daily_r(df),
        'monthly_r': calc_monthly_r(df),
        'dow_stats': calc_dow_stats(df),
        'consistency_score': calc_consistency_score(df, ss)[0],
        'consistency_breakdown': calc_consistency_score(df, ss)[1],
        'best_setup': find_best_setup(df),
        'green_checklist': generate_checklist(df, ss)[0],
        'red_checklist': generate_checklist(df, ss)[1],
    }

@st.cache_data(ttl=300)
def compute_all_stats(notion_token, database_id):
    df, status = load_and_process(notion_token, database_id)
    if status != "ok" or len(df) == 0:
        return None, status
    df_x = df[df['Pair'] == 'XAUUSD'].copy() if 'Pair' in df.columns else pd.DataFrame()
    df_n = df[df['Pair'] == 'NASDAQ'].copy() if 'Pair' in df.columns else pd.DataFrame()
    df_f = df[df['Type of Trade'].str.strip() == 'Funded'].copy() if 'Type of Trade' in df.columns else pd.DataFrame()
    ss = calc_session_stats(df)
    cs, cb = calc_consistency_score(df, ss)
    gc, rc = generate_checklist(df, ss)
    return {
        'df_main': df,
        'df_xau': df_x,
        'df_nas': df_n,
        'df_funded': df_f,
        'main_stats': calc_stats(df),
        'xau_stats': calc_stats(df_x) if len(df_x) > 0 else {},
        'nas_stats': calc_stats(df_n) if len(df_n) > 0 else {},
        'session_stats': ss,
        'daily_r': calc_daily_r(df),
        'monthly_r': calc_monthly_r(df),
        'dow_stats': calc_dow_stats(df),
        'consistency_score': cs,
        'consistency_breakdown': cb,
        'best_setup': find_best_setup(df),
        'green_checklist': gc,
        'red_checklist': rc,
    }, "ok"

data, data_status = compute_all_stats(NOTION_TOKEN, DATABASE_ID)

# Handle errors before rendering anything
if data_status == "empty" or data is None:
    BG2 = 'rgba(255,255,255,0.03)'
    TEXT = '#ffffff'
    TEXT2 = 'rgba(255,255,255,0.45)'
    ACCENT = '#94a3b8'

    if data_status == "empty":
        st.markdown(
            f'<div style="background:{BG2};border-radius:16px;padding:40px 24px;text-align:center;margin:40px auto;max-width:480px;">'
            f'<div style="font-size:2em;margin-bottom:12px;">📊</div>'
            f'<div style="font-size:0.92em;font-weight:600;color:{TEXT};margin-bottom:6px;">No trades logged yet</div>'
            f'<div style="font-size:0.72em;color:{TEXT2};line-height:1.6;max-width:320px;margin:0 auto;">Start logging trades in your Notion database and they\'ll appear here automatically. Hit Refresh once you\'ve added some.</div>'
            f'</div>', unsafe_allow_html=True)
    else:
        error_msg = data_status.replace("error:", "") if data_status.startswith("error:") else "Unknown error"
        st.markdown(
            f'<div style="background:rgba(248,113,113,0.04);border:1px solid rgba(248,113,113,0.15);border-radius:16px;padding:24px;display:flex;align-items:flex-start;gap:16px;margin:40px auto;max-width:480px;">'
            f'<div style="width:40px;height:40px;border-radius:10px;background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.15);display:flex;align-items:center;justify-content:center;font-size:1.1em;flex-shrink:0;">🔌</div>'
            f'<div>'
            f'<div style="font-size:0.88em;font-weight:600;color:#f87171;margin-bottom:4px;">Can\'t reach Notion</div>'
            f'<div style="font-size:0.72em;color:{TEXT2};line-height:1.5;margin-bottom:10px;">{error_msg}</div>'
            f'</div></div>', unsafe_allow_html=True)
        if st.button("↻ Try again"):
            st.cache_data.clear()
            st.rerun()
    st.stop()

df_main = data['df_main']
df_xau = data['df_xau']
df_nas = data['df_nas']
df_funded = data['df_funded']
main_stats = data['main_stats']
xau_stats = data['xau_stats']
nas_stats = data['nas_stats']
session_stats = data['session_stats']
daily_r = data['daily_r']
monthly_r = data['monthly_r']
dow_stats = data['dow_stats']
consistency_score = data['consistency_score']
consistency_breakdown = data['consistency_breakdown']
best_setup = data['best_setup']
green_checklist = data['green_checklist']
red_checklist = data['red_checklist']

# ============ CSS ============
st.markdown(get_css(c), unsafe_allow_html=True)

# ============ SIDEBAR ============
ACCENT = c['ACCENT']
ACCENT_SOFT = c['ACCENT_SOFT']
RGB = c['RGB']
BG = c['BG']
BG2 = c['BG2']
BG3 = c['BG3']
TEXT = c['TEXT']
TEXT2 = c['TEXT2']
TEXT3 = c['TEXT3']
BORDER = c['BORDER']
BORDER2 = c['BORDER2']
SIDEBAR = c['SIDEBAR']
SIDEBAR_B = c['SIDEBAR_B']
IS_DARK = st.session_state.dark_mode

with st.sidebar:
    st.markdown(f'<div style="padding:20px 16px 16px;border-bottom:1px solid {BORDER};margin-bottom:8px;"><span style="font-size:1em;font-weight:700;color:{TEXT};">Trading Data</span></div>', unsafe_allow_html=True)
    pages = ['Overview', 'P&L Tracker', 'Charts', 'Calendar', 'Edge Analysis', 'Best Setups', 'Coach']
    for p in pages:
        is_active = st.session_state.active_page == p
        icon = '⚡ ' if p == 'Coach' else ''
        if is_active:
            st.markdown(f'<div style="background:{BG2};border-left:2px solid {ACCENT};border-radius:8px;padding:9px 12px;margin:0;font-size:0.85em;font-weight:600;color:{ACCENT};line-height:1.6;">{icon}{p}</div>', unsafe_allow_html=True)
        else:
            if st.button(f"{icon}{p}", key=f"nav_{p}", use_container_width=True):
                st.session_state.active_page = p
                st.rerun()

    st.markdown(f'<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    if st.button("↻  Refresh", key="refresh_btn", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.button("⎋  Logout", key="logout_btn", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    st.markdown(f'<div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:16px;"><div style="font-size:0.58em;color:{TEXT3};letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;">Theme</div></div>', unsafe_allow_html=True)
    theme_opts = {'Blue': '#60a5fa', 'Purple': '#a78bfa', 'Green': '#34d399', 'Gold': '#fcd34d', 'Neutral': '#94a3b8'}
    tcols = st.columns(5)
    for i, (name, hex_c) in enumerate(theme_opts.items()):
        active_t = st.session_state.theme == name
        bdr = '2px solid #fff' if active_t else '2px solid transparent'
        tcols[i].markdown(f'<div style="width:20px;height:20px;border-radius:50%;background:{hex_c};border:{bdr};margin:auto;"></div>', unsafe_allow_html=True)
        if tcols[i].button(" ", key=f"theme_{name}", use_container_width=True):
            st.session_state.theme = name
            st.rerun()

    st.markdown(f'<div style="border-top:1px solid {BORDER};padding-top:12px;margin-top:12px;"></div>', unsafe_allow_html=True)
    cg, cb = st.columns([3, 1])
    cg.markdown(f'<div style="font-size:0.7em;color:{TEXT2};padding-top:8px;">{"Light" if IS_DARK else "Dark"} Mode</div>', unsafe_allow_html=True)
    with cb:
        if st.button("☀️" if IS_DARK else "🌙", key="mode_toggle", use_container_width=True):
            st.session_state.dark_mode = not IS_DARK
            st.rerun()

# ============ PAGE ROUTING ============
page = st.session_state.active_page
st.markdown('<div class="page-content">', unsafe_allow_html=True)

if page == 'Overview':
    pg_overview.render(df_main, main_stats, xau_stats, nas_stats, session_stats, monthly_r, consistency_score, consistency_breakdown, c, today)
elif page == 'P&L Tracker':
    pg_pnl.render(df_funded, main_stats, c, today, st.session_state.num_accounts, ACCOUNT_SIZE)
elif page == 'Charts':
    pg_charts.render(main_stats, xau_stats, nas_stats, c)
elif page == 'Calendar':
    pg_calendar.render(df_main, daily_r, dow_stats, c, today)
elif page == 'Edge Analysis':
    pg_edge.render(df_main, green_checklist, red_checklist, consistency_score, consistency_breakdown, c)
elif page == 'Best Setups':
    pg_setups.render(df_main, best_setup, c)
elif page == 'Coach':
    pg_coach.render(df_main, c, today, st.session_state.num_accounts, ACCOUNT_SIZE, ANTHROPIC_API_KEY, NOTION_TOKEN, COACH_MEMORY_PAGE_ID)

st.markdown('</div>', unsafe_allow_html=True)
