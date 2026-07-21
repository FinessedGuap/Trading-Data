import streamlit as st
from utils.calculations import breakdown_by_col


def render_breakdown(df_in, col, title, c):
    TEXT = c['TEXT']
    TEXT2 = c['TEXT2']
    TEXT3 = c['TEXT3']
    BORDER = c['BORDER']
    BG3 = c['BG3']
    RGB = c['RGB']
    RANK_COLORS = c['RANK_COLORS']

    data = breakdown_by_col(df_in, col)
    if not data:
        return
    data = data[:3]
    st.markdown(f'<div style="color:{TEXT2};font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin:20px 0 10px;">{title}</div>', unsafe_allow_html=True)
    max_exp = max(abs(d['exp']) for d in data) if data else 1
    if max_exp == 0: max_exp = 1
    for rank, d in enumerate(data):
        bar_pct = round(abs(d['exp']) / max_exp * 100, 1)
        color = '#4ade80' if d['exp'] >= 0 else '#f87171'
        lbl = d['label'][:26] + '…' if len(d['label']) > 26 else d['label']
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


def render(df_main, green_checklist, red_checklist, consistency_score, consistency_breakdown, c):
    ACCENT = c['ACCENT']
    ACCENT_SOFT = c['ACCENT_SOFT']
    RGB = c['RGB']
    BG2 = c['BG2']
    BG3 = c['BG3']
    TEXT = c['TEXT']
    TEXT2 = c['TEXT2']
    TEXT3 = c['TEXT3']
    BORDER = c['BORDER']

    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:20px;">Edge Analysis</div>', unsafe_allow_html=True)

    ea1, ea2 = st.columns(2)
    with ea1:
        for col, title in [
            ('Entry Model', 'Entry Model'),
            ('Entry Model Timeframe', 'Entry Timeframe'),
            ('Double Confirmation', 'Double Confirmation'),
            ('Target', 'Target'),
            ('Entry + Confirmation', 'Rejection Candle'),
            ('News Proximity', 'News Proximity'),
        ]:
            render_breakdown(df_main, col, title, c)
    with ea2:
        for col, title in [
            ('Entry Confluences', 'Entry Confluences'),
            ('Stop Loss Logic', 'Stop Loss'),
            ('Hour', 'Time of Day'),
            ('Trade Quality Rating', 'Trade Quality'),
            ('Emotional State Before...', 'Emotional State'),
            ('Conditions MTF/HTF', 'Market Conditions'),
        ]:
            render_breakdown(df_main, col, title, c)

    st.markdown(f'<hr class="v3-divider">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin-bottom:14px;">Next Trade Checklist</div>', unsafe_allow_html=True)

    if green_checklist or red_checklist:
        cl1, cl2 = st.columns(2)
        with cl1:
            st.markdown(f'<div style="font-size:0.62em;color:#4ade80;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">✓ Do more of this</div>', unsafe_allow_html=True)
            for i, item in enumerate(green_checklist):
                st.markdown(
                    f'<div class="checklist-item" style="animation-delay:{i*40}ms;">'
                    f'<div style="width:6px;height:6px;border-radius:50%;background:#4ade80;margin-top:5px;flex-shrink:0;"></div>'
                    f'<div><div style="color:{TEXT};font-size:0.85em;font-weight:500;">{item["label"]}</div>'
                    f'<div style="color:{TEXT2};font-size:0.72em;margin-top:2px;">{item["detail"]}</div></div>'
                    f'</div>', unsafe_allow_html=True)
        with cl2:
            st.markdown(f'<div style="font-size:0.62em;color:#f87171;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">✗ Avoid this</div>', unsafe_allow_html=True)
            for i, item in enumerate(red_checklist):
                st.markdown(
                    f'<div class="checklist-item" style="animation-delay:{i*40}ms;">'
                    f'<div style="width:6px;height:6px;border-radius:50%;background:#f87171;margin-top:5px;flex-shrink:0;"></div>'
                    f'<div><div style="color:{TEXT};font-size:0.85em;font-weight:500;">{item["label"]}</div>'
                    f'<div style="color:{TEXT2};font-size:0.72em;margin-top:2px;">{item["detail"]}</div></div>'
                    f'</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="color:{TEXT2};font-size:0.85em;">Not enough data yet.</div>', unsafe_allow_html=True)

    st.markdown(f'<hr class="v3-divider">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin-bottom:14px;">Consistency Score</div>', unsafe_allow_html=True)

    csc1, csc2 = st.columns([1, 2])
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
        for i, (lbl, score) in enumerate(consistency_breakdown):
            color = '#4ade80' if score >= 70 else ('#f59e0b' if score >= 50 else '#f87171')
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid {BORDER};animation:slideInLeft 0.4s cubic-bezier(0.16,1,0.3,1) {i*70}ms both;">'
                f'<span style="color:{TEXT2};font-size:0.82em;">{lbl}</span>'
                f'<span style="color:{color};font-weight:600;font-size:0.82em;">{score}%</span>'
                f'</div>', unsafe_allow_html=True)
