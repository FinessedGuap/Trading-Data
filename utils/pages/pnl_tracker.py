import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from utils.calculations import calc_stats


def render(df_funded, main_stats, c, today, num_accounts, account_size):
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
    SHADOW = c['SHADOW']

    total_capital = account_size * num_accounts

    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:20px;">P&L Tracker</div>', unsafe_allow_html=True)

    _, num_col, _ = st.columns([2, 1, 2])
    with num_col:
        na = st.number_input("Accounts", min_value=1, max_value=50, value=num_accounts, step=1)
        if na != num_accounts:
            st.session_state.num_accounts = na
            st.rerun()

    if len(df_funded) > 0 and 'R_Result' in df_funded.columns:
        df_fc = df_funded.dropna(subset=['R_Result', 'Date']).copy().sort_values('Date').reset_index(drop=True)

        if 'Risk Management' in df_fc.columns:
            avg_risk_pct = pd.to_numeric(df_fc['Risk Management'].str.replace('%', '').str.strip(), errors='coerce').mean()
            if pd.isna(avg_risk_pct): avg_risk_pct = 1.0
        else:
            avg_risk_pct = 1.0

        def calc_pnl(df_sub):
            if 'Risk Management' in df_sub.columns:
                rp = pd.to_numeric(df_sub['Risk Management'].str.replace('%', '').str.strip(), errors='coerce').fillna(avg_risk_pct)
                return round((df_sub['R_Result'].values * rp.values / 100 * account_size * num_accounts).sum(), 2)
            return round(df_sub['R_Result'].sum() * avg_risk_pct / 100 * account_size * num_accounts, 2)

        month_funded = df_fc[(df_fc['Date'].dt.month == today.month) & (df_fc['Date'].dt.year == today.year)]
        month_pnl = calc_pnl(month_funded)
        month_pct = round(month_pnl / total_capital * 100, 2)
        month_r = round(month_funded['R_Result'].sum(), 2)

        week_start = today - pd.Timedelta(days=today.weekday())
        week_funded = df_fc[df_fc['Date'].dt.date >= week_start.date()]
        week_pnl = calc_pnl(week_funded)
        week_pct = round(week_pnl / total_capital * 100, 2)
        week_r = round(week_funded['R_Result'].sum(), 2)

        today_funded = df_fc[df_fc['Date'].dt.date == today.date()]
        today_pnl = calc_pnl(today_funded)
        today_pct = round(today_pnl / total_capital * 100, 2)
        today_r = round(today_funded['R_Result'].sum(), 2)

        total_pnl = calc_pnl(df_fc)
        total_r = round(df_fc['R_Result'].sum(), 2)

        def fmt(v): return f"+${v:,.2f}" if v >= 0 else f"-${abs(v):,.2f}"
        def fmtp(v): return f"+{v}%" if v >= 0 else f"{v}%"
        def pc(v): return '#4ade80' if v >= 0 else '#f87171'

        st.markdown(f'<div class="v3-section">Performance</div>', unsafe_allow_html=True)
        pcols = st.columns(3)
        for i, (col, (period, pnl, pct, rv, nt)) in enumerate(zip(pcols, [
            ('This Month', month_pnl, month_pct, f"{month_r}R", len(month_funded)),
            ('This Week', week_pnl, week_pct, f"{week_r}R", len(week_funded)),
            ('Today', today_pnl, today_pct, f"{today_r}R", len(today_funded)),
        ])):
            c2 = pc(pnl)
            col.markdown(
                f'<div class="v3-card" style="animation-delay:{i*60}ms;">'
                f'<div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">{period}</div>'
                f'<div style="font-size:1.5em;font-weight:700;color:{c2};" id="pnl-{i}">{fmt(pnl)}</div>'
                f'<div style="font-size:0.9em;font-weight:600;color:{c2};margin-top:3px;" id="pct-{i}">{fmtp(pct)}</div>'
                f'<div style="font-size:0.6em;color:{TEXT2};margin-top:10px;padding-top:10px;border-top:1px solid {BORDER};">{rv} · {nt} trades</div>'
                f'</div>', unsafe_allow_html=True)

        components.html(f"""
<script>
function cm(id,t,dur){{var el=window.parent.document.getElementById(id);if(!el)return;var t0=null,pfx=t>=0?'+$':'-$',at=Math.abs(t);function s(ts){{if(!t0)t0=ts;var p=Math.min((ts-t0)/dur,1),e=1-Math.pow(1-p,3);el.textContent=pfx+(at*e).toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});if(p<1)requestAnimationFrame(s);}}requestAnimationFrame(s);}}
function cp(id,t,dur){{var el=window.parent.document.getElementById(id);if(!el)return;var t0=null,pfx=t>=0?'+':'-',at=Math.abs(t);function s(ts){{if(!t0)t0=ts;var p=Math.min((ts-t0)/dur,1),e=1-Math.pow(1-p,3);el.textContent=pfx+(at*e).toFixed(2)+'%';if(p<1)requestAnimationFrame(s);}}requestAnimationFrame(s);}}
setTimeout(function(){{cm('pnl-0',{month_pnl},900);cm('pnl-1',{week_pnl},900);cm('pnl-2',{today_pnl},900);cp('pct-0',{month_pct},900);cp('pct-1',{week_pct},900);cp('pct-2',{today_pct},900);}},200);
</script>
        """, height=0)

        st.markdown(f'<div class="v3-section">All Time · Funded</div>', unsafe_allow_html=True)
        at_cols = st.columns(3)
        sign_t = '+' if total_pnl >= 0 else ''
        at_cols[0].markdown(f'<div class="v3-card" style="animation-delay:0ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total P&L</div><div style="font-size:1.3em;font-weight:700;color:{pc(total_pnl)};">{fmt(total_pnl)}</div><div style="font-size:0.72em;color:{pc(total_pnl)};margin-top:3px;">{sign_t}{round(total_pnl/total_capital*100,2)}%</div></div>', unsafe_allow_html=True)
        at_cols[1].markdown(f'<div class="v3-card" style="animation-delay:60ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total R</div><div style="font-size:1.3em;font-weight:700;color:{TEXT};">{sign_t}{total_r}R</div></div>', unsafe_allow_html=True)
        at_cols[2].markdown(f'<div class="v3-card" style="animation-delay:120ms;"><div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Total Capital</div><div style="font-size:1.3em;font-weight:700;color:{ACCENT_SOFT};">${total_capital:,}</div></div>', unsafe_allow_html=True)

        st.markdown(f'<div class="v3-section">Goals</div>', unsafe_allow_html=True)
        goal_pnl_target = 10000
        goal_wr = 60
        funded_stats = calc_stats(df_fc)
        current_wr = funded_stats.get('win_rate', 0)
        pnl_prog = min(round(max(total_pnl, 0) / goal_pnl_target * 100, 1), 100)
        wr_prog = min(round(current_wr / goal_wr * 100, 1), 100)
        pnl_rem = round(max(goal_pnl_target - max(total_pnl, 0), 0), 2)

        gcols = st.columns(2)
        gcols[0].markdown(
            f'<div class="v3-card" style="text-align:left;animation-delay:0ms;">'
            f'<div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">Monthly P&L Goal</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:12px;"><span style="font-size:1.2em;font-weight:700;color:{TEXT};">${max(total_pnl,0):,.0f}</span><span style="font-size:0.72em;color:{TEXT2};">/ ${goal_pnl_target:,}</span></div>'
            f'<div style="background:{BG3};border-radius:4px;height:4px;overflow:hidden;margin-bottom:8px;"><div style="width:{pnl_prog}%;height:100%;background:{ACCENT};border-radius:4px;"></div></div>'
            f'<div style="font-size:0.62em;color:{TEXT2};">{pnl_prog}% · ${pnl_rem:,.0f} to go</div>'
            f'</div>', unsafe_allow_html=True)

        gcols[1].markdown(
            f'<div class="v3-card" style="text-align:left;animation-delay:60ms;">'
            f'<div style="font-size:0.6em;color:{TEXT2};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">Win Rate Goal</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:12px;"><span style="font-size:1.2em;font-weight:700;color:{TEXT};">{current_wr}%</span><span style="font-size:0.72em;color:{TEXT2};">/ {goal_wr}%</span></div>'
            f'<div style="background:{BG3};border-radius:4px;height:4px;overflow:hidden;margin-bottom:8px;"><div style="width:{wr_prog}%;height:100%;background:{ACCENT};border-radius:4px;"></div></div>'
            f'<div style="font-size:0.62em;color:{TEXT2};">{wr_prog}% there</div>'
            f'</div>', unsafe_allow_html=True)

        pnl_dash = round(239 - (pnl_prog / 100) * 239)
        wr_dash = round(239 - (wr_prog / 100) * 239)
        st.markdown(
            f'<div class="v3-panel" style="display:flex;justify-content:space-around;align-items:center;padding:24px;margin-top:16px;">'
            f'<div style="text-align:center;"><div style="position:relative;width:88px;height:88px;margin:0 auto;"><svg viewBox="0 0 100 100" style="width:88px;height:88px;transform:rotate(-90deg);"><circle cx="50" cy="50" r="38" fill="none" stroke="{BG3}" stroke-width="8"/><circle cx="50" cy="50" r="38" fill="none" stroke="{ACCENT}" stroke-width="8" stroke-dasharray="239" stroke-dashoffset="{pnl_dash}" stroke-linecap="round"/></svg><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:0.82em;font-weight:700;color:{TEXT};">{pnl_prog}%</div></div><div style="font-size:0.7em;font-weight:600;color:{TEXT};margin-top:8px;">${max(total_pnl,0):,.0f}</div><div style="font-size:0.58em;color:{TEXT2};">of ${goal_pnl_target:,}</div></div>'
            f'<div style="text-align:center;"><div style="position:relative;width:88px;height:88px;margin:0 auto;"><svg viewBox="0 0 100 100" style="width:88px;height:88px;transform:rotate(-90deg);"><circle cx="50" cy="50" r="38" fill="none" stroke="{BG3}" stroke-width="8"/><circle cx="50" cy="50" r="38" fill="none" stroke="{ACCENT}" stroke-width="8" stroke-dasharray="239" stroke-dashoffset="{wr_dash}" stroke-linecap="round"/></svg><div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:0.82em;font-weight:700;color:{TEXT};">{wr_prog}%</div></div><div style="font-size:0.7em;font-weight:600;color:{TEXT};margin-top:8px;">{current_wr}%</div><div style="font-size:0.58em;color:{TEXT2};">WR goal</div></div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="v3-panel" style="text-align:center;padding:48px;"><div style="color:{TEXT2};">No trades yet</div></div>', unsafe_allow_html=True)
