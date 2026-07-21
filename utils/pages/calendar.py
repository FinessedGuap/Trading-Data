import streamlit as st
import calendar as cal_module
from datetime import datetime


def render(df_main, daily_r, dow_stats, c, today):
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
    GOLD_S = c['GOLD_S']
    PURPLE_S = c['PURPLE_S']
    IS_DARK = c.get('IS_DARK', True)
    RANK_COLORS = c['RANK_COLORS']

    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:24px;">Calendar</div>', unsafe_allow_html=True)

    cm = st.session_state.cal_month
    cy = st.session_state.cal_year
    mt_r = sum(v['total_r'] for k, v in daily_r.items() if k.month == cm and k.year == cy)
    ms2 = '+' if mt_r > 0 else ''
    mn = datetime(cy, cm, 1).strftime("%B %Y")

    nl2, nr = st.columns([7, 2])
    nl2.markdown(
        f'<div style="background:{BG2};border-radius:14px;height:40px;display:flex;align-items:center;padding:0 18px;margin-bottom:14px;">'
        f'<span style="font-size:1em;font-weight:700;color:{TEXT};">{mn}</span>'
        f'<span style="font-size:0.72em;color:{ACCENT};font-weight:600;margin-left:10px;">{ms2}{round(mt_r,2)}R</span>'
        f'</div>', unsafe_allow_html=True)

    with nr:
        st.markdown('<div class="cal-arrows">', unsafe_allow_html=True)
        al, ar2 = st.columns(2)
        with al:
            if st.button("‹", key="prev_m", use_container_width=True):
                if st.session_state.cal_month == 1:
                    st.session_state.cal_month = 12
                    st.session_state.cal_year -= 1
                else:
                    st.session_state.cal_month -= 1
                st.rerun()
        with ar2:
            if st.button("›", key="next_m", use_container_width=True):
                if st.session_state.cal_month == 12:
                    st.session_state.cal_month = 1
                    st.session_state.cal_year += 1
                else:
                    st.session_state.cal_month += 1
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    cal_module.setfirstweekday(cal_module.MONDAY)
    mm = cal_module.monthcalendar(cy, cm)
    dhc = st.columns(8)
    for i, d in enumerate(['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']):
        dhc[i].markdown(f'<div class="cal-header">{d}</div>', unsafe_allow_html=True)
    dhc[7].markdown(f'<div class="cal-header">Wk</div>', unsafe_allow_html=True)

    for wn, week in enumerate(mm):
        if wn > 0:
            st.write("")
        wc = st.columns(8)
        wt = wtr = 0
        for i, dn in enumerate(week):
            if dn == 0:
                wc[i].markdown('<div style="min-height:72px;"></div>', unsafe_allow_html=True)
            else:
                dd = datetime(cy, cm, dn).date()
                dd_data = daily_r.get(dd)
                if dd_data:
                    wt += dd_data['total_r']
                    wtr += dd_data['trades']
                    rv = dd_data['total_r']
                    sg = '+' if rv > 0 else ''
                    if rv >= 0:
                        ds = "background:rgba(74,222,128,0.06);border:1px solid rgba(74,222,128,0.15);"
                        rc = '#4ade80' if IS_DARK else '#16a34a'
                        nc = 'rgba(74,222,128,0.9)' if IS_DARK else '#14532d'
                    else:
                        ds = "background:rgba(248,113,113,0.06);border:1px solid rgba(248,113,113,0.15);"
                        rc = '#f87171' if IS_DARK else '#dc2626'
                        nc = 'rgba(248,113,113,0.9)' if IS_DARK else '#7f1d1d'
                    delay = (wn * 7 + i) * 30
                    wc[i].markdown(
                        f'<div style="{ds}border-radius:10px;min-height:72px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:6px;text-align:center;animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) {delay}ms both;">'
                        f'<div style="color:{nc};font-size:0.7em;font-weight:600;">{dn}</div>'
                        f'<div style="color:{rc};font-size:0.82em;font-weight:700;margin-top:3px;">{sg}{rv}R</div>'
                        f'<div style="color:{TEXT2};font-size:0.58em;margin-top:2px;">{dd_data["trades"]}t</div>'
                        f'</div>', unsafe_allow_html=True)
                else:
                    wc[i].markdown(
                        f'<div style="min-height:72px;display:flex;align-items:center;justify-content:center;">'
                        f'<div class="cal-day-num">{dn}</div></div>', unsafe_allow_html=True)
        ws = '+' if wt > 0 else ''
        wc[7].markdown(
            f'<div style="background:{BG2};border-radius:10px;min-height:72px;padding:8px 4px;text-align:center;animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) {wn*60}ms both;">'
            f'<div style="color:{TEXT2};font-size:0.58em;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">W{wn+1}</div>'
            f'<div style="font-size:0.92em;font-weight:700;color:{TEXT};margin-top:8px;">{ws}{round(wt,2)}R</div>'
            f'<div style="color:{TEXT2};font-size:0.55em;margin-top:2px;">{wtr}t</div>'
            f'</div>', unsafe_allow_html=True)

    if st.session_state.selected_day:
        st.markdown(f'<hr class="v3-divider">', unsafe_allow_html=True)
        sd = st.session_state.selected_day
        dtdf = df_main.dropna(subset=['Date', 'R_Result']).copy()
        dtdf['day'] = dtdf['Date'].dt.date
        dtdf = dtdf[dtdf['day'] == sd]
        st.markdown(f'<div style="font-size:0.85em;font-weight:600;color:{TEXT};margin-bottom:12px;">Trades on {sd.strftime("%B %d, %Y")}</div>', unsafe_allow_html=True)
        for _, trade in dtdf.iterrows():
            rv = trade['R_Result']
            lbl = 'Win' if rv > 0 else ('Loss' if rv < 0 else 'BE')
            sg = '+' if rv > 0 else ''
            pair = trade.get('Pair', '—')
            pc2 = GOLD_S if pair == 'XAUUSD' else (PURPLE_S if pair == 'NASDAQ' else ACCENT_SOFT)
            st.markdown(
                f'<div style="background:{BG2};border-radius:10px;padding:12px 16px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">'
                f'<span style="color:{pc2};font-weight:600;font-size:0.88em;">{lbl} · {pair}</span>'
                f'<span style="color:{TEXT};font-weight:700;">{sg}{rv}R</span></div>', unsafe_allow_html=True)
        if st.button("Close"):
            st.session_state.selected_day = None
            st.rerun()

    st.markdown(f'<hr class="v3-divider">', unsafe_allow_html=True)
    st.markdown(f'<div class="v3-section">Best Day of the Week</div>', unsafe_allow_html=True)
    if dow_stats:
        best_day = dow_stats[0]
        bc = '#4ade80' if best_day['exp'] >= 0 else '#f87171'
        bs = '+' if best_day['exp'] >= 0 else ''
        dow_cols = st.columns([1, 2])
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
            for i, d in enumerate(dow_stats):
                c2 = '#4ade80' if d['exp'] >= 0 else '#f87171'
                s = '+' if d['exp'] >= 0 else ''
                rc = RANK_COLORS[i] if i < len(RANK_COLORS) else TEXT3
                rows += (
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid {BORDER};">'
                    f'<span style="color:{rc};font-size:0.68em;font-weight:700;min-width:20px;">#{i+1}</span>'
                    f'<span style="color:{TEXT};font-size:0.82em;font-weight:500;flex:1;margin-left:8px;">{d["day"]}</span>'
                    f'<span style="color:{c2};font-size:0.82em;font-weight:700;min-width:46px;text-align:right;">{s}{d["exp"]}R</span>'
                    f'<span style="color:{TEXT2};font-size:0.78em;min-width:38px;text-align:right;">{d["wr"]}%</span>'
                    f'<span style="color:{TEXT3};font-size:0.72em;min-width:24px;text-align:right;">{d["n"]}t</span>'
                    f'</div>')
            st.markdown(f'<div class="v3-panel">{rows}</div>', unsafe_allow_html=True)
