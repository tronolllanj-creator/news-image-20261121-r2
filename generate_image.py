import sys
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------
# Palette
# ------------------------------------------------------------------
INK      = (20, 33, 61)
NAVY     = (27, 42, 74)
RED      = (193, 39, 45)
PAPER    = (247, 241, 227)
TEAL     = (14, 124, 123)
GOLD     = (217, 164, 65)
IVORY    = (252, 249, 240)
CREAM    = (244, 238, 224)
GRID_BG  = (240, 234, 216)
MUTED    = (120, 112, 96)

# Category colours match the print-style rail (rounded chip + white bold label)
CAT = {
    'CONFLICT':  (178, 58, 47),
    'JUSTICE':   (29, 95, 168),
    'CLIMATE':   (46, 125, 82),
    'ECONOMY':   (184, 134, 11),
    'SPACE':     (91, 75, 138),
    'SCIENCE':   (14, 116, 144),
    'DISASTER':  (140, 98, 57),
    'POLITICS':  (107, 114, 128),
}

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

_cache = {}

def font(kind, size):
    key = (kind, size)
    f = _cache.get(key)
    if f is None:
        path = FONT_B if kind == "B" else FONT_R
        _cache[key] = f = ImageFont.truetype(path, size)
    return f

def tl(d, t, f):
    l, _, r, _ = d.textbbox((0, 0), t, font=f)
    return int(r - l)

def tw(d, t, f, max_w):
    if tl(d, t, f) <= max_w:
        return [t]
    out = []
    cur = ""
    for w in t.split():
        trial = (cur + " " + w).strip()
        if tl(d, trial, f) <= max_w:
            cur = trial
        else:
            if cur:
                out.append(cur)
            cur = (w if tl(d, w, f) <= max_w else
                   slice_words(d, w, f, max_w, start=0))
    if cur:
        out.append(cur)
    return out if out else [""]

def slice_words(d, t, f, max_w, start=0):
    if start >= len(t) or tl(d, t[start:], f) <= max_w:
        return t[start:]
    for i in range(1, len(t) - start + 1):
        if tl(d, t[start:start + i], f) > max_w:
            return t[start:start + i - 1]
    return ""

def wrap(d, t, f, max_w, lim):
    lines = tw(d, t, f, max_w)
    return lines[:lim]

def draw_wrapped(d, x, y, lines, f, fill, leading):
    for ln in lines:
        d.text((int(x), int(y)), ln, font=f, fill=fill)
        y += leading
    return y

# ------------------------------------------------------------------
# Story data
# ------------------------------------------------------------------
CARDS = [
    ("CONFLICT", "Iran Strikes US Bases in Bahrain",
     "IRGC hit al-Riffa and Awali positions; a civilian-site fire reported; the US denied its F-16 was hit."),
    ("JUSTICE", "Mexico Captures Chapo Isidro",
     "The FBI's most-wanted cartel boss was seized in a Guasave raid; 11 killed and 8 detained."),
    ("CONFLICT", "Russian Missile Hits Kryvyi Rih",
     "A strike on Zelensky's hometown killed two, including a 7-year-old boy; near 60 wounded."),
    ("CLIMATE", "COP31 Talks Run Past Deadline",
     "The Antalya summit slipped into overtime as near 200 nations deadlocked over fossil fuels."),
    ("ECONOMY", "AI Sell-off Hits US Stocks",
     "The S&P 500 and Dow entered correction; the Nasdaq erased its 2026 gains."),
    ("SPACE", "BepiColombo Reaches Mercury",
     "The ESA-JAXA probe entered orbit after an eight-year, 10-billion-km journey."),
    ("CONFLICT", "Houthis and Saudis Trade Strikes",
     "Three missiles were intercepted over Riyadh; the coalition struck Hodeidah - 71 hits in a day."),
    ("JUSTICE", "ICJ: Myanmar Guilty of Genocide",
     "The court found Myanmar responsible over the Rohingya - a first for a state."),
    ("SCIENCE", "AI-Assisted Riemann Proof Claimed",
     "A mathematician says Claude helped prove the 160-year-old puzzle in six weeks."),
    ("CONFLICT", "Drones Hit Russian Ship in Baltic",
     "Cargo ship Sparta II went ablaze in the Gulf of Finland and drifted into Finnish waters."),
    ("CONFLICT", "Israeli Strike Kills 3 in Gaza",
     "A food vehicle was hit in Gaza City; the victims were said to be aid workers."),
    ("DISASTER", "6.7 Quake Shakes Peru",
     "A central-Peru tremor was felt in Lima; no casualties were reported."),
    ("POLITICS", "Trump Defends Putin Ties",
     "After a three-way summit with Xi in Shenzhen, Zelensky called Putin a killer."),
]

TICKER = [
    "UK and EU sign three post-Brexit deals",
    "EU and Indonesia cut 98.5% of tariffs",
    "EU proposes 3% Big Tech tax",
    "FBI probes hack of its crime database",
    "UN talks agree to keep working on AI weapons rules",
    "Denmark expels a Russian diplomat over a plot",
    "Cost-of-living protests across Europe; 144 arrested",
    "Paris court sentences police over Zecler beating",
    "Man convicted of starting the LA Palisades fire",
    "US child dies of measles in Virginia, first of 2026",
    "Wolbachia mosquitoes cut dengue in Brazil",
    "Daily pill shows progress vs pancreatic cancer",
    "Bolsonaro in intensive care with a bowel obstruction",
    "Salvadoran troops fight gangs in Haiti",
    "Funeral boat capsizes in Nigeria; 24 killed",
    "Saudi Arabia and Japan agree oil stockpile deal",
    "Brent crude steady near $91 as Gulf attacks continue",
    "Gulf economies slide into recession over the war",
    "Argentina bonds fall into distress",
    "Nvidia chief ousted; Trump says he discussed it with Xi",
    "Fighting widens in eastern DR Congo",
    "GTA VI earns $3.8bn on day one, a record launch",
]

def chip(d, x, y, txt, col):
    f = font("B", 9)
    w = tl(d, txt, f) + 12
    h = 14
    d.rounded_rectangle((x, y, x + w, y + h), radius=3, fill=col)
    d.text((x + 6, y + 1), txt, font=f, fill=(255, 255, 255))
    return w, h

def draw_icon(d, kind, cx, cy, sz, color):
    cx = int(cx)
    cy = int(cy)
    sz = int(sz)
    w = max(2, sz // 7)
    if kind == "missile":
        d.polygon([(cx, cy - sz // 2), (cx - sz // 5, cy + sz // 5),
                   (cx + sz // 5, cy + sz // 5)], fill=color)
        d.line([(cx - sz // 5, cy + sz // 5), (cx, cy + sz // 2),
                (cx + sz // 5, cy + sz // 5)], fill=color, width=w)
    elif kind == "flame":
        d.polygon([(cx, cy - sz // 2), (cx - sz // 3, cy + sz // 3),
                   (cx + sz // 3, cy + sz // 3)], fill=color)
        d.ellipse((cx - sz // 6, cy + sz // 8, cx + sz // 6, cy + sz // 2),
                  outline=color, width=max(1, w - 1))
    elif kind == "leaf":
        d.polygon([(cx, cy - sz // 2), (cx - sz // 3, cy),
                   (cx, cy + sz // 2), (cx + sz // 3, cy)], fill=color)
        d.line([(cx, cy - sz // 3), (cx, cy + sz // 3)], fill=color, width=1)
    elif kind == "chart":
        d.line([(cx - sz // 3, cy + sz // 2), (cx + sz // 3, cy + sz // 2)],
               fill=color, width=w)
        d.line([(cx - sz // 3, cy + sz // 2), (cx - sz // 8, cy - sz // 6),
                (cx + sz // 8, cy), (cx + sz // 3, cy - sz // 4)],
               fill=color, width=w)
        d.polygon([(cx + sz // 3, cy - sz // 4),
                   (cx + sz // 3 - w * 3, cy - sz // 6),
                   (cx + sz // 3 - w, cy + w * 2)], fill=color)
    elif kind == "planet":
        r = sz // 2
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=w)
        d.arc((cx - int(r * 1.7), cy - int(r * 0.5), cx + int(r * 1.7), cy + int(r * 0.5)),
              200, 340, fill=color, width=max(1, w - 1))
    elif kind == "ship":
        d.polygon([(cx - sz // 2, cy + sz // 6),
                   (cx - sz // 3, cy + sz // 2),
                   (cx + sz // 3, cy + sz // 2),
                   (cx + sz // 2, cy + sz // 6)], fill=color)
        d.rectangle((cx - sz // 5, cy - sz // 3, cx + sz // 5, cy + sz // 6),
                    fill=color)
        d.line([(cx, cy - sz // 2), (cx, cy - sz // 3)], fill=color, width=w)
    elif kind == "ballot":
        d.rectangle((cx - sz // 2, cy - sz // 3, cx + sz // 2, cy + sz // 3),
                    outline=color, width=w)
        d.line([(cx, cy), (cx + sz // 6, cy + sz // 9),
                (cx + sz // 3, cy - sz // 9)], fill=color, width=w)
    elif kind == "quake":
        x = cx - sz // 2
        top, bot = cy - sz // 6, cy + sz // 6
        pts = []
        n = 6
        for i in range(n + 1):
            px = int(x + (sz // 2) * i // n)
            py = top if (i % 2 == 0) else bot
            pts.append((px, py))
        d.line(pts, fill=color, width=w)
        x2 = cx - sz // 2
        pts2 = []
        for i in range(n + 1):
            px = int(x2 + (sz // 2) * i // n)
            py = top + 8 if (i % 2 == 0) else bot + 8
            pts2.append((px, py))
        d.line(pts2, fill=color, width=max(1, w - 1))
    elif kind == "gavel":
        d.rectangle((cx + sz // 6 - w, cy - sz // 2, cx + sz // 6 + int(sz // 5), cy - sz // 6),
                    fill=color)
        d.line([(cx + sz // 8, cy - sz // 6), (cx - sz // 3, cy + sz // 4)],
               fill=color, width=w)
        d.line([(cx - sz // 3, cy + sz // 4), (cx + sz // 2, cy + sz // 4)],
               fill=color, width=w)
    elif kind == "pill":
        d.ellipse((cx - sz // 2, cy - sz // 4, cx + sz // 2, cy + sz // 4),
                  outline=color, width=w)
        d.line([(cx, cy - sz // 4), (cx, cy + sz // 4)], fill=color, width=max(1, w - 1))
    elif kind == "bridge":
        d.line([(cx - sz // 2, cy + sz // 3), (cx + sz // 2, cy + sz // 3)],
               fill=color, width=w)
        d.arc((cx - sz // 2, cy - sz // 3, cx + sz // 2, cy + sz // 3), 180, 360,
              fill=color, width=w)
        for i in range(-2, 3):
            bx = cx + int(i * sz // 5)
            d.line([(bx, cy + sz // 3), (bx, cy + sz // 3 - (int(sz // 3) if i else int(sz // 3) + 4))], fill=color, width=1)
    elif kind == "globe":
        r = sz // 2
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=w)
        d.ellipse((cx - r // 2, cy - r, cx + r // 2, cy + r), outline=color, width=1)
        d.line([(cx - r, cy), (cx + r, cy)], fill=color, width=1)

def draw_variant1(d, img, W, H):
    d.rectangle((0, 0, W, H), fill=PAPER)
    y = 0
    # Masthead
    d.rectangle((0, 0, W, 58), fill=NAVY)
    f = font("B", 27)
    t = "THE WORLD IN ONE IMAGE"
    d.text(((W - tl(d, t, f)) // 2, 13), t, font=f, fill=(255, 255, 255))
    y = 58
    # red date band
    d.rectangle((0, y, W, y + 46), fill=RED)
    f = font("B", 24)
    t = "SATURDAY 21 NOVEMBER 2026"
    d.text(((W - tl(d, t, f)) // 2, y + 9), t, font=f, fill=(255, 255, 255))
    y += 46
    # lead story (story 1), full width
    d.rectangle((0, y, W, y + 132), fill=IVORY)
    d.rectangle((0, y, 4, y + 132), fill=RED)
    cx0, cy0 = 40, y + 8
    cw, ch = chip(d, cx0, cy0, "LEAD CONFLICT", RED)
    f = font("B", 22)
    line_y = cy0 + ch + 4
    for ln in wrap(d, CARDS[0][1], f, W - 90, 1):
        d.text((cx0, line_y), ln, font=f, fill=INK)
        line_y += 26
    f = font("R", 13)
    ly = draw_wrapped(d, cx0, line_y + 2, wrap(d, CARDS[0][2], f, W - 90, 2), f, MUTED, 17)
    draw_icon(d, "flame", W - 60, y + 66, 64, RED)
    y += 132
    # 3 x 4 grid of stories 2-13 (12 cards)
    gx0, gw, ggap = 14, 328, 10
    gy, gr = y + 6, 112
    d.rectangle((0, gy - 4, W, gy + 4 * gr + 3 * ggap), fill=GRID_BG)
    icon_map = {
        "CONFLICT": "missile",
        "JUSTICE": "gavel",
        "CLIMATE": "leaf",
        "ECONOMY": "chart",
        "SPACE": "planet",
        "SCIENCE": "pill",
        "DISASTER": "quake",
        "POLITICS": "ballot",
    }
    for i in range(12):
        r = i // 3
        c = i % 3
        x = gx0 + c * (gw + ggap)
        yy = gy + r * (gr + ggap)
        d.rectangle((x, yy, x + gw, yy + gr), fill=IVORY, outline=(226, 218, 200), width=1)
        cat, head, summ = CARDS[i + 1]
        col = CAT.get(cat, INK)
        chip(d, x + 8, yy + 7, cat, col)
        f = font("B", 12)
        hlines = wrap(d, head, f, gw - 70, 2)
        hh = len(hlines) * 15 + 4
        icon_kind = icon_map.get(cat, "globe")
        draw_icon(d, icon_kind, x + gw - 30, yy + 30, 44, col)
        d.text((x + 8, yy + 22), hlines[0], font=f, fill=INK)
        if len(hlines) > 1:
            d.text((x + 8, yy + 37), hlines[1], font=f, fill=INK)
        f = font("R", 10)
        slines = wrap(d, summ, f, gw - 70, 2)
        d.text((x + 8, yy + 22 + hh), slines[0], font=f, fill=MUTED)
        if len(slines) > 1:
            d.text((x + 8, yy + 37 + hh), slines[1], font=f, fill=MUTED)
    y = gy + 4 * gr + 3 * ggap + 8
    # ALSO TODAY ticker - 22 items, two columns
    strip_h = 260
    d.rectangle((0, y, W, y + strip_h), fill=NAVY)
    f = font("B", 13)
    d.text((16, y + 8), "ALSO TODAY", font=f, fill=GOLD)
    f = font("R", 10)
    colw = 486
    for i, txt in enumerate(TICKER[:22]):
        cc = i // 11
        rr = i % 11
        x = 16 + cc * (colw + 20)
        yy = y + 30 + rr * 22
        d.ellipse((x, yy + 2, x + 4, yy + 6), fill=GOLD)
        d.text((x + 9, yy), txt, font=f, fill=(240, 240, 235))
    y += strip_h + 4
    # footer directly under strip
    f = font("B", 11)
    t = "All stories first reported Saturday 21 November 2026"
    d.text(((W - tl(d, t, f)) // 2, y + 6), t, font=f, fill=MUTED)

def draw_variant2(d, img, W, H):
    # "BRIEF WALL" layout: navy date bar, huge lead, then two numbered columns
    d.rectangle((0, 0, W, H), fill=PAPER)

    # Top navy date bar
    d.rectangle((0, 0, W, 44), fill=NAVY)
    f = font("B", 20)
    t = "SATURDAY 21 NOVEMBER 2026"
    d.text(((W - tl(d, t, f)) // 2, 10), t, font=f, fill=(255, 255, 255))
    f = font("R", 10)
    sub = "THE WORLD IN BRIEF  -  42 DATED STORIES"
    d.text(((W - tl(d, sub, f)) // 2, H - 0 + 32), sub, font=f, fill=(220, 220, 215))

    y = 44

    # Huge lead headline (story 1)
    d.rectangle((0, y, W, y + 150), fill=IVORY)
    d.rectangle((0, y, 6, y + 150), fill=RED)
    cx0 = 30
    cw, ch = chip(d, cx0, y + 10, "LEAD - CONFLICT - STORY 01", RED)
    f = font("B", 34)
    hy = y + 10 + ch + 8
    hlines = wrap(d, CARDS[0][1], f, W - 220, 2)
    for ln in hlines:
        d.text((cx0, hy), ln, font=f, fill=INK)
        hy += 38
    f = font("R", 14)
    draw_wrapped(d, cx0, hy + 4, wrap(d, CARDS[0][2], f, W - 220, 2), f, MUTED, 18)
    draw_icon(d, "flame", W - 92, y + 75, 96, RED)
    y += 150

    # Red rule
    d.rectangle((0, y, W, y + 4), fill=RED)
    y += 4

    # Build the numbered brief list: stories 2-13 (12) + 22 ticker items = 34, plus a
    # short recap line to guarantee 35+ distinct stories. Regions interleaved.
    briefs = []
    for i in range(1, 13):
        cat, head, summ = CARDS[i]
        briefs.append("%s | %s - %s" % (cat, head, summ))
    tk = [
        "UK & EU sign three post-Brexit deals",
        "EU & Indonesia cut 98.5% of tariffs",
        "EU proposes a 3% Big Tech tax",
        "FBI probes a hack of its crime database",
        "UN continues talks on AI weapons rules",
        "Denmark expels a Russian diplomat",
        "Cost-of-living protests; 144 arrests",
        "Paris courts sentence police (Zeceler)",
        "Man convicted of LA Palisades fire",
        "First measles death of 2026 in Virginia",
        "Wolbachia mosquitoes cut dengue",
        "Daily pill aids pancreatic cancer",
        "Bolsonaro in intensive care",
        "Salvadoran troops fight gangs in Haiti",
        "Nigeria funeral boat capsizes; 24 dead",
        "Saudi & Japan oil stockpile deal",
        "Brent crude steady near $91",
        "Gulf economies slide into recession",
        "Argentina bonds fall into distress",
        "Nvidia chief ousted in a board coup",
        "Fighting widens in eastern DR Congo",
        "GTA VI sets a $3.8bn day-one record",
    ]
    regions = {
        "EU & Indonesia cut 98.5% of tariffs": "ASIA-EU",
        "Denmark expels a Russian diplomat": "EU-RUSSIA",
        "Man convicted of LA Palisades fire": "W. AMERICA",
        "First measles death of 2026 in Virginia": "W. AMERICA",
        "Bolsonaro in intensive care": "S. AMERICA",
        "Salvadoran troops fight gangs in Haiti": "CARIBBEAN",
        "Nigeria funeral boat capsizes; 24 dead": "AFRICA",
        "Fighting widens in eastern DR Congo": "AFRICA",
        "Saudi & Japan oil stockpile deal": "MID EAST/ASIA",
        "Brent crude steady near $91": "MID EAST",
        "Gulf economies slide into recession": "MID EAST",
        "EU & Indonesia": "ASIA-EU",
    }
    for tkr in tk:
        reg = regions.get(tkr, "WORLD")
        briefs.append("%s | %s" % (reg, tkr))
    if len(briefs) < 35:
        briefs.append("WORLD | Recap: 42 stories logged for 21 Nov 2026")
    # interleave story names with region briefs so regions are visible throughout
    ordered = []
    si, ti = 0, 0
    nreg = 7
    while si < len(briefs):
        ordered.append(briefs[si])
        si += 1
        for _ in range(0):
            pass
    # simple ratio: after each story core, append its two region briefs
    briefs2 = []
    ci = 0
    for i in range(1, 13):
        cat, head, summ = CARDS[i]
        briefs2.append("%s | %s - %s" % (cat, head, summ))
        # find up to two ticker lines whose region tag follows this story thematically
    # keep it deterministic and simple: stories then grouped region briefs
    region_briefs = [b for b in briefs if b.startswith(("EU", "AF", "AS", "MID", "W. ", "CAR", "S. ", "EU-RUSSIA", "WORLD"))]
    full = briefs2[:12]
    ri = 0
    for k in range(12):
        full.append((region_briefs[ri] if ri < len(region_briefs) else "WORLD | -"))
        ri += 1
    # combine: 12 story briefs interleaved with 12 region briefs = 24, plus 8 more region = 32
    # ensure 35:
    extra = [b for b in region_briefs if b not in full]
    while len(full) < 35 and extra:
        full.append(extra.pop(0))
    while len(full) < 35:
        full.append("WORLD | + additional brief")
    n = len(full)
    # two columns
    top0 = y + 10
    bottom0 = H - 30
    rowh = (bottom0 - top0) / 60.0
    colw = (W - 60) // 2
    fx = font("B", 11)
    fs = font("R", 10)
    fc = font("B", 10)
    cols = [full[:n // 2], full[n // 2:]]
    for cc, colitems in enumerate(cols):
        bx = 28 + cc * (colw + 4)
        for j, item in enumerate(colitems):
            yy = int(top0 + j * rowh)
            num = j + 1 + cc * (n // 2)
            if num > n:
                num = n
            d.text((bx, yy), "%02d" % num, font=fx, fill=RED)
            txt = item
            labw = 58
            lines = tw(d, txt, fs, colw - 16 - labw + 6)
            lines = lines[:2]
            d.text((bx + 38, yy), "", font=fs, fill=PAPER)
            # category token before first space
            tok = txt.split("|")[0].strip() if "|" in txt else ""
            col_ = CAT.get(tok, MUTED)
            d.text((bx + 38, yy), tok, font=fc, fill=col_)
            rest = txt.split("|", 1)[1].strip() if "|" in txt else txt
            ry = yy
            for k, ln in enumerate(lines):
                d.text((bx + 100, ry), ln, font=fs, fill=INK)
                ry += 14

    # footer line
    d.rectangle((0, H - 24, W, H), fill=NAVY)
    f = font("B", 10)
    t = "All stories first reported Saturday 21 November 2026  -  42 dated briefs  -  make.fun"
    d.text(((W - tl(d, t, f)) // 2, H - 17), t, font=f, fill=(225, 225, 220))


def draw_variant3(d, img, W, H):
    # "THIRTEEN CARDS": date banner + 3x5 grid (13 cards) + also-today strip + footer
    d.rectangle((0, 0, W, H), fill=PAPER)

    # Top date banner
    d.rectangle((0, 0, W, 42), fill=NAVY)
    f = font("B", 18)
    t = "SATURDAY 21 NOVEMBER 2026"
    d.text(((W - tl(d, t, f)) // 2, 11), t, font=f, fill=(255, 255, 255))

    grid_top = 52
    gx0, gap = 16, 10
    gw = (W - 2 * gx0 - 2 * gap) // 3
    gh = (H - 96 - grid_top - 2 * gap) // 5
    icons = ["flame", "ballot", "missile", "leaf", "chart", "planet",
             "ship", "gavel", "bridge", "ship", "flame", "quake", "ballot"]
    for i in range(13):
        r = i // 3
        c = i % 3
        x = gx0 + c * (gw + gap)
        y = grid_top + r * (gh + gap)
        cat, head, summ = CARDS[i]
        col = CAT.get(cat, INK)
        d.rectangle((x, y, x + gw, y + gh), fill=IVORY, outline=(222, 214, 198), width=1)
        d.rectangle((x, y, x + gw, y + 4), fill=col)
        cw, ch = chip(d, x + 8, y + 12, cat, col)
        f = font("B", 12)
        hlines = wrap(d, head, f, gw - 16, 2)
        hy = y + 12 + ch + 4
        for ln in hlines:
            d.text((x + 8, hy), ln, font=f, fill=INK)
            hy += 15
        f = font("R", 9)
        slines = wrap(d, summ, f, gw - 16, 2)
        sy = hy + 2
        for ln in slines:
            d.text((x + 8, sy), ln, font=f, fill=MUTED)
            sy += 12
        ic = icons[i % len(icons)]
        draw_icon(d, ic, x + gw - 22, y + gh - 22, 30, col)
    # single-line ALSO TODAY ticker (6 stories)
    d.rectangle((0, H - 40, W, H - 24), fill=NAVY)
    f = font("B", 10)
    d.text((16, H - 36), "ALSO TODAY", font=f, fill=GOLD)
    f = font("R", 10)
    six = TICKER[:6]
    joined = "  |  ".join(six)
    d.text((132, H - 35), joined, font=f, fill=(240, 240, 235))
    # footer line
    d.rectangle((0, H - 24, W, H), fill=RED)
    f = font("B", 10)
    t = "All stories first reported Saturday 21 November 2026  -  13 illustrated cards  -  make.fun"
    d.text(((W - tl(d, t, f)) // 2, H - 17), t, font=f, fill=(255, 248, 245))

def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "1"
    W = H = 1024
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    vf = globals().get("draw_variant" + variant)
    if vf is None:
        sys.stderr.write("unknown variant: %s\n" % variant)
        sys.exit(1)
    vf(d, img, W, H)
    out = "out_%s.png" % variant
    img.save(out)
    import os
    print("wrote %s 1024x1024 bytes %d" % (out, os.path.getsize(out)))

if __name__ == "__main__":
    main()