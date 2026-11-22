#!/usr/bin/env python3
"""Draw "The World in One Day" -- Sunday 22 November 2026.

A newspaper front page that sums up one day of world news in a single
1024x1024 picture.  Every story is drawn from lines, shapes and a small
bitmap font that is embedded below as data; there are no photographs,
no external files and no third-party libraries.

Standard library only: base64, math, os, struct, zlib.

Run from this folder:

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

That writes out/entry.png.  Without MAKEFUN_OUTPUT_DIR the image is
written next to this script.  Running it again produces a byte-identical
file: no randomness, no timestamps, no dictionary-order dependence.

Layout (top to bottom): masthead and date, a subtitle of the three lead
stories, a strip of six numbers, a colour bar of the seven regions,
three large front-page panels, ten smaller panels, a world map with
numbered pins, a numbered list of the remaining stories, a date-check
box of stories that were deliberately left out, and a footer.
"""

import base64
import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- colours
PAPER = (253, 253, 248)   # newsprint white
INK = (17, 17, 17)        # near-black ink
GREY = (110, 110, 105)    # secondary text
LIGHT = (238, 236, 228)   # panel borders and rules
RED = (179, 38, 30)       # kickers, pins, accents
SEA = (214, 231, 240)     # map sea
LAND = (222, 209, 168)    # map land
LAND_LINE = (150, 135, 95)

REGION_COLOURS = {
    "MIDDLE EAST": (179, 57, 46),
    "EUROPE": (31, 78, 121),
    "ASIA-PACIFIC": (46, 125, 50),
    "THE AMERICAS": (211, 108, 24),
    "AFRICA": (106, 76, 147),
    "MARKETS & TECH": (0, 121, 134),
    "SPORT": (93, 64, 55),
}

# ------------------------------------------------------- embedded bitmap font
# Glyphs rasterised from DejaVu Sans (regular and bold) at the sizes the
# layout needs, packed as 1-bit bitmaps, zlib-compressed and base64-encoded.
# The decoder below is the only thing that touches this blob.
CHARSET = "".join(chr(c) for c in range(32, 127)) + "\u2022"
# (weight, pixel size, cell height) in the same order as the packed data.
FONT_COMBOS = [
    ("R", 8, 10), ("R", 9, 12), ("R", 10, 13), ("R", 11, 14), ("R", 12, 15),
    ("B", 9, 12), ("B", 10, 13), ("B", 11, 14), ("B", 13, 17), ("B", 14, 17),
    ("B", 20, 24), ("B", 24, 29), ("B", 36, 43),
]
FONT_B64 = (
"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"
"2fD/AOHfhp4="
)


def _decode_font():
    """Unpack the embedded font blob into {(weight, size): glyph table}."""
    raw = zlib.decompress(base64.b64decode(FONT_B64))
    fonts = {}
    pos = 0
    for weight, size, height in FONT_COMBOS:
        widths = raw[pos:pos + len(CHARSET)]
        pos += len(CHARSET)
        glyphs = {}
        for i, ch in enumerate(CHARSET):
            w = widths[i]
            nbytes = height * ((w + 7) // 8)
            glyphs[ch] = (w, raw[pos:pos + nbytes])
            pos += nbytes
        fonts[(weight, size)] = (height, glyphs)
    return fonts


FONTS = _decode_font()


def text_width(text, weight, size):
    _, glyphs = FONTS[(weight, size)]
    total = 0
    for ch in text:
        g = glyphs.get(ch)
        total += g[0] if g else size // 2
    return total


def draw_text(cv, x, y, text, colour, weight, size):
    """Draw one line of text with its top at y.  Returns the width drawn."""
    height, glyphs = FONTS[(weight, size)]
    cx = x
    for ch in text:
        g = glyphs.get(ch)
        if g is None:
            cx += size // 2
            continue
        w, data = g
        rowbytes = (w + 7) // 8
        for row in range(height):
            base = row * rowbytes
            for col in range(w):
                if data[base + col // 8] & (0x80 >> (col % 8)):
                    cv.set(cx + col, y + row, colour)
        cx += w
    return cx - x


def draw_text_centred(cv, cx, y, text, colour, weight, size):
    draw_text(cv, cx - text_width(text, weight, size) // 2, y, text,
              colour, weight, size)


def wrap_text(text, weight, size, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, weight, size) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(cv, x, y, text, colour, weight, size, max_width, leading):
    lines = wrap_text(text, weight, size, max_width)
    for i, line in enumerate(lines):
        draw_text(cv, x, y + i * leading, line, colour, weight, size)
    return len(lines)


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bg * (w * h))

    def set(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = colour[0]
            self.buf[i + 1] = colour[1]
            self.buf[i + 2] = colour[2]

    def rect(self, x, y, w, h, colour):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.buf[i] = colour[0]
                self.buf[i + 1] = colour[1]
                self.buf[i + 2] = colour[2]
                i += 3

    def rect_outline(self, x, y, w, h, colour, thick=1):
        self.rect(x, y, w, thick, colour)
        self.rect(x, y + h - thick, w, thick, colour)
        self.rect(x, y, thick, h, colour)
        self.rect(x + w - thick, y, thick, h, colour)

    def hline(self, x0, x1, y, colour, thick=1):
        for t in range(thick):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                self.set(x, y + t, colour)

    def vline(self, x, y0, y1, colour, thick=1):
        for t in range(thick):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                self.set(x + t, y, colour)

    def line(self, x0, y0, x1, y1, colour, thick=1):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for s in range(steps + 1):
            x = x0 + dx * s // steps
            y = y0 + dy * s // steps
            if thick <= 1:
                self.set(x, y, colour)
            else:
                r = thick // 2
                for ox in range(-r, r + 1):
                    for oy in range(-r, r + 1):
                        if ox * ox + oy * oy <= r * r + 1:
                            self.set(x + ox, y + oy, colour)

    def circle(self, cx, cy, r, colour, fill=True):
        if fill:
            for dy in range(-r, r + 1):
                half = int(math.sqrt(max(0, r * r - dy * dy)))
                for dx in range(-half, half + 1):
                    self.set(cx + dx, cy + dy, colour)
        else:
            steps = max(24, int(2 * math.pi * r))
            for s in range(steps):
                a = 2 * math.pi * s / steps
                self.set(cx + int(r * math.cos(a) + 0.5),
                         cy + int(r * math.sin(a) + 0.5), colour)

    def ellipse(self, cx, cy, rx, ry, colour, fill=True):
        if fill:
            for dy in range(-ry, ry + 1):
                half = int(rx * math.sqrt(max(0.0, 1.0 - (dy * dy) / float(ry * ry))))
                for dx in range(-half, half + 1):
                    self.set(cx + dx, cy + dy, colour)
        else:
            steps = max(24, int(2 * math.pi * max(rx, ry)))
            for s in range(steps):
                a = 2 * math.pi * s / steps
                self.set(cx + int(rx * math.cos(a) + 0.5),
                         cy + int(ry * math.sin(a) + 0.5), colour)

    def poly(self, points, colour, fill=True):
        if fill:
            ys = [p[1] for p in points]
            for y in range(min(ys), max(ys) + 1):
                xs = []
                n = len(points)
                for i in range(n):
                    x0, y0 = points[i]
                    x1, y1 = points[(i + 1) % n]
                    if (y0 <= y < y1) or (y1 <= y < y0):
                        xs.append(x0 + (y - y0) * (x1 - x0) // (y1 - y0))
                xs.sort()
                for k in range(0, len(xs) - 1, 2):
                    for x in range(xs[k], xs[k + 1] + 1):
                        self.set(x, y, colour)
        else:
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                self.line(x0, y0, x1, y1, colour)


# ----------------------------------------------------------------- PNG output
def write_png(path, cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw.extend(cv.buf[y * cv.w * 3:(y + 1) * cv.w * 3])
    data = zlib.compress(bytes(raw), 9)

    def chunk(kind, payload):
        out = struct.pack(">I", len(payload)) + kind + payload
        out += struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", data)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

# --------------------------------------------------------------- pictograms
# Each pictogram draws inside a square of side s with top-left corner
# (x, y).  All coordinates below live on a 0..100 grid, scaled by s/100.
# fg is the main ink colour, accent a second colour (usually RED).

def draw_pic(cv, kind, x, y, s, fg, accent):
    u = s / 100.0

    def P(px, py):
        return (int(x + px * u + 0.5), int(y + py * u + 0.5))

    def ln(ax, ay, bx, by, col, th=2):
        p0, p1 = P(ax, ay), P(bx, by)
        cv.line(p0[0], p0[1], p1[0], p1[1], col, max(1, int(th * u + 0.5)))

    def rc(ax, ay, w, h, col):
        p0 = P(ax, ay)
        cv.rect(p0[0], p0[1], max(1, int(w * u + 0.5)),
                max(1, int(h * u + 0.5)), col)

    def ro(ax, ay, w, h, col):
        p0 = P(ax, ay)
        cv.rect_outline(p0[0], p0[1], max(1, int(w * u + 0.5)),
                        max(1, int(h * u + 0.5)), col, 1)

    def ci(cx, cy, r, col, fill=True):
        p = P(cx, cy)
        cv.circle(p[0], p[1], max(1, int(r * u + 0.5)), col, fill)

    def el(cx, cy, rx, ry, col, fill=True):
        p = P(cx, cy)
        cv.ellipse(p[0], p[1], max(1, int(rx * u + 0.5)),
                   max(1, int(ry * u + 0.5)), col, fill)

    def pg(pts, col, fill=True):
        cv.poly([P(a, b) for a, b in pts], col, fill)

    if kind == "missile":
        pg([(62, 8), (74, 22), (58, 30)], fg)                 # nose cone
        pg([(58, 28), (74, 22), (66, 52), (50, 58)], fg)      # body
        pg([(50, 58), (66, 52), (72, 66), (56, 72)], fg)      # fins
        pg([(52, 70), (60, 88), (68, 70)], accent)            # flame
        ln(20, 20, 34, 34, accent, 3)
        ln(14, 44, 30, 44, accent, 3)
        ln(22, 68, 36, 60, accent, 3)
    elif kind == "van":
        rc(14, 40, 48, 26, fg)
        pg([(62, 40), (82, 48), (86, 66), (62, 66)], fg)      # cab
        rc(68, 50, 12, 10, PAPER)
        ci(28, 70, 8, INK)
        ci(72, 70, 8, INK)
        rc(32, 46, 6, 16, RED)
        rc(27, 51, 16, 6, RED)
    elif kind == "bulb":
        ci(50, 38, 24, fg)
        ci(50, 38, 24, fg, fill=False)
        rc(42, 60, 16, 6, fg)
        rc(44, 68, 12, 5, fg)
        ln(26, 14, 74, 62, accent, 4)
    elif kind == "shield":
        pg([(50, 10), (82, 22), (82, 52), (50, 88), (18, 52), (18, 22)], fg)
        pg([(50, 18), (74, 27), (74, 50), (50, 78), (26, 50), (26, 27)], PAPER)
        ln(36, 46, 46, 58, RED, 4)
        ln(46, 58, 66, 30, RED, 4)
        for dx, dy in ((-14, -8), (14, -8), (0, 6)):
            ci(50 + dx, 22 + dy, 2, fg)
    elif kind == "cedar":
        pg([(50, 12), (72, 38), (28, 38)], (46, 125, 50))
        pg([(50, 28), (78, 56), (22, 56)], (46, 125, 50))
        pg([(50, 46), (82, 74), (18, 74)], (46, 125, 50))
        rc(46, 74, 8, 14, (93, 64, 55))
    elif kind == "globe":
        ci(50, 50, 36, fg, fill=False)
        el(50, 50, 36, 14, fg, fill=False)
        el(50, 50, 14, 36, fg, fill=False)
        ln(14, 50, 86, 50, fg, 2)
        pg([(62, 26), (78, 10), (84, 26)], (46, 125, 50))
    elif kind == "ship":
        pg([(16, 56), (84, 56), (76, 74), (24, 74)], fg)
        rc(24, 40, 14, 16, accent)
        rc(42, 36, 14, 20, fg)
        rc(60, 42, 14, 14, accent)
        pg([(30, 30), (36, 16), (42, 30)], (232, 122, 36))
        pg([(52, 28), (58, 12), (64, 28)], (232, 122, 36))
        ln(10, 82, 90, 82, fg, 2)
        ln(16, 90, 84, 90, fg, 2)
    elif kind == "passport":
        rc(24, 14, 52, 72, fg)
        rc(30, 20, 40, 60, PAPER)
        ci(50, 40, 10, fg)
        rc(36, 54, 28, 4, fg)
        rc(36, 62, 20, 4, fg)
        ln(70, 70, 88, 88, RED, 5)
        ln(88, 70, 70, 88, RED, 5)
    elif kind == "fence":
        for bx in (18, 38, 58, 78):
            rc(bx, 22, 5, 56, fg)
        ln(12, 34, 88, 34, fg, 3)
        ln(12, 64, 88, 64, fg, 3)
        rc(34, 78, 32, 12, RED)
        ln(34, 78, 66, 90, PAPER, 2)
    elif kind == "crowd":
        ci(30, 34, 10, fg)
        ci(50, 26, 10, fg)
        ci(70, 34, 10, fg)
        pg([(20, 78), (30, 48), (40, 78)], fg)
        pg([(40, 78), (50, 44), (60, 78)], fg)
        pg([(60, 78), (70, 48), (80, 78)], fg)
        rc(72, 12, 22, 14, RED)
        ln(82, 26, 82, 48, fg, 2)
    elif kind == "building":
        rc(16, 34, 22, 48, fg)
        rc(42, 20, 22, 62, fg)
        rc(68, 44, 18, 38, fg)
        for bx in (20, 28, 46, 54, 72):
            rc(bx, 30, 5, 5, PAPER)
        ln(42, 20, 52, 40, accent, 3)
        ln(52, 40, 44, 58, accent, 3)
        ln(44, 58, 56, 74, accent, 3)
        pg([(72, 12), (78, 2), (84, 12)], (232, 122, 36))
    elif kind == "mercury":
        ci(50, 50, 34, (150, 135, 95))
        ci(38, 38, 7, (120, 105, 70))
        ci(60, 58, 9, (120, 105, 70))
        ci(56, 32, 5, (120, 105, 70))
        ci(40, 62, 4, (120, 105, 70))
        rc(70, 12, 16, 8, fg)
        rc(64, 20, 4, 12, fg)
        rc(82, 20, 4, 12, fg)
        ln(74, 8, 86, 2, accent, 2)
    elif kind == "heli":
        el(48, 52, 26, 14, fg)
        pg([(70, 46), (90, 50), (90, 56), (70, 58)], fg)
        ln(14, 34, 86, 34, fg, 3)
        ln(40, 66, 34, 78, fg, 2)
        ln(56, 66, 62, 78, fg, 2)
        ln(30, 78, 66, 78, fg, 2)
        ci(86, 52, 4, accent)
    elif kind == "ballot":
        rc(22, 44, 56, 40, fg)
        rc(30, 52, 40, 24, PAPER)
        ln(36, 64, 46, 72, RED, 3)
        ln(46, 72, 64, 52, RED, 3)
        rc(40, 18, 20, 30, PAPER)
        ro(40, 18, 20, 30, fg)
        ln(44, 30, 56, 30, fg, 2)
    elif kind == "plane":
        el(50, 50, 30, 9, fg)
        pg([(34, 50), (58, 30), (66, 50)], fg)
        pg([(44, 50), (62, 68), (70, 50)], fg)
        pg([(74, 44), (88, 36), (88, 48)], fg)
        ci(28, 48, 3, PAPER)
    elif kind == "cyclone":
        ci(50, 50, 30, fg, fill=False)
        ci(50, 50, 20, fg, fill=False)
        ci(50, 50, 10, fg, fill=False)
        pg([(50, 50), (72, 34), (78, 52)], accent)
        ln(30, 84, 26, 92, (31, 78, 121), 3)
        ln(50, 84, 46, 92, (31, 78, 121), 3)
        ln(70, 84, 66, 92, (31, 78, 121), 3)
    elif kind == "seismo":
        ln(10, 50, 24, 50, fg, 2)
        ln(24, 50, 32, 26, accent, 3)
        ln(32, 26, 40, 70, accent, 3)
        ln(40, 70, 48, 38, accent, 3)
        ln(48, 38, 56, 58, accent, 3)
        ln(56, 58, 66, 50, accent, 3)
        ln(66, 50, 90, 50, fg, 2)
        ln(10, 78, 90, 78, fg, 2)
    elif kind == "sub":
        el(50, 48, 34, 12, fg)
        rc(40, 30, 18, 12, fg)
        ln(49, 30, 49, 20, fg, 3)
        ln(20, 34, 30, 34, fg, 2)
        ci(66, 46, 3, PAPER)
        ci(58, 46, 3, PAPER)
        ln(12, 74, 88, 74, (31, 78, 121), 2)
        ln(20, 82, 80, 82, (31, 78, 121), 2)
    elif kind == "bridge":
        ln(10, 70, 90, 70, fg, 3)
        rc(48, 24, 4, 46, fg)
        for tx in (18, 28, 38, 62, 72, 82):
            ln(50, 26, tx, 70, fg, 1)
        pg([(44, 24), (52, 24), (50, 12)], accent)
    elif kind == "mountain":
        pg([(8, 82), (38, 30), (62, 82)], fg)
        pg([(34, 82), (66, 16), (92, 82)], (90, 90, 85))
        pg([(38, 30), (46, 42), (30, 42)], PAPER)
        pg([(66, 16), (74, 30), (58, 30)], PAPER)
        ln(14, 90, 28, 78, accent, 2)
        ln(28, 78, 36, 88, accent, 2)
        ln(36, 88, 46, 76, accent, 2)
    elif kind == "cuffs":
        ci(30, 50, 16, fg, fill=False)
        ci(70, 50, 16, fg, fill=False)
        ci(30, 50, 16, fg, fill=False)
        ln(44, 44, 56, 44, fg, 3)
        ln(44, 56, 56, 56, fg, 3)
        ci(50, 50, 4, accent)
    elif kind == "racecar":
        pg([(14, 58), (22, 44), (52, 40), (76, 48), (86, 58), (86, 64),
            (14, 64)], fg)
        rc(30, 46, 16, 8, PAPER)
        ci(30, 66, 8, INK)
        ci(70, 66, 8, INK)
        for i in range(4):
            for j in range(2):
                if (i + j) % 2 == 0:
                    rc(62 + i * 6, 14 + j * 6, 6, 6, INK)
        ln(62, 14, 62, 38, fg, 2)
    elif kind == "hospital":
        rc(20, 20, 60, 60, fg)
        rc(44, 30, 12, 40, PAPER)
        rc(30, 44, 40, 12, PAPER)
        ln(20, 88, 80, 88, fg, 2)
    elif kind == "spray":
        rc(36, 34, 22, 48, fg)
        rc(40, 24, 14, 10, fg)
        ln(54, 26, 72, 20, fg, 3)
        ci(76, 18, 2, (31, 78, 121))
        ci(82, 26, 2, (31, 78, 121))
        ci(78, 34, 2, (31, 78, 121))
        ln(66, 40, 74, 60, (211, 178, 60), 2)
        ln(70, 50, 80, 44, (211, 178, 60), 2)
    elif kind == "boat":
        pg([(18, 46), (78, 60), (72, 74), (26, 66)], fg)
        ln(52, 52, 60, 22, fg, 3)
        pg([(60, 22), (60, 48), (78, 48)], accent)
        ln(10, 82, 90, 82, (31, 78, 121), 2)
        ln(18, 90, 82, 90, (31, 78, 121), 2)
    elif kind == "suitcase":
        rc(24, 36, 52, 44, fg)
        rc(38, 26, 24, 10, fg)
        rc(48, 36, 4, 44, PAPER)
        ci(34, 84, 4, INK)
        ci(66, 84, 4, INK)
        ln(76, 20, 88, 12, accent, 3)
        pg([(88, 12), (80, 12), (86, 20)], accent)
    elif kind == "football":
        ci(50, 50, 32, fg, fill=False)
        pg([(50, 38), (62, 47), (57, 62), (43, 62), (38, 47)], fg)
        ln(50, 38, 50, 18, fg, 2)
        ln(62, 47, 80, 40, fg, 2)
        ln(57, 62, 70, 76, fg, 2)
        ln(43, 62, 30, 76, fg, 2)
        ln(38, 47, 20, 40, fg, 2)
    elif kind == "bitcoin":
        ci(50, 50, 34, (232, 160, 32))
        draw_text(cv, P(41, 28)[0], P(41, 28)[1], "B", PAPER, "B",
                  36 if s >= 60 else 24)
    elif kind == "note":
        el(38, 66, 12, 9, fg)
        ln(48, 66, 48, 22, fg, 3)
        pg([(48, 22), (72, 34), (48, 40)], fg)
    elif kind == "tennis":
        ci(36, 62, 24, (211, 178, 60))
        ln(18, 48, 30, 72, PAPER, 2)
        ln(54, 48, 42, 72, PAPER, 2)
        el(72, 30, 12, 16, fg, fill=False)
        ln(66, 44, 56, 58, fg, 3)
    elif kind == "rugby":
        el(50, 50, 34, 20, (120, 72, 30))
        ln(38, 44, 62, 56, PAPER, 2)
        ln(44, 40, 48, 46, PAPER, 2)
        ln(52, 44, 56, 50, PAPER, 2)
        ln(56, 50, 60, 56, PAPER, 2)
    elif kind == "cricket":
        pg([(30, 30), (52, 30), (52, 74), (30, 74)], (200, 170, 120))
        rc(38, 74, 6, 16, fg)
        ci(70, 60, 10, RED)
        ln(66, 56, 74, 64, PAPER, 1)
    elif kind == "rings":
        ci(30, 36, 10, (0, 90, 160), fill=False)
        ci(50, 36, 10, (20, 20, 20), fill=False)
        ci(70, 36, 10, (200, 30, 30), fill=False)
        ci(40, 52, 10, (220, 180, 0), fill=False)
        ci(60, 52, 10, (0, 140, 60), fill=False)
        pg([(46, 84), (54, 84), (50, 72)], (232, 122, 36))
        rc(47, 84, 6, 8, fg)
    elif kind == "doubles":
        el(34, 34, 12, 16, fg, fill=False)
        ln(28, 48, 18, 62, fg, 3)
        el(66, 34, 12, 16, fg, fill=False)
        ln(72, 48, 82, 62, fg, 3)
        ci(50, 62, 8, (211, 178, 60))
    else:  # fallback: a simple star
        pg([(50, 14), (60, 40), (88, 40), (66, 56), (74, 84), (50, 66),
            (26, 84), (34, 56), (12, 40), (40, 40)], accent)

# ------------------------------------------------------------------ stories
# (number, region, headline, body, source, pictogram, map u, map v)
# Map positions are fractions of the map area; None means "not pinned".
# All 34 stories happened, or were first reported, on Sunday 22 Nov 2026
# (several broke late on Saturday 21 Nov and were reported on Sunday).
STORIES = [
    (1, "MIDDLE EAST", "IRAN STRIKES US BASES IN THE GULF",
     "Missiles and drones hit US positions in Bahrain, Kuwait and Jordan "
     "late on Saturday. Washington says almost all were intercepted; a "
     "civilian site in Bahrain caught fire.",
     "Reuters - Al Jazeera - ANI", "missile", 0.650, 0.390),
    (2, "MIDDLE EAST", "AID VAN HIT IN GAZA CITY",
     "A drone strike killed three in a van carrying food-aid papers.",
     "Reuters - AFP - Al Jazeera", "van", 0.600, 0.350),
    (3, "MIDDLE EAST", "IRAN STARTS RATIONING POWER",
     "Rolling cuts of up to two hours a day begin on Sunday as war damage "
     "and fuel shortages hit the grid, the national electricity company says.",
     "RFE/RL - Reuters", "bulb", None, None),
    (4, "MIDDLE EAST", "JORDAN DOWNS FIVE MISSILES",
     "Five missiles were shot down near Azraq as Iran's wave passed over "
     "the region. No casualties or material damage were reported.",
     "Al Jazeera - Philippine Daily Post", "shield", None, None),
    (5, "MIDDLE EAST", "LEBANON MARKS INDEPENDENCE DAY",
     "Lebanon marks 83 years since independence from France on 22 "
     "November 1943.",
     "Bestie10", "cedar", None, None),
    (6, "EUROPE", "COP31 NEARS A DEAL IN ANTALYA",
     "A new package text was put to nearly 200 nations late on Saturday. "
     "Objections are due by 03:00 GMT; an approval session is set for "
     "06:00 GMT on Sunday.",
     "Reuters", "globe", 0.575, 0.270),
    (7, "EUROPE", "RUSSIAN SHIP BURNING OFF FINLAND",
     "Drones hit the cargo ship Sparta II; its 16 crew took to lifeboats.",
     "CNN - Reuters - ISW", "ship", 0.575, 0.115),
    (8, "EUROPE", "DENMARK EXPELS RUSSIAN ATTACHE",
     "Copenhagen will expel Russia's defence attache after accusing Moscow "
     "of a foiled plot to kill rapper Kyivstoner at a concert near the capital.",
     "WSJ - CNN - Al Jazeera", "passport", None, None),
    (9, "EUROPE", "ESTONIA TO SHUT ITS RUSSIA BORDER",
     "All five road crossings with Russia will close from 1 December for "
     "six months, after an arson attempt Estonia blames on Russian "
     "military intelligence.",
     "Reuters - Zot News", "fence", None, None),
    (10, "EUROPE", "FRANCE MARCHES FOR A SIXTH SATURDAY",
     "82,500 marched over living costs, down from 106,000 a week earlier.",
     "Reuters", "crowd", 0.515, 0.230),
    (11, "EUROPE", "DOUBLE-TAP STRIKE HITS KRYVYI RIH",
     "A Russian ballistic-missile strike on Zelenskyy's home city killed "
     "two, including a seven-year-old boy, and wounded 60. A second wave "
     "hit rescuers.",
     "AP - NY Post - Ukrinform", "building", None, None),
    (12, "EUROPE", "BEPICOLOMBO REACHES MERCURY",
     "After eight years in space, the ESA-JAXA mission entered orbit around "
     "Mercury, only the second mission ever to do so. Science begins in "
     "April 2027.",
     "ESA - Nature - Sky & Telescope", "mercury", None, None),
    (13, "EUROPE", "RUSSIAN HELICOPTER IN FINNISH SKIES",
     "Finland says a Russian helicopter is suspected of violating its "
     "airspace near Loviisa on the same day the Sparta II was hit.",
     "ISW - CNN", "heli", None, None),
    (14, "ASIA-PACIFIC", "HONG KONG VOTES FOR ITS ELECTION BODY",
     "856 candidates contest 723 seats on the Election Committee.",
     "China Daily Asia - World Today Journal", "ballot", 0.817, 0.405),
    (15, "ASIA-PACIFIC", "NEPAL'S PM ARRIVES IN DELHI",
     "Balendra Shah begins a two-day state visit, his first trip abroad "
     "since taking office in March. Talks with Narendra Modi are set for Monday.",
     "IANS - Radio Nepal - MEA", "plane", None, None),
    (16, "ASIA-PACIFIC", "CYCLONE AKVAN GROUNDS FLIGHTS",
     "The storm's remnants forced 14 flights to be cancelled at Ranchi "
     "airport as visibility fell to about 1,000 metres. The cyclone has "
     "weakened to a depression.",
     "PTI - Jagran Josh", "cyclone", None, None),
    (17, "ASIA-PACIFIC", "DEEP QUAKE RATTLES SULU SEA",
     "A magnitude 5.9 earthquake struck 586 km deep in the Sulu Sea on "
     "Saturday evening. No damage was reported from the very deep tremor.",
     "BMKG - VolcanoDiscovery", "seismo", None, None),
    (18, "ASIA-PACIFIC", "AUSTRALIA REJECTS US REPORT ON AUKUS",
     "Richard Marles criticised a US report on the submarine pact.",
     "Reuters", "sub", 0.869, 0.769),
    (19, "ASIA-PACIFIC", "MODI OPENS NITISH SETU BRIDGE",
     "The six-lane cable-stayed bridge over the Ganga in Bihar, worth "
     "Rs 4,280 crore, will cut the Patna-Vaishali trip to about 20 minutes.",
     "PIB - Jagran - Zee News", "bridge", None, None),
    (20, "THE AMERICAS", "PERU SHAKEN BY STRONG QUAKE",
     "A magnitude 6.7 quake - first read as high as 6.9 - struck near "
     "Junin on Friday night, sending Lima residents into the streets. "
     "No deaths; 128 homes damaged, eight people hurt.",
     "IGP - USGS - The Hindu BusinessLine", "mountain", 0.291, 0.663),
    (21, "THE AMERICAS", "MEXICO CAPTURES 'EL CHAPO ISIDRO'",
     "Special forces seized cartel boss Isidro Meza Flores in Sinaloa.",
     "Reuters - CNN - US DOJ", "cuffs", 0.199, 0.380),
    (22, "THE AMERICAS", "VERSTAPPEN INHERITS VEGAS POLE",
     "Kimi Antonelli was fastest in qualifying, but a five-place grid "
     "penalty for an engine change hands pole to Max Verstappen for "
     "Saturday's race.",
     "FIA - Formula 1 - AP", "racecar", None, None),
    (23, "THE AMERICAS", "BOLSONARO TAKEN TO INTENSIVE CARE",
     "Brazil's ex-president, 71, is in intensive care in Brasilia.",
     "Reuters - AFP - The Times", "hospital", 0.367, 0.698),
    (24, "THE AMERICAS", "ROUNDUP DEAL WORTH $7.25BN APPROVED",
     "A Missouri judge approved Bayer's nationwide settlement over claims "
     "the weedkiller caused cancer. Payouts run from $10,000 to $165,000.",
     "AP - NPR - Agri-Pulse", "spray", None, None),
    (25, "AFRICA", "BOAT CAPSIZES IN NIGERIA, 24 DEAD",
     "A boat carrying mourners sank in Bayelsa; 24 bodies were recovered.",
     "AP - NEMA - Radio Nigeria", "boat", 0.518, 0.540),
    (26, "AFRICA", "25 DEPORTEES ARRIVE IN LIBERIA",
     "Twenty-five migrants deported from the United States arrived in "
     "Liberia, officials said.",
     "AFP", "suitcase", None, None),
    (27, "AFRICA", "GHANA FACE MOROCCO IN HISTORIC FINAL",
     "Ghana beat holders Turkiye 4-3 on penalties and Morocco beat Brazil "
     "2-1 to set up the first all-African Amputee Football World Cup "
     "final, on Sunday in Mexico.",
     "Ghana Guardian - Ghana SoccerNet", "football", None, None),
    (28, "MARKETS & TECH", "BITCOIN CLAWS BACK $60,000",
     "Bitcoin fell to $55,130, then bounced 9% to about $60,300.",
     "Reuters - CoinDesk", "bitcoin", 0.294, 0.264),
    (29, "MARKETS & TECH", "TIKTOK ROLLS OUT DEEPFAKE TOOL",
     "TikTok launched a likeness-detection tool for politicians and public "
     "figures, plus a public checker for AI-made media, ahead of European "
     "elections in 2027.",
     "AFP - CNA - Asia Daily", "note", None, None),
    (30, "SPORT", "ENGLAND ROUT THE ALL BLACKS 37-12",
     "Five tries gave England a record 25-point win over New Zealand.",
     "Reuters - AP - RFU", "rugby", 0.485, 0.165),
    (31, "SPORT", "ZVEREV MEETS ALCARAZ FOR THE TITLE",
     "World No. 1 Zverev, yet to drop a set in Turin, faces Alcaraz in the "
     "ATP Finals title match on Sunday evening. Alcaraz is chasing his "
     "first crown.",
     "ATP Tour - TennisNow", "tennis", None, None),
    (32, "SPORT", "PANT HITS 128 AS INDIA PILE UP 629-6",
     "Rishabh Pant's ninth Test hundred powered India to their highest "
     "Test total in New Zealand, a lead of 261 on day four in Wellington.",
     "Reuters - AP - IANS", "cricket", None, None),
    (33, "SPORT", "MELBOURNE MARKS 70 YEARS SINCE '56",
     "Surviving Olympians gather at the MCG for the 70th anniversary of "
     "the 1956 Games. Swimmer Jon Henricks, Australia's first swimming "
     "gold medallist there, died aged 91.",
     "AAP - Australian Olympic Team", "rings", None, None),
    (34, "SPORT", "DOUBLES CROWN DECIDED IN TURIN",
     "Arevalo and Pavic meet Arribage and Olivetti in the ATP Finals "
     "doubles final on Sunday afternoon, before the singles title match.",
     "Tennis Tour Calendar - ATP Tour", "doubles", None, None),
]

# One-line versions of the stories that only appear in the numbered list.
ALSO = {
    3: "Iran begins power rationing from Sunday, with rolling cuts of up to two hours a day.",
    4: "Jordan shot down five missiles near Azraq; no casualties or damage were reported.",
    5: "Lebanon marks its Independence Day, 83 years after independence from France.",
    8: "Denmark expels Russia's defence attache over a foiled plot to kill rapper Kyivstoner.",
    9: "Estonia will shut all five road crossings with Russia from 1 December, for six months.",
    11: "A Russian double-tap strike on Kryvyi Rih killed two, including a seven-year-old boy.",
    12: "BepiColombo entered orbit around Mercury, only the second mission ever to do so.",
    13: "A Russian helicopter is suspected of violating Finnish airspace near Loviisa.",
    15: "Nepal's PM Balendra Shah arrives in Delhi on his first trip abroad since taking office.",
    16: "Cyclone Akvan's remnants forced 14 flights to be cancelled at Ranchi airport.",
    17: "A magnitude 5.9 quake struck the Sulu Sea, 586 km deep; no damage was reported.",
    19: "Modi opens Nitish Setu, a six-lane bridge over the Ganga in Bihar, worth Rs 4,280 crore.",
    22: "Verstappen inherits pole in Las Vegas after fastest man Antonelli takes a penalty.",
    24: "A Missouri judge approves a $7.25bn Roundup settlement covering current and future claims.",
    26: "Twenty-five migrants deported from the US arrived in Liberia.",
    27: "Ghana face Morocco in the first all-African Amputee Football World Cup final, on Sunday.",
    29: "TikTok rolls out a deepfake-spotting tool for politicians and public figures.",
    31: "Zverev meets Alcaraz in the ATP Finals title match in Turin on Sunday evening.",
    32: "Pant hits 128 as India pile up 629-6 in Wellington, their highest Test total in New Zealand.",
    33: "Melbourne marks 70 years since the 1956 Olympics opened; swimmer Jon Henricks dies at 91.",
    34: "Arevalo and Pavic meet Arribage and Olivetti in the ATP Finals doubles final.",
}

TOP_NUMBERS = (1, 6, 20)
SMALL_NUMBERS = (2, 7, 10, 14, 18, 21, 23, 25, 28, 30)

REGION_ORDER = ["MIDDLE EAST", "EUROPE", "ASIA-PACIFIC", "THE AMERICAS",
                "AFRICA", "MARKETS & TECH", "SPORT"]

STATS = [
    ("34", "STORIES IN THIS EDITION"),
    ("7", "REGIONS COVERED"),
    ("24", "KILLED AS BOAT CAPSIZES IN NIGERIA"),
    ("6.7", "PERU QUAKE, MAGNITUDE"),
    ("82,500", "MARCH IN FRANCE"),
    ("$60,000", "BITCOIN REBOUNDS"),
]

DATE_CHECK = ("Left out on purpose: the Trump-Xi-Putin summit in Shenzhen "
              "(19 Nov) - the Kerch Bridge strikes (earlier in the week) - "
              "the ICJ ruling on Myanmar (19 Nov) - Voyager 1 reaching one "
              "light-day (18 Nov) - the Wall Street sell-off (Fri 20 Nov).")

# Simplified continent outlines, in fractions of the map area.
CONTINENTS = [
    [(0.02, 0.24), (0.07, 0.12), (0.15, 0.09), (0.23, 0.14), (0.27, 0.22),
     (0.25, 0.30), (0.19, 0.33), (0.16, 0.44), (0.10, 0.42), (0.05, 0.33)],
    [(0.29, 0.05), (0.34, 0.04), (0.35, 0.11), (0.30, 0.12)],
    [(0.23, 0.50), (0.29, 0.45), (0.35, 0.50), (0.36, 0.62), (0.32, 0.76),
     (0.28, 0.82), (0.25, 0.66), (0.22, 0.56)],
    [(0.46, 0.15), (0.51, 0.10), (0.57, 0.13), (0.59, 0.20), (0.55, 0.26),
     (0.50, 0.27), (0.46, 0.21)],
    [(0.46, 0.36), (0.53, 0.34), (0.60, 0.40), (0.59, 0.52), (0.55, 0.64),
     (0.51, 0.66), (0.48, 0.50), (0.45, 0.42)],
    [(0.60, 0.09), (0.74, 0.06), (0.87, 0.12), (0.95, 0.20), (0.92, 0.30),
     (0.86, 0.38), (0.80, 0.34), (0.76, 0.42), (0.70, 0.44), (0.64, 0.34),
     (0.59, 0.24)],
    [(0.78, 0.47), (0.82, 0.45), (0.84, 0.50), (0.80, 0.52)],
    [(0.85, 0.50), (0.88, 0.49), (0.89, 0.53), (0.86, 0.54)],
    [(0.81, 0.64), (0.89, 0.62), (0.94, 0.68), (0.90, 0.75), (0.84, 0.73)],
]
MAP_LABELS = [
    ("NORTH AMERICA", 0.07, 0.28), ("SOUTH AMERICA", 0.185, 0.585),
    ("EUROPE", 0.47, 0.065), ("AFRICA", 0.50, 0.44),
    ("ASIA", 0.70, 0.22), ("AUSTRALIA", 0.80, 0.69),
]


def by_number(n):
    for story in STORIES:
        if story[0] == n:
            return story
    raise KeyError(n)


# ------------------------------------------------------------------ layout
def draw_top_panel(cv, story, x, y, w, h, tint):
    n, region, headline, body, source, pic, _, _ = story
    cv.rect(x, y, w, h, PAPER)
    cv.rect_outline(x, y, w, h, INK, 1)
    cv.rect(x + 1, y + 1, w - 2, 80, tint)
    draw_pic(cv, pic, x + (w - 64) // 2, y + 8, 64, INK, RED)
    draw_text(cv, x + 8, y + 88, region + " - LEAD STORY", RED, "B", 9)
    draw_wrapped(cv, x + 8, y + 104, headline, INK, "B", 13, w - 16, 17)
    draw_wrapped(cv, x + 8, y + 140, body, INK, "R", 10, w - 16, 13)
    draw_text(cv, x + 8, y + h - 14, "Sources: " + source, GREY, "R", 8)


def draw_small_panel(cv, story, x, y, w, h):
    n, region, headline, body, source, pic, _, _ = story
    cv.rect(x, y, w, h, PAPER)
    cv.rect_outline(x, y, w, h, INK, 1)
    draw_pic(cv, pic, x + 6, y + 6, 44, INK, RED)
    draw_wrapped(cv, x + 56, y + 8, headline, INK, "B", 10, w - 62, 12)
    draw_wrapped(cv, x + 6, y + 56, body, INK, "R", 9, w - 12, 11)
    draw_text(cv, x + 6, y + h - 13, region, GREY, "R", 8)


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, SEA)
    cv.rect_outline(x, y, w, h, INK, 1)
    grid = (198, 214, 224)
    for i in range(1, 6):
        cv.vline(x + w * i // 6, y, y + h - 1, grid)
    for i in range(1, 4):
        cv.hline(x, x + w - 1, y + h * i // 4, grid)
    for poly in CONTINENTS:
        pts = [(x + int(u * w + 0.5), y + int(v * h + 0.5)) for u, v in poly]
        cv.poly(pts, LAND)
        cv.poly(pts, LAND_LINE, fill=False)
    for label, u, v in MAP_LABELS:
        draw_text(cv, x + int(u * w + 0.5), y + int(v * h + 0.5),
                  label, GREY, "R", 8)
    for n in list(TOP_NUMBERS) + list(SMALL_NUMBERS):
        story = by_number(n)
        _, _, _, _, _, _, mu, mv = story
        px = x + int(mu * w + 0.5)
        py = y + int(mv * h + 0.5)
        cv.circle(px, py, 9, RED)
        cv.circle(px, py, 9, PAPER, fill=False)
        num = str(n)
        draw_text(cv, px - text_width(num, "B", 9) // 2, py - 6,
                  num, PAPER, "B", 9)


def build():
    cv = Canvas(W, H, PAPER)
    cv.rect_outline(3, 3, W - 6, H - 6, INK, 3)

    # Masthead.
    draw_text_centred(cv, W // 2, 14, "THE WORLD IN ONE DAY", INK, "B", 24)
    draw_text_centred(cv, W // 2, 46, "Sunday 22 November 2026", INK, "B", 36)
    draw_text_centred(cv, W // 2, 92,
                      "Iran hits US bases in the Gulf  \u2022  COP31 nears a "
                      "deal in Antalya  \u2022  Peru reels from a 6.7 quake",
                      INK, "R", 12)
    cv.hline(10, W - 10, 110, INK, 2)

    # Stat strip.
    cell = 1004 // 6
    for i, (num, label) in enumerate(STATS):
        cx = 10 + cell * i + cell // 2
        draw_text_centred(cv, cx, 118, num, INK, "B", 20)
        draw_text_centred(cv, cx, 143, label, GREY, "R", 8)
        if i:
            cv.vline(10 + cell * i, 116, 152, LIGHT, 1)
    cv.hline(10, W - 10, 154, LIGHT, 1)

    # Region bar.
    counts = {}
    for story in STORIES:
        counts[story[1]] = counts.get(story[1], 0) + 1
    seg_w = [143, 143, 143, 144, 143, 144, 144]
    rx = 10
    for name, sw in zip(REGION_ORDER, seg_w):
        cv.rect(rx, 158, sw, 22, REGION_COLOURS[name])
        draw_text_centred(cv, rx + sw // 2, 164,
                          name + " " + str(counts[name]), PAPER, "B", 11)
        rx += sw
    cv.hline(10, W - 10, 186, INK, 2)

    # Three large panels.
    tints = [(246, 232, 232), (232, 238, 246), (238, 243, 232)]
    for i, n in enumerate(TOP_NUMBERS):
        draw_top_panel(cv, by_number(n), 10 + i * 338, 192, 328, 196,
                       tints[i])

    # Ten smaller panels, two rows of five.
    for i, n in enumerate(SMALL_NUMBERS):
        row, col = divmod(i, 5)
        draw_small_panel(cv, by_number(n), 10 + col * 202, 396 + row * 95,
                         196, 89)

    # Map (left) and the numbered list (right).
    draw_text(cv, 10, 588, "WHERE IT HAPPENED - 13 PLACES ON THE MAP",
              INK, "B", 11)
    draw_map(cv, 10, 606, 456, 278)
    draw_text(cv, 10, 890, "Pins 1-13 mark the front-page stories. "
              "Map not to scale.", GREY, "R", 8)
    draw_text(cv, 474, 588, "ALSO ON SUNDAY 22 NOVEMBER - 21 MORE STORIES",
              INK, "B", 11)
    also_numbers = sorted(ALSO.keys())
    for i, n in enumerate(also_numbers):
        yy = 610 + i * 14
        draw_text(cv, 474, yy, str(n) + ".", RED, "B", 10)
        draw_text(cv, 500, yy, ALSO[n], INK, "R", 10)

    # Date check.
    cv.rect(10, 922, 1004, 48, (246, 243, 235))
    cv.rect_outline(10, 922, 1004, 48, INK, 1)
    draw_text(cv, 18, 928, "DATE CHECK - NOT SUNDAY'S NEWS", RED, "B", 10)
    draw_wrapped(cv, 18, 942, DATE_CHECK, INK, "R", 9, 988, 11)

    # Footer.
    draw_text_centred(cv, W // 2, 978,
                      "Every story here happened, or was first reported, on "
                      "Sunday 22 November 2026.", GREY, "R", 8)
    draw_text_centred(cv, W // 2, 991,
                      "Sources: Reuters, Associated Press, AFP, Al Jazeera, "
                      "BBC, The Times, ESA, ATP Tour, Formula 1, PHIVOLCS, "
                      "NEMA, Press Information Bureau of India.",
                      GREY, "R", 8)
    draw_text_centred(cv, W // 2, 1004,
                      "Drawn by a Python program using only the standard "
                      "library. No photographs: every picture is drawn from "
                      "lines and shapes.", GREY, "R", 8)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.dirname(
        os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)
    write_png(os.path.join(out_dir, "entry.png"), build())


if __name__ == "__main__":
    main()
