import streamlit as st
from utils.calculations import make_curve, catmull, build_donut


def render(main_stats, xau_stats, nas_stats, c):
    ACCENT = c['ACCENT']
    ACCENT_SOFT = c['ACCENT_SOFT']
    RGB = c['RGB']
    BG2 = c['BG2']
    BG3 = c['BG3']
    TEXT = c['TEXT']
    TEXT2 = c['TEXT2']
    BORDER2 = c['BORDER2']
    GOLD_S = c['GOLD_S']
    PURPLE_S = c['PURPLE_S']
    GOLD = c['GOLD']
    PURPLE_C = c['PURPLE_C']

    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:24px;">Charts</div>', unsafe_allow_html=True)

    xau_eq = xau_stats.get('equity_curve', [])
    nas_eq = nas_stats.get('equity_curve', [])
    sw, sh = 800, 200
    xl, xf = make_curve(xau_eq, sw, sh)
    nl, nf = make_curve(nas_eq, sw, sh)

    xfp = f'<path d="{xf}" fill="url(#xFill)" opacity="0.3"/>' if xf else ''
    xlp = f'<path d="{xl}" fill="none" stroke="{GOLD}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2.5s" begin="0s" fill="freeze"/></path>' if xl else ''
    nlp = f'<path d="{nl}" fill="none" stroke="{PURPLE_C}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2.5s" begin="0.3s" fill="freeze"/></path>' if nl else ''
    svg = f'<svg viewBox="0 0 {sw} {sh}" style="width:100%;height:260px;display:block;"><defs><linearGradient id="xFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba(245,158,11,0.2)"/><stop offset="100%" stop-color="rgba(245,158,11,0)"/></linearGradient></defs>{xfp}{xlp}{nlp}</svg>'

    st.markdown(
        f'<div class="v3-panel"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">'
        f'<div style="font-size:0.95em;font-weight:600;color:{TEXT};">Equity Curve</div>'
        f'<div style="display:flex;gap:16px;">'
        f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:20px;height:2px;background:{GOLD};border-radius:2px;"></div><span style="font-size:0.72em;color:{TEXT2};">XAUUSD</span></div>'
        f'<div style="display:flex;align-items:center;gap:6px;"><div style="width:20px;height:2px;background:{PURPLE_C};border-radius:2px;"></div><span style="font-size:0.72em;color:{TEXT2};">NASDAQ</span></div>'
        f'</div></div>{svg}</div>', unsafe_allow_html=True)

    rolling = main_stats.get('rolling_wr', [])
    if rolling:
        rw, rh = 800, 100
        n = len(rolling)
        pts = [((i / (n-1)) * rw if n > 1 else 0, rh - ((v / 100) * (rh - 16)) - 8) for i, v in enumerate(rolling)]
        rl = catmull(pts)
        rf = rl + f"L{rw},{rh} L0,{rh} Z" if rl else ""
        by = rh - (0.5 * (rh - 16)) - 8
        trending = rolling[-1] > rolling[0] if len(rolling) > 1 else False
        tc = '#4ade80' if trending else '#f87171'
        tt = 'Trending up ↑' if trending else 'Trending down ↓'
        rsvg = (
            f'<svg viewBox="0 0 {rw} {rh}" style="width:100%;height:100px;display:block;">'
            f'<defs><linearGradient id="rFill" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="rgba({RGB},0.15)"/>'
            f'<stop offset="100%" stop-color="rgba({RGB},0)"/>'
            f'</linearGradient></defs>'
            f'<line x1="0" y1="{by:.1f}" x2="{rw}" y2="{by:.1f}" stroke="{BORDER2}" stroke-width="1" stroke-dasharray="4,4"/>'
            + (f'<path d="{rf}" fill="url(#rFill)"/>' if rf else '')
            + (f'<path d="{rl}" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round" stroke-dasharray="2000" stroke-dashoffset="2000"><animate attributeName="stroke-dashoffset" from="2000" to="0" dur="2s" begin="0s" fill="freeze"/></path>' if rl else '')
            + '</svg>'
        )
        st.markdown(
            f'<div class="v3-panel"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
            f'<div><div style="font-size:0.95em;font-weight:600;color:{TEXT};">Rolling Win Rate</div>'
            f'<div style="font-size:0.68em;color:{TEXT2};margin-top:2px;">Last 10 trades window</div></div>'
            f'<div style="font-size:0.7em;color:{tc};font-weight:500;">{tt}</div>'
            f'</div>{rsvg}</div>', unsafe_allow_html=True)

    donut_configs = [
        ('Overall', main_stats.get('wins', 0), main_stats.get('losses', 0), main_stats.get('breakevens', 0),
         [ACCENT, f'{ACCENT}88', f'{ACCENT}33'], f'rgba({RGB},0.3)', ACCENT_SOFT),
        ('XAUUSD', xau_stats.get('wins', 0), xau_stats.get('losses', 0), xau_stats.get('breakevens', 0),
         ['#b45309', '#f59e0b', '#fde68a33'], 'rgba(245,158,11,0.3)', GOLD_S),
        ('NASDAQ', nas_stats.get('wins', 0), nas_stats.get('losses', 0), nas_stats.get('breakevens', 0),
         ['#6d28d9', '#a78bfa', '#ede9fe33'], 'rgba(167,139,250,0.3)', PURPLE_S),
    ]
    dcols = st.columns(3)
    for col, (lbl, w, l, b, colors, glow, tc) in zip(dcols, donut_configs):
        svg, legend = build_donut(w, l, b, colors, glow, BG2, TEXT2)
        col.markdown(
            f'<div class="v3-panel"><div style="font-size:0.85em;font-weight:600;color:{tc};margin-bottom:14px;">{lbl}</div>'
            f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
            f'<div>{svg}</div><div style="flex:1;min-width:90px;">{legend}</div>'
            f'</div></div>', unsafe_allow_html=True)
