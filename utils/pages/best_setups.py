import streamlit as st
from utils.calculations import get_best


def render(df_main, best_setup, c):
    ACCENT = c['ACCENT']
    ACCENT_SOFT = c['ACCENT_SOFT']
    RGB = c['RGB']
    BG2 = c['BG2']
    TEXT = c['TEXT']
    TEXT2 = c['TEXT2']
    TEXT3 = c['TEXT3']
    BORDER = c['BORDER']

    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:20px;">Best Setups</div>', unsafe_allow_html=True)

    if best_setup:
        st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin-bottom:12px;">Top Setup Finder</div>', unsafe_allow_html=True)
        tags = ''.join([
            f'<span style="background:rgba({RGB},0.1);border-radius:6px;padding:4px 10px;font-size:0.75em;color:{ACCENT};margin:3px;display:inline-block;animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) {i*50}ms both;">{b["label"]}</span>'
            for i, b in enumerate(best_setup['combos'])
        ])
        oc = '#4ade80' if best_setup['overall_wr'] >= 60 else ('#f59e0b' if best_setup['overall_wr'] >= 45 else '#f87171')
        st.markdown(
            f'<div class="v3-panel">'
            f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:18px;">{tags}</div>'
            f'<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">'
            f'<div style="text-align:center;"><div style="font-size:1.3em;font-weight:700;color:{oc};">{best_setup["overall_wr"]}%</div><div style="font-size:0.58em;color:{TEXT2};margin-top:3px;text-transform:uppercase;letter-spacing:0.5px;">Avg Win Rate</div></div>'
            f'<div style="text-align:center;"><div style="font-size:1.3em;font-weight:700;color:{TEXT};">+{best_setup["overall_exp"]}R</div><div style="font-size:0.58em;color:{TEXT2};margin-top:3px;text-transform:uppercase;letter-spacing:0.5px;">Avg Expectancy</div></div>'
            f'</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:24px 0 12px;">Best of Each Variable</div>', unsafe_allow_html=True)

    setup_cols = [
        ('Entry Model', 'Entry Model'),
        ('Entry Model Timeframe', 'Timeframe'),
        ('3SL Window', '3SL Window'),
        ('Target', 'Target'),
        ('Stop Loss Logic', 'Stop Loss'),
        ('Entry + Confirmation', 'Rejection Candle'),
        ('Double Confirmation', 'Double Confirmation'),
        ('Hour', 'Time of Day'),
        ('Trade Quality Rating', 'Trade Quality'),
        ('Emotional State Before...', 'Emotional State'),
        ('News Proximity', 'News Proximity'),
        ('Conditions MTF/HTF', 'Market Conditions'),
    ]

    rows = ''
    for i, (cn, lbl) in enumerate(setup_cols):
        best = get_best(df_main, cn)
        if not best:
            continue
        color = '#4ade80' if best['exp'] >= 0 else '#f87171'
        s = '+' if best['exp'] >= 0 else ''
        rows += (
            f'<div class="setup-row" style="animation-delay:{i*35}ms;">'
            f'<span style="color:{TEXT2};font-size:0.68em;text-transform:uppercase;letter-spacing:0.5px;min-width:110px;">{lbl}</span>'
            f'<span style="color:{TEXT};font-size:0.85em;font-weight:500;flex:1;">{best["label"]}</span>'
            f'<span style="color:{color};font-size:0.82em;font-weight:700;min-width:46px;text-align:right;">{s}{best["exp"]}R</span>'
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
