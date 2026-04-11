"""
Generate Chinese reference images for TTS 40K mod:
1. wall_cn_keyword_ref.png - Keyword Reference (關鍵字參考)
2. wall_cn_core_stratagems.png - Core Stratagems Reference (核心詭計參考)
3. wall_cn_combat_patrol.png - Combat Patrol Missions (戰鬥巡邏任務)
"""

from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

# --- Font setup ---
FONT_DIR = "C:/Windows/Fonts"
# Use Microsoft JhengHei (微軟正黑體) for Traditional Chinese
FONT_BOLD = os.path.join(FONT_DIR, "msjhbd.ttc")
FONT_REGULAR = os.path.join(FONT_DIR, "msjh.ttc")
FONT_LIGHT = os.path.join(FONT_DIR, "msjhl.ttc")

def get_font(size, bold=False, light=False):
    path = FONT_BOLD if bold else (FONT_LIGHT if light else FONT_REGULAR)
    return ImageFont.truetype(path, size)

# --- Colors ---
BG_COLOR = (30, 30, 30)          # Dark background
TITLE_BG = (45, 45, 45)         # Title bar background
TEXT_COLOR = (230, 230, 230)     # Main text
KEYWORD_COLOR = (255, 200, 60)  # Keyword name - gold
PHASE_COLOR = (100, 180, 255)   # Phase indicator - blue
CP_COLOR = (255, 100, 100)      # CP cost - red
DIVIDER_COLOR = (80, 80, 80)    # Divider lines
CATEGORY_COLORS = {
    "BATTLE_TACTIC": (80, 200, 80),    # Green
    "EPIC_DEED": (255, 180, 60),       # Orange
    "STRATEGIC_PLOY": (100, 160, 255), # Blue
    "WARGEAR": (200, 100, 255),        # Purple
}
SECTION_BG = (40, 40, 40)


def draw_rounded_rect(draw, xy, fill, radius=8):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.pieslice([x0, y0, x0 + 2*radius, y0 + 2*radius], 180, 270, fill=fill)
    draw.pieslice([x1 - 2*radius, y0, x1, y0 + 2*radius], 270, 360, fill=fill)
    draw.pieslice([x0, y1 - 2*radius, x0 + 2*radius, y1], 90, 180, fill=fill)
    draw.pieslice([x1 - 2*radius, y1 - 2*radius, x1, y1], 0, 90, fill=fill)


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width pixels."""
    words = text
    lines = []
    current_line = ""
    # For Chinese text, wrap character by character when needed
    for char in text:
        test = current_line + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current_line:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test
    if current_line:
        lines.append(current_line)
    return lines


# =============================================================
# 1. KEYWORD REFERENCE (關鍵字參考)
# =============================================================
def generate_keyword_reference():
    keywords = [
        ("反-<關鍵字> X+", "ANTI-<KEYWORD> X+",
         "對指定關鍵字單位進行傷害骰時，擲出X+即為致命傷害(CRITICAL WOUND)。\n例：反-載具 3+ 對載具單位傷害骰擲3+即致命傷害。"),
        ("突擊", "ASSAULT",
         "可在推進(Advance)後射擊。"),
        ("爆破", "BLAST",
         "目標單位每5個模型（無條件捨去），攻擊次數+1。不可對在接戰範圍內的單位射擊。"),
        ("轉化 X", "CONVERSION X",
         "若模型距離目標超過X\"，未修正命中骰4+即為致命命中(CRITICAL HIT)。"),
        ("致命命中", "CRITICAL HITS",
         "未修正命中骰6。必定成功。"),
        ("致命傷害", "CRITICAL WOUNDS",
         "未修正傷害骰6。必定成功。"),
        ("殉爆 X", "DEADLY DEMISE X",
         "此模型被摧毀時擲1D6，擲出6則6\"內每個單位承受X點致命傷(Mortal Wounds)。"),
        ("深入打擊", "DEEP STRIKE",
         "可部署至預備隊而非戰場。須距離所有敵方模型水平9\"以上。"),
        ("拼死突圍", "DESPERATE ESCAPE",
         "戰意動搖後撤退時，或穿越敵方模型撤退時，為單位中每個模型擲骰，1或2則移除一個模型。"),
        ("毀滅性傷害", "DEVASTATING WOUNDS",
         "此武器造成的致命傷害(CRITICAL WOUND)不可進行豁免投擲（包含不屈豁免）。"),
        ("額外攻擊", "EXTRA ATTACKS",
         "近戰時可用此武器進行列出數量的額外攻擊。此數量不可被其他規則修改。"),
        ("無視苦痛 X+", "FEEL NO PAIN X+",
         "此模型每次將失去一點生命時，擲1D6：結果≥X則該傷害不生效。"),
        ("先制攻擊", "FIGHT FIRST",
         "具此能力的合格單位在「先制攻擊步驟」進行近戰（須單位所有模型皆有此能力）。"),
        ("射擊甲板 X", "FIRING DECK X",
         "允許X個搭載於運輸載具的模型向外射擊。"),
        ("飛行", "FLY",
         "一般移動、推進、撤退或衝鋒時可飛越敵方模型。移動距離沿空中計算。"),
        ("危險", "HAZARDOUS",
         "射擊/近戰結束後，每個使用此武器的模型進行危險測試，骰1則該模型被摧毀。角色、巨獸、載具改為承受3點致命傷。"),
        ("重型", "HEAVY",
         "持有者單位保持靜止時，命中+1。"),
        ("無視掩護", "IGNORES COVER",
         "此武器的攻擊不允許目標獲得掩護效益。"),
        ("間接射擊", "INDIRECT FIRE",
         "可射擊不可見的模型。若如此做，命中-1，且目標獲得掩護效益。"),
        ("滲透者", "INFILTRATORS",
         "可部署在己方部署區外。須距離敵方模型及敵方部署區9\"以上。"),
        ("長槍", "LANCE",
         "衝鋒時傷害骰+1。"),
        ("致命命中傳導", "LETHAL HITS",
         "致命命中(CRITICAL HIT)自動造成傷害，無需傷害骰。"),
        ("領袖", "LEADER",
         "具領袖能力的角色單位可在戰前附屬於其護衛單位。附屬單位只能有一個領袖。攻擊不可分配至附屬單位中的角色模型。"),
        ("熔融 X", "MELTA X",
         "在半射程內射擊時，傷害值+X。"),
        ("目標控制值 (OC)", "OBJECTIVE CONTROL",
         "表示模型控制目標標記的效力。"),
        ("單發", "ONE SHOT",
         "此武器每場戰鬥只能發射一次。"),
        ("手槍", "PISTOL",
         "可在接戰範圍內射擊，但須以接戰範圍內的敵方單位為目標。不可與非手槍武器同時射擊（巨獸/載具除外）。"),
        ("精確打擊", "PRECISION",
         "瞄準附屬單位時，可將攻擊分配至可見的角色模型。"),
        ("快速展開", "RAPID DEPLOYMENT",
         "模型推進後仍可下車。下車的單位不可衝鋒，但可正常行動。"),
        ("速射 X", "RAPID FIRE X",
         "目標在半射程內時，攻擊次數+X。"),
        ("斥候 X", "SCOUT X",
         "部署階段後的預先移動X\"。若搭載斥候單位，專屬運輸亦獲得此能力。須距離敵方模型水平9\"以上。"),
        ("隱匿", "STEALTH",
         "若單位所有模型皆有此能力，被遠程攻擊時命中-1。"),
        ("持續命中 X", "SUSTAINED HITS X",
         "致命命中(CRITICAL HIT)額外產生X次命中。"),
        ("洪流", "TORRENT",
         "此武器的攻擊自動命中。"),
        ("雙聯", "TWIN-LINKED",
         "可重擲傷害骰。"),
    ]

    W = 1200
    MARGIN = 40
    COL_GAP = 30
    col_w = (W - 2 * MARGIN - COL_GAP) // 2

    # Pre-calculate height
    title_h = 80
    item_spacing = 8
    font_keyword = get_font(20, bold=True)
    font_en = get_font(13, light=True)
    font_desc = get_font(15)

    # First pass: calculate total height
    tmp_img = Image.new('RGB', (W, 100))
    tmp_draw = ImageDraw.Draw(tmp_img)

    def calc_item_height(kw, en, desc):
        h = 0
        # Keyword line
        h += 26
        # English name
        h += 18
        # Description
        lines = wrap_text(desc.replace('\n', ''), font_desc, col_w - 20, tmp_draw)
        h += len(lines) * 20
        h += item_spacing + 6  # padding
        return h

    # Split keywords into two columns
    mid = (len(keywords) + 1) // 2
    col1 = keywords[:mid]
    col2 = keywords[mid:]

    col1_h = sum(calc_item_height(*kw) for kw in col1)
    col2_h = sum(calc_item_height(*kw) for kw in col2)
    content_h = max(col1_h, col2_h)

    H = title_h + content_h + MARGIN + 20
    img = Image.new('RGB', (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Title bar
    draw_rounded_rect(draw, (0, 0, W, title_h), TITLE_BG, radius=0)
    font_title = get_font(36, bold=True)
    title_text = "關鍵字參考  KEYWORD REFERENCE"
    bbox = draw.textbbox((0, 0), title_text, font=font_title)
    tx = (W - (bbox[2] - bbox[0])) // 2
    draw.text((tx, (title_h - (bbox[3] - bbox[1])) // 2), title_text, fill=KEYWORD_COLOR, font=font_title)

    # Draw items in columns
    def draw_column(items, x_start, y_start):
        y = y_start
        for zh_name, en_name, desc in items:
            # Keyword name in gold
            draw.text((x_start, y), zh_name, fill=KEYWORD_COLOR, font=font_keyword)
            y += 26
            # English name in dim
            draw.text((x_start + 4, y), en_name, fill=(140, 140, 140), font=font_en)
            y += 18
            # Description
            desc_clean = desc.replace('\n', '')
            lines = wrap_text(desc_clean, font_desc, col_w - 20, draw)
            for line in lines:
                draw.text((x_start + 4, y), line, fill=TEXT_COLOR, font=font_desc)
                y += 20
            y += item_spacing
            # Divider
            draw.line([(x_start, y), (x_start + col_w - 10, y)], fill=DIVIDER_COLOR, width=1)
            y += 6
        return y

    y_start = title_h + 15
    draw_column(col1, MARGIN, y_start)
    draw_column(col2, MARGIN + col_w + COL_GAP, y_start)

    # Divider between columns
    cx = MARGIN + col_w + COL_GAP // 2
    draw.line([(cx, title_h + 10), (cx, H - 10)], fill=DIVIDER_COLOR, width=1)

    out_path = os.path.join(os.path.dirname(__file__), "..", "graphics", "wall_cn_keyword_ref.png")
    img.save(out_path, "PNG")
    print(f"Saved keyword reference: {out_path} ({W}x{H})")
    return out_path


# =============================================================
# 2. CORE STRATAGEMS REFERENCE (核心詭計參考)
# =============================================================
def generate_core_stratagems():
    stratagems = [
        {
            "name": "指揮重擲",
            "en": "COMMAND RE-ROLL",
            "cp": "1CP",
            "category": "BATTLE_TACTIC",
            "cat_zh": "戰鬥策略",
            "when": "任何階段，在你剛完成命中骰、傷害骰、損傷骰、豁免投擲、推進骰、衝鋒骰、拼死突圍測試、危險測試或武器攻擊次數骰之後。",
            "target": "",
            "effect": "重擲該骰。",
            "restriction": "",
            "turn": "ANY",
        },
        {
            "name": "反擊",
            "en": "COUNTER-OFFENSIVE",
            "cp": "2CP",
            "category": "STRATEGIC_PLOY",
            "cat_zh": "策略詭計",
            "when": "近戰階段，在一個敵方單位剛完成近戰後。",
            "target": "你軍中一個在接戰範圍內且本階段尚未被選擇進行近戰的單位。",
            "effect": "你的單位接下來進行近戰。",
            "restriction": "",
            "turn": "ANY",
        },
        {
            "name": "史詩對決",
            "en": "EPIC CHALLENGE",
            "cp": "1CP",
            "category": "EPIC_DEED",
            "cat_zh": "英勇事蹟",
            "when": "近戰階段，當你軍中一個角色單位在一個或多個附屬單位的接戰範圍內時被選擇進行近戰。",
            "target": "你單位中的一個角色模型。",
            "effect": "直到階段結束，該模型所有近戰攻擊獲得[精確打擊]能力。",
            "restriction": "",
            "turn": "YOUR",
        },
        {
            "name": "火力攔截",
            "en": "FIRE OVERWATCH",
            "cp": "1CP",
            "category": "STRATEGIC_PLOY",
            "cat_zh": "策略詭計",
            "when": "對手的移動或衝鋒階段，在一個敵方單位完成部署、開始或結束一般移動/推進/撤退/衝鋒後。",
            "target": "你軍中一個距離該敵方單位24\"內、且在你的射擊階段有資格射擊的單位。",
            "effect": "你的單位可視為你的射擊階段向該敵方單位射擊。",
            "restriction": "直到階段結束，你單位每次遠程攻擊須未修正命中骰6才能命中（無視武器BS及修正值）。每回合只能使用一次。",
            "turn": "OPP",
        },
        {
            "name": "臥倒掩護",
            "en": "GO TO GROUND",
            "cp": "1CP",
            "category": "BATTLE_TACTIC",
            "cat_zh": "戰鬥策略",
            "when": "對手的射擊階段，在一個敵方單位選定目標後。",
            "target": "你軍中一個被選為攻擊目標的步兵單位。",
            "effect": "直到階段結束，你單位所有模型獲得6+不屈豁免，並獲得掩護效益。",
            "restriction": "",
            "turn": "OPP",
        },
        {
            "name": "手榴彈",
            "en": "GRENADE",
            "cp": "1CP",
            "category": "WARGEAR",
            "cat_zh": "戰爭裝備",
            "when": "你的射擊階段。",
            "target": "你軍中一個具手榴彈關鍵字、不在接戰範圍內且本階段未被選擇射擊的單位。",
            "effect": "選擇一個不在你軍任何單位接戰範圍內、且在你手榴彈單位8\"內可見的敵方單位。擲6D6：每個4+該敵方單位承受1點致命傷。",
            "restriction": "",
            "turn": "YOUR",
        },
        {
            "name": "英勇介入",
            "en": "HEROIC INTERVENTION",
            "cp": "2CP",
            "category": "STRATEGIC_PLOY",
            "cat_zh": "策略詭計",
            "when": "對手的衝鋒階段，在一個敵方單位完成衝鋒移動後。",
            "target": "你軍中一個距離該敵方單位6\"內、且在你的衝鋒階段有資格向該敵方宣告衝鋒的單位。",
            "effect": "你的單位宣告僅以該敵方單位為目標的衝鋒，並視為你的衝鋒階段結算。",
            "restriction": "只能選擇步行者(Walker)類型的載具。即使衝鋒成功，本回合你的單位不獲得衝鋒加成。",
            "turn": "OPP",
        },
        {
            "name": "無畏勇氣",
            "en": "INSANE BRAVERY",
            "cp": "1CP",
            "category": "EPIC_DEED",
            "cat_zh": "英勇事蹟",
            "when": "你的指揮階段的戰意動搖步驟，在你剛為你軍一個單位的戰意動搖測試失敗後。",
            "target": "剛進行該測試的單位（即使戰意動搖單位通常不能被你的詭計影響）。",
            "effect": "視為該測試通過，該單位不會因此而戰意動搖。",
            "restriction": "",
            "turn": "YOUR",
        },
        {
            "name": "快速進入",
            "en": "RAPID INGRESS",
            "cp": "1CP",
            "category": "STRATEGIC_PLOY",
            "cat_zh": "策略詭計",
            "when": "對手移動階段結束時。",
            "target": "你軍中一個在預備隊的單位。",
            "effect": "你的單位可視為你移動階段的增援步驟進入戰場。",
            "restriction": "不可在該單位通常無法進入戰場的戰鬥回合使用。",
            "turn": "OPP",
        },
        {
            "name": "煙霧彈",
            "en": "SMOKESCREEN",
            "cp": "1CP",
            "category": "WARGEAR",
            "cat_zh": "戰爭裝備",
            "when": "對手的射擊階段，在一個敵方單位選定目標後。",
            "target": "你軍中一個具煙霧關鍵字、被選為攻擊目標的單位。",
            "effect": "直到階段結束，你單位所有模型獲得掩護效益及隱匿能力。",
            "restriction": "",
            "turn": "OPP",
        },
        {
            "name": "坦克衝撞",
            "en": "TANK SHOCK",
            "cp": "1CP",
            "category": "STRATEGIC_PLOY",
            "cat_zh": "策略詭計",
            "when": "你的衝鋒階段。",
            "target": "你軍中一個載具單位。",
            "effect": "直到階段結束，你的單位完成衝鋒移動後，選擇接戰範圍內一個敵方單位及你單位一把近戰武器。擲等同該武器力量值的D6（若力量>敵韌性則額外擲2D6）。每個5+造成1點致命傷（最多6點）。",
            "restriction": "",
            "turn": "YOUR",
        },
    ]

    W = 1200
    MARGIN = 30
    COL_GAP = 24
    col_w = (W - 2 * MARGIN - COL_GAP) // 2

    font_title = get_font(32, bold=True)
    font_name = get_font(20, bold=True)
    font_en_name = get_font(12, light=True)
    font_cp = get_font(18, bold=True)
    font_cat = get_font(12, bold=True)
    font_label = get_font(13, bold=True)
    font_body = get_font(14)
    font_restrict = get_font(13)

    title_h = 70

    # Pre-calculate heights
    tmp_img = Image.new('RGB', (W, 100))
    tmp_draw = ImageDraw.Draw(tmp_img)

    def calc_strat_height(s):
        h = 0
        h += 28  # name + cp
        h += 16  # english name
        h += 18  # category
        inner_w = col_w - 24
        # when
        h += 18  # label
        lines = wrap_text(s["when"], font_body, inner_w, tmp_draw)
        h += len(lines) * 18
        # target
        if s["target"]:
            h += 18
            lines = wrap_text(s["target"], font_body, inner_w, tmp_draw)
            h += len(lines) * 18
        # effect
        h += 18
        lines = wrap_text(s["effect"], font_body, inner_w, tmp_draw)
        h += len(lines) * 18
        # restriction
        if s["restriction"]:
            h += 18
            lines = wrap_text(s["restriction"], font_restrict, inner_w, tmp_draw)
            h += len(lines) * 17
        h += 20  # padding
        return h

    # Split into two columns
    mid = (len(stratagems) + 1) // 2
    col1 = stratagems[:mid]
    col2 = stratagems[mid:]

    # Also add a key section at top
    key_h = 50  # space for the key

    col1_h = sum(calc_strat_height(s) for s in col1)
    col2_h = sum(calc_strat_height(s) for s in col2)
    content_h = max(col1_h, col2_h)

    H = title_h + key_h + content_h + MARGIN + 20
    img = Image.new('RGB', (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Title
    draw_rounded_rect(draw, (0, 0, W, title_h), TITLE_BG, radius=0)
    title_text = "核心詭計參考  CORE STRATAGEMS"
    bbox = draw.textbbox((0, 0), title_text, font=font_title)
    tx = (W - (bbox[2] - bbox[0])) // 2
    draw.text((tx, (title_h - (bbox[3] - bbox[1])) // 2), title_text, fill=CP_COLOR, font=font_title)

    # Key section
    ky = title_h + 8
    font_key = get_font(14, bold=True)
    font_key_body = get_font(13)
    # Turn indicators
    indicators = [
        ("任一方回合", (100, 180, 255)),
        ("你的回合", (100, 220, 100)),
        ("對手的回合", (255, 130, 130)),
    ]
    kx = MARGIN
    for label, color in indicators:
        draw.ellipse([(kx, ky + 4), (kx + 12, ky + 16)], fill=color)
        draw.text((kx + 16, ky + 2), label, fill=TEXT_COLOR, font=font_key_body)
        kx += 140

    # Category legend
    ky += 22
    kx = MARGIN
    cats = [("戰鬥策略", "BATTLE_TACTIC"), ("英勇事蹟", "EPIC_DEED"),
            ("策略詭計", "STRATEGIC_PLOY"), ("戰爭裝備", "WARGEAR")]
    for cat_name, cat_key in cats:
        c = CATEGORY_COLORS[cat_key]
        draw.rectangle([(kx, ky + 2), (kx + 10, ky + 14)], fill=c)
        draw.text((kx + 14, ky), cat_name, fill=c, font=font_key_body)
        kx += 130

    # Draw stratagems
    def draw_strat_column(items, x_start, y_start):
        y = y_start
        for s in items:
            cat_color = CATEGORY_COLORS[s["category"]]
            turn_color = {
                "ANY": (100, 180, 255),
                "YOUR": (100, 220, 100),
                "OPP": (255, 130, 130),
            }[s["turn"]]

            # Background card
            sh = calc_strat_height(s)
            draw_rounded_rect(draw, (x_start, y, x_start + col_w, y + sh), SECTION_BG, radius=6)

            # Left color bar
            draw.rectangle([(x_start, y + 6), (x_start + 4, y + sh - 6)], fill=cat_color)

            # Turn indicator dot
            draw.ellipse([(x_start + col_w - 20, y + 8), (x_start + col_w - 8, y + 20)], fill=turn_color)

            inner_x = x_start + 12
            inner_w = col_w - 24
            cy = y + 6

            # Name + CP
            draw.text((inner_x, cy), s["name"], fill=TEXT_COLOR, font=font_name)
            # CP on the right
            cp_bbox = draw.textbbox((0, 0), s["cp"], font=font_cp)
            draw.text((x_start + col_w - 30 - (cp_bbox[2] - cp_bbox[0]), cy + 2), s["cp"], fill=CP_COLOR, font=font_cp)
            cy += 28

            # English name
            draw.text((inner_x, cy), s["en"], fill=(120, 120, 120), font=font_en_name)
            cy += 16

            # Category
            draw.text((inner_x, cy), f"核心 - {s['cat_zh']}", fill=cat_color, font=font_cat)
            cy += 18

            # When
            draw.text((inner_x, cy), "時機：", fill=PHASE_COLOR, font=font_label)
            cy += 18
            lines = wrap_text(s["when"], font_body, inner_w, draw)
            for line in lines:
                draw.text((inner_x + 4, cy), line, fill=TEXT_COLOR, font=font_body)
                cy += 18

            # Target
            if s["target"]:
                draw.text((inner_x, cy), "目標：", fill=PHASE_COLOR, font=font_label)
                cy += 18
                lines = wrap_text(s["target"], font_body, inner_w, draw)
                for line in lines:
                    draw.text((inner_x + 4, cy), line, fill=TEXT_COLOR, font=font_body)
                    cy += 18

            # Effect
            draw.text((inner_x, cy), "效果：", fill=(100, 220, 100), font=font_label)
            cy += 18
            lines = wrap_text(s["effect"], font_body, inner_w, draw)
            for line in lines:
                draw.text((inner_x + 4, cy), line, fill=TEXT_COLOR, font=font_body)
                cy += 18

            # Restriction
            if s["restriction"]:
                draw.text((inner_x, cy), "限制：", fill=(255, 130, 100), font=font_label)
                cy += 18
                lines = wrap_text(s["restriction"], font_restrict, inner_w, draw)
                for line in lines:
                    draw.text((inner_x + 4, cy), line, fill=(200, 180, 150), font=font_restrict)
                    cy += 17

            y += sh + 8
        return y

    content_y = title_h + key_h + 10
    draw_strat_column(col1, MARGIN, content_y)
    draw_strat_column(col2, MARGIN + col_w + COL_GAP, content_y)

    # Center divider
    cx = MARGIN + col_w + COL_GAP // 2
    draw.line([(cx, content_y), (cx, H - 10)], fill=DIVIDER_COLOR, width=1)

    out_path = os.path.join(os.path.dirname(__file__), "..", "graphics", "wall_cn_core_stratagems.png")
    img.save(out_path, "PNG")
    print(f"Saved core stratagems: {out_path} ({W}x{H})")
    return out_path


# =============================================================
# 3. COMBAT PATROL MISSIONS (戰鬥巡邏任務)
# =============================================================
def generate_combat_patrol():
    W = 1200
    MARGIN = 40
    font_title = get_font(32, bold=True)
    font_section = get_font(22, bold=True)
    font_step_num = get_font(28, bold=True)
    font_step_title = get_font(18, bold=True)
    font_body = get_font(15)
    font_body_bold = get_font(15, bold=True)
    font_small = get_font(13)
    font_mission_title = get_font(20, bold=True)
    font_mission_sub = get_font(16, bold=True)

    title_h = 70
    inner_w = W - 2 * MARGIN

    tmp_img = Image.new('RGB', (W, 100))
    tmp_draw = ImageDraw.Draw(tmp_img)

    # Content sections
    setup_steps = [
        ("3", "建立戰場", "玩家佈置地形和目標標記。戰鬥巡邏任務使用44\"x30\"的矩形戰區。地形應均勻分佈，讓雙方都能受益於掩護。每個任務的部署圖會標示目標標記的數量和位置。"),
        ("4", "決定攻守方", "玩家商定哪個戰場邊緣為攻方/守方。擲骰決勝，勝者決定誰為攻方、誰為守方，決定部署區使用。"),
        ("5", "宣告戰鬥編制",
         "雙方依序秘密記錄：\n"
         "- 哪些單位使用巡邏小隊分割\n"
         "- 哪些領袖附屬於哪些護衛單位\n"
         "- 哪些單位搭載於運輸載具\n"
         "- 哪些單位進入預備隊\n"
         "完成後向對手公開。預備隊不可在第一回合進場，第三回合結束前未進場視為被摧毀。"),
        ("6", "部署軍隊", "玩家輪流部署單位（守方先行），模型須完全在己方部署區內。若一方先部署完畢，對方繼續部署其餘單位。"),
        ("7", "決定先手", "擲骰決勝，勝者先手。"),
        ("8", "結算戰前規則", "玩家輪流結算戰前規則（如斥候能力），先手方先行。"),
        ("9", "開戰", "第一戰鬥回合開始。"),
        ("10", "結束戰鬥", "五個戰鬥回合後結束。若一方無模型，另一方可繼續直到戰鬥結束。"),
        ("11", "判定勝負", "VP最高者獲勝。平分為平局。全軍塗裝達Battle Ready標準可獲10VP加成。"),
    ]

    securing_text = "在每個指揮階段結束時，若當回合玩家控制一個目標標記且其軍中一個或多個戰線單位（不含戰意動搖）在該標記範圍內，則該標記被該玩家「鎖定」。鎖定的標記即使無模型在範圍內仍維持控制，直到對手在後續指揮階段結束時控制該標記。"

    missions = [
        {
            "name": "巡邏衝突",
            "en": "CLASH OF PATROLS",
            "rule_name": "回收情報",
            "rule_en": "Retrieve Intelligence",
            "rule_text": "從第二回合開始，每個指揮階段中，當回合玩家可選擇其控制的一個目標標記回收情報。每次回收情報時，若該玩家的戰將在戰場上（或搭載於運輸載具中），獲得1CP。每個標記只能被選擇一次（任一方）。",
            "primary_name": "佔領據守",
            "primary_en": "TAKE AND HOLD",
            "primary_text": "第二至四回合：每個指揮階段結束時，當回合玩家每控制一個目標標記得5VP（每回合最多15VP）。\n第五回合：先手方同上；後手方在其回合結束時計分（而非指揮階段結束時）。",
        },
        {
            "name": "遠古科技回收",
            "en": "ARCHEOTECH RECOVERY",
            "rule_name": "輻射動力核心",
            "rule_en": "Irradiated Power Cells",
            "rule_text": "戰鬥中兩個目標標記將被移除：\n- 第三回合開始時：守方隨機選擇無人區一個標記為Gamma標記。\n- 第四回合開始時：Gamma標記被移除，攻方隨機選擇無人區剩餘兩個標記之一為Beta標記。\n- 第五回合開始時：Beta標記被移除。",
            "primary_name": "回收遠古科技",
            "primary_en": "RECOVER ARCHEOTECH",
            "primary_text": "第二至五回合：每個指揮階段結束時，當回合玩家每控制一個目標標記得5VP（每回合最多15VP）。\n戰鬥結束時：若玩家控制無人區最後一個目標標記，得10VP。",
        },
    ]

    # Calculate total height
    def calc_body_lines(text, font, w):
        total = 0
        for paragraph in text.split('\n'):
            lines = wrap_text(paragraph, font, w, tmp_draw)
            total += len(lines)
        return total

    total_h = title_h + 20
    # Setup steps
    total_h += 36  # section header
    for num, title, text in setup_steps:
        total_h += 30  # step header
        total_h += calc_body_lines(text, font_body, inner_w - 50) * 20
        total_h += 10

    # Securing objectives
    total_h += 50  # header
    total_h += calc_body_lines(securing_text, font_body, inner_w - 20) * 20
    total_h += 20

    # Missions
    for m in missions:
        total_h += 44  # mission title
        total_h += 30  # rule header
        total_h += calc_body_lines(m["rule_text"], font_body, inner_w - 30) * 20
        total_h += 30  # primary header
        total_h += calc_body_lines(m["primary_text"], font_body, inner_w - 30) * 20
        total_h += 30

    total_h += 30  # bottom padding

    H = total_h
    img = Image.new('RGB', (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Title
    draw_rounded_rect(draw, (0, 0, W, title_h), TITLE_BG, radius=0)
    title_text = "戰鬥巡邏任務  COMBAT PATROL MISSIONS"
    bbox = draw.textbbox((0, 0), title_text, font=font_title)
    tx = (W - (bbox[2] - bbox[0])) // 2
    draw.text((tx, (title_h - (bbox[3] - bbox[1])) // 2), title_text, fill=(100, 200, 255), font=font_title)

    y = title_h + 20

    # Setup steps section
    draw.text((MARGIN, y), "任務設置流程", fill=KEYWORD_COLOR, font=font_section)
    y += 36

    for num, title, text in setup_steps:
        # Step number circle
        draw.ellipse([(MARGIN, y + 2), (MARGIN + 26, y + 28)], fill=(80, 80, 80))
        num_bbox = draw.textbbox((0, 0), num, font=font_step_num)
        nx = MARGIN + 13 - (num_bbox[2] - num_bbox[0]) // 2
        ny = y + 15 - (num_bbox[3] - num_bbox[1]) // 2
        draw.text((nx, ny - 2), num, fill=TEXT_COLOR, font=font_step_num)

        # Step title
        draw.text((MARGIN + 34, y + 4), title, fill=TEXT_COLOR, font=font_step_title)
        y += 30

        # Step body
        for paragraph in text.split('\n'):
            lines = wrap_text(paragraph, font_body, inner_w - 50, draw)
            for line in lines:
                draw.text((MARGIN + 40, y), line, fill=(200, 200, 200), font=font_body)
                y += 20
        y += 10

    # Divider
    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=DIVIDER_COLOR, width=2)
    y += 15

    # Securing Objective Markers
    draw.text((MARGIN, y), "鎖定目標標記", fill=KEYWORD_COLOR, font=font_section)
    draw.text((MARGIN + 170, y + 6), "SECURING OBJECTIVE MARKERS", fill=(120, 120, 120), font=font_small)
    y += 34
    for paragraph in securing_text.split('\n'):
        lines = wrap_text(paragraph, font_body, inner_w - 20, draw)
        for line in lines:
            draw.text((MARGIN + 10, y), line, fill=(200, 200, 200), font=font_body)
            y += 20
    y += 20

    # Divider
    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=DIVIDER_COLOR, width=2)
    y += 15

    # Missions
    draw.text((MARGIN, y), "任務", fill=KEYWORD_COLOR, font=font_section)
    y += 36

    for m in missions:
        # Mission card
        card_start = y
        draw_rounded_rect(draw, (MARGIN, y, W - MARGIN, y + 40), SECTION_BG, radius=6)
        draw.text((MARGIN + 12, y + 8), m["name"], fill=(100, 200, 255), font=font_mission_title)
        draw.text((MARGIN + 12 + len(m["name"]) * 22 + 10, y + 12), m["en"], fill=(120, 120, 120), font=font_small)
        y += 44

        # Mission rule
        draw.text((MARGIN + 12, y), f"任務規則 - {m['rule_name']}", fill=KEYWORD_COLOR, font=font_mission_sub)
        y += 28
        for paragraph in m["rule_text"].split('\n'):
            lines = wrap_text(paragraph, font_body, inner_w - 30, draw)
            for line in lines:
                draw.text((MARGIN + 20, y), line, fill=(200, 200, 200), font=font_body)
                y += 20
        y += 10

        # Primary objective
        draw.text((MARGIN + 12, y), f"主要目標 - {m['primary_name']}", fill=(100, 220, 100), font=font_mission_sub)
        y += 28
        for paragraph in m["primary_text"].split('\n'):
            lines = wrap_text(paragraph, font_body, inner_w - 30, draw)
            for line in lines:
                draw.text((MARGIN + 20, y), line, fill=(200, 200, 200), font=font_body)
                y += 20
        y += 20

    out_path = os.path.join(os.path.dirname(__file__), "..", "graphics", "wall_cn_combat_patrol.png")
    img.save(out_path, "PNG")
    print(f"Saved combat patrol: {out_path} ({W}x{H})")
    return out_path


if __name__ == "__main__":
    print("Generating Chinese reference images...")
    generate_keyword_reference()
    generate_core_stratagems()
    generate_combat_patrol()
    print("Done!")
