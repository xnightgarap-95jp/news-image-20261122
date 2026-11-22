#!/usr/bin/env python3
"""Draw the world news of Sunday 22 November 2026 as one front page.

Pure Python standard library only. Renders a 1024x1024 PNG with a small
raster canvas (rectangles, lines, polygons, a 5x7 bitmap font) and encodes
it with zlib. No network, no clock, no randomness outside a fixed seed,
so every run writes byte-identical output.
"""
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 232)
CREAM = (250, 246, 236)
INK = (20, 24, 34)
NAVY = (18, 33, 61)
NAVY2 = (28, 52, 92)
RED = (179, 18, 46)
RED2 = (214, 48, 49)
ORANGE = (232, 122, 36)
GOLD = (245, 197, 66)
GREEN = (24, 110, 74)
GREEN2 = (46, 148, 102)
TEAL = (24, 92, 96)
SKY = (140, 178, 208)
WHITE = (255, 255, 255)
GREY = (120, 124, 132)
DARK = (12, 16, 28)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x, y, w, c, t=1):
        for k in range(t):
            self.rect(x, y + k, w, 1, c)

    def vline(self, x, y, h, c, t=1):
        for k in range(t):
            self.rect(x + k, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x + a, y + b, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=2):
        for k in range(t):
            rr = r - k
            for a in range(360):
                import math
                x = cx + int(rr * math.cos(a * math.pi / 180.0))
                y = cy + int(rr * math.sin(a * math.pi / 180.0))
                self.set(x, y, c)

    def poly(self, pts, c):
        # scanline fill, pts = list of (x, y)
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.rect(int(xs[j]), y, int(xs[j + 1]) - int(xs[j]) + 1, 1, c)

    def vgrad(self, x, y, w, h, top, bot):
        for yy in range(h):
            f = yy / max(1, h - 1)
            c = tuple(int(top[i] + (bot[i] - top[i]) * f) for i in range(3))
            self.rect(x, y + yy, w, 1, c)


# ------------------------------------------------------------------ font
# 5x7 bitmap glyphs, rows as strings of '#' / '.'.
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "<": ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color, center_x=None):
    if center_x is not None:
        x = center_x - text_w(s, scale) // 2
    cx = x
    for ch in s:
        g = GLYPHS.get(ch, GLYPHS[" "])
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == "1":
                    cv.rect(cx + c * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def frame(cv, x, y, w, h, color=INK, t=2):
    cv.rect(x, y, w, t, color)
    cv.rect(x, y + h - t, w, t, color)
    cv.rect(x, y, t, h, color)
    cv.rect(x + w - t, y, t, h, color)


def burst(cv, cx, cy, r, c1, c2):
    pts = []
    for k in range(16):
        ang = k * 22.5
        rr = r if k % 2 == 0 else r // 2
        import math
        pts.append((cx + int(rr * math.cos(ang * math.pi / 180.0)),
                    cy + int(rr * math.sin(ang * math.pi / 180.0))))
    cv.poly(pts, c1)
    cv.disc(cx, cy, max(3, r // 3), c2)


def missile_arc(cv, x0, y0, x1, y1, lift, color, head):
    # quadratic bezier polyline
    n = 26
    prev = None
    for i in range(n + 1):
        t = i / n
        mx = (x0 + x1) // 2
        my = min(y0, y1) - lift
        x = int((1 - t) * (1 - t) * x0 + 2 * (1 - t) * t * mx + t * t * x1)
        y = int((1 - t) * (1 - t) * y0 + 2 * (1 - t) * t * my + t * t * y1)
        if prev is not None:
            cv.line(prev[0], prev[1], x, y, color, 2)
        prev = (x, y)
    cv.disc(x1, y1, 4, head)
    cv.disc(x1, y1, 2, WHITE)


# ------------------------------------------------------------------ scenes
def masthead(cv):
    cv.rect(0, 0, W, 104, NAVY)
    cv.rect(0, 104, W, 6, RED)
    draw_text(cv, 0, 16, "THE WORLD IN ONE DAY", 2, GOLD, center_x=512)
    draw_text(cv, 0, 46, "SUNDAY 22 NOVEMBER 2026", 5, WHITE, center_x=512)


def gulf_panel(cv):
    x, y, w, h = 16, 126, 640, 470
    frame(cv, x, y, w, h)
    # night sky over the Gulf, horizon glow low
    cv.vgrad(x + 2, y + 2, w - 4, 300, (14, 22, 48), (196, 96, 38))
    cv.rect(x + 2, y + 302, w - 4, 22, (16, 40, 70))
    # fixed stars
    seed = 22
    for i in range(46):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        sx = x + 8 + seed % (w - 16)
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        sy = y + 8 + seed % 150
        cv.set(sx, sy, WHITE)
    # sea
    cv.rect(x + 2, y + 324, w - 4, 32, (13, 34, 62))
    cv.hline(x + 10, y + 332, 180, (90, 140, 190), 2)
    cv.hline(x + 380, y + 342, 220, (90, 140, 190), 2)
    # base silhouette on the shore
    cv.rect(x + 60, y + 268, 90, 56, DARK)
    cv.rect(x + 170, y + 288, 60, 36, DARK)
    cv.rect(x + 250, y + 252, 26, 72, DARK)
    cv.rect(x + 300, y + 292, 120, 32, DARK)
    cv.rect(x + 470, y + 276, 70, 48, DARK)
    # radar mast and dish
    cv.line(x + 263, y + 252, x + 263, y + 208, DARK, 3)
    cv.disc(x + 263, y + 206, 16, DARK)
    cv.disc(x + 263, y + 206, 12, (40, 56, 84))
    # missile arcs crossing the sky
    missile_arc(cv, x + 30, y + 60, x + 520, y + 250, 90, ORANGE, GOLD)
    missile_arc(cv, x + 620, y + 40, x + 300, y + 240, 70, ORANGE, GOLD)
    missile_arc(cv, x + 120, y + 20, x + 470, y + 210, 60, (255, 170, 60), GOLD)
    # explosions over the base
    burst(cv, x + 520, y + 250, 26, GOLD, RED2)
    burst(cv, x + 300, y + 240, 20, GOLD, ORANGE)
    burst(cv, x + 470, y + 210, 14, (255, 220, 120), ORANGE)
    # smoke
    cv.disc(x + 540, y + 226, 14, (96, 96, 100))
    cv.disc(x + 318, y + 220, 10, (96, 96, 100))
    # kicker + headline band
    cv.rect(x + 2, y + 356, w - 4, 112, PAPER)
    cv.rect(x + 2, y + 356, w - 4, 3, RED)
    draw_text(cv, x + 16, y + 362, "MIDDLE EAST", 2, RED)
    draw_text(cv, x + 16, y + 380, "IRAN FIRES AT US BASES", 3, INK)
    draw_text(cv, x + 16, y + 402, "IN THE GULF", 3, INK)
    draw_text(cv, x + 16, y + 428, "MISSILES AND DRONES AT KUWAIT AND BAHRAIN", 2, INK)
    draw_text(cv, x + 16, y + 448, "US AND ALLIES SAY ALMOST ALL SHOT DOWN", 2, INK)


def cop31_panel(cv):
    x, y, w, h = 672, 126, 336, 230
    frame(cv, x, y, w, h)
    cv.vgrad(x + 2, y + 2, w - 4, h - 4, (18, 84, 58), (58, 158, 104))
    # sun and globe
    cv.disc(x + 262, y + 52, 26, GOLD)
    cv.disc(x + 262, y + 52, 18, (255, 222, 120))
    cv.ring(x + 78, y + 62, 34, WHITE, 3)
    cv.line(x + 44, y + 62, x + 112, y + 62, WHITE, 2)
    cv.line(x + 78, y + 28, x + 78, y + 96, WHITE, 2)
    # sprout
    cv.line(x + 250, y + 150, x + 250, y + 110, GREEN, 4)
    cv.poly([(x + 250, y + 110), (x + 214, y + 92), (x + 246, y + 84)], GREEN2)
    cv.poly([(x + 250, y + 110), (x + 286, y + 92), (x + 254, y + 84)], GREEN2)
    draw_text(cv, x + 16, y + 156, "CLIMATE", 2, GOLD)
    draw_text(cv, x + 16, y + 176, "COP31 NEARS", 3, WHITE)
    draw_text(cv, x + 16, y + 198, "FINAL DEAL", 3, WHITE)


def hongkong_panel(cv):
    x, y, w, h = 672, 372, 336, 224
    frame(cv, x, y, w, h)
    cv.rect(x + 2, y + 2, w - 4, h - 4, (226, 234, 240))
    # ballot box with a paper going in and a red check
    cv.rect(x + 96, y + 60, 144, 84, WHITE)
    frame(cv, x + 96, y + 60, 144, 84, INK, 3)
    cv.rect(x + 136, y + 60, 64, 8, INK)
    cv.poly([(x + 150, y + 30), (x + 186, y + 30), (x + 182, y + 62),
             (x + 154, y + 62)], PAPER)
    cv.line(x + 158, y + 40, x + 178, y + 40, GREY, 2)
    cv.line(x + 158, y + 48, x + 178, y + 48, GREY, 2)
    cv.line(x + 120, y + 118, x + 138, y + 136, RED, 5)
    cv.line(x + 138, y + 136, x + 176, y + 88, RED, 5)
    draw_text(cv, x + 16, y + 148, "ASIA", 2, RED)
    draw_text(cv, x + 16, y + 168, "HONG KONG", 3, INK)
    draw_text(cv, x + 16, y + 190, "VOTES TODAY", 3, INK)


def quake_panel(cv):
    x, y, w, h = 16, 612, 496, 220
    frame(cv, x, y, w, h)
    cv.rect(x + 2, y + 2, w - 4, h - 4, CREAM)
    # seismograph trace
    pts = [(x + 14, y + 70), (x + 60, y + 70), (x + 74, y + 52),
           (x + 88, y + 92), (x + 102, y + 44), (x + 116, y + 98),
           (x + 130, y + 58), (x + 150, y + 70), (x + 210, y + 70),
           (x + 224, y + 40), (x + 238, y + 100), (x + 252, y + 62),
           (x + 272, y + 70), (x + 340, y + 70), (x + 354, y + 56),
           (x + 368, y + 84), (x + 382, y + 70), (x + 482, y + 70)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED2, 3)
    # cracked ground
    cv.line(x + 20, y + 150, x + 120, y + 150, INK, 2)
    cv.line(x + 120, y + 150, x + 140, y + 168, INK, 2)
    cv.line(x + 140, y + 168, x + 260, y + 168, INK, 2)
    cv.line(x + 260, y + 168, x + 280, y + 150, INK, 2)
    cv.line(x + 280, y + 150, x + 470, y + 150, INK, 2)
    draw_text(cv, x + 16, y + 176, "QUAKE SHAKES MYANMAR", 3, INK)
    draw_text(cv, x + 16, y + 200, "MAGNITUDE 4.1 IN THE EARLY HOURS", 2, INK)


def strip_panel(cv):
    x, y, w, h = 528, 612, 480, 220
    frame(cv, x, y, w, h)
    cv.rect(x + 2, y + 2, w - 4, h - 4, NAVY)
    draw_text(cv, x + 16, y + 18, "ALSO TODAY", 2, GOLD)
    cv.hline(x + 16, y + 44, w - 32, RED, 3)
    lines = [
        "AUSTRALIA FAULTS US REPORT",
        "SAYING AUKUS CUTS SUBMARINE",
        "NUMBERS",
        "",
        "25 MIGRANTS DEPORTED FROM",
        "THE US ARRIVE IN LIBERIA",
        "",
        "TRUMP WARNS IRAN'S LEADERS",
        "AS GULF STRIKES SPREAD",
    ]
    yy = y + 58
    for ln in lines:
        if ln:
            draw_text(cv, x + 16, yy, ln, 2, WHITE)
        yy += 16


def footer(cv):
    draw_text(cv, 0, 1000, "SOURCES: REUTERS - AL JAZEERA - ANI - CHINA DAILY - AFP", 2,
              GREY, center_x=512)


def build():
    cv = Canvas(W, H, PAPER)
    masthead(cv)
    gulf_panel(cv)
    cop31_panel(cv)
    hongkong_panel(cv)
    quake_panel(cv)
    strip_panel(cv)
    footer(cv)
    return cv


# -------------------------------------------------------------------- png
def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * stride:(yy + 1) * stride]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(build())
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)
    print("wrote %d bytes to %s" % (len(data),
                                    os.path.join(outdir, "entry.png")))


if __name__ == "__main__":
    main()
