# ============ CONSTANTS ============
ACCOUNT_SIZE = 50000
COACH_MEMORY_PAGE_ID = "3a4c0c4c46ff8044b44ee780f7a0c6d8"
TRADER_NAME = "Kaea"

THEMES = {
    'Blue':    {'ACCENT': '#60a5fa', 'ACCENT_SOFT': '#93c5fd', 'RGB': '96,165,250'},
    'Purple':  {'ACCENT': '#a78bfa', 'ACCENT_SOFT': '#c4b5fd', 'RGB': '167,139,250'},
    'Green':   {'ACCENT': '#34d399', 'ACCENT_SOFT': '#6ee7b7', 'RGB': '52,211,153'},
    'Gold':    {'ACCENT': '#fcd34d', 'ACCENT_SOFT': '#fde68a', 'RGB': '252,211,77'},
    'Neutral': {'ACCENT': '#94a3b8', 'ACCENT_SOFT': '#cbd5e1', 'RGB': '148,163,184'},
}

RANK_COLORS = ['#fcd34d', '#94a3b8', '#64748b']
GOLD = '#f59e0b'
GOLD_S = '#fcd34d'
PURPLE_C = '#a78bfa'
PURPLE_S = '#c4b5fd'

def get_colors(theme_name, is_dark):
    T = THEMES.get(theme_name, THEMES['Neutral'])
    if is_dark:
        c = {
            'BG': '#070b14', 'BG2': 'rgba(255,255,255,0.03)', 'BG3': 'rgba(255,255,255,0.05)',
            'TEXT': '#ffffff', 'TEXT2': 'rgba(255,255,255,0.45)', 'TEXT3': 'rgba(255,255,255,0.2)',
            'BORDER': 'rgba(255,255,255,0.06)', 'BORDER2': 'rgba(255,255,255,0.08)',
            'SIDEBAR': 'rgba(255,255,255,0.02)', 'SIDEBAR_B': 'rgba(255,255,255,0.05)',
            'SHADOW': 'rgba(0,0,0,0.3)',
        }
    else:
        c = {
            'BG': '#f8f9fa', 'BG2': 'rgba(0,0,0,0.02)', 'BG3': 'rgba(0,0,0,0.04)',
            'TEXT': '#0f172a', 'TEXT2': 'rgba(0,0,0,0.4)', 'TEXT3': 'rgba(0,0,0,0.15)',
            'BORDER': 'rgba(0,0,0,0.05)', 'BORDER2': 'rgba(0,0,0,0.08)',
            'SIDEBAR': 'rgba(0,0,0,0.02)', 'SIDEBAR_B': 'rgba(0,0,0,0.06)',
            'SHADOW': 'rgba(0,0,0,0.08)',
        }
    c.update({
        'ACCENT': T['ACCENT'], 'ACCENT_SOFT': T['ACCENT_SOFT'], 'RGB': T['RGB'],
        'GOLD': GOLD, 'GOLD_S': GOLD_S, 'PURPLE_C': PURPLE_C, 'PURPLE_S': PURPLE_S,
        'RANK_COLORS': RANK_COLORS, 'ACCOUNT_SIZE': ACCOUNT_SIZE,
        'COACH_MEMORY_PAGE_ID': COACH_MEMORY_PAGE_ID, 'TRADER_NAME': TRADER_NAME,
    })
    return c
