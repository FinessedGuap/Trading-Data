import pandas as pd
import math


def calc_stats(df_in):
    s = {}
    r = df_in['R_Result'].dropna()
    if len(r) == 0: return s
    s['total_trades'] = len(r)
    s['wins'] = int((r > 0).sum())
    s['losses'] = int((r < 0).sum())
    s['breakevens'] = int((r == 0).sum())
    nb = s['wins'] + s['losses']
    s['win_rate'] = round(s['wins'] / nb * 100, 1) if nb > 0 else 0
    s['total_r'] = round(r.sum(), 2)
    s['avg_r'] = round(r.mean(), 2)
    s['avg_win'] = round(r[r > 0].mean(), 2) if s['wins'] > 0 else 0
    s['avg_loss'] = round(r[r < 0].mean(), 2) if s['losses'] > 0 else 0
    s['best_trade'] = round(r.max(), 2)
    s['worst_trade'] = round(r.min(), 2)
    s['expectancy'] = round(r.sum() / len(r), 2)
    eq = r.cumsum()
    peak = eq.cummax()
    s['max_drawdown'] = round((eq - peak).min(), 2)
    s['equity_curve'] = eq.tolist()
    streak = ms = 0
    for v in r:
        streak = streak + 1 if v < 0 else 0
        ms = max(ms, streak)
    s['max_consec_losses'] = ms
    cur = 0
    ct = None
    for v in reversed(r.tolist()):
        t = 'W' if v > 0 else ('L' if v < 0 else 'B')
        if ct is None: ct = t
        if t == ct: cur += 1
        else: break
    s['cur_streak'] = cur
    s['cur_streak_type'] = ct
    vals = r.tolist()
    rolling = []
    for i in range(len(vals)):
        w = vals[max(0, i - 9):i + 1]
        ww = sum(1 for v in w if v > 0)
        lw = sum(1 for v in w if v < 0)
        rolling.append(round(ww / (ww + lw) * 100, 1) if (ww + lw) > 0 else 0)
    s['rolling_wr'] = rolling
    s['trade_results'] = ['W' if v > 0 else ('L' if v < 0 else 'B') for v in vals]
    return s


def calc_session_stats(df_in):
    if '3SL Window' not in df_in.columns: return []
    df_t = df_in.copy()
    df_t['3SL Window'] = df_t['3SL Window'].fillna('No Window').replace('', 'No Window')
    results = []
    for session in ['Asia', 'London', 'New York', 'No Window']:
        r = df_t[df_t['3SL Window'] == session]['R_Result'].dropna()
        n = len(r)
        if n == 0:
            results.append({'session': session, 'exp': 0, 'wr': 0, 'n': 0})
            continue
        w = int((r > 0).sum())
        l = int((r < 0).sum())
        nb = w + l
        results.append({'session': session, 'exp': round(r.sum() / n, 3), 'wr': round(w / nb, 2) if nb > 0 else 0, 'n': n})
    return sorted(results, key=lambda x: x['exp'], reverse=True)


def calc_daily_r(df_in):
    df_t = df_in.dropna(subset=['Date', 'R_Result']).copy()
    df_t['day'] = df_t['Date'].dt.date
    daily = {}
    for day, row in df_t.groupby('day')['R_Result'].agg(['count', 'sum']).iterrows():
        daily[day] = {'trades': int(row['count']), 'total_r': round(row['sum'], 2)}
    return daily


def calc_monthly_r(df_in):
    df_t = df_in.dropna(subset=['Date', 'R_Result']).copy()
    df_t['month'] = df_t['Date'].dt.to_period('M')
    monthly = {}
    for period, grp in df_t.groupby('month')['R_Result']:
        r = grp
        n = len(r)
        w = int((r > 0).sum())
        nb = w + int((r < 0).sum())
        monthly[str(period)] = {
            'trades': n,
            'total_r': round(r.sum(), 2),
            'win_rate': round(w / nb * 100, 1) if nb > 0 else 0
        }
    return monthly


def calc_dow_stats(df_in):
    df_t = df_in.dropna(subset=['Date', 'R_Result']).copy()
    df_t['dow'] = df_t['Date'].dt.day_name()
    results = []
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        r = df_t[df_t['dow'] == day]['R_Result'].dropna()
        n = len(r)
        if n == 0: continue
        w = int((r > 0).sum())
        l = int((r < 0).sum())
        nb = w + l
        results.append({
            'day': day,
            'short': day[:3],
            'exp': round(r.sum() / n, 2),
            'wr': round(w / nb * 100, 1) if nb > 0 else 0,
            'n': n
        })
    return sorted(results, key=lambda x: x['exp'], reverse=True)


def breakdown_by_col(df_in, col, min_trades=2):
    if col not in df_in.columns: return []
    temp = df_in.dropna(subset=['R_Result', col]).copy()
    temp = temp[temp[col].notna() & (temp[col] != '') & (temp[col] != 'NA') & (temp[col] != 'N/A')]
    results = []
    for val, grp in temp.groupby(col):
        r = grp['R_Result'].dropna()
        n = len(r)
        if n < min_trades: continue
        w = int((r > 0).sum())
        l = int((r < 0).sum())
        nb = w + l
        results.append({
            'label': str(val),
            'wr': round(w / nb * 100, 1) if nb > 0 else 0,
            'exp': round(r.sum() / n, 2),
            'n': n
        })
    return sorted(results, key=lambda x: x['exp'], reverse=True)


def get_best(df_in, col):
    data = breakdown_by_col(df_in, col, min_trades=2)
    return data[0] if data else None


def calc_consistency_score(df_in, session_stats):
    scores = []
    if 'Trade Quality Rating' in df_in.columns:
        temp = df_in.dropna(subset=['Trade Quality Rating'])
        aplus = temp[temp['Trade Quality Rating'].str.contains('A\\+', na=False, regex=True)]
        if len(temp) > 0: scores.append(('A+ quality trades', round(len(aplus) / len(temp) * 100)))
    if 'Rules Followed? Y/N' in df_in.columns:
        temp = df_in.dropna(subset=['Rules Followed? Y/N'])
        yes = temp[temp['Rules Followed? Y/N'].str.lower().str.startswith('yes', na=False)]
        if len(temp) > 0: scores.append(('Rules followed', round(len(yes) / len(temp) * 100)))
    if session_stats:
        best = max(session_stats, key=lambda x: x['exp'])
        if '3SL Window' in df_in.columns:
            temp = df_in.dropna(subset=['3SL Window', 'R_Result'])
            in_best = temp[temp['3SL Window'] == best['session']]
            if len(temp) > 0: scores.append((f"In {best['session']} session", round(len(in_best) / len(temp) * 100)))
    if 'Emotional State Before...' in df_in.columns:
        temp = df_in.dropna(subset=['Emotional State Before...'])
        conf = temp[temp['Emotional State Before...'].str.lower().str.contains('confident', na=False)]
        if len(temp) > 0: scores.append(('Confident entries', round(len(conf) / len(temp) * 100)))
    overall = round(sum(s[1] for s in scores) / len(scores)) if scores else 0
    return overall, scores


def find_best_setup(df_in):
    cols = ['3SL Window', 'Entry Confluences', 'Entry Model Timeframe', 'Double Confirmation', 'Target']
    best_combos = []
    for col in [c for c in cols if c in df_in.columns]:
        data = breakdown_by_col(df_in, col, min_trades=2)
        if data and data[0]['exp'] > 0:
            best_combos.append({
                'col': col,
                'label': data[0]['label'],
                'wr': data[0]['wr'],
                'exp': data[0]['exp'],
                'n': data[0]['n']
            })
    if not best_combos: return None
    return {
        'combos': best_combos,
        'overall_wr': round(sum(b['wr'] for b in best_combos) / len(best_combos), 1),
        'overall_exp': round(sum(b['exp'] for b in best_combos) / len(best_combos), 2)
    }


def generate_checklist(df_in, session_stats):
    green = []
    red = []
    for col, label in [
        ('Entry Model', 'entry model'),
        ('Entry Model Timeframe', 'timeframe'),
        ('Double Confirmation', 'double confirmation'),
        ('Target', 'target'),
        ('Stop Loss Logic', 'stop loss'),
        ('Entry + Confirmation', 'rejection candle'),
        ('Trade Quality Rating', 'trade quality'),
        ('Entry Confluences', 'entry confluence'),
        ('Conditions MTF/HTF', 'market conditions')
    ]:
        data = breakdown_by_col(df_in, col, min_trades=2)
        if data and data[0]['exp'] > 0:
            green.append({
                'label': f"Use {data[0]['label']} for {label}",
                'detail': f"{data[0]['exp']}R avg · {data[0]['wr']}% WR · {data[0]['n']} trades"
            })
    if session_stats:
        best_s = max(session_stats, key=lambda x: x['exp'])
        if best_s['exp'] > 0:
            green.append({
                'label': f"Trade {best_s['session']} session",
                'detail': f"{best_s['exp']}R avg · {round(best_s['wr'] * 100)}% WR · {best_s['n']} trades"
            })
        for s in session_stats:
            if s['exp'] < 0 or s['wr'] < 0.4:
                red.append({
                    'label': f"Avoid {s['session']} session",
                    'detail': f"{s['exp']}R avg · {round(s['wr'] * 100)}% WR · {s['n']} trades"
                })
    for col, wr_thresh, tmpl in [
        ('Emotional State Before...', 45, "Avoid trading when {}"),
        ('Trade Quality Rating', 45, "Avoid {} quality trades"),
        ('News Proximity', 45, "Avoid trading {}"),
        ('Entry Model', 45, "Avoid {} entry model"),
        ('Conditions MTF/HTF', 45, "Avoid trading in {} conditions"),
        ('Stop Loss Logic', 45, "Avoid {} stop loss"),
        ('Target', 45, "Avoid {} as target")
    ]:
        if col in df_in.columns:
            for d in breakdown_by_col(df_in, col, min_trades=2):
                if d['exp'] < 0 or d['wr'] < wr_thresh:
                    red.append({
                        'label': tmpl.format(d['label']),
                        'detail': f"{d['exp']}R avg · {d['wr']}% WR · {d['n']} trades"
                    })
    return green, red


def catmull(pts):
    if len(pts) < 2: return ""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f} "
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1x = p1[0] + (p2[0] - p0[0]) / 6
        c1y = p1[1] + (p2[1] - p0[1]) / 6
        c2x = p2[0] - (p3[0] - p1[0]) / 6
        c2y = p2[1] - (p3[1] - p1[1]) / 6
        d += f"C{c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {p2[0]:.1f},{p2[1]:.1f} "
    return d


def make_curve(eq, w, h):
    if not eq: return "", ""
    mn = min(min(eq), 0)
    mx = max(eq)
    rng = (mx - mn) if (mx - mn) != 0 else 1
    n = len(eq)
    pts = [((i / (n - 1)) * w if n > 1 else 0, h - ((v - mn) / rng) * (h - 20) - 10) for i, v in enumerate(eq)]
    line = catmull(pts)
    return line, line + f"L{w},{h} L0,{h} Z"


def build_donut(wins, losses, bes, colors, glow, bg2, text2):
    total = wins + losses + bes if wins + losses + bes > 0 else 1
    cx = cy = 110
    ro = 95
    ri = 60
    sa = -90
    arcs = ""
    legend = ""
    for label, val, color in [('Win', wins, colors[0]), ('Loss', losses, colors[1]), ('BE', bes, colors[2])]:
        if val == 0: continue
        frac = val / total
        sw = frac * 360
        ea = sa + sw
        def polar(r, a):
            rad = math.radians(a)
            return cx + r * math.cos(rad), cy + r * math.sin(rad)
        x1o, y1o = polar(ro, sa)
        x2o, y2o = polar(ro, ea)
        x1i, y1i = polar(ri, ea)
        x2i, y2i = polar(ri, sa)
        la = 1 if sw > 180 else 0
        arcs += f'<path d="M{x1o:.1f},{y1o:.1f} A{ro},{ro} 0 {la} 1 {x2o:.1f},{y2o:.1f} L{x1i:.1f},{y1i:.1f} A{ri},{ri} 0 {la} 0 {x2i:.1f},{y2i:.1f} Z" fill="{color}" opacity="0.9"/>'
        legend += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><div style="width:8px;height:8px;border-radius:50%;background:{color};"></div><span style="color:{text2};font-size:0.82em;">{label}</span><span style="color:{color};font-weight:700;margin-left:auto;">{round(frac * 100)}%</span></div>'
        sa = ea
    fid = f"dg{colors[0].replace('#', '')}"
    svg = f'<svg viewBox="0 0 220 220" style="width:160px;height:160px;display:block;"><defs><filter id="{fid}"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><g filter="url(#{fid})">{arcs}</g><circle cx="{cx}" cy="{cy}" r="{ri - 4}" fill="{bg2}"/></svg>'
    return svg, legend
