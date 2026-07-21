import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from utils.coach import call_coach_api, call_midweek_api
from utils.data import save_coach_memory, load_coach_memory, get_headers


def render(df_main, c, today, num_accounts, account_size, anthropic_api_key, notion_token, coach_memory_page_id):
    ACCENT = c['ACCENT']
    ACCENT_SOFT = c['ACCENT_SOFT']
    RGB = c['RGB']
    BG2 = c['BG2']
    BG3 = c['BG3']
    TEXT = c['TEXT']
    TEXT2 = c['TEXT2']
    TEXT3 = c['TEXT3']
    BORDER = c['BORDER']
    BORDER2 = c['BORDER2']

    headers = get_headers(notion_token)

    # Load persistent memory
    saved_profile, saved_character = load_coach_memory(headers, coach_memory_page_id)
    if saved_profile:
        st.session_state.coach_profile = saved_profile
    if saved_character:
        st.session_state.coach_character = saved_character

    st.markdown(f'<div style="font-size:1.5em;font-weight:700;color:{TEXT};margin-bottom:20px;">Coach</div>', unsafe_allow_html=True)

    # Coach header
    st.markdown(
        f'<div class="coach-card" style="background:{BG2};border-radius:20px;padding:24px;margin-bottom:20px;display:flex;align-items:center;gap:20px;">'
        f'<div class="coach-avatar" style="width:56px;height:56px;border-radius:50%;background:rgba({RGB},0.08);border:1px solid rgba({RGB},0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;"><span style="font-size:1.5em;">⚡</span></div>'
        f'<div><div style="font-size:1.05em;font-weight:700;color:{TEXT};">Your AI Trading Coach</div>'
        f'<div style="font-size:0.75em;color:{TEXT2};margin-top:3px;">Brutally honest · Tracks your patterns · Gets smarter every week</div></div>'
        f'</div>', unsafe_allow_html=True)

    # Date ranges
    today_date = today.date()
    days_since_sunday = (today_date.weekday() + 1) % 7
    last_sunday_date = today_date - pd.Timedelta(days=days_since_sunday)
    last_monday_date = last_sunday_date - pd.Timedelta(days=6)
    week_start = today_date - pd.Timedelta(days=today_date.weekday())

    # Last week trades
    df_lw = df_main.dropna(subset=['Date', 'R_Result']).copy()
    df_lw = df_lw[(df_lw['Date'].dt.date >= last_monday_date) & (df_lw['Date'].dt.date <= last_sunday_date)]

    # This week trades for midweek checkin
    df_tw = df_main.dropna(subset=['Date', 'R_Result']).copy()
    df_tw = df_tw[df_tw['Date'].dt.date >= week_start]

    if 'Risk Management' in df_lw.columns and len(df_lw) > 0:
        avg_rp = pd.to_numeric(df_lw['Risk Management'].str.replace('%', '').str.strip(), errors='coerce').mean()
        if pd.isna(avg_rp): avg_rp = 1.0
    else:
        avg_rp = 1.0

    def lw_pnl(df_s):
        if len(df_s) == 0: return 0
        if 'Risk Management' in df_s.columns:
            rp = pd.to_numeric(df_s['Risk Management'].str.replace('%', '').str.strip(), errors='coerce').fillna(avg_rp)
            return round((df_s['R_Result'].values * rp.values / 100 * account_size * num_accounts).sum(), 2)
        return round(df_s['R_Result'].sum() * avg_rp / 100 * account_size * num_accounts, 2)

    total_v = len(df_lw)
    wins_v = int((df_lw['R_Result'] > 0).sum()) if total_v > 0 else 0
    losses_v = int((df_lw['R_Result'] < 0).sum()) if total_v > 0 else 0
    wr_v = round(wins_v / (wins_v + losses_v) * 100, 1) if (wins_v + losses_v) > 0 else 0
    avg_rr_v = round(df_lw['R_Result'].mean(), 2) if total_v > 0 else 0

    # Week stats banner
    st.markdown(
        f'<div class="coach-card" style="background:{BG2};border-radius:16px;padding:20px 24px;margin-bottom:16px;display:grid;grid-template-columns:repeat(3,1fr);gap:0;animation-delay:0.1s;">'
        f'<div style="text-align:center;border-right:1px solid {BORDER};"><div style="font-size:1.6em;font-weight:800;color:{TEXT};">{total_v}</div><div style="font-size:0.58em;color:{TEXT2};margin-top:4px;text-transform:uppercase;letter-spacing:0.8px;">Trades</div></div>'
        f'<div style="text-align:center;border-right:1px solid {BORDER};"><div style="font-size:1.6em;font-weight:800;color:{TEXT};">{wr_v}%</div><div style="font-size:0.58em;color:{TEXT2};margin-top:4px;text-transform:uppercase;letter-spacing:0.8px;">Win Rate</div></div>'
        f'<div style="text-align:center;"><div style="font-size:1.6em;font-weight:800;color:{TEXT};">{avg_rr_v}R</div><div style="font-size:0.58em;color:{TEXT2};margin-top:4px;text-transform:uppercase;letter-spacing:0.8px;">Avg RR</div></div>'
        f'</div>', unsafe_allow_html=True)

    # Best/worst trade
    if total_v > 0:
        bt = df_lw.loc[df_lw['R_Result'].idxmax()]
        wt = df_lw.loc[df_lw['R_Result'].idxmin()]
        tw1, tw2 = st.columns(2)
        with tw1:
            bt_r = bt.get('R_Result', 0)
            bt_pair = bt.get('Pair', '?')
            bt_session = bt.get('3SL Window', '?')
            bt_date = bt['Date'].strftime('%b %d') if pd.notna(bt['Date']) else '?'
            st.markdown(
                f'<div class="coach-card" style="background:rgba(74,222,128,0.04);border:1px solid rgba(74,222,128,0.12);border-radius:14px;padding:16px;animation-delay:0.2s;">'
                f'<div style="font-size:0.58em;color:#4ade80;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">↑ Best Trade</div>'
                f'<div style="font-size:0.88em;font-weight:600;color:{TEXT};">{bt_pair} · {bt_session}</div>'
                f'<div style="font-size:0.7em;color:{TEXT2};margin-top:3px;">{bt_date}</div>'
                f'<div style="font-size:1.05em;font-weight:700;color:#4ade80;margin-top:8px;">+{bt_r}R</div>'
                f'</div>', unsafe_allow_html=True)
        with tw2:
            wt_r = wt.get('R_Result', 0)
            wt_pair = wt.get('Pair', '?')
            wt_session = wt.get('3SL Window', '?')
            wt_date = wt['Date'].strftime('%b %d') if pd.notna(wt['Date']) else '?'
            st.markdown(
                f'<div class="coach-card" style="background:rgba(248,113,113,0.04);border:1px solid rgba(248,113,113,0.12);border-radius:14px;padding:16px;animation-delay:0.25s;">'
                f'<div style="font-size:0.58em;color:#f87171;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">↓ Worst Trade</div>'
                f'<div style="font-size:0.88em;font-weight:600;color:{TEXT};">{wt_pair} · {wt_session}</div>'
                f'<div style="font-size:0.7em;color:{TEXT2};margin-top:3px;">{wt_date}</div>'
                f'<div style="font-size:1.05em;font-weight:700;color:#f87171;margin-top:8px;">{wt_r}R</div>'
                f'</div>', unsafe_allow_html=True)

    # Mid-week check-in
    st.markdown(f'<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
    if len(df_tw) > 0:
        st.markdown(f'<div class="v3-section">Mid-Week Check-in</div>', unsafe_allow_html=True)
        midweek_col, _ = st.columns([1, 3])
        with midweek_col:
            midweek_btn = st.button("💬  Get Mid-Week Update", key="midweek_btn", use_container_width=True)
        if midweek_btn:
            if not anthropic_api_key:
                st.error("Add your ANTHROPIC_API_KEY to Streamlit secrets.")
            else:
                with st.spinner("Coach is checking in..."):
                    try:
                        result = call_midweek_api(df_tw, st.session_state.coach_profile, num_accounts, account_size, anthropic_api_key)
                        if result:
                            st.session_state.midweek_checkin = result
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        if st.session_state.get('midweek_checkin'):
            mc = st.session_state.midweek_checkin
            st.markdown(
                f'<div style="background:{BG2};border-radius:14px;padding:20px;border-left:3px solid {ACCENT};margin-top:12px;">'
                f'<div style="font-size:0.58em;color:{TEXT2};font-weight:600;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Coach · Mid-Week · {len(df_tw)} trades so far</div>'
                f'<div style="font-size:0.88em;color:{TEXT};line-height:1.8;">{mc.get("checkin","")}</div>'
                f'<div style="margin-top:12px;padding-top:12px;border-top:1px solid {BORDER};font-size:0.82em;color:{ACCENT};">→ {mc.get("focus","")}</div>'
                f'</div>', unsafe_allow_html=True)

    # Run debrief
    st.markdown(f'<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
    run_col, _ = st.columns([1, 3])
    with run_col:
        run_btn = st.button("⚡  Run Weekly Debrief", key="run_debrief", use_container_width=True)

    if run_btn:
        if total_v == 0:
            st.markdown(f'<div style="background:{BG2};border-radius:14px;padding:20px;color:{TEXT2};font-size:0.88em;margin-top:12px;">No trades found for last week ({last_monday_date.strftime("%b %d")} – {last_sunday_date.strftime("%b %d")}). Log some trades and come back!</div>', unsafe_allow_html=True)
        elif not anthropic_api_key:
            st.error("Add your ANTHROPIC_API_KEY to Streamlit secrets to enable Coach.")
        else:
            with st.spinner("Coach is reviewing your week..."):
                try:
                    result = call_coach_api(df_lw, st.session_state.coach_profile, num_accounts, account_size, anthropic_api_key, df_main)
                    if result:
                        st.session_state.coach_debrief = result
                        if result.get('updated_profile'):
                            st.session_state.coach_profile = result['updated_profile']
                        if result.get('trader_character'):
                            st.session_state.coach_character = result['trader_character']
                        save_coach_memory(headers, coach_memory_page_id, st.session_state.coach_profile, st.session_state.coach_character)
                        st.rerun()
                    else:
                        st.error("Coach couldn't connect. Check your API key.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    cached = st.session_state.coach_debrief
    if cached:
        grade = cached.get('grade', '—')
        grade_reason = cached.get('grade_reason', '')
        grade_color = '#4ade80' if grade in ['A+', 'A'] else ('#fcd34d' if grade in ['B+', 'B'] else ('#f59e0b' if grade in ['C+', 'C'] else '#f87171'))

        st.markdown(
            f'<div class="coach-card" style="background:{BG2};border-radius:16px;padding:20px 24px;margin-bottom:14px;display:flex;align-items:center;gap:16px;animation-delay:0.1s;">'
            f'<div style="font-size:2em;font-weight:800;color:{grade_color};min-width:52px;">{grade}</div>'
            f'<div style="width:1px;height:36px;background:{BORDER};"></div>'
            f'<div style="font-size:0.85em;color:{TEXT2};font-style:italic;line-height:1.5;">{grade_reason}</div>'
            f'</div>', unsafe_allow_html=True)

        debrief_text = cached.get('debrief', '')
        st.markdown(
            f'<div class="coach-message" style="background:{BG2};border-radius:16px;padding:24px;margin-bottom:14px;border-left:3px solid {ACCENT};">'
            f'<div style="font-size:0.58em;color:{TEXT2};font-weight:600;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:14px;">Coach · Weekly Debrief · {last_monday_date.strftime("%b %d")} – {last_sunday_date.strftime("%b %d")}</div>'
            f'<div style="color:{TEXT};line-height:1.85;font-size:0.92em;">{debrief_text}</div>'
            f'</div>', unsafe_allow_html=True)

        fps = cached.get('focus_points', [])
        if fps:
            st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:20px 0 10px;">Your {len(fps)} Focus Points This Week</div>', unsafe_allow_html=True)
            for i, fp in enumerate(fps):
                st.markdown(
                    f'<div class="focus-item" style="background:{BG2};border-radius:12px;padding:14px 16px;margin-bottom:8px;display:flex;gap:14px;align-items:flex-start;animation-delay:{i*80}ms;">'
                    f'<div style="width:26px;height:26px;border-radius:50%;background:rgba({RGB},0.08);border:1px solid rgba({RGB},0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:0.72em;font-weight:700;color:{ACCENT};">{i+1}</div>'
                    f'<div style="font-size:0.85em;color:{TEXT};line-height:1.7;">{fp}</div>'
                    f'</div>', unsafe_allow_html=True)

        action = cached.get('action_plan', '')
        if action:
            st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:20px 0 10px;">Action Plan</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="focus-item" style="background:rgba({RGB},0.04);border:1px solid rgba({RGB},0.1);border-radius:12px;padding:16px;margin-bottom:8px;">'
                f'<div style="font-size:0.88em;color:{TEXT};line-height:1.7;">→ {action}</div>'
                f'</div>', unsafe_allow_html=True)

        patterns = [p for p in cached.get('behavioral_patterns', []) if p]
        if patterns:
            st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:20px 0 10px;">Behavioral Patterns</div>', unsafe_allow_html=True)
            for i, p in enumerate(patterns):
                st.markdown(
                    f'<div class="pattern-item" style="background:rgba(252,211,77,0.03);border:1px solid rgba(252,211,77,0.1);border-radius:12px;padding:14px 16px;margin-bottom:8px;animation-delay:{i*80}ms;">'
                    f'<div style="font-size:0.85em;color:{TEXT};line-height:1.7;">{p}</div>'
                    f'</div>', unsafe_allow_html=True)

        red_flags = [r for r in cached.get('red_flags', []) if r]
        if red_flags:
            st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:20px 0 10px;">Red Flags</div>', unsafe_allow_html=True)
            for i, rf in enumerate(red_flags):
                st.markdown(
                    f'<div class="pattern-item" style="background:rgba(248,113,113,0.03);border:1px solid rgba(248,113,113,0.1);border-radius:12px;padding:14px 16px;margin-bottom:8px;animation-delay:{i*80}ms;">'
                    f'<div style="font-size:0.85em;color:{TEXT};line-height:1.7;">⚠ {rf}</div>'
                    f'</div>', unsafe_allow_html=True)

        st.markdown(f'<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
        if st.button("↺  Clear & Re-run", key="clear_debrief", use_container_width=False):
            st.session_state.coach_debrief = None
            st.rerun()

    elif total_v > 0 and not cached:
        st.markdown(
            f'<div style="background:{BG2};border-radius:14px;padding:24px;text-align:center;margin-top:12px;">'
            f'<div style="font-size:0.92em;color:{TEXT};font-weight:600;margin-bottom:6px;">Last week: {total_v} trades · {wr_v}% WR</div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="background:{BG2};border-radius:14px;padding:32px;text-align:center;margin-top:12px;">'
            f'<div style="font-size:1.2em;margin-bottom:10px;">⚡</div>'
            f'<div style="font-size:0.92em;color:{TEXT};font-weight:600;margin-bottom:6px;">No trades last week</div>'
            f'<div style="font-size:0.75em;color:{TEXT2};">Keep logging trades in Notion — Coach will analyse them every Sunday</div>'
            f'</div>', unsafe_allow_html=True)

    # Always show character and profile
    character = st.session_state.coach_character
    if character and isinstance(character, dict):
        title = character.get('title', '—')
        tier = character.get('tier', 'B')
        desc = character.get('desc', '')
        stats = character.get('stats', {'patience': 50, 'discipline': 50, 'edge': 50})
        patience = stats.get('patience', 50)
        discipline = stats.get('discipline', 50)
        edge = stats.get('edge', 50)
        tier_colors = {'S': '#fcd34d', 'A': '#a78bfa', 'B': '#60a5fa', 'C': '#4ade80', 'D': '#f59e0b', 'F': '#f87171'}
        tier_labels = {'S': 'S Tier · Elite', 'A': 'A Tier · Disciplined', 'B': 'B Tier · Developing', 'C': 'C Tier · Potential', 'D': 'D Tier · Struggling', 'F': 'F Tier · Reset Required'}
        char_color = tier_colors.get(tier, '#94a3b8')
        tier_label = tier_labels.get(tier, 'Unknown')

        st.markdown(f'<div style="font-size:0.65em;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin:24px 0 12px;">Trader Character</div>', unsafe_allow_html=True)
        char_html = (
            "<!DOCTYPE html><html><head>"
            "<style>"
            "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');"
            "@keyframes revealTitle{0%{opacity:0;letter-spacing:20px;transform:scale(0.88);}60%{opacity:1;letter-spacing:6px;transform:scale(1.04);}100%{opacity:1;letter-spacing:4px;transform:scale(1);}}"
            "@keyframes scanLine{from{top:0;opacity:0.8;}to{top:100%;opacity:0;}}"
            "@keyframes tierBadge{from{opacity:0;transform:scale(0.7);}to{opacity:1;transform:scale(1);}}"
            "@keyframes charFadeUp{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}"
            f"@keyframes charGlow{{0%,100%{{box-shadow:0 0 0 rgba(0,0,0,0);}}50%{{box-shadow:0 0 30px {char_color}33;}}}}"
            "body{margin:0;padding:0;background:transparent;font-family:'Inter',sans-serif;}"
            f".char-card{{position:relative;overflow:hidden;background:rgba(255,255,255,0.02);border:1px solid {char_color}40;border-radius:20px;padding:32px 28px;text-align:center;animation:charGlow 3s ease-in-out infinite;}}"
            f".char-scan{{position:absolute;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,{char_color},transparent);animation:none;}}"
            f".char-tier-badge{{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.03);border:1px solid {char_color}40;border-radius:6px;padding:4px 12px;font-size:0.55em;font-weight:700;color:{char_color};letter-spacing:2px;text-transform:uppercase;animation:tierBadge 0.6s cubic-bezier(0.16,1,0.3,1) 0.1s both;animation-play-state:paused;margin-bottom:16px;}}"
            f".char-title{{font-size:2.4em;font-weight:900;background:linear-gradient(135deg,#fff 30%,{char_color});-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px;text-transform:uppercase;animation:revealTitle 1.4s cubic-bezier(0.16,1,0.3,1) 0.3s both;animation-play-state:paused;}}"
            f".char-divider{{width:48px;height:2px;background:{char_color};margin:16px auto;opacity:0.4;animation:charFadeUp 0.5s ease 1.2s both;animation-play-state:paused;}}"
            ".char-desc{font-size:0.82em;color:rgba(255,255,255,0.4);font-style:italic;line-height:1.7;animation:charFadeUp 0.8s ease 1.3s both;animation-play-state:paused;max-width:340px;margin:0 auto;}"
            ".char-stats{display:flex;justify-content:center;gap:24px;margin-top:20px;animation:charFadeUp 0.6s ease 1.6s both;animation-play-state:paused;}"
            ".char-stat{text-align:center;}"
            ".char-stat-label{font-size:0.48em;color:rgba(255,255,255,0.2);text-transform:uppercase;letter-spacing:1px;margin-bottom:5px;}"
            ".char-stat-bar-bg{width:64px;height:3px;background:rgba(255,255,255,0.06);border-radius:2px;}"
            f".char-stat-bar-fill{{height:3px;background:{char_color};border-radius:2px;}}"
            "</style></head><body>"
            "<div class='char-card'>"
            "<div class='char-scan'></div>"
            f"<div class='char-tier-badge'>&#x2B23; {tier_label}</div>"
            f"<div class='char-title'>{title}</div>"
            "<div class='char-divider'></div>"
            f"<div class='char-desc'>{desc}</div>"
            "<div class='char-stats'>"
            f"<div class='char-stat'><div class='char-stat-label'>Patience</div><div class='char-stat-bar-bg'><div class='char-stat-bar-fill' style='width:{patience}%;'></div></div></div>"
            f"<div class='char-stat'><div class='char-stat-label'>Discipline</div><div class='char-stat-bar-bg'><div class='char-stat-bar-fill' style='width:{discipline}%;'></div></div></div>"
            f"<div class='char-stat'><div class='char-stat-label'>Edge</div><div class='char-stat-bar-bg'><div class='char-stat-bar-fill' style='width:{edge}%;'></div></div></div>"
            "</div></div>"
            "<script>"
            "setTimeout(function(){"
            "var card=document.querySelector('.char-card');"
            "if(!card)return;"
            "var obs=new IntersectionObserver(function(entries){"
            "entries.forEach(function(e){"
            "if(e.isIntersecting){"
            "var scan=card.querySelector('.char-scan');"
            "if(scan)scan.style.animation='scanLine 1.5s ease 0.2s forwards';"
            "var animated=card.querySelectorAll('.char-tier-badge,.char-title,.char-divider,.char-desc,.char-stats');"
            "animated.forEach(function(el){el.style.animationPlayState='running';});"
            "obs.unobserve(e.target);}});},{threshold:0.3});"
            "obs.observe(card);"
            "},300);"
            "</script></body></html>"
        )
        components.html(char_html, height=280)

        # Tier rankings
        with st.expander("Tier Rankings"):
            tier_data = [
                ('S', '#fcd34d', 'Elite · Rare unlock', ['The Phantom', 'The Oracle', 'The Legend']),
                ('A', '#a78bfa', 'Disciplined · Precise', ['The Sniper', 'The Ghost', 'The Assassin', 'The Architect']),
                ('B', '#60a5fa', 'Developing · Solid', ['The Maverick', 'The Commander', 'The Grinder', 'The Titan']),
                ('C', '#4ade80', 'Potential · Inconsistent', ['The Prodigy', 'The Survivor']),
                ('D', '#f59e0b', 'Struggling', ['The Wild Card', 'The Apprentice', 'The Berserker']),
                ('F', '#f87171', 'Reset required', ['The Warmonger']),
            ]
            for t_tier, t_color, t_desc, t_names in tier_data:
                is_active = t_tier == tier
                names_html = ''
                for n in t_names:
                    is_cur = n == title
                    if is_cur:
                        names_html += f'<span style="color:{t_color};font-weight:700;">{n}</span>'
                    else:
                        names_html += f'<span style="color:rgba(255,255,255,0.3);">{n}</span>'
                    names_html += ' · '
                names_html = names_html.rstrip(' · ')
                you_badge = f'<span style="font-size:0.5em;color:{t_color};font-weight:700;background:rgba(255,255,255,0.06);border-radius:4px;padding:2px 6px;margin-left:8px;">You</span>' if is_active else ''
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid {BORDER};{"background:rgba(255,255,255,0.02);border-radius:6px;padding:10px 8px;" if is_active else ""}">'
                    f'<div style="width:4px;height:24px;border-radius:2px;background:{t_color};{"box-shadow:0 0 8px "+t_color+";" if is_active else ""}flex-shrink:0;"></div>'
                    f'<div style="font-size:0.75em;font-weight:800;color:{t_color};min-width:20px;">{t_tier}</div>'
                    f'<div style="font-size:0.62em;flex:1;">{names_html}</div>'
                    f'{you_badge}'
                    f'</div>', unsafe_allow_html=True)

    # Trader profile
    profile = st.session_state.coach_profile
    if profile:
        st.markdown(f'<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
        with st.expander("Your Trader Profile"):
            st.markdown(f'<div style="font-size:0.85em;color:{TEXT2};line-height:1.85;padding:8px 0;">{profile}</div>', unsafe_allow_html=True)
