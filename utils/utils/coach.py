import requests
import pandas as pd
import json
from datetime import datetime


def build_trade_summary(df_week, num_accounts, account_size):
    if len(df_week) == 0:
        return "No trades logged this week."
    lines = []
    for _, t in df_week.iterrows():
        pair = t.get('Pair', '?')
        r = t.get('R_Result', '?')
        date = t['Date'].strftime('%a %b %d') if pd.notna(t['Date']) else '?'
        session = t.get('3SL Window', '?')
        model = t.get('Entry Model', '?')
        quality = t.get('Trade Quality Rating', '?')
        rules = t.get('Rules Followed? Y/N', '?')
        emotion = t.get('Emotional State Before...', '?')
        teaching = t.get('Teachings/Learning Curve', '')
        pnl = ''
        if 'Risk Management' in t.index and pd.notna(t.get('Risk Management')):
            try:
                rp = float(str(t['Risk Management']).replace('%', '').strip())
                pnl = f"${round(r * rp / 100 * account_size * num_accounts, 2):,.2f}"
            except:
                pass
        line = f"- {date} | {pair} | {session} | {model} | R:{r} {pnl} | Quality:{quality} | Rules:{rules} | Emotion:{emotion}"
        if teaching and str(teaching) not in ['nan', 'None', '']:
            line += f" | Notes:{teaching}"
        lines.append(line)
    return '\n'.join(lines)


def build_alltime_summary(df_all):
    if df_all is None or len(df_all) == 0:
        return ""
    at_r = df_all['R_Result'].dropna()
    at_wins = int((at_r > 0).sum())
    at_losses = int((at_r < 0).sum())
    at_nb = at_wins + at_losses
    at_wr = round(at_wins / at_nb * 100, 1) if at_nb > 0 else 0
    at_total_r = round(at_r.sum(), 2)
    at_avg = round(at_r.mean(), 2)
    at_best = round(at_r.max(), 2)
    at_worst = round(at_r.min(), 2)
    first_date = df_all['Date'].dropna().min().strftime('%b %d %Y') if len(df_all) > 0 else '?'
    return f"""
ALL-TIME HISTORY (from {first_date}):
- Total trades: {len(at_r)} | Win rate: {at_wr}% | Total R: {at_total_r}R | Avg R: {at_avg} | Best: {at_best}R | Worst: {at_worst}R | Wins: {at_wins} | Losses: {at_losses}
"""


def call_coach_api(df_week, profile, num_accounts, account_size, anthropic_api_key, df_all=None):
    week_pnl_val = 0
    if len(df_week) > 0:
        if 'Risk Management' in df_week.columns:
            rp = pd.to_numeric(df_week['Risk Management'].str.replace('%', '').str.strip(), errors='coerce').fillna(1.0)
            week_pnl_val = round((df_week['R_Result'].values * rp.values / 100 * account_size * num_accounts).sum(), 2)
        else:
            week_pnl_val = round(df_week['R_Result'].sum() * 500, 2)

    week_r = round(df_week['R_Result'].sum(), 2) if len(df_week) > 0 else 0
    wins = int((df_week['R_Result'] > 0).sum()) if len(df_week) > 0 else 0
    losses = int((df_week['R_Result'] < 0).sum()) if len(df_week) > 0 else 0
    total = len(df_week)
    wr = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0
    avg_rr = round(df_week['R_Result'].mean(), 2) if len(df_week) > 0 else 0

    trade_summary = build_trade_summary(df_week, num_accounts, account_size)
    alltime_ctx = build_alltime_summary(df_all)
    profile_ctx = f"EXISTING TRADER PROFILE:\n{profile}" if profile else "No prior profile. This is Kaea's first week of analysis."

    prompt = f"""You are Coach, a brutally honest AI trading coach. Your trader's name is Kaea.

{profile_ctx}
{alltime_ctx}
THIS WEEK'S TRADES:
{trade_summary}

WEEK STATS:
- Total trades: {total} | Win rate: {wr}% | Net P&L: ${week_pnl_val:,.2f} | Total R: {week_r}R | Avg RR: {avg_rr} | Wins: {wins} | Losses: {losses}

You are NOT generic. Reference specific trades, dates, patterns, language from notes. Brutally honest with tough love but genuine encouragement where earned.

Respond ONLY in this exact JSON format with no other text:
{{
  "debrief": "4-6 sentences. Specific, personal, brutally honest. Reference actual trades and numbers. End with one genuine encouraging line if earned.",
  "focus_points": [
    "Specific actionable focus point 1 referencing actual trade data",
    "Specific actionable focus point 2",
    "Specific actionable focus point 3"
  ],
  "behavioral_patterns": [
    "Specific pattern observed this week with evidence",
    "Second pattern if exists, otherwise empty string"
  ],
  "red_flags": [
    "Specific red flag with evidence, or empty string if none"
  ],
  "action_plan": "One specific concrete action Kaea must implement next week.",
  "updated_profile": "Updated 4-6 sentence trader profile of Kaea. Specific about tendencies, strengths, leaks, psychological patterns.",
  "grade": "A+/A/B+/B/C+/C/D/F",
  "grade_reason": "One honest sentence explaining the grade.",
  "trader_character": {{
    "title": "Pick ONE title from: The Phantom, The Oracle, The Legend (S - only if truly elite), The Sniper, The Ghost, The Assassin, The Architect (A - disciplined/precise), The Strategist, The Commander, The Grinder, The Titan (B - solid/developing), The Maverick, The Prodigy, The Survivor (C - potential/inconsistent), The Wild Card, The Apprentice, The Berserker (D - struggling), The Warmonger (F - reckless). Be honest.",
    "tier": "S, A, B, C, D, or F",
    "desc": "One punchy sentence max 12 words. Playful but honest.",
    "stats": {{
      "patience": 0,
      "discipline": 0,
      "edge": 0
    }}
  }}
}}"""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": anthropic_api_key,
            "anthropic-version": "2023-06-01"
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    if response.status_code != 200:
        return None

    data = response.json()
    text = data['content'][0]['text'].strip()
    if '```' in text:
        parts = text.split('```')
        text = parts[1] if len(parts) > 1 else text
        if text.startswith('json'):
            text = text[4:]

    return json.loads(text.strip())


def call_midweek_api(df_so_far, profile, num_accounts, account_size, anthropic_api_key):
    if len(df_so_far) == 0:
        return None

    wins = int((df_so_far['R_Result'] > 0).sum())
    losses = int((df_so_far['R_Result'] < 0).sum())
    total = len(df_so_far)
    wr = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0
    total_r = round(df_so_far['R_Result'].sum(), 2)
    trade_summary = build_trade_summary(df_so_far, num_accounts, account_size)
    profile_ctx = f"TRADER PROFILE:\n{profile}" if profile else "No prior profile yet."

    prompt = f"""You are Coach, a brutally honest AI trading coach. Kaea's name is Kaea.

{profile_ctx}

TRADES SO FAR THIS WEEK:
{trade_summary}

WEEK SO FAR: {total} trades | {wr}% WR | {total_r}R total

Give Kaea a quick mid-week check-in. 2-3 sentences max. Be direct and specific. Reference actual trades. No fluff.

Respond in JSON:
{{
  "checkin": "2-3 sentence mid-week update. Specific. Direct. Reference actual trades.",
  "focus": "One thing Kaea must focus on for the rest of the week."
}}"""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": anthropic_api_key,
            "anthropic-version": "2023-06-01"
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    if response.status_code != 200:
        return None

    data = response.json()
    text = data['content'][0]['text'].strip()
    if '```' in text:
        parts = text.split('```')
        text = parts[1] if len(parts) > 1 else text
        if text.startswith('json'):
            text = text[4:]

    return json.loads(text.strip())
