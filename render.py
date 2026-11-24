#!/usr/bin/env python3
"""Render a 1024x1024 newspaper front page summing up 24 Nov 2026.

Drawn entirely with Pillow primitives (no AI imagery, no external assets).
Deterministic: same input always produces byte-identical PNG output.
"""

import os

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- palette
PAPER = (247, 240, 221)   # warm newsprint
INK = (26, 26, 26)        # near-black type
RED = (139, 26, 26)       # deep red accent
GREY = (107, 101, 88)     # grey deck text
RULE = (201, 191, 165)    # hairline rule
GLOBE_BLUE = (58, 92, 122)
GLOBE_GREEN = (86, 122, 74)

W, H = 1024, 1024
MARGIN = 32
CW = W - 2 * MARGIN  # 960 content width

# ---------------------------------------------------------------- fonts
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------- text utils
def tracked_width(draw, text, fnt, tracking):
    """Width of text drawn with extra tracking between glyphs."""
    total = 0
    for ch in text:
        total += draw.textlength(ch, font=fnt) + tracking
    return total - tracking if text else 0


def draw_tracked(draw, cx, y, text, fnt, fill, tracking=3):
    """Draw centred text with letter tracking."""
    w = tracked_width(draw, text, fnt, tracking)
    x = cx - w / 2
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking


def fit_line(draw, text, fnt, max_w):
    """Truncate a single line with an ellipsis so it fits max_w."""
    if draw.textlength(text, font=fnt) <= max_w:
        return text
    ell = "\u2026"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if draw.textlength(text[:mid] + ell, font=fnt) <= max_w:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + ell


def wrap_lines(draw, text, fnt, max_w, max_lines):
    """Greedy word wrap; last line gets an ellipsis when text overflows."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and (len(lines) < len(words) or
                                     draw.textlength(lines[-1], font=fnt) > max_w):
        lines[-1] = fit_line(draw, lines[-1], fnt, max_w)
    return lines


# ---------------------------------------------------------------- content
MASTHEAD = "THE WORLD IN ONE DAY"
DATE_LINE = "TUESDAY 24 NOVEMBER 2026"

LEAD = {
    "kicker": "CLIMATE SUMMIT  \u2022  ANTALYA",
    "headline": "COP31 COLLAPSES",
    "subhead": "NO DEAL AFTER 49 HOURS",
    "deck": ("After 49+ hours of overtime, 197 nations leave Antalya with no "
             "agreement \u2014 the first COP failure since Copenhagen 2009. A final "
             "text that never mentioned fossil fuels was rejected by the EU, UK "
             "and island states, while oil producers blocked phase-out language."),
}

SECOND = [
    {
        "kicker": "WAR WIDENS",
        "headline": "IRAN HITS BAHRAIN, TANKERS IN HORMUZ",
        "body": ("IRGC missiles and drones hit US Patriot radars at Al-Riffa and "
                 "Awali bases in Bahrain and a civilian site on Sitra Island. Two "
                 "tankers were struck in the Strait of Hormuz as Iran readies 14 "
                 "tankers to test the blockade."),
    },
    {
        "kicker": "UKRAINE",
        "headline": "KYIV: 15 DEAD, PLEA FOR PATRIOTS",
        "body": ("Fifteen were killed across Ukraine, including 10 in a five-storey "
                 "collapse in Dymer. Zelenskyy urged the US to release paid-for "
                 "Patriot interceptors as Russia fired about 2,700 drones in a week."),
    },
]

# (region, [(title, deck), ...]) — 33 briefs across 7 regions
REGIONS = [
    ("EUROPE", [
        ("MANCHESTER EVACUATES 12,000", "Concert-goers cleared over mystery substance"),
        ("TURKEY SHUTS MEDIA", "Thousands march as outlets closed"),
        ("MACRON EYES SPENDING CURBS", "President seeks constitutional change"),
        ("LEGO PICKS PORTUGAL", "Eighth factory to rise in Portugal"),
        ("GRIPEN PILOT HELD FIRE", "Swedish jet spared suspected Russian missile"),
        ("FRENCH MPS: BAN TEAR GAS", "Lawmakers urge halt to riot gas"),
        ("GERMAN SCHOOLS GET THREATS", "Bomb-threat emails sent to schools"),
    ]),
    ("MIDDLE EAST", [
        ("UAE CONDEMNS IRAN", "Emirates denounces attack on Bahrain"),
        ("ISRAEL PROBES ARSON", "West Bank fire blamed on settlers"),
        ("NETANYAHU TALKS REVIVE", "Coalition talks with Eisenkot resume"),
    ]),
    ("NORTH AMERICA", [
        ("DEMOCRATS TAKE HOUSE", "258+ seats, most since 1992"),
        ("TRUMP SIGNALS HEALTH DEAL", "President open to talks with Democrats"),
        ("HUANG BACK AT NVIDIA", "CEO reinstated after Trump steps in"),
        ("10% CREDIT-CARD CAP", "Trump pledges rate ceiling"),
        ("SEATTLE ICE ARRESTS ANGER", "Detentions draw public fury"),
        ("STORM THREATENS THANKSGIVING", "East Coast travel at risk"),
        ("PRINCETON STUDENT HELD", "US detains Chinese national"),
    ]),
    ("ASIA-PACIFIC", [
        ("INDONESIA FACTORY FIRE", "3 dead, 37 missing in candy plant"),
        ("NEPAL PM IN DELHI", "Meets Modi; Rs 1.5tn package agreed"),
        ("KIM INSPECTS FACTORY", "North Korean leader tours plant"),
        ("KOREA RESHUFFLES CABINET", "Seoul announces ministerial changes"),
        ("THAI COURT UPHOLDS VERDICT", "Opposition MP's conviction stands"),
        ("AUSTRALIA PUTS AI FIRST", "AI at core of foreign policy"),
        ("INDIA TEST ENDS IN DRAW", "Cricket series level after draw"),
        ("HONG KONG MARKS FIRE YEAR", "Tai Po blaze remembered, one year on"),
    ]),
    ("AFRICA", [
        ("DRONES HIT KHARTOUM", "Homes and UN building struck"),
        ("NIGERIA PALACE GOES DARK", "President admits water, power cut"),
        ("COP32 HEADS TO ETHIOPIA", "Addis Ababa to host in 2027"),
    ]),
    ("LATIN AMERICA", [
        ("MEXICO NABS WANTED KINGPIN", "FBI-listed drug lord killed in shootout"),
    ]),
    ("GLOBAL", [
        ("UN: AI RULES IN A YEAR", "Chief urges risk framework in 12 months"),
        ("UN MAY LACK A CHIEF", "No successor in sight as year ends"),
        ("ROHINGYA HAIL ICJ RULING", "Court backs genocide case vs Myanmar"),
        ("THUNBERG FINED IN DENMARK", "Greta penalised for trespass"),
    ]),
]

ALSO_TODAY = [
    "Lisbon marches on cost of living",
    "Myanmar slams ASEAN",
    "Nvidia faces probe",
    "Korea minister quits in AI row",
]

SOURCES = ("Sources: AFP, AP, Reuters, Al Jazeera, SCMP, Firstpost, Gulf News, "
           "Khaleej Times \u2014 24 November 2026 editions.")

# ---------------------------------------------------------------- illustration
def draw_lead_art(draw, x0, y0, x1, y1):
    """Cracked globe + gavel + NO DEAL stamp, drawn with primitives."""
    cx, cy = (x0 + x1) // 2 - 10, y0 + 78
    r = 62
    # globe
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(233, 226, 205),
                 outline=INK, width=3)
    # simple land blobs
    draw.ellipse([cx - 42, cy - 38, cx - 2, cy - 6], fill=GLOBE_GREEN)
    draw.ellipse([cx + 4, cy + 8, cx + 44, cy + 42], fill=GLOBE_GREEN)
    draw.ellipse([cx + 18, cy - 44, cx + 46, cy - 14], fill=GLOBE_GREEN)
    # latitude / longitude hints
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=200, end=340, fill=GREY)
    draw.line([cx - r + 6, cy, cx + r - 6, cy], fill=GREY, width=1)
    # jagged crack across the globe
    crack = [(cx - 52, cy - 44), (cx - 28, cy - 18), (cx - 38, cy + 6),
             (cx - 10, cy + 22), (cx - 22, cy + 48), (cx + 6, cy + 58)]
    draw.line(crack, fill=RED, width=4, joint="curve")
    # gavel: handle + head, lower right of the globe (wood tone)
    wood = (122, 74, 42)
    gx, gy = cx + 30, cy + 44
    draw.line([gx, gy, gx + 48, gy + 24], fill=wood, width=6)
    draw.rectangle([gx + 40, gy + 6, gx + 70, gy + 26], fill=wood,
                   outline=INK, width=2)
    # NO DEAL stamp
    stamp = Image.new("RGBA", (200, 50), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    sf = font(SANS_B, 32)
    sd.text((6, 4), "NO DEAL", font=sf, fill=RED + (255,))
    sd.rectangle([2, 2, 197, 47], outline=RED + (255,), width=3)
    stamp = stamp.rotate(-7, expand=True, resample=Image.BICUBIC)
    return stamp


# ---------------------------------------------------------------- page build
def build(out_path):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    truncations = []

    # ---- masthead
    d.line([MARGIN, 26, W - MARGIN, 26], fill=INK, width=2)
    title_f = font(SERIF_B, 56)
    d.text(((W - d.textlength(MASTHEAD, font=title_f)) / 2, 34),
           MASTHEAD, font=title_f, fill=INK)
    draw_tracked(d, W // 2, 100, DATE_LINE, font(SANS_B, 18), RED, tracking=4)
    d.line([MARGIN, 126, W - MARGIN, 126], fill=INK, width=2)

    # ---- lead story
    lx, lw = MARGIN, 668
    rx = MARGIN + lw + 16
    rw = W - MARGIN - rx
    kick_f = font(SANS_B, 15)
    d.text((lx, 140), LEAD["kicker"], font=kick_f, fill=RED)
    head_f = font(SERIF_B, 52)
    d.text((lx, 162), LEAD["headline"], font=head_f, fill=INK)
    sub_f = font(SERIF_B, 27)
    d.text((lx, 222), LEAD["subhead"], font=sub_f, fill=INK)
    deck_f = font(SERIF, 17)
    deck_lines = wrap_lines(d, LEAD["deck"], deck_f, lw, 4)
    y = 254
    for line in deck_lines:
        d.text((lx, y), line, font=deck_f, fill=INK)
        y += 20
    # lead illustration (right): cracked globe, gavel, NO DEAL stamp
    stamp = draw_lead_art(d, rx, 138, rx + rw, 330)
    img.paste(stamp, (rx + 22, 248), stamp)

    # ---- divider
    d.line([MARGIN, 340, W - MARGIN, 340], fill=RULE, width=1)

    # ---- two half-page stories
    col_w = (CW - 16) // 2
    y0 = 352
    for i, story in enumerate(SECOND):
        x = MARGIN + i * (col_w + 16)
        d.text((x, y0), story["kicker"], font=kick_f, fill=RED)
        h_f = font(SERIF_B, 24)
        h_lines = wrap_lines(d, story["headline"], h_f, col_w, 1)
        yy = y0 + 22
        for line in h_lines:
            d.text((x, yy), line, font=h_f, fill=INK)
            yy += 28
        b_f = font(SERIF, 15)
        b_lines = wrap_lines(d, story["body"], b_f, col_w, 4)
        for line in b_lines:
            d.text((x, yy), line, font=b_f, fill=INK)
            yy += 19
    d.line([MARGIN, 486, W - MARGIN, 486], fill=RULE, width=1)

    # ---- region cards, 3 columns
    col_x = [MARGIN, MARGIN + 328, MARGIN + 656]
    col_w = 312
    # column assignment: balance card counts
    columns = [
        [REGIONS[0], REGIONS[1]],                 # EUROPE 7 + MIDDLE EAST 3
        [REGIONS[2], REGIONS[4], REGIONS[5]],     # N AMERICA 7 + AFRICA 3 + LATAM 1
        [REGIONS[3], REGIONS[6]],                 # ASIA-PACIFIC 8 + GLOBAL 4
    ]
    hdr_f = font(SANS_B, 15)
    t_f = font(SANS_B, 14)
    de_f = font(SANS, 12)
    top = 498
    card_h = 32
    hdr_h = 20
    for ci, groups in enumerate(columns):
        x = col_x[ci]
        y = top
        for name, cards in groups:
            d.text((x, y), name, font=hdr_f, fill=RED)
            d.line([x, y + 17, x + col_w, y + 17], fill=RULE, width=1)
            y += hdr_h
            for title, deck in cards:
                t = fit_line(d, title, t_f, col_w)
                if t != title:
                    truncations.append(("title", title))
                de = fit_line(d, deck, de_f, col_w)
                if de != deck:
                    truncations.append(("deck", deck))
                d.text((x, y), t, font=t_f, fill=INK)
                d.text((x, y + 16), de, font=de_f, fill=GREY)
                y += card_h
            y += 2
        if y > 936:
            truncations.append(("overflow", f"column {ci} ends at {y}"))

    # ---- also today strip
    y = 944
    d.line([MARGIN, y, W - MARGIN, y], fill=INK, width=2)
    at_f = font(SANS_B, 12)
    at_label = "ALSO TODAY:"
    d.text((MARGIN, y + 8), at_label, font=at_f, fill=RED)
    lx = MARGIN + d.textlength(at_label, font=at_f) + 10
    item_w = (W - MARGIN - lx) // len(ALSO_TODAY)
    it_f = font(SANS, 12)
    for i, item in enumerate(ALSO_TODAY):
        txt = fit_line(d, item, it_f, item_w - 12)
        if txt != item:
            truncations.append(("also", item))
        d.text((lx + i * item_w, y + 8), txt, font=it_f, fill=INK)

    # ---- sources line
    src_f = font(SANS, 12)
    sw = d.textlength(SOURCES, font=src_f)
    if sw > CW:
        truncations.append(("sources", "too wide"))
    d.text(((W - sw) / 2, 976), SOURCES, font=src_f, fill=GREY)

    img.save(out_path, format="PNG", optimize=True)
    return truncations


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    notes = build(os.path.join(here, "entry.png"))
    print("truncations/overflow:", notes if notes else "none")
    print("saved entry.png")
