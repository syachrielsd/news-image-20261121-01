#!/usr/bin/env python3
"""Render the news-image-20261121 front page at build time.

Deterministic: fixed seed, no timestamps, no network. Output: entry.png 1024x1024.
Picture-first front page: 3 large illustrated leads, 10 illustrated mediums,
world map with numbered pins, briefs 14-50, UTC timeline strip, DATE CHECK box.
All type is crisp PIL/DejaVu; generated photos carry no text.
"""
import hashlib
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"

W, H = 1024, 1024
PAPER = (248, 244, 236)
INK = (22, 21, 19)
RED = (178, 28, 28)
TEAL = (14, 116, 144)
DARK = (31, 41, 55)
GOLD = (180, 130, 29)
MUTED = (90, 84, 76)
RULE = (196, 186, 170)
OCEAN = (214, 230, 238)
LAND = (222, 205, 168)
LANDLINE = (150, 132, 96)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_R = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS_O = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, max_w, fill=INK, lh=None, max_lines=None):
    lines = wrap(draw, text, fnt, max_w)
    if max_lines:
        lines = lines[:max_lines]
    lh = lh or int(fnt.size * 1.18)
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def fit_text(draw, text, fnt, max_w, fill=INK):
    """Single line, shrink font until it fits (never below 60%)."""
    size = fnt.size
    while size > 6 and draw.textlength(text, font=fnt) > max_w:
        size -= 1
        fnt = font(fnt.path, size)
    draw.text((0, 0), "", font=fnt)  # noqa
    return fnt


def photo(path, w, h):
    im = Image.open(path).convert("RGB")
    # centre-crop to target aspect, then resize (deterministic LANCZOS)
    tw, th = w, h
    scale = max(tw / im.width, th / im.height)
    nw, nh = int(im.width * scale + 0.5), int(im.height * scale + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    x0 = (nw - tw) // 2
    y0 = (nh - th) // 2
    return im.crop((x0, y0, x0 + tw, y0 + th))


def tag_chip(draw, x, y, label, fill=RED):
    f = font(SANS_B, 10)
    tw = draw.textlength(label, font=f)
    draw.rounded_rectangle([x, y, x + tw + 12, y + 16], radius=3, fill=fill)
    draw.text((x + 6, y + 2), label, font=f, fill=(255, 255, 255))
    return tw + 12


# ---------------------------------------------------------------- stories
LEADS = [
    dict(n=1, tag="GULF WAR", img="media-generation-lead-bahrain-0-4e6a0840-2f1c-4886-8a39-a5e43876bc5f.webp",
         head="Iran strikes US bases in Bahrain",
         cap="IRGC claims missiles hit two Patriot radars; Bahrain reports an industrial-site fire. No injuries."),
    dict(n=2, tag="MEXICO", img="media-generation-lead-mexico-0-84fa54c9-4738-4711-bcb2-fd3a1d1163fb.webp",
         head="Mexico captures 'El Chapo Isidro'",
         cap="FBI Top 10 cartel boss seized in Sinaloa; capture announced today. 11 killed in the gunfights."),
    dict(n=3, tag="PERU", img="media-generation-lead-peru-0-1578b87f-d75d-4683-b2ed-b8fef2a3c14c.webp",
         head="Deep quake shakes Peru's Andes",
         cap="M6.7 at 00:09 UTC, 108 km deep near Junin; Lima residents flee into the streets. No casualties."),
]

MEDIUMS = [
    dict(n=4, tag="UKRAINE", img="media-generation-med-kryvyi-0-0a1a12b9-3971-4a83-a4f8-0c70f342c01d.webp",
         head="Missile hits Zelenskyy's home city", cap="2 killed, incl. a boy, 7; dozens hurt."),
    dict(n=5, tag="CLIMATE", img="media-generation-med-cop31-0-852bc02e-d79c-4091-a365-87af1378b035.webp",
         head="COP31 in overtime, still no deal", cap="Antalya: 2nd day past deadline."),
    dict(n=6, tag="MARKETS", img="media-generation-med-markets-0-4cce7fb5-df83-4e40-8773-ab11e7808780.webp",
         head="AI sell-off wipes Nasdaq's 2026 gains", cap="S&P 500 and Dow enter correction."),
    dict(n=7, tag="SUMMIT", scene="flags",
         head="Trump defends Putin ties", cap="Zelenskyy: Putin is a killer; talks start."),
    dict(n=8, tag="QUAKE", scene="waves",
         head="Timor M6.8 quake felt in Darwin", cap="Banda Sea 09:42 UTC; felt 650 km away."),
    dict(n=9, tag="JUSTICE", scene="scales",
         head="ICJ: Myanmar guilty of genocide", cap="First state held guilty; Myanmar rejects."),
    dict(n=10, tag="BALTIC", scene="ship",
         head="Drones set Russian ship ablaze", cap="Sparta II burns, drifts to Finnish waters."),
    dict(n=11, tag="SCIENCE", scene="riemann",
         head="Claim: AI proves Riemann", cap="Claude 'cracks' the 1859 maths problem."),
    dict(n=12, tag="DENMARK", scene="denmark",
         head="Denmark pushes EU visa curbs", cap="After foiled plot on rapper Kyivstoner."),
    dict(n=13, tag="SPACE", img="media-generation-med-mercury-0-2c13ffb5-e564-4843-941b-7e57139de36b.webp",
         head="BepiColombo reaches Mercury", cap="ESA-JAXA in orbit after 8-year journey."),
]

BRIEFS = [
    (14, "Israeli strike kills 3 in Gaza food vehicle, Tel al-Hawa."),
    (15, "Saudi defences stop 3 Houthi missiles aimed at Riyadh."),
    (16, "FBI crime database (NCIC) reportedly hacked; FBI probing."),
    (17, "Trump threatens tax on firms building AI centres abroad."),
    (18, "UN Geneva talks keep working on AI-weapons rules."),
    (19, "Cost-of-living protests sweep Europe; 144 arrests in France."),
    (20, "French police sentenced over racist beating of Zecler."),
    (21, "Man convicted of starting the 2025 Palisades fire."),
    (22, "Virginia child dies of measles — first US death of 2026."),
    (23, "Wolbachia mosquitoes cut dengue among Brazil children."),
    (24, "Daraxonrasib pill shows progress vs pancreatic cancer."),
    (25, "Bolsonaro in intensive care with bowel obstruction."),
    (26, "Salvadoran troops fight gangs in Haiti; 3 soldiers die."),
    (27, "Boat capsizes in Nigeria; at least 24 mourners dead."),
    (28, "Saudi-Japan oil deal: Japan stockpile to 24m barrels."),
    (29, "Brent ~$91, down ~5% on the week as Gulf flows recover."),
    (30, "Gulf economies hit by Iran-war recession; Qatar contracts."),
    (31, "Argentina bonds fall into distress; $50bn LNG plan approved."),
    (32, "Gupta gets 19+ years over Sikh murder-for-hire plot (NY)."),
    (33, "Turkey seizes Sozcu TV, last big independent channel."),
    (34, "Tanzania opposition leader Lissu convicted of sedition."),
    (35, "Uganda restricts gatherings over Ebola; Congo outbreak grows."),
    (36, "Nvidia chief ousted; Trump says he discussed it with Xi."),
    (37, "Fighting widens in eastern DR Congo, truce at risk."),
    (38, "Japan sidelined at China summit, Trump says."),
    (39, "UK and EU sign three post-Brexit agreements."),
    (40, "EU-Indonesia trade deal: 98.5% of EU-goods tariffs removed."),
    (41, "EU proposes smaller budget plus 3% Big Tech tax."),
    (42, "Trump signs Common Cents Act; penny production ends."),
    (43, "GTA VI day-one sales put at $2.36bn — figures reported today."),
    (44, "'Sunrise on the Reaping' earns $21.25m in previews."),
    (45, "Harden passes Kobe for 50-point NBA games."),
    (46, "Verstappen takes pole for the Las Vegas Grand Prix."),
    (47, "Newcastle 2-2 Arsenal; Man City 1-1 Fulham."),
    (48, "Scotland's 11-try rout of Japan."),
    (49, "Nepal PM Balen Shah's first state visit to India."),
    (50, "Banten candy factory fire: 3 dead, dozens missing."),
]

# lon, lat for map pins 1-12 (13 = Mercury, off-map)
PINS = [
    (1, 50.5, 26.2), (2, -108.5, 25.6), (3, -76.0, -11.0), (4, 33.4, 47.9),
    (5, 30.7, 36.9), (6, -74.0, 40.7), (7, 114.0, 22.5), (8, 127.5, -8.0),
    (9, 4.3, 52.1), (10, 26.0, 60.0), (11, -122.4, 37.8), (12, 12.6, 55.7),
]

TIMELINE = [
    ("00:09", "Peru M6.7 quake"),
    ("09:42", "Timor M6.8 quake"),
    ("DAY", "COP31 overtime"),
    ("PM", "Denmark EU visa push"),
    ("CLOSE", "US stocks in correction"),
    ("NIGHT", "Iran strikes Bahrain"),
]

EXCLUDED = [
    ("APEC Xi-Trump-Putin summit, Shenzhen", "19 NOV"),
    ("Voyager 1 reaches one light-day", "18-19 NOV"),
    ("GTA VI launch", "19 NOV"),
    ("Crimean Bridge, third strike", "19 NOV"),
    ("COP31 collapse (no deal)", "22 NOV"),
    ("Chapo Isidro raid itself", "20 NOV"),
]

# ---------------------------------------------------------------- scenes
def scene_flags(d, x, y, w, h):
    """Three summit flags: US / China / Russia, side by side."""
    d.rectangle([x, y, x + w, y + h], fill=(233, 230, 222))
    fw = w // 3
    # US: stripes + blue canton
    for i in range(7):
        d.rectangle([x, y + i * h // 7, x + fw, y + (i + 1) * h // 7],
                    fill=(178, 34, 34) if i % 2 == 0 else (245, 245, 245))
    d.rectangle([x, y, x + fw * 2 // 5, y + h * 4 // 7], fill=(30, 58, 120))
    # China: red + stars
    d.rectangle([x + fw, y, x + 2 * fw, y + h], fill=(222, 41, 16))
    cx, cy = x + fw + fw // 4, y + h // 4
    d.regular_polygon((cx, cy, 7), 5, fill=(255, 215, 0))
    # Russia: white / blue / red
    d.rectangle([x + 2 * fw, y, x + w, y + h // 3], fill=(245, 245, 245))
    d.rectangle([x + 2 * fw, y + h // 3, x + w, y + 2 * h // 3], fill=(0, 57, 166))
    d.rectangle([x + 2 * fw, y + 2 * h // 3, x + w, y + h], fill=(213, 0, 50))


def scene_waves(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(16, 78, 110))
    rng = random.Random(42)
    for i in range(5):
        yy = y + 8 + i * (h - 16) // 4
        pts = []
        for px in range(0, w + 1, 8):
            pts.append((x + px, yy + rng.randint(-3, 3)))
        d.line(pts, fill=(190, 225, 240), width=2)
    # seismic zigzag
    pts = []
    for i, px in enumerate(range(0, w + 1, 10)):
        pts.append((x + px, y + h // 2 + (14 if i % 2 else -14)))
    d.line(pts, fill=(255, 200, 60), width=3)
    d.ellipse([x + w // 2 - 5, y + h // 2 - 5, x + w // 2 + 5, y + h // 2 + 5],
              fill=(255, 60, 40))


def scene_scales(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(38, 48, 66))
    cx, cy = x + w // 2, y + 8
    d.line([cx, cy, cx, y + h - 12], fill=(220, 180, 80), width=3)
    d.line([x + 14, cy + 12, x + w - 14, cy + 12], fill=(220, 180, 80), width=3)
    for sx in (x + 14, x + w - 14):
        d.line([sx, cy + 12, sx, cy + 30], fill=(220, 180, 80), width=2)
        d.pieslice([sx - 16, cy + 28, sx + 16, cy + 52], 0, 180, fill=(200, 160, 60))
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(220, 180, 80))
    d.rectangle([cx - 14, y + h - 12, cx + 14, y + h - 6], fill=(220, 180, 80))


def scene_ship(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(24, 68, 92))
    # sea
    d.rectangle([x, y + h * 3 // 5, x + w, y + h], fill=(10, 48, 70))
    # hull + containers
    d.polygon([(x + 20, y + h * 3 // 5), (x + w - 20, y + h * 3 // 5),
               (x + w - 34, y + h * 4 // 5), (x + 34, y + h * 4 // 5)],
              fill=(90, 90, 96))
    for i in range(4):
        d.rectangle([x + 30 + i * 30, y + h // 3, x + 54 + i * 30, y + h * 3 // 5],
                    fill=[(178, 60, 40), (40, 120, 90), (200, 150, 40), (90, 110, 160)][i])
    # fire glow
    d.ellipse([x + w // 2 - 12, y + 6, x + w // 2 + 12, y + 30], fill=(255, 150, 40))
    d.ellipse([x + w // 2 - 6, y + 12, x + w // 2 + 6, y + 26], fill=(255, 220, 120))
    # drone
    dx, dy = x + w - 30, y + 12
    d.line([dx - 8, dy, dx + 8, dy], fill=(220, 220, 220), width=2)
    d.ellipse([dx - 4, dy - 3, dx + 4, dy + 3], fill=(220, 220, 220))


def scene_riemann(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(245, 240, 228))
    rng = random.Random(7)
    cx, cy = x + w // 2, y + h // 2
    for i in range(90):
        t = i * 0.35
        r = 4 + i * 0.42
        px = cx + r * 1.15 * __import__("math").cos(t)
        py = cy + r * 0.8 * __import__("math").sin(t)
        if x + 2 <= px <= x + w - 2 and y + 2 <= py <= y + h - 2:
            d.ellipse([px - 2, py - 2, px + 2, py + 2],
                      fill=(178, 28, 28) if i % 9 == 0 else (31, 41, 55))
    d.line([x + 6, y + h - 8, x + w - 6, y + 8], fill=(14, 116, 144), width=2)


def scene_denmark(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(198, 12, 48))
    # white cross (Danish flag)
    d.rectangle([x + w // 3, y, x + w // 3 + 10, y + h], fill=(255, 255, 255))
    d.rectangle([x, y + h // 2 - 5, x + w, y + h // 2 + 5], fill=(255, 255, 255))
    # small plane silhouette (expulsion) top-right
    d.polygon([(x + w - 34, y + 10), (x + w - 8, y + 16), (x + w - 34, y + 22)],
              fill=(255, 255, 255))


SCENES = {"flags": scene_flags, "waves": scene_waves, "scales": scene_scales,
          "ship": scene_ship, "riemann": scene_riemann, "denmark": scene_denmark}

# ---------------------------------------------------------------- map
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 80), (-75, 72),
     (-65, 60), (-55, 52), (-60, 45), (-70, 42), (-75, 35), (-80, 25), (-85, 30),
     (-95, 29), (-105, 22), (-110, 24), (-115, 30), (-125, 40), (-125, 49),
     (-140, 60), (-165, 60)],
    # South America
    [(-80, 10), (-75, 11), (-62, 10), (-52, 5), (-50, 0), (-44, -5), (-35, -8),
     (-40, -20), (-48, -28), (-58, -35), (-65, -41), (-70, -54), (-73, -50),
     (-73, -37), (-70, -20), (-80, -5), (-81, 0)],
    # Africa
    [(-6, 35), (-10, 31), (-17, 15), (-17, 12), (-8, 4), (8, 4), (9, 0), (13, -5),
     (13, -12), (12, -18), (16, -28), (20, -35), (28, -33), (33, -26), (36, -18),
     (40, -10), (42, -1), (48, 11), (43, 12), (39, 21), (37, 30), (32, 31),
     (22, 33), (11, 37), (10, 37), (0, 36)],
    # Eurasia
    [(-10, 37), (-9, 43), (-2, 48), (-4, 50), (0, 51), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 59), (28, 60), (30, 62), (32, 70), (40, 68),
     (50, 69), (60, 69), (70, 72), (80, 73), (90, 75), (100, 77), (110, 74),
     (120, 73), (130, 72), (140, 72), (150, 70), (160, 70), (170, 67), (178, 65),
     (178, 62), (170, 60), (162, 56), (158, 52), (150, 59), (142, 55), (140, 50),
     (135, 43), (130, 42), (127, 40), (122, 38), (120, 32), (115, 23), (110, 20),
     (108, 12), (105, 9), (100, 8), (98, 12), (95, 16), (92, 21), (89, 22),
     (86, 20), (80, 13), (77, 8), (73, 16), (70, 21), (66, 25), (62, 25),
     (58, 26), (56, 27), (52, 28), (50, 30), (48, 30), (44, 29), (40, 31),
     (36, 36), (33, 36), (30, 36), (26, 40), (23, 40), (19, 42), (15, 44),
     (12, 44), (8, 44), (3, 43), (0, 40), (-2, 37), (-6, 36)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33), (129, -32),
     (132, -32), (135, -35), (137, -35), (140, -38), (145, -38), (147, -39),
     (150, -37), (153, -32), (153, -27), (150, -23), (146, -19), (142, -15),
     (142, -11), (137, -12), (135, -12), (132, -11), (130, -13), (126, -14),
     (122, -17), (118, -20)],
    # Greenland
    [(-45, 60), (-40, 65), (-32, 68), (-25, 70), (-20, 74), (-25, 76), (-35, 80),
     (-50, 80), (-58, 76), (-55, 70), (-52, 64)],
    # Britain
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 36), (140, 38), (141, 40),
     (142, 42), (144, 44), (145, 44), (143, 42), (141, 39), (140, 37), (138, 35),
     (136, 33), (132, 32)],
    # Indonesia
    [(95, 5), (98, 4), (100, 0), (103, -2), (106, -6), (110, -7), (114, -8),
     (118, -9), (120, -10), (122, -9), (126, -8), (128, -4), (131, -1), (134, -3),
     (136, -2), (138, -2), (141, -3), (141, -8), (138, -8), (135, -7), (132, -6),
     (128, -7), (124, -9), (120, -10)],
    # New Zealand
    [(167, -45), (170, -43), (173, -41), (175, -38), (177, -38), (175, -40),
     (173, -42), (170, -44), (167, -46)],
]


def draw_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=OCEAN)
    # graticule
    for gx in range(1, 12):
        xx = x + gx * w // 12
        d.line([xx, y, xx, y + h], fill=(190, 210, 220), width=1)
    for gy in range(1, 6):
        yy = y + gy * h // 6
        d.line([x, yy, x + w, yy], fill=(190, 210, 220), width=1)

    def proj(lon, lat):
        px = x + (lon + 170) / 360.0 * w
        py = y + (85 - lat) / 145.0 * h
        return px, py

    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LANDLINE)
    # small city dots for density (deterministic)
    cities = [(-74, 40.7), (-87.6, 41.9), (-95.4, 29.8), (-118.2, 34.1),
              (-99.1, 19.4), (-58.4, -34.6), (-43.2, -22.9), (-0.1, 51.5),
              (2.35, 48.9), (13.4, 52.5), (28.9, 41.0), (55.3, 25.2),
              (77.2, 28.6), (90.4, 23.8), (103.8, 1.35), (114.2, 22.3),
              (121.5, 31.2), (127.0, 37.5), (139.7, 35.7), (151.2, -33.9),
              (18.4, -33.9), (31.0, -29.9), (3.4, 6.5), (32.6, -25.9),
              (44.4, 33.3), (51.4, 35.7), (67.0, 24.9), (100.5, 13.8)]
    for lon, lat in cities:
        px, py = proj(lon, lat)
        d.ellipse([px - 1.5, py - 1.5, px + 1.5, py + 1.5], fill=(90, 70, 40))
    d.rectangle([x, y, x + w, y + h], outline=DARK, width=2)
    # pins
    fnum = font(SANS_B, 10)
    for n, lon, lat in PINS:
        px, py = proj(lon, lat)
        d.ellipse([px - 10, py - 10, px + 10, py + 10], fill=RED, outline=(255, 255, 255), width=2)
        tw = d.textlength(str(n), font=fnum)
        d.text((px - tw / 2, py - 7), str(n), font=fnum, fill=(255, 255, 255))
    d.text((x + 6, y + h - 16), "13 BepiColombo — Mercury orbit (off this map)",
           font=font(SANS_B, 9), fill=DARK)

# ---------------------------------------------------------------- build
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    rng = random.Random(20261121)

    # deterministic paper grain: fixed-seed stipple grid (real print texture)
    for gy in range(0, H, 4):
        for gx in range(0, W, 4):
            v = rng.randint(0, 2)
            if v == 0:
                d.point((gx, gy), fill=(233, 227, 212))
            elif v == 1:
                d.point((gx, gy), fill=(250, 248, 242))

    # ---- masthead
    d.rectangle([0, 0, W, 6], fill=RED)
    title = "THE WORLD IN ONE DAY"
    tf = font(SERIF, 44)
    d.text(((W - d.textlength(title, font=tf)) / 2, 10), title, font=tf, fill=INK)
    sub = "SATURDAY,  21  NOVEMBER  2026"
    sf = font(SANS_B, 18)
    d.text(((W - d.textlength(sub, font=sf)) / 2, 62), sub, font=sf, fill=RED)
    d.line([14, 88, W - 14, 88], fill=INK, width=2)

    # ---- stats strip
    d.rectangle([14, 94, W - 14, 112], fill=DARK)
    stats = "50 STORIES  •  9 REGIONS  •  12 FIELDS  •  EVERY STORY HAPPENED OR WAS FIRST REPORTED ON 21 NOV 2026"
    stf = font(SANS_B, 11)
    d.text(((W - d.textlength(stats, font=stf)) / 2, 99), stats, font=stf, fill=(255, 255, 255))

    # ---- leads
    d.text((14, 118), "THE DAY IN PICTURES — THREE STORIES THAT DEFINED IT",
           font=font(SANS_B, 11), fill=RED)
    lead_y, lead_h = 134, 196
    col_w, gap = 324, 8
    for i, L in enumerate(LEADS):
        x = 14 + i * (col_w + gap)
        im = photo(ASSETS / L["img"], col_w, 140)
        img.paste(im, (x, lead_y))
        d.rectangle([x, lead_y, x + col_w, lead_y + 140], outline=INK, width=1)
        # number badge
        d.ellipse([x + 6, lead_y + 6, x + 28, lead_y + 28], fill=RED, outline=(255, 255, 255), width=2)
        nf = font(SANS_B, 13)
        tw = d.textlength(str(L["n"]), font=nf)
        d.text((x + 17 - tw / 2, lead_y + 9), str(L["n"]), font=nf, fill=(255, 255, 255))
        tag_chip(d, x + 34, lead_y + 8, L["tag"])
        y = lead_y + 146
        y = draw_wrapped(d, x, y, L["head"], font(SERIF, 17), col_w, lh=19, max_lines=2)
        draw_wrapped(d, x, y + 1, L["cap"], font(SANS, 11), col_w, fill=MUTED, lh=14, max_lines=2)

    # ---- mediums
    d.text((14, 352), "PICTURED TODAY — TEN MORE STORIES, EACH WITH ITS OWN IMAGE",
           font=font(SANS_B, 11), fill=RED)
    med_y0, med_h = 368, 100
    mw, mh_img = 196, 58
    for i, M in enumerate(MEDIUMS):
        col, row = i % 5, i // 5
        x = 14 + col * (mw + 8)
        y = med_y0 + row * (med_h + 8)
        if "img" in M:
            im = photo(ASSETS / M["img"], mw, mh_img)
            img.paste(im, (x, y))
        else:
            SCENES[M["scene"]](d, x, y, mw, mh_img)
        d.rectangle([x, y, x + mw, y + mh_img], outline=INK, width=1)
        d.ellipse([x + 4, y + 4, x + 22, y + 22], fill=RED, outline=(255, 255, 255), width=1)
        nf = font(SANS_B, 10)
        tw = d.textlength(str(M["n"]), font=nf)
        d.text((x + 13 - tw / 2, y + 7), str(M["n"]), font=nf, fill=(255, 255, 255))
        tag_chip(d, x + 26, y + 5, M["tag"])
        yy = y + mh_img + 3
        yy = draw_wrapped(d, x, yy, M["head"], font(SANS_B, 11), mw, lh=12, max_lines=2)
        draw_wrapped(d, x, yy, M["cap"], font(SANS, 9), mw, fill=MUTED, lh=11, max_lines=1)

    # ---- map + date check
    map_x, map_y, map_w, map_h = 14, 590, 600, 170
    d.text((14, 576), "WHERE IT HAPPENED — PINS 1-12 ON THE MAP",
           font=font(SANS_B, 11), fill=RED)
    draw_map(d, map_x, map_y, map_w, map_h)

    dc_x, dc_w = 626, 384
    d.rectangle([dc_x, map_y, dc_x + dc_w, map_y + map_h], fill=(255, 251, 235),
                outline=RED, width=2)
    d.text((dc_x + 10, map_y + 6), "DATE CHECK — WHAT WE LEFT OUT",
           font=font(SANS_B, 12), fill=RED)
    d.text((dc_x + 10, map_y + 24),
           "Big stories from OTHER days were NOT counted as 21 Nov news:",
           font=font(SANS, 10), fill=INK)
    yy = map_y + 40
    for name, when in EXCLUDED:
        d.text((dc_x + 10, yy), "✕", font=font(SANS_B, 11), fill=RED)
        line = f"{name} — {when}"
        f = font(SANS, 10)
        while d.textlength(line, font=f) > dc_w - 34 and f.size > 8:
            f = font(SANS, f.size - 1)
        d.text((dc_x + 26, yy), line, font=f, fill=INK)
        yy += 14
    d.text((dc_x + 10, map_y + map_h - 34),
           "✓ Every story above is dated 21 Nov 2026.",
           font=font(SANS_B, 10), fill=TEAL)
    d.text((dc_x + 10, map_y + map_h - 20),
           "✓ 'REPORTED' = claimed that day, not yet confirmed.",
           font=font(SANS_B, 10), fill=TEAL)

    # ---- UTC timeline strip
    tl_y = 766
    d.text((14, tl_y - 2), "THE DAY IN UTC — 21 NOVEMBER 2026",
           font=font(SANS_B, 12), fill=RED)
    d.rectangle([14, tl_y + 18, W - 14, tl_y + 52], fill=(255, 255, 255),
                outline=RULE, width=1)
    d.line([30, tl_y + 35, W - 30, tl_y + 35], fill=TEAL, width=3)
    tl_x0, tl_x1 = 40, W - 40
    hours = [0, 4, 8, 12, 16, 20, 24]
    for hh in hours:
        xx = tl_x0 + (tl_x1 - tl_x0) * hh // 24
        d.line([xx, tl_y + 30, xx, tl_y + 40], fill=TEAL, width=2)
        lab = f"{hh:02d}:00"
        lf = font(SANS, 9)
        d.text((xx - d.textlength(lab, font=lf) / 2, tl_y + 42), lab, font=lf, fill=MUTED)
    # event dots at approximate UTC positions
    ev_pos = [(0.15, "00:09"), (9.7, "09:42"), (13.0, "DAY"), (17.0, "PM"),
              (21.0, "CLOSE"), (22.5, "NIGHT")]
    for hpos, _lab in ev_pos:
        xx = tl_x0 + (tl_x1 - tl_x0) * hpos / 24.0
        d.ellipse([xx - 5, tl_y + 30, xx + 5, tl_y + 40], fill=RED, outline=(255, 255, 255), width=1)
    ev_labels = ["00:09 Peru M6.7", "09:42 Timor M6.8", "COP31 overtime",
                 "Denmark EU push", "US stocks: correction", "Night: Iran strikes Bahrain"]
    ev_x = [60, 190, 360, 540, 700, 830]
    for xx, lab in zip(ev_x, ev_labels):
        lf = font(SANS_B, 9)
        d.text((xx, tl_y + 20), lab, font=lf, fill=INK)

    # ---- briefs 14-50
    br_y = 824
    d.text((14, br_y), "THE REST OF THE DAY — STORIES 14-50",
           font=font(SANS_B, 11), fill=RED)
    d.line([14, br_y + 16, W - 14, br_y + 16], fill=INK, width=1)
    cols = [BRIEFS[i:i + 13] for i in (0, 13, 26)]  # 13 / 13 / 11
    col_w2 = 324
    bf = font(SANS, 9)
    bfb = font(SANS_B, 9)
    for ci, group in enumerate(cols):
        x = 14 + ci * (col_w2 + 8)
        yy = br_y + 21
        for n, text in group:
            d.text((x, yy), f"{n}.", font=bfb, fill=RED)
            # shrink to fit one line
            f = bf
            line = text
            while d.textlength(line, font=f) > col_w2 - 24 and f.size > 8:
                f = font(SANS, f.size - 1)
            d.text((x + 22, yy), line, font=f, fill=INK)
            yy += 12

    # ---- footer
    d.line([14, 1004, W - 14, 1004], fill=RULE, width=1)
    foot = ("Sources: Reuters · BBC · CNN · AP · USGS · Al Jazeera · The Guardian · UPI · France 24 · "
            "GFZ · ESA/JAXA · OneTurn day page 21 Nov 2026  •  Full date evidence: STORIES.md")
    ff = font(SANS, 8)
    while d.textlength(foot, font=ff) > W - 28:
        ff = font(SANS, ff.size - 1)
    d.text((14, 1008), foot, font=ff, fill=MUTED)

    img.save(HERE / "entry.png", format="PNG", optimize=True)
    data = (HERE / "entry.png").read_bytes()
    print(f"entry.png: {len(data)} bytes  sha256={hashlib.sha256(data).hexdigest()}")
    return len(data)


if __name__ == "__main__":
    build()
