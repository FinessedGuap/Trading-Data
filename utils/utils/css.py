def get_css(c):
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
    SIDEBAR = c['SIDEBAR']
    SIDEBAR_B = c['SIDEBAR_B']
    SHADOW = c['SHADOW']

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
*{{box-sizing:border-box;}}
.stApp{{background:{BG};font-family:'Inter',sans-serif;}}
@keyframes pageIn{{from{{opacity:0;transform:translateY(8px);}}to{{opacity:1;transform:translateY(0);}}}}
@keyframes staggerIn{{from{{opacity:0;transform:translateY(12px) scale(0.98);}}to{{opacity:1;transform:translateY(0) scale(1);}}}}
@keyframes slideInLeft{{from{{opacity:0;transform:translateX(-16px);}}to{{opacity:1;transform:translateX(0);}}}}
@keyframes growBar{{from{{width:0;}}to{{width:100%;}}}}
@keyframes pulseGlow{{0%,100%{{box-shadow:0 0 0 rgba(74,222,128,0);}}50%{{box-shadow:0 0 20px rgba(74,222,128,0.4);}}}}
@keyframes coachGlow{{0%,100%{{box-shadow:0 0 0 rgba({RGB},0);}}50%{{box-shadow:0 0 24px rgba({RGB},0.15);}}}}
@keyframes typingDot{{0%,60%,100%{{transform:translateY(0);opacity:0.4;}}30%{{transform:translateY(-5px);opacity:1;}}}}
@keyframes fadeInUp{{from{{opacity:0;transform:translateY(16px);}}to{{opacity:1;transform:translateY(0);}}}}
.page-content{{animation:pageIn 0.35s cubic-bezier(0.16,1,0.3,1) both;}}
.v3-card{{background:{BG2};border-radius:16px;padding:20px 16px;text-align:center;transition:background 0.2s ease,transform 0.2s ease;cursor:pointer;animation:staggerIn 0.5s cubic-bezier(0.16,1,0.3,1) both;}}
.v3-card:hover{{background:{BG3};transform:translateY(-2px);}}
.v3-val{{font-size:1.5em;font-weight:700;color:{TEXT};}}
.v3-lbl{{font-size:0.6em;color:{TEXT2};margin-top:6px;text-transform:uppercase;letter-spacing:0.8px;font-weight:500;}}
.v3-panel{{background:{BG2};border-radius:20px;padding:24px;margin-bottom:16px;animation:staggerIn 0.5s cubic-bezier(0.16,1,0.3,1) both;}}
.v3-section{{font-size:0.65em;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:{TEXT3};margin:28px 0 14px;display:flex;align-items:center;gap:12px;}}
.v3-section::after{{content:'';flex:1;height:1px;background:{BORDER};}}
.v3-divider{{border:none;border-top:1px solid {BORDER};margin:28px 0;}}
.coach-card{{animation:fadeInUp 0.6s cubic-bezier(0.16,1,0.3,1) both;}}
.coach-avatar{{animation:coachGlow 3s ease-in-out infinite;}}
.coach-message{{animation:fadeInUp 0.8s cubic-bezier(0.16,1,0.3,1) 0.2s both;line-height:1.8;}}
.focus-item{{animation:fadeInUp 0.5s cubic-bezier(0.16,1,0.3,1) both;}}
.pattern-item{{animation:fadeInUp 0.5s cubic-bezier(0.16,1,0.3,1) both;}}
.typing-dot{{display:inline-block;width:5px;height:5px;background:{ACCENT};border-radius:50%;margin:0 2px;animation:typingDot 1.2s ease infinite;}}
.typing-dot:nth-child(2){{animation-delay:0.2s;}}
.typing-dot:nth-child(3){{animation-delay:0.4s;}}
section[data-testid="stSidebar"]{{background:{SIDEBAR} !important;border-right:1px solid {SIDEBAR_B} !important;}}
section[data-testid="stSidebar"]>div{{padding-top:0 !important;}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button{{min-height:40px !important;background:transparent !important;border:none !important;color:{TEXT2} !important;border-radius:8px !important;font-size:0.85em !important;text-align:left !important;padding-left:12px !important;display:flex !important;align-items:center !important;justify-content:flex-start !important;box-shadow:none !important;transition:all 0.15s ease !important;}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button *{{text-align:left !important;justify-content:flex-start !important;}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover{{background:{BG2} !important;color:{TEXT} !important;}}
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"]{{margin:0 !important;padding:0 !important;}}
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p{{margin:0 !important;padding:0 !important;}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[data-testid="baseButton-secondary"]{{min-height:4px !important;max-height:4px !important;opacity:0 !important;overflow:hidden !important;box-shadow:none !important;border:none !important;background:transparent !important;padding:0 !important;margin:0 !important;}}
div[data-testid="stButton"] button{{width:100%;min-height:44px;border-radius:10px;font-family:'Inter',sans-serif;transition:all 0.15s ease;font-weight:500;background:{BG2} !important;border:1px solid {BORDER2} !important;color:{TEXT} !important;box-shadow:none !important;}}
div[data-testid="stButton"] button:hover{{background:{BG3} !important;transform:translateY(-1px);}}
div[data-testid="column"]:first-child div[data-testid="stButton"] button,div[data-testid="column"]:last-child div[data-testid="stButton"] button{{min-height:52px !important;border-radius:12px !important;}}
div[data-testid="stButton"] button[data-testid="mode_toggle"]{{border-radius:50% !important;width:36px !important;height:36px !important;min-height:36px !important;max-width:36px !important;padding:0 !important;font-size:1em !important;}}
.cal-arrows div[data-testid="stButton"] button{{min-height:40px !important;max-height:40px !important;height:40px !important;border-radius:8px !important;padding:0 !important;margin:0 !important;}}
.cal-header{{color:{TEXT2};font-size:0.65em;text-align:center;letter-spacing:1px;font-weight:600;text-transform:uppercase;padding:8px 0;}}
.cal-day-num{{color:{TEXT3};font-size:0.72em;font-weight:600;text-align:center;}}
.streak-box{{width:28px;height:28px;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;margin:2px;animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) both;}}
.streak-box.active{{animation:pulseGlow 2s ease-in-out infinite !important;}}
.grow-bar{{animation:growBar 1.2s cubic-bezier(0.16,1,0.3,1) both;animation-play-state:paused;}}
.checklist-item{{display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-bottom:1px solid {BORDER};animation:slideInLeft 0.4s cubic-bezier(0.16,1,0.3,1) both;}}
.setup-row{{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid {BORDER};animation:staggerIn 0.4s cubic-bezier(0.16,1,0.3,1) both;}}
div[data-testid="stNumberInput"] input{{background:{BG2} !important;border:1px solid {BORDER2} !important;border-radius:8px !important;color:{TEXT} !important;}}
div[data-testid="stNumberInput"] label{{color:{TEXT2} !important;font-size:0.82em !important;}}
</style>
"""
