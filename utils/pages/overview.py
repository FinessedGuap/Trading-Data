import streamlit as st
import streamlit.components.v1 as components


def render(df_main, main_stats, xau_stats, nas_stats, session_stats, monthly_r, consistency_score, consistency_breakdown, c, today):
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

    this_month_key = today.strftime('%Y-%m')
    last_month_key = (today.replace(day=1) - __import__('pandas').Timedelta(days=1)).strftime('%Y-%m')
    this_month_r = monthly_r.get(this_month_key, {}).get('total_r', 0)
    last_month_r = monthly_r.get(last_month_key, {}).get('total_r', 0)
    diff = round(this_month_r - last_month_r, 2)

    cur = main_stats.get('cur_streak', 0)
    cur_type = main_stats.get('cur_streak_type', '—')
    cur_color = '#4ade80' if cur_type == 'W' else ('#f87171' if cur_type == 'L' else ACCENT)
    cur_label = 'Win Streak' if cur_type == 'W' else ('Loss Streak' if cur_type == 'L' else 'Streak')
    diff_color = '#4ade80' if diff >= 0 else '#f87171'
    diff_sign = '+' if diff >= 0 else ''
    month_sign = '+' if this_month_r > 0 else ''

    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:20px;">Overview</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="background:{BG2};border-radius:18px;padding:22px 28px;display:flex;align-items:center;margin-bottom:24px;">'
        f'<div style="flex:1;text-align:center;"><div style="font-size:1.8em;font-weight:800;color:{cur_color};">{cur}</div><div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">{cur_label}</div></div>'
        f'<div style="width:1px;height:36px;background:{BORDER};"></div>'
        f'<div style="flex:1;text-align:center;"><div style="font-size:1.8em;font-weight:800;color:{ACCENT};" id="b-cons">—</div><div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">Consistency</div></div>'
        f'<div style="width:1px;height:36px;background:{BORDER};"></div>'
        f'<div style="flex:1;text-align:center;"><div style="font-size:1.8em;font-weight:800;color:{TEXT};" id="b-month">—</div><div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">This Month</div></div>'
        f'<div style="width:1px;height:36px;background:{BORDER};"></div>'
        f'<div style="flex:1;text-align:center;"><div style="font-size:1.8em;font-weight:800;color:{diff_color};" id="b-diff">—</div><div style="font-size:0.58em;color:{TEXT2};margin-top:5px;text-transform:uppercase;letter-spacing:0.8px;">vs Last Month</div></div>'
        f'</div>', unsafe_allow_html=True)

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
    """, height=0)

    st.markdown(f'<div class="v3-section">Performance</div>', unsafe_allow_html=True)
    overviews = [
        {'label': 'Overall', 'stats': main_stats, 'color': ACCENT_SOFT},
        {'label': 'XAUUSD', 'stats': xau_stats, 'color': GOLD_S},
        {'label': 'NASDAQ', 'stats': nas_stats, 'color': PURPLE_S},
    ]
    idx = st.session_state.overview_idx
    current = overviews[idx]

    pc, nc = st.columns(2)
    with pc:
        if st.button(f"← {overviews[(idx-1)%3]['label']}", key="prev_ov", use_container_width=True):
            st.session_state.overview_idx = (idx - 1) % 3
            st.rerun()
    with nc:
        if st.button(f"{overviews[(idx+1)%3]['label']} →", key="next_ov", use_container_width=True):
            st.session_state.overview_idx = (idx + 1) % 3
            st.rerun()

    st.markdown(f'<div style="background:{BG2};border-radius:14px;padding:14px 20px;text-align:center;margin-bottom:16px;font-size:1em;font-weight:700;color:{current["color"]};">{current["label"]} Performance</div>', unsafe_allow_html=True)

    stat_data = [
        ('Total Trades', current['stats'].get('total_trades', '—')),
        ('Win Rate', f"{current['stats'].get('win_rate', '—')}%"),
        ('Total R', current['stats'].get('total_r', '—')),
        ('Avg R', current['stats'].get('avg_r', '—')),
        ('Expectancy', current['stats'].get('expectancy', '—')),
        ('Avg Win', current['stats'].get('avg_win', '—')),
        ('Avg Loss', current['stats'].get('avg_loss', '—')),
        ('Best Trade', current['stats'].get('best_trade', '—')),
        ('Worst Trade', current['stats'].get('worst_trade', '—')),
        ('Max DD', current['stats'].get('max_drawdown', '—')),
        ('Consec L', current['stats'].get('max_consec_losses', '—')),
        ('Wins', current['stats'].get('wins', '—')),
        ('Losses', current['stats'].get('losses', '—')),
        ('Breakevens', current['stats'].get('breakevens', '—')),
    ]

    for i in range(0, len(stat_data), 7):
        row = stat_data[i:i+7]
        cols = st.columns(len(row))
        for j, (col, (lbl, val)) in enumerate(zip(cols, row)):
            col.markdown(
                f'<div class="v3-card" style="animation-delay:{j*40}ms;">'
                f'<div class="v3-val">{val}</div>'
                f'<div class="v3-lbl" style="color:{current["color"]};">{lbl}</div>'
                f'</div>', unsafe_allow_html=True)
        st.write("")

    st.markdown(f'<div class="v3-section">Recent Trades</div>', unsafe_allow_html=True)
    tr = main_stats.get('trade_results', [])
    streak_html = f'<div style="display:flex;gap:3px;overflow-x:auto;padding-bottom:6px;scrollbar-width:none;margin-bottom:10px;">'
    for i, r in enumerate(tr):
        is_last = i == len(tr) - 1
        bg = 'rgba(74,222,128,0.85)' if r == 'W' else ('rgba(248,113,113,0.75)' if r == 'L' else f'rgba({RGB},0.3)')
        tc = '#000' if r == 'W' else '#fff'
        cls = 'streak-box active' if is_last else 'streak-box'
        streak_html += f'<div class="{cls}" style="background:{bg};color:{tc};animation-delay:{i*25}ms;flex-shrink:0;">{r}</div>'
    streak_html += f'<div class="streak-box" style="background:{BG2};color:{TEXT3};border:1px dashed {BORDER2};flex-shrink:0;">?</div></div>'
    streak_html += f'<div style="font-size:0.75em;color:{TEXT2};">Current streak: <span style="color:{cur_color};font-weight:600;">{cur} {cur_type}</span></div>'
    st.markdown(f'<div class="v3-panel">{streak_html}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="v3-section">Month vs Month</div>', unsafe_allow_html=True)
    months = sorted(monthly_r.keys())[-4:]
    if months:
        mcols = st.columns(len(months))
        for i, (col, m) in enumerate(zip(mcols, months)):
            d = monthly_r[m]
            sign = '+' if d['total_r'] > 0 else ''
            is_cur = m == this_month_key
            current_badge = f'<div style="color:{ACCENT_SOFT};font-size:0.58em;margin-top:3px;">Current</div>' if is_cur else ''
            col.markdown(
                f'<div style="background:{"rgba("+RGB+",0.08)" if is_cur else BG2};border-radius:12px;padding:14px;text-align:center;{"border:1px solid rgba("+RGB+",0.2);" if is_cur else ""}animation:staggerIn 0.5s cubic-bezier(0.16,1,0.3,1) {i*60}ms both;">'
                f'<div style="color:{ACCENT_SOFT if is_cur else TEXT2};font-size:0.6em;margin-bottom:6px;text-transform:uppercase;">{m}</div>'
                f'<div style="color:{TEXT};font-size:1.15em;font-weight:700;">{sign}{d["total_r"]}R</div>'
                f'<div style="color:{TEXT2};font-size:0.6em;margin-top:4px;">{d["win_rate"]}% · {d["trades"]}t</div>'
                f'{current_badge}</div>', unsafe_allow_html=True)

    max_abs_exp = max([abs(s['exp']) for s in session_stats]) if session_stats else 1
    if max_abs_exp == 0: max_abs_exp = 1

    st.markdown(f'<div class="v3-section">3SL Window</div>', unsafe_allow_html=True)
    rows_html = ""
    for i, s in enumerate(session_stats):
        bar_pct = round(abs(s['exp']) / max_abs_exp * 100, 1)
        bar_color = f'linear-gradient(90deg,rgba({RGB},0.4),{ACCENT})' if s['exp'] >= 0 else 'linear-gradient(90deg,rgba(248,113,113,0.4),#f87171)'
        delay = i * 300
        rows_html += (
            f'<div style="display:grid;grid-template-columns:90px 1fr 60px 55px 35px;gap:14px;align-items:center;padding:10px 0;border-bottom:1px solid {BORDER};">'
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
        f'</div>{rows_html}</div>', unsafe_allow_html=True)
