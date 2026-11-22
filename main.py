#!/usr/bin/env python3
"""Draw "The World in One Day" -- Sunday 22 November 2026.

A newspaper front page that sums up one day of world news in a single
1024x1024 picture.  Every picture on the page is drawn from lines and
shapes; there are no photographs, no external files and no third-party
libraries.  The type is DejaVu Serif, rasterised into the blob below by
/tmp/gen_font.py (PIL, run once on this machine) and decoded here with
the standard library only.

Standard library only: base64, json, math, os, struct, zlib.

Run from this folder:

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

That writes out/entry.png.  Without MAKEFUN_OUTPUT_DIR the image is
written next to this script.  Running it again produces a byte-identical
file: no randomness, no timestamps, no dictionary-order dependence.

Layout (top to bottom): masthead and date, a subtitle of the three lead
stories, a strip of six numbers, a colour bar of the six regions, three
large front-page panels with drawn scenes, ten smaller panels with drawn
scenes, a world map with numbered pins, a numbered list of the remaining
stories, a date-check box of stories that were deliberately left out,
and a footer.
"""

import base64
import json
import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- colours
PAPER = (253, 251, 242)   # newsprint cream
INK = (17, 17, 17)        # near-black ink
GREY = (96, 96, 90)       # secondary text
LIGHT = (226, 222, 208)   # panel borders and rules
RED = (178, 34, 28)       # kickers, pins, accents
DARKRED = (122, 20, 16)
SEA = (203, 226, 238)     # map sea
LAND = (224, 210, 166)    # map land
LAND_LINE = (150, 135, 95)
NAVY = (18, 32, 64)       # night sky
SKY = (168, 205, 228)     # day sky
GOLD = (201, 162, 39)

REGION_COLOURS = {
    "MIDDLE EAST": (178, 57, 46),
    "EUROPE": (31, 78, 121),
    "ASIA-PACIFIC": (46, 125, 50),
    "THE AMERICAS": (211, 108, 24),
    "AFRICA": (106, 76, 147),
    "GLOBAL": (90, 90, 90),
}

FONT_BLOB = "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"  # __GENERATED__

_FONT = None


def _font():
    global _FONT
    if _FONT is None:
        _FONT = json.loads(zlib.decompress(base64.b64decode(FONT_BLOB)))
    return _FONT


def _glyphs(name):
    return _font()["fonts"][name]["glyphs"]


def text_width(text, name, scale=1):
    g = _glyphs(name)
    total = 0
    for ch in text:
        rec = g.get(ch) or g.get("?")
        total += rec[0] * scale
    return total


def _blit(cv, x, y, w, h, rows, color, scale):
    stride = (w + 7) // 8
    for yy in range(h):
        for xx in range(w):
            byte = rows[yy * stride + xx // 8]
            if byte & (0x80 >> (xx % 8)):
                if scale == 1:
                    cv.set(x + xx, y + yy, color)
                else:
                    cv.fill(x + xx * scale, y + yy * scale, scale, scale, color)


def draw_text(cv, x, y, text, name, color, scale=1):
    """Draw text; returns the x just past the last glyph.

    Each glyph carries its ink-box top relative to the font's ascender
    line, so every glyph in a line shares one baseline: draw at y + top.
    """
    g = _glyphs(name)
    cx = x
    for ch in text:
        rec = g.get(ch) or g.get("?")
        adv, w, h, top, b64 = rec
        if w and h:
            rows = base64.b64decode(b64)
            _blit(cv, cx, y + top, w, h, rows, color, scale)
        cx += adv * scale
    return cx


def wrap(text, name, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, name, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(cv, x, y, text, name, color, scale, max_w, leading):
    lines = wrap(text, name, scale, max_w)
    for i, line in enumerate(lines):
        draw_text(cv, x, y + i * leading, line, name, color, scale)
    return len(lines)


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def fill(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, color):
        self.fill(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        for yy in range(-r, r + 1):
            half = int(math.sqrt(max(0, r * r - yy * yy)))
            self.fill(cx - half, cy + yy, half * 2 + 1, 1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for yy in range(-ry, ry + 1):
            t = 1.0 - (yy * yy) / float(ry * ry)
            half = int(rx * math.sqrt(max(0.0, t)))
            self.fill(cx - half, cy + yy, half * 2 + 1, 1, color)

    def polygon(self, pts, color):
        # scanline fill, integer math, deterministic order
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / float(y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill(int(math.ceil(xs[k])), y,
                          int(math.floor(xs[k + 1])) - int(math.ceil(xs[k])) + 1, 1, color)

    def rect(self, x, y, w, h, color):
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)


def write_png(path, cv):
    raw = b""
    for y in range(cv.h):
        raw += b"\x00" + bytes(cv.buf[y * cv.w * 3:(y + 1) * cv.w * 3])

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        c += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
           chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


# ------------------------------------------------------------------ scenes
# Every scene draws inside its box (x, y, w, h) with flat shapes only.
# The scenes are the front page's pictures: a viewer who cannot read the
# headlines should still tell, from each picture, what the story is.

def _stars(cv, x, y, w, h, n, seed):
    # deterministic pseudo-random stars from a tiny LCG
    s = seed
    for _ in range(n):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        sx = x + s % w
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        sy = y + s % (h // 2)
        cv.set(sx, sy, (255, 255, 220))
        if s % 3 == 0:
            cv.set(sx + 1, sy, (255, 255, 220))


def _flame(cv, x, y, w, h):
    # a stylised flame: orange triangle stack with a yellow core
    cv.polygon([(x, y + h), (x + w // 2, y), (x + w, y + h)], (232, 98, 20))
    cv.polygon([(x + w // 4, y + h), (x + w // 2, y + h // 3),
                (x + 3 * w // 4, y + h)], (245, 196, 40))


def _smoke(cv, x, y, r, color=(120, 120, 118)):
    cv.circle(x, y, r, color)
    cv.circle(x + r // 2, y - r // 2, r * 3 // 4, color)
    cv.circle(x - r // 3, y - r // 2, r // 2, color)


def scene_gulf_strikes(cv, x, y, w, h):
    # Night over the Gulf: dark sky, missile trails, base, explosions.
    cv.fill(x, y, w, h, NAVY)
    _stars(cv, x, y, w, h, 26, 7)
    # missile trails: bright arcs falling to the base
    for tx, ty, lx in ((x + w // 4, y + 8, 26), (x + w // 2, y + 4, 34),
                       (x + 3 * w // 4, y + 10, 22)):
        cv.line(tx, ty, tx - lx // 2, ty + 44, (255, 240, 180))
        cv.line(tx, ty, tx - lx // 2, ty + 44, (255, 240, 180))
        cv.circle(tx - lx // 2, ty + 44, 3, (255, 200, 60))
    # base buildings on the ground
    gy = y + h - 26
    cv.fill(x, gy, w, 26, (10, 18, 38))
    for bx, bw, bh in ((8, 34, 16), (52, 22, 22), (88, 40, 13),
                       (140, 26, 19), (180, 34, 15), (226, 24, 21),
                       (262, 30, 14)):
        cv.fill(x + bx, gy - bh, bw, bh, (24, 38, 70))
        for wy in range(gy - bh + 4, gy - 2, 7):
            cv.fill(x + bx + 4, wy, 3, 3, (255, 220, 120))
    # explosions over two buildings
    _flame(cv, x + 56, gy - 34, 16, 16)
    _flame(cv, x + 232, gy - 30, 14, 14)
    _smoke(cv, x + 64, gy - 40, 8)
    _smoke(cv, x + 240, gy - 36, 7)


def scene_cop31(cv, x, y, w, h):
    # Conference hall: long table, delegates, globe, thermometer, clock.
    cv.fill(x, y, w, h, (233, 228, 210))
    # back wall and flags
    for i, col in enumerate(((31, 78, 121), (178, 57, 46), (46, 125, 50),
                             (211, 108, 24), (106, 76, 147))):
        fx = x + 14 + i * 52
        cv.fill(fx, y + 8, 30, 18, col)
        cv.vline(fx + 15, y + 8, 30, INK)
    # globe on a stand, left
    gx, gy = x + 44, y + 46
    cv.circle(gx, gy, 20, (52, 120, 170))
    cv.ellipse(gx - 6, gy - 4, 12, 7, (86, 170, 90))
    cv.ellipse(gx + 4, gy + 8, 9, 5, (86, 170, 90))
    cv.fill(gx - 2, gy + 20, 4, 10, INK)
    cv.fill(gx - 12, gy + 30, 24, 3, INK)
    # thermometer, right of the globe
    tx = x + 96
    cv.fill(tx, y + 30, 8, 34, (255, 255, 255))
    cv.rect(tx, y + 30, 8, 34, INK)
    cv.fill(tx + 1, y + 48, 6, 15, RED)
    cv.circle(tx + 4, y + 66, 7, RED)
    # clock on the wall
    cx, cy = x + w - 46, y + 40
    cv.circle(cx, cy, 16, (255, 255, 255))
    cv.circle(cx, cy, 16, INK)
    cv.line(cx, cy, cx, cy - 10, INK)
    cv.line(cx, cy, cx + 8, cy + 3, INK)
    # long table with delegates
    ty = y + h - 34
    cv.fill(x + 10, ty, w - 20, 8, (120, 72, 40))
    cv.fill(x + 10, ty + 8, w - 20, 22, (88, 52, 28))
    for i in range(7):
        dx = x + 26 + i * 40
        cv.circle(dx, ty - 12, 7, (222, 184, 150))
        cv.polygon([(dx - 10, ty - 4), (dx, ty - 16), (dx + 10, ty - 4)],
                   ((31, 78, 121), (178, 57, 46), (46, 125, 50),
                    (211, 108, 24), (106, 76, 147), (90, 90, 90),
                    (31, 78, 121))[i])
    # "NEW TEXT" document on the table
    cv.fill(x + w - 66, ty - 22, 44, 16, (255, 255, 255))
    cv.rect(x + w - 66, ty - 22, 44, 16, INK)
    cv.hline(x + w - 60, ty - 16, 32, INK)
    cv.hline(x + w - 60, ty - 11, 32, GREY)


def scene_barrage(cv, x, y, w, h):
    # Night city under a drone barrage: skyline, trails, fires, river.
    cv.fill(x, y, w, h, NAVY)
    _stars(cv, x, y, w, h, 22, 21)
    # drone trails: dotted diagonals with a bright head
    for sx, sy, ex, ey in ((x + 30, y + 6, x + 90, y + 66),
                           (x + 120, y + 2, x + 170, y + 58),
                           (x + 210, y + 8, x + 250, y + 62),
                           (x + 260, y + 4, x + 300, y + 54)):
        steps = 7
        for i in range(steps):
            px = sx + (ex - sx) * i // steps
            py = sy + (ey - sy) * i // steps
            cv.circle(px, py, 2, (255, 240, 180))
        cv.circle(ex, ey, 3, (255, 200, 60))
    # skyline
    gy = y + h - 30
    for bx, bw, bh in ((6, 30, 34), (42, 22, 48), (70, 34, 28),
                       (110, 26, 52), (142, 30, 36), (178, 24, 46),
                       (208, 34, 30), (248, 28, 44), (282, 30, 32)):
        cv.fill(x + bx, gy - bh, bw, bh, (12, 20, 44))
        for wy in range(gy - bh + 5, gy - 3, 9):
            for wx in range(4, bw - 4, 9):
                cv.fill(x + bx + wx, wy, 3, 4, (255, 220, 120))
    # fires on two buildings (kept inside the scene box)
    _flame(cv, x + 116, gy - 58, 14, 14)
    _flame(cv, x + 254, gy - 52, 12, 12)
    # river with three bridges at the bottom
    cv.fill(x, gy, w, 30, (40, 90, 140))
    for bx in (60, 150, 240):
        cv.fill(x + bx, gy + 8, 46, 4, (200, 200, 200))
        cv.fill(x + bx + 4, gy + 12, 4, 10, (200, 200, 200))
        cv.fill(x + bx + 38, gy + 12, 4, 10, (200, 200, 200))


def scene_tankers(cv, x, y, w, h):
    # Two tankers in the Strait of Hormuz; one burning, one listing.
    cv.fill(x, y, w, h, SKY)
    cv.circle(x + w - 26, y + 16, 12, (245, 214, 110))
    # coastline top right
    cv.polygon([(x + w, y), (x + w - 70, y), (x + w - 40, y + 22),
                (x + w, y + 26)], (222, 209, 168))
    # sea
    sy = y + h // 2
    cv.fill(x, sy, w, h - h // 2, (52, 120, 170))
    for wy in range(sy + 8, y + h - 4, 12):
        cv.hline(x + 6, wy, w - 12, (120, 180, 210))
    # tanker one (left), stern hit, smoke
    tx, ty = x + 12, sy + 12
    cv.polygon([(tx, ty + 18), (tx + 78, ty + 18), (tx + 70, ty),
                (tx + 8, ty)], (30, 30, 34))
    cv.fill(tx + 52, ty - 12, 14, 12, (200, 200, 200))
    cv.fill(tx + 56, ty - 16, 6, 4, RED)
    _flame(cv, tx + 4, ty - 12, 14, 12)
    _smoke(cv, tx + 10, ty - 20, 7)
    # tanker two (right), engine-room fire
    tx2, ty2 = x + w - 92, sy + 12
    cv.polygon([(tx2, ty2 + 16), (tx2 + 80, ty2 + 16), (tx2 + 72, ty2),
                (tx2 + 8, ty2)], (44, 44, 48))
    cv.fill(tx2 + 14, ty2 - 10, 12, 10, (200, 200, 200))
    _flame(cv, tx2 + 52, ty2 - 10, 16, 12)
    _smoke(cv, tx2 + 60, ty2 - 18, 8)
    # dashed shipping lane
    for dx in range(0, w, 16):
        cv.fill(x + dx, sy - 6, 9, 2, (255, 255, 255))


def scene_sparta(cv, x, y, w, h):
    # Sanctioned cargo ship burning in the Gulf of Finland.
    cv.fill(x, y, w, h, (178, 205, 220))
    cv.circle(x + 24, y + 14, 10, (245, 214, 110))
    # Finnish coast, top right, with a lighthouse
    cv.polygon([(x + w, y), (x + w - 56, y), (x + w - 34, y + 20),
                (x + w, y + 24)], (222, 209, 168))
    cv.fill(x + w - 30, y + 2, 6, 20, (255, 255, 255))
    cv.fill(x + w - 32, y, 10, 4, RED)
    # sea
    sy = y + h // 2 + 4
    cv.fill(x, sy, w, h - h // 2 - 4, (52, 120, 170))
    for wy in range(sy + 8, y + h - 4, 12):
        cv.hline(x + 6, wy, w - 12, (120, 180, 210))
    # cargo ship, fire amidships (kept inside the scene box)
    sx, syy = x + 18, sy + 8
    cv.polygon([(sx, syy + 16), (sx + 120, syy + 16), (sx + 110, syy),
                (sx + 10, syy)], (40, 40, 44))
    cv.fill(sx + 16, syy - 12, 22, 12, (178, 57, 46))
    cv.fill(sx + 44, syy - 12, 22, 12, (210, 180, 90))
    cv.fill(sx + 72, syy - 12, 22, 12, (120, 120, 120))
    _flame(cv, sx + 52, syy - 16, 18, 16)
    _smoke(cv, sx + 62, syy - 26, 9)
    _smoke(cv, sx + 74, syy - 34, 7)
    # lifeboat with crew, inside the scene box
    cv.ellipse(x + w - 46, sy + 20, 16, 5, (245, 160, 40))
    cv.circle(x + w - 52, sy + 14, 3, (222, 184, 150))
    cv.circle(x + w - 40, sy + 14, 3, (222, 184, 150))


def scene_quake(cv, x, y, w, h):
    # Andes mountains, a seismograph trace, houses shaken.
    cv.fill(x, y, w, h, (238, 226, 198))
    cv.circle(x + w - 24, y + 14, 11, (245, 214, 110))
    # mountains
    cv.polygon([(x, y + h), (x + 44, y + 14), (x + 88, y + h)],
               (120, 130, 140))
    cv.polygon([(x + 8, y + 40), (x + 44, y + 14), (x + 76, y + 44)],
               (250, 250, 250))
    cv.polygon([(x + 70, y + h), (x + 130, y + 8), (x + 190, y + h)],
               (96, 108, 120))
    cv.polygon([(x + 104, y + 34), (x + 130, y + 8), (x + 154, y + 36)],
               (250, 250, 250))
    # seismograph strip
    sy = y + h - 44
    cv.fill(x + 8, sy, w - 16, 26, (255, 255, 255))
    cv.rect(x + 8, sy, w - 16, 26, INK)
    pts = []
    for i in range(w - 16):
        amp = 2
        if 60 < i < 130:
            amp = 2 + int(9 * abs(math.sin(i * 0.55)))
        pts.append((x + 8 + i, sy + 13 + (amp if i % 2 else -amp)))
    for (px0, py0), (px1, py1) in zip(pts, pts[1:]):
        cv.line(px0, py0, px1, py1, RED)
    # two houses, one tilted
    hx, hy = x + 16, y + h - 58
    cv.polygon([(hx, hy), (hx + 12, hy - 10), (hx + 24, hy)], (178, 57, 46))
    cv.fill(hx + 2, hy, 20, 12, (240, 230, 200))
    hx2 = x + w - 44
    cv.polygon([(hx2, hy + 2), (hx2 + 12, hy - 8), (hx2 + 24, hy + 2)],
               (178, 57, 46))
    cv.fill(hx2 + 2, hy + 2, 20, 12, (240, 230, 200))


def scene_gaza_van(cv, x, y, w, h):
    # A street in Gaza City: white van, smoke column, buildings.
    # All drawing stays inside the (x, y, w, h) box.
    cv.fill(x, y, w, h, (232, 222, 198))
    street = y + h - 14
    # buildings behind, sitting on the street
    for bx, bw, bh, col in ((4, 34, 22, (190, 175, 150)),
                            (44, 28, 30, (176, 160, 134)),
                            (150, 36, 24, (190, 175, 150))):
        top = max(y + 4, street - bh)
        cv.fill(x + bx, top, bw, street - top, col)
        for wy in range(top + 5, street - 2, 10):
            cv.fill(x + bx + 6, wy, 6, 6, (90, 80, 66))
    # street
    cv.fill(x, street, w, 14, (120, 112, 100))
    cv.hline(x, street, w, (255, 255, 255))
    # white van
    vx, vy = x + 52, street - 14
    cv.fill(vx, vy, 62, 14, (245, 245, 240))
    cv.rect(vx, vy, 62, 14, INK)
    cv.polygon([(vx + 46, vy), (vx + 62, vy + 6), (vx + 62, vy + 14),
                (vx + 46, vy + 14)], (210, 225, 235))
    cv.circle(vx + 14, vy + 14, 3, INK)
    cv.circle(vx + 48, vy + 14, 3, INK)
    # smoke column above the van, inside the box
    _smoke(cv, vx + 30, vy - 8, 6, (90, 90, 88))
    _smoke(cv, vx + 36, vy - 16, 5, (110, 110, 108))


def scene_basra(cv, x, y, w, h):
    # Hartha power station: cooling towers, flames, black smoke, houses.
    # All drawing stays inside the (x, y, w, h) box.
    cv.fill(x, y, w, h, (226, 210, 180))
    ground = y + h - 12
    # cooling towers
    for tx, tw in ((14, 34), (56, 30)):
        top = y + 12
        cv.polygon([(x + tx, ground), (x + tx + 5, top),
                    (x + tx + tw - 5, top), (x + tx + tw, ground)],
                   (200, 196, 186))
        cv.fill(x + tx + 2, top, tw - 4, 4, (160, 156, 146))
    # turbine hall with flames
    hx = x + 100
    hall_top = ground - 20
    cv.fill(hx, hall_top, 66, 20, (150, 140, 120))
    _flame(cv, hx + 10, hall_top - 10, 14, 10)
    _flame(cv, hx + 36, hall_top - 8, 12, 8)
    _smoke(cv, hx + 18, hall_top - 18, 7, (60, 60, 58))
    _smoke(cv, hx + 44, hall_top - 14, 6, (80, 80, 78))
    # small houses in front
    for bx in (10, 44, 140):
        cv.polygon([(x + bx, ground), (x + bx + 10, ground - 10),
                    (x + bx + 20, ground)], (178, 57, 46))
        cv.fill(x + bx + 2, ground, 16, 12, (240, 230, 200))


def scene_rationing(cv, x, y, w, h):
    # A pylon, a clock showing two hours, dark houses, one lit window.
    cv.fill(x, y, w, h, (24, 36, 62))
    _stars(cv, x, y, w, h, 10, 31)
    # pylon
    px = x + w // 2
    cv.polygon([(px - 22, y + h - 8), (px - 6, y + 18), (px + 6, y + 18),
                (px + 22, y + h - 8)], (140, 140, 138))
    cv.line(px - 26, y + 26, px + 26, y + 26, (140, 140, 138))
    cv.line(px - 20, y + 40, px + 20, y + 40, (140, 140, 138))
    # wires to the houses
    cv.line(x + 8, y + h - 34, px - 20, y + 30, (140, 140, 138))
    cv.line(px + 20, y + 30, x + w - 8, y + h - 34, (140, 140, 138))
    # dark houses
    for bx in (8, w - 48):
        cv.fill(x + bx, y + h - 30, 40, 30, (12, 18, 36))
        cv.polygon([(x + bx, y + h - 30), (x + bx + 20, y + h - 44),
                    (x + bx + 40, y + h - 30)], (10, 14, 30))
    # one lit window
    cv.fill(x + 20, y + h - 22, 8, 8, (255, 220, 120))
    # clock showing 2 hours
    cx, cy = x + w - 30, y + 20
    cv.circle(cx, cy, 13, (255, 255, 255))
    cv.circle(cx, cy, 13, INK)
    cv.line(cx, cy, cx, cy - 8, INK)
    cv.line(cx, cy, cx + 6, cy + 4, INK)


def scene_rutte(cv, x, y, w, h):
    # NATO compass star over the Warsaw skyline, Polish flag.
    cv.fill(x, y, w, h, SKY)
    # Warsaw skyline
    gy = y + h - 26
    for bx, bw, bh in ((6, 26, 30), (38, 20, 44), (64, 30, 24),
                       (100, 22, 40), (128, 26, 28), (160, 24, 36)):
        cv.fill(x + bx, gy - bh, bw, bh, (90, 100, 118))
        for wy in range(gy - bh + 5, gy - 3, 9):
            cv.fill(x + bx + 4, wy, 3, 3, (255, 220, 120))
    # NATO compass star
    cx, cy = x + w // 2, y + 34
    cv.circle(cx, cy, 26, (28, 52, 110))
    for ang in range(0, 360, 90):
        a = math.radians(ang)
        tip = (cx + int(22 * math.cos(a)), cy + int(22 * math.sin(a)))
        side = (cx + int(6 * math.cos(a + 1.57)),
                cy + int(6 * math.sin(a + 1.57)))
        side2 = (cx + int(6 * math.cos(a - 1.57)),
                 cy + int(6 * math.sin(a - 1.57)))
        cv.polygon([tip, side, (cx, cy)], (255, 255, 255))
        cv.polygon([tip, side2, (cx, cy)], (200, 210, 230))
    cv.circle(cx, cy, 5, (255, 255, 255))
    # Polish flag on a pole
    fx = x + 16
    cv.vline(fx, y + 12, 44, INK)
    cv.fill(fx, y + 12, 30, 9, (255, 255, 255))
    cv.fill(fx, y + 21, 30, 9, (220, 20, 60))


def scene_sudan(cv, x, y, w, h):
    # Desert road under a hard sun; a UN-blue flag, a drone overhead.
    cv.fill(x, y, w, h, (238, 220, 170))
    cv.circle(x + w - 26, y + 16, 13, (245, 200, 80))
    # dunes
    cv.polygon([(x, y + h), (x + 60, y + h - 34), (x + 130, y + h)],
               (214, 188, 130))
    cv.polygon([(x + 90, y + h), (x + 150, y + h - 26), (x + w, y + h)],
               (200, 172, 112))
    # road with dashed centre
    cv.polygon([(x + w // 2 - 12, y + h), (x + w // 2 - 4, y + 34),
                (x + w // 2 + 4, y + 34), (x + w // 2 + 12, y + h)],
               (120, 110, 96))
    for i in range(4):
        yy = y + 44 + i * 14
        cv.fill(x + w // 2 - 1, yy, 2, 7, (255, 255, 255))
    # UN flag on a pole, inside the scene box
    fx = x + 16
    cv.vline(fx, y + 30, 28, INK)
    cv.fill(fx, y + 30, 30, 18, (60, 110, 200))
    cv.circle(fx + 15, y + 39, 5, (255, 255, 255))
    # small drone silhouette
    dx, dy = x + w - 52, y + 44
    cv.fill(dx - 12, dy, 24, 3, INK)
    cv.circle(dx - 12, dy, 4, INK)
    cv.circle(dx + 12, dy, 4, INK)
    cv.fill(dx - 3, dy, 6, 8, INK)


def scene_eu_indonesia(cv, x, y, w, h):
    # Two flags, a handshake and a signed document.
    cv.fill(x, y, w, h, (238, 232, 214))
    # EU flag
    ex, ey = x + 12, y + 12
    cv.fill(ex, ey, 52, 30, (0, 51, 153))
    for i in range(12):
        a = math.radians(i * 30 - 90)
        cv.circle(ex + 26 + int(11 * math.cos(a)),
                  ey + 15 + int(11 * math.sin(a)), 1, (255, 209, 0))
    # Indonesian flag
    ix, iy = x + w - 64, y + 12
    cv.fill(ix, iy, 52, 15, (220, 20, 60))
    cv.fill(ix, iy + 15, 52, 15, (255, 255, 255))
    cv.rect(ix, iy, 52, 30, INK)
    # handshake: two sleeves and clasped hands
    hx, hy = x + w // 2, y + h - 34
    cv.polygon([(hx - 52, hy - 12), (hx - 12, hy - 2), (hx - 12, hy + 10),
                (hx - 52, hy + 10)], (31, 78, 121))
    cv.polygon([(hx + 52, hy - 12), (hx + 12, hy - 2), (hx + 12, hy + 10),
                (hx + 52, hy + 10)], (178, 57, 46))
    cv.circle(hx - 6, hy + 2, 7, (222, 184, 150))
    cv.circle(hx + 6, hy + 2, 7, (222, 184, 150))
    # signed document below
    cv.fill(x + w // 2 - 34, y + h - 22, 68, 16, (255, 255, 255))
    cv.rect(x + w // 2 - 34, y + h - 22, 68, 16, INK)
    cv.hline(x + w // 2 - 28, y + h - 16, 40, GREY)
    cv.circle(x + w // 2 + 22, y + h - 12, 5, RED)


def scene_belgium(cv, x, y, w, h):
    # An airport with a grounded plane, tower and a strike placard.
    cv.fill(x, y, w, h, (206, 220, 232))
    # control tower
    tx = x + 16
    cv.fill(tx, y + 10, 10, 44, (120, 120, 118))
    cv.fill(tx - 4, y + 4, 18, 10, (60, 90, 140))
    # grounded plane
    px, py = x + 52, y + h - 40
    cv.ellipse(px + 40, py, 42, 8, (255, 255, 255))
    cv.polygon([(px + 78, py - 2), (px + 92, py - 12), (px + 92, py + 2)],
               (200, 30, 40))
    cv.fill(px + 30, py - 14, 26, 4, (200, 200, 200))
    cv.fill(px + 44, py + 6, 4, 10, INK)
    cv.fill(px + 66, py + 6, 4, 10, INK)
    # runway
    cv.fill(x, y + h - 14, w, 6, (80, 80, 78))
    for dx in range(0, w, 18):
        cv.fill(x + dx, y + h - 12, 10, 2, (255, 255, 255))
    # strike placard
    cv.fill(x + w - 46, y + 12, 34, 24, (255, 255, 255))
    cv.rect(x + w - 46, y + 12, 34, 24, RED)
    cv.fill(x + w - 42, y + 16, 26, 3, RED)
    cv.fill(x + w - 42, y + 22, 18, 3, RED)
    cv.fill(x + w - 42, y + 28, 22, 3, RED)


# -------------------------------------------------------------------- data
LEADS = [
    dict(n=1, place="GULF", topic="IRAN WAR",
         head="Iran strikes US bases in the Gulf",
         body=("Iran fired missiles and drones at US bases in Bahrain, "
               "Kuwait and Jordan late on Saturday. Almost all were "
               "intercepted."),
         src="Reuters · Al Jazeera", tag="CONFIRMED",
         scene=scene_gulf_strikes),
    dict(n=2, place="ANTALYA", topic="CLIMATE",
         head="COP31 nears a deal in Antalya",
         body=("A new package text went to nearly 200 nations late on "
               "Saturday. Objections due 03:00 GMT; approval set for "
               "06:00 GMT."),
         src="Reuters", tag="CONFIRMED",
         scene=scene_cop31),
    dict(n=3, place="KYIV", topic="UKRAINE WAR",
         head="Russia fires 400 drones and 110 missiles",
         body=("Over 400 drones and 110 missiles hit Ukraine overnight into "
               "Friday — one of the war's largest attacks. Nine were "
               "killed."),
         src="Reuters · Kyiv Independent", tag="CONFIRMED",
         scene=scene_barrage),
]

MEDIUMS = [
    dict(n=4, place="HORMUZ", topic="SHIPPING",
         head="Two tankers hit off Oman",
         body="Two tankers hit near Khasab; no casualties.",
         src="UKMTO · Reuters", tag="CONFIRMED",
         scene=scene_tankers),
    dict(n=5, place="GULF OF FINLAND", topic="WAR",
         head="Sparta II still burns off Finland",
         body="Ship hit by drones; 16 crew took to lifeboats.",
         src="Reuters · CNN", tag="CONFIRMED",
         scene=scene_sparta),
    dict(n=6, place="PERU", topic="EARTHQUAKE",
         head="Peru shaken by 6.7 quake",
         body="6.7 quake near Junin; 128 homes damaged.",
         src="USGS · IGP", tag="CONFIRMED",
         scene=scene_quake),
    dict(n=7, place="GAZA CITY", topic="CEASEFIRE",
         head="Gaza aid van hit; three killed",
         body="Drone strike kills three in Gaza City.",
         src="Reuters · AFP", tag="CONFIRMED",
         scene=scene_gaza_van),
    dict(n=8, place="BASRA", topic="DISASTER",
         head="Basra power-station fire kills four",
         body="Gas pipeline fire; 800 MW plant shut down.",
         src="Reuters · INA", tag="CONFIRMED",
         scene=scene_basra),
    dict(n=9, place="TEHRAN", topic="ENERGY",
         head="Iran to ration electricity",
         body="Rolling cuts of up to two hours a day.",
         src="RFE/RL", tag="CONFIRMED",
         scene=scene_rationing),
    dict(n=10, place="WARSAW", topic="NATO",
         head="Rutte: NATO stands with Poland",
         body="NATO will defend every inch of Poland.",
         src="Reuters · PAP", tag="CONFIRMED",
         scene=scene_rutte),
    dict(n=11, place="SUDAN", topic="WAR",
         head="UN counts Sudan's drone dead",
         body="UN counts 1,630 civilian drone deaths.",
         src="UN · Amnesty", tag="CONFIRMED",
         scene=scene_sudan),
    dict(n=12, place="BRUSSELS", topic="TRADE",
         head="EU and Indonesia sign trade deal",
         body="Deal signed in Brussels after 10 years.",
         src="Reuters · AFP", tag="CONFIRMED",
         scene=scene_eu_indonesia),
    dict(n=13, place="BELGIUM", topic="LABOUR",
         head="Belgium braces for Monday strike",
         body="Controllers join strike; flights halted.",
         src="Brussels Airport · skeyes", tag="CONFIRMED",
         scene=scene_belgium),
]

ALSO = [
    "France marches for a sixth Saturday (82,500)",
    "Hong Kong votes for its Election Committee",
    "Australia rejects US report on AUKUS",
    "Mexico captures 'El Chapo Isidro'",
    "Bolsonaro taken to intensive care",
    "Boat capsizes in Nigeria, 24 dead",
    "Bitcoin claws back above $60,000",
    "England rout the All Blacks 37-12",
    "Jordan shoots down five missiles",
    "Lebanon marks 83 years of independence",
    "Denmark expels Russian defence attache",
    "Estonia to shut its Russia border crossings",
    "Double-tap strike hits Kryvyi Rih",
    "BepiColombo enters orbit around Mercury",
    "Nepal's PM arrives in Delhi",
    "Cyclone Akvan grounds flights at Ranchi",
    "Modi opens Nitish Setu bridge",
    "Verstappen inherits Las Vegas pole",
    "Missouri approves $7.25bn Roundup deal",
    "25 deportees from the US land in Liberia",
    "FBI probes hack of its crime database",
    "Russia says it downed 275 drones overnight",
]

STATS = [
    ("400+", "drones fired at Ukraine"),
    ("2", "tankers hit off Oman"),
    ("6.7", "Peru quake magnitude"),
    ("24", "killed as boat capsizes in Nigeria"),
    ("82,500", "march in France"),
    ("$60,000", "bitcoin rebounds"),
]

REGIONS = [
    ("MIDDLE EAST", 7),
    ("EUROPE", 11),
    ("ASIA-PACIFIC", 6),
    ("THE AMERICAS", 6),
    ("AFRICA", 3),
    ("GLOBAL", 2),
]

DATE_CHECK = (
    "Left out as other days' news: the Trump-Xi-Putin summit in Shenzhen "
    "(19 Nov) · the Kerch Bridge strikes (earlier in the week) · the ICJ "
    "ruling on Myanmar (19 Nov) · Voyager 1 reaching one light-day "
    "(18 Nov) · the Wall Street sell-off (Fri 20 Nov) · the Las Vegas "
    "Grand Prix race (04:00 UTC, Mon 23 Nov) · the ATP Finals result "
    "(played Sunday evening). The Russia barrage struck overnight into "
    "Friday and is the weekend's biggest war story; the EU-Indonesia deal "
    "was signed on Saturday."
)

PINS = [  # (story, true x, true y, label x, label y) in the map box.
    # The true spot gets a small dot; the numbered pin sits at the label
    # spot with a thin leader line.  Labels are spread so no two pins
    # touch, even in the crowded Europe and Gulf clusters.
    (1, 232, 48, 218, 34), (2, 170, 40, 150, 50), (3, 188, 22, 208, 16),
    (4, 252, 56, 264, 68), (5, 186, 14, 196, 8), (6, 88, 108, 88, 108),
    (7, 176, 50, 188, 60), (8, 224, 52, 206, 62), (9, 240, 42, 250, 28),
    (10, 182, 24, 176, 30), (11, 180, 78, 180, 78),
    (12, 158, 26, 136, 14), (13, 166, 20, 158, 8),
]


# --------------------------------------------------------------------- map
def draw_map(cv, x, y, w, h):
    cv.fill(x, y, w, h, SEA)
    cv.rect(x, y, w, h, INK)
    # graticule
    for gx in range(x + 40, x + w, 40):
        cv.vline(gx, y, h, (190, 214, 228))
    for gy in range(y + 30, y + h, 30):
        cv.hline(x, gy, w, (190, 214, 228))
    # rough continents, drawn from simple polygons
    land = [
        [(x + 14, y + 26), (x + 38, y + 14), (x + 76, y + 12),
         (x + 102, y + 22), (x + 96, y + 44), (x + 74, y + 58),
         (x + 50, y + 68), (x + 28, y + 58), (x + 14, y + 44)],  # N America
        [(x + 70, y + 80), (x + 96, y + 76), (x + 108, y + 94),
         (x + 102, y + 124), (x + 88, y + 146), (x + 74, y + 124),
         (x + 66, y + 100)],  # S America
        [(x + 146, y + 16), (x + 166, y + 8), (x + 186, y + 12),
         (x + 192, y + 28), (x + 174, y + 42), (x + 154, y + 40),
         (x + 142, y + 28)],  # Europe
        [(x + 146, y + 54), (x + 174, y + 48), (x + 198, y + 56),
         (x + 206, y + 86), (x + 192, y + 116), (x + 168, y + 124),
         (x + 150, y + 96), (x + 142, y + 70)],  # Africa
        [(x + 196, y + 12), (x + 248, y + 6), (x + 298, y + 10),
         (x + 312, y + 34), (x + 300, y + 58), (x + 268, y + 72),
         (x + 228, y + 64), (x + 204, y + 48), (x + 192, y + 28)],  # Asia
        [(x + 266, y + 106), (x + 298, y + 102), (x + 306, y + 122),
         (x + 292, y + 138), (x + 270, y + 134)],  # Australia
    ]
    for poly in land:
        cv.polygon(poly, LAND)
        for (px0, py0), (px1, py1) in zip(poly, poly[1:] + poly[:1]):
            cv.line(px0, py0, px1, py1, LAND_LINE)
    # region labels, placed on clear sea or land (no EUROPE label: the
    # cluster of pins there leaves no clear spot for it)
    draw_text(cv, x + 28, y + 36, "NORTH AMERICA", "r12", GREY)
    draw_text(cv, x + 58, y + 128, "SOUTH AMERICA", "r12", GREY)
    draw_text(cv, x + 156, y + 92, "AFRICA", "r12", GREY)
    draw_text(cv, x + 256, y + 44, "ASIA", "r12", GREY)
    draw_text(cv, x + 260, y + 142, "AUSTRALIA", "r12", GREY)
    # numbered pins with leader lines to their true spots
    for n, tx, ty, lx, ly in PINS:
        if (tx, ty) != (lx, ly):
            cv.line(x + tx, y + ty, x + lx, y + ly, GREY)
            cv.circle(x + tx, y + ty, 2, RED)
        cv.circle(x + lx, y + ly, 6, RED)
        cv.circle(x + lx, y + ly, 6, INK)
        label = str(n)
        tw = text_width(label, "b12")
        draw_text(cv, x + lx - tw // 2, y + ly - 6, label, "b12",
                  (255, 255, 255))


# ------------------------------------------------------------------ layout
def _centred(cv, y, text, name, color, scale=1):
    tw = text_width(text, name, scale)
    draw_text(cv, (W - tw) // 2, y, text, name, color, scale)


def _panel_border(cv, x, y, w, h):
    cv.rect(x, y, w, h, INK)


def draw_lead(cv, x, y, w, h, story):
    _panel_border(cv, x, y, w, h)
    story["scene"](cv, x + 1, y + 1, w - 2, 88)
    ky = y + 92
    kicker = "%d · %s · %s" % (story["n"], story["place"], story["topic"])
    draw_text(cv, x + 8, ky, kicker, "b12", RED)
    hy = ky + 16
    n_head = draw_wrapped(cv, x + 8, hy, story["head"], "b18", INK, 1,
                          w - 16, 22)
    by = hy + n_head * 22 + 4
    n_body = draw_wrapped(cv, x + 8, by, story["body"], "r12", INK, 1,
                          w - 16, 15)
    sy = y + h - 14
    draw_text(cv, x + 8, sy, story["src"], "r12", GREY)
    tag = story["tag"]
    tw = text_width(tag, "b12")
    draw_text(cv, x + w - 8 - tw, sy, tag, "b12", RED)


def draw_medium(cv, x, y, w, h, story):
    _panel_border(cv, x, y, w, h)
    story["scene"](cv, x + 1, y + 1, w - 2, 62)
    # kicker banner
    ky = y + 63
    cv.fill(x + 1, ky, w - 2, 15, RED)
    kicker = "%s · %s" % (story["place"], story["topic"])
    draw_text(cv, x + 6, ky + 2, kicker, "b12", (255, 255, 255))
    # number badge, top right of the scene
    badge = str(story["n"])
    cv.circle(x + w - 12, y + 12, 8, RED)
    tw = text_width(badge, "b12")
    draw_text(cv, x + w - 12 - tw // 2, y + 6, badge, "b12",
              (255, 255, 255))
    hy = ky + 18
    n_head = draw_wrapped(cv, x + 6, hy, story["head"], "b12", INK, 1,
                          w - 12, 15)
    by = hy + n_head * 15 + 2
    draw_wrapped(cv, x + 6, by, story["body"], "r12", INK, 1, w - 12, 14)
    sy = y + h - 13
    # source only: the red CONFIRMED tag (88px) does not fit next to any
    # source string in a 192px panel, and a half-fitted tag looks broken
    draw_text(cv, x + 6, sy, story["src"], "r12", GREY)


def build():
    cv = Canvas(W, H, PAPER)
    # masthead
    draw_text(cv, 12, 8, "THE WORLD IN ONE DAY", "b12", RED)
    right = "35 STORIES · 6 REGIONS · EVERY ONE DATED SUNDAY 22 NOVEMBER 2026"
    tw = text_width(right, "r12")
    draw_text(cv, W - 12 - tw, 8, right, "r12", INK)
    cv.fill(12, 26, W - 24, 2, INK)
    # date
    _centred(cv, 34, "Sunday 22 November 2026", "b40", INK)
    _centred(cv, 82, "Iran hits US bases in the Gulf · COP31 nears a deal · "
                     "Russia fires 400 drones at Ukraine", "r12", INK)
    cv.fill(12, 102, W - 24, 1, INK)
    cv.fill(12, 105, W - 24, 1, INK)
    # stat strip
    cell_w = (W - 24) // 6
    for i, (num, label) in enumerate(STATS):
        cx0 = 12 + i * cell_w
        _centred_num = text_width(num, "b28")
        draw_text(cv, cx0 + (cell_w - _centred_num) // 2, 112, num, "b28",
                  INK)
        lab_lines = wrap(label, "r12", 1, cell_w - 12)
        for j, line in enumerate(lab_lines[:2]):
            lw = text_width(line, "r12")
            draw_text(cv, cx0 + (cell_w - lw) // 2, 142 + j * 14, line,
                      "r12", GREY)
        if i:
            cv.vline(cx0, 112, 44, LIGHT)
    cv.fill(12, 158, W - 24, 1, INK)
    # region bar
    total = sum(c for _, c in REGIONS)
    rx = 12
    for name, count in REGIONS:
        seg_w = (W - 24) * count // total
        col = REGION_COLOURS[name]
        cv.fill(rx, 162, seg_w, 16, col)
        label = "%s %d" % (name, count)
        lw = text_width(label, "b12")
        if lw <= seg_w - 6:
            draw_text(cv, rx + (seg_w - lw) // 2, 165, label, "b12",
                      (255, 255, 255))
        rx += seg_w
    # leads
    lead_w = 326
    for i, story in enumerate(LEADS):
        draw_lead(cv, 12 + i * (lead_w + 11), 182, lead_w, 218, story)
    # mediums: two rows of five
    med_w = 192
    for row in range(2):
        for col in range(5):
            story = MEDIUMS[row * 5 + col]
            draw_medium(cv, 12 + col * (med_w + 10), 404 + row * 160,
                        med_w, 156, story)
    # section headers
    draw_text(cv, 12, 724, "WHERE IT HAPPENED · 13 PLACES ON THE MAP",
              "b12", INK)
    draw_text(cv, 344, 724, "ALSO ON SUNDAY 22 NOVEMBER — 22 MORE STORIES",
              "b12", RED)
    # map and also list
    draw_map(cv, 12, 740, 320, 164)
    draw_text(cv, 12, 890, "Pins 1-13 mark the front-page stories.",
              "r12", GREY)
    for i, item in enumerate(ALSO):
        col = i // 11
        row = i % 11
        ix = 344 + col * 334
        iy = 740 + row * 15
        num = "%d " % (14 + i)
        draw_text(cv, ix, iy, num, "b12", RED)
        draw_text(cv, ix + text_width(num, "b12"), iy, item, "r12", INK)
    # date check
    cv.rect(12, 910, W - 24, 64, RED)
    draw_text(cv, 20, 916, "DATE CHECK — LEFT OUT AS OTHER DAYS' NEWS",
              "b12", RED)
    draw_wrapped(cv, 20, 932, DATE_CHECK, "r12", INK, 1, W - 40, 14)
    # footer
    _centred(cv, 982, "Every story here happened, or was first reported, on "
                      "Sunday 22 November 2026.", "r12", INK)
    _centred(cv, 998, "Sources: Reuters, AP, AFP, Al Jazeera, BBC, USGS, "
                      "ESA, ATP Tour, Formula 1. Original drawings.",
              "r12", GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.dirname(
        os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)
    write_png(os.path.join(out_dir, "entry.png"), build())
    print("wrote", os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
