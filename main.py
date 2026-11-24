#!/usr/bin/env python3
"""The Isle of Almost-Arrr -- a treasure map of an island that does not exist.

Pure-stdlib procedural art: writes a 1024x1024 PNG to /output/entry.png.
No third-party dependencies, no network, no secrets -- everything the
program runs is in this repository.
"""
import math
import os
import random
import struct
import zlib

W = H = 1024
OUT = os.environ.get("OUTPUT_PATH", "/output/entry.png")
rng = random.Random(20261124)

# ---------------------------------------------------------------- palette
PARCH   = (233, 213, 172)
PARCH_D = (214, 190, 148)
SEA     = (151, 178, 170)
SEA_D   = (128, 156, 150)
LAND    = (226, 205, 154)
LAND_H  = (208, 184, 134)
GREEN   = (168, 178, 128)
MOUNT   = (156, 138, 106)
INK     = (66, 46, 32)
INK_SOFT= (110, 84, 60)
RED     = (150, 48, 36)

buf = bytearray(bytes(PARCH) * (W * H))

def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i:i+3] = bytes(c)

def get(x, y):
    i = (y * W + x) * 3
    return buf[i], buf[i+1], buf[i+2]

def fill_rect(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1)):
        row = bytes(c) * (min(W, x1) - max(0, x0))
        i = (y * W + max(0, x0)) * 3
        buf[i:i + len(row)] = row

# parchment mottling
for _ in range(2600):
    x, y = rng.randrange(W), rng.randrange(H)
    r = rng.randint(3, 26)
    c = PARCH_D if rng.random() < 0.6 else PARCH
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                X, Y = x + dx, y + dy
                if 0 <= X < W and 0 <= Y < H:
                    i = (Y * W + X) * 3
                    buf[i:i+3] = bytes(c)

# ---------------------------------------------------------------- geometry
def fill_poly(pts, c):
    ys = [p[1] for p in pts]
    for y in range(max(0, int(min(ys))), min(H, int(max(ys)) + 1)):
        xs = []
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                px(x, y, c)

def line(x0, y0, x1, y1, c, t=1):
    dx, dy = x1 - x0, y1 - y0
    n = int(max(abs(dx), abs(dy))) + 1
    for k in range(n + 1):
        x = x0 + dx * k / n
        y = y0 + dy * k / n
        for a in range(-(t // 2), t // 2 + 1):
            for b in range(-(t // 2), t // 2 + 1):
                px(int(x) + a, int(y) + b, c)

def dashed(x0, y0, x1, y1, c, t=1, dash=8, gap=6):
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy)
    n = int(d) + 1
    s = 0
    while s < n:
        e = min(s + dash, n)
        for k in range(s, e + 1):
            x = x0 + dx * k / n
            y = y0 + dy * k / n
            for a in range(-t, t + 1):
                px(int(x) + a, int(y), c)
        s = e + gap

def circle(cx, cy, r, c, fill=False, t=1):
    if fill:
        for y in range(-r, r + 1):
            w = int(math.sqrt(max(0, r * r - y * y)))
            for x in range(-w, w + 1):
                px(cx + x, cy + y, c)
    else:
        for k in range(360):
            a = math.radians(k)
            for q in range(t):
                px(int(cx + (r - q) * math.cos(a)), int(cy + (r - q) * math.sin(a)), c)

# ---------------------------------------------------------------- island
# irregular coastline as radial noise polygon
CX, CY = 470, 500
base_r = 330
ang = 0.0
coast = []
while ang < 2 * math.pi:
    r = base_r + 62 * math.sin(ang * 2.3 + 1.2) + 40 * math.sin(ang * 3.7) \
        + 26 * math.sin(ang * 5.9 + 2.4) + 14 * math.sin(ang * 9.1)
    coast.append((CX + r * math.cos(ang), CY + r * math.sin(ang) * 0.92))
    ang += 0.035

# sea wash: fill everything outside the coast with sea
ys_all = [p[1] for p in coast]
for y in range(max(0, int(min(ys_all))), min(H, int(max(ys_all)) + 1)):
    xs = []
    n = len(coast)
    for i in range(n):
        x0, y0 = coast[i]
        x1, y1 = coast[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    xs.sort()
    prev = 0
    for j in range(0, len(xs) - 1, 2):
        for x in range(prev, max(prev, int(xs[j]))):
            px(x, y, SEA)
            for q in (1, 2):
                px(x, y + q, SEA_D)
        prev = int(xs[j + 1]) + 1
    for x in range(prev, W):
        px(x, y, SEA)
        for q in (1, 2):
            px(x, y + q, SEA_D)
fill_rect(0, 0, W, max(0, int(min(ys_all))), SEA)
fill_rect(0, min(H, int(max(ys_all)) + 1), W, H, SEA)
# widen sea by drawing a thick coastline
for i in range(len(coast)):
    x0, y0 = coast[i]
    x1, y1 = coast[(i + 1) % len(coast)]
    line(x0, y0, x1, y1, SEA, t=10)
    line(x0, y0, x1, y1, SEA_D, t=4)

fill_poly(coast, LAND)

# beach hatching: inward hatch lines along the coast
import bisect
for i in range(0, len(coast), 3):
    x0, y0 = coast[i]
    ang_i = math.atan2(y0 - CY, x0 - CX)
    for q in range(1, 5):
        x = x0 - 8 * q * math.cos(ang_i)
        y = y0 - 8 * q * math.sin(ang_i) - 3 * q * math.sin(ang_i)
        px(int(x), int(y), LAND_H)

# inside shading / meadow patches
for _ in range(70):
    x = CX + rng.randint(-230, 230)
    y = CY + rng.randint(-210, 210)
    if math.hypot(x - CX, y - CY) < 250:
        r = rng.randint(14, 42)
        c = GREEN if rng.random() < 0.55 else LAND_H
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r and rng.random() < 0.85:
                    px(x + dx, y + dy, c)

# ---------------------------------------------------------------- mountains
MOUNTS = [(430, 380), (480, 370), (530, 385), (455, 415), (505, 418)]
for (mx, my) in MOUNTS:
    h = rng.randint(26, 40)
    fill_poly([(mx - h, my + h // 2), (mx + h, my + h // 2), (mx, my - h)], MOUNT)
    line(mx, my - h, mx - h, my + h // 2, INK, t=1)
    line(mx, my - h, mx + h, my + h // 2, INK, t=1)
    # snow cap
    fill_poly([(mx - h // 3, my - h // 4), (mx + h // 3, my - h // 4), (mx, my - h)],
              PARCH)

# river from mountains to the southern coast
RIVER = [(505, 430), (520, 470), (505, 520), (470, 560), (445, 610), (430, 660), (415, 710)]
pts = [(x + rng.randint(-4, 4), y + rng.randint(-4, 4)) for (x, y) in RIVER]
for i in range(len(pts) - 1):
    line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], SEA_D, t=3)

# ---------------------------------------------------------------- trees
def tree(x, y, s=1):
    circle(x, y - 4 * s, 4 * s, (94, 118, 84), fill=True)
    line(x, y - 1 * s, x, y + 4 * s, INK, t=1)

for (tx, ty) in [(300, 520), (330, 555), (355, 505), (610, 460), (640, 500),
                 (600, 545), (660, 430), (340, 460), (370, 430), (560, 610),
                 (590, 640), (540, 660), (330, 620), (360, 650)]:
    tree(tx, ty, rng.choice([1, 1, 2]))

# ---------------------------------------------------------------- font (5x7)
FONT = {
 'A':["01110","10001","10001","11111","10001","10001","10001"],
 'B':["11110","10001","10001","11110","10001","10001","11110"],
 'C':["01110","10001","10000","10000","10000","10001","01110"],
 'D':["11110","10001","10001","10001","10001","10001","11110"],
 'E':["11111","10000","10000","11110","10000","10000","11111"],
 'F':["11111","10000","10000","11110","10000","10000","10000"],
 'G':["01110","10001","10000","10111","10001","10001","01110"],
 'H':["10001","10001","10001","11111","10001","10001","10001"],
 'I':["11111","00100","00100","00100","00100","00100","11111"],
 'J':["00111","00010","00010","00010","00010","10010","01100"],
 'K':["10001","10010","10100","11000","10100","10010","10001"],
 'L':["10000","10000","10000","10000","10000","10000","11111"],
 'M':["10001","11011","10101","10101","10001","10001","10001"],
 'N':["10001","11001","10101","10011","10001","10001","10001"],
 'O':["01110","10001","10001","10001","10001","10001","01110"],
 'P':["11110","10001","10001","11110","10000","10000","10000"],
 'Q':["01110","10001","10001","10001","10101","10011","01101"],
 'R':["11110","10001","10001","11110","10100","10010","10001"],
 'S':["01111","10000","10000","01110","00001","00001","11110"],
 'T':["11111","00100","00100","00100","00100","00100","00100"],
 'U':["10001","10001","10001","10001","10001","10001","01110"],
 'V':["10001","10001","10001","10001","10001","01010","00100"],
 'W':["10001","10001","10001","10101","10101","11011","10001"],
 'X':["10001","10001","01010","00100","01010","10001","10001"],
 'Y':["10001","10001","01010","00100","00100","00100","00100"],
 'Z':["11111","00001","00010","00100","01000","10000","11111"],
 ' ':["00000"]*7,
 "'":["00100","00100","00000","00000","00000","00000","00000"],
 ',':["00000","00000","00000","00000","00100","00100","01000"],
 '-':["00000","00000","00000","11111","00000","00000","00000"],
 '.':["00000","00000","00000","00000","00000","00110","00110"],
 '!':["00100","00100","00100","00100","00100","00000","00100"],
 '(':["00010","00100","01000","01000","01000","00100","00010"],
 ')':["01000","00100","00010","00010","00010","00100","01000"],
 '&':["01100","10010","01100","10101","10101","10010","01101"],
 '0':["01110","10001","10011","10101","11001","10001","01110"],
 '1':["00100","01100","00100","00100","00100","00100","01110"],
 '2':["01110","10001","00001","00110","01000","10000","11111"],
 '3':["11110","00001","00001","01110","00001","00001","11110"],
 '4':["00010","00110","01010","10010","11111","00010","00010"],
 '5':["11111","10000","11110","00001","00001","10001","01110"],
 '6':["01110","10000","11110","10001","10001","10001","01110"],
 '7':["11111","00001","00010","00100","01000","01000","01000"],
 '8':["01110","10001","10001","01110","10001","10001","01110"],
 '9':["01110","10001","10001","01111","00001","00001","01110"],
 ':':["00000","00100","00100","00000","00100","00100","00000"],
 '?':["01110","10001","00001","00110","00100","00000","00100"],
}

def text(s, x, y, c=INK, scale=2, spacing=1):
    cx = x
    for ch in s.upper():
        g = FONT.get(ch, FONT['?'])
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == '1':
                    for a in range(scale):
                        for b in range(scale):
                            px(cx + gx * scale + a, y + gy * scale + b, c)
        cx += (5 * scale + spacing * scale)
    return cx - x

def text_w(s, scale=2, spacing=1):
    return len(s) * (6 * scale) - scale

def banner(s, cy, scale=3, c=INK):
    w = text_w(s, scale)
    text(s, (W - w) // 2, cy, c, scale)

# ---------------------------------------------------------------- compass rose
RX, RY = 840, 210
circle(RX, RY, 52, INK, t=2)
circle(RX, RY, 44, INK, t=1)
for k in range(0, 360, 30):
    a = math.radians(k)
    line(RX + 44 * math.cos(a), RY + 44 * math.sin(a),
         RX + 52 * math.cos(a), RY + 52 * math.sin(a), INK, t=2)
for (dx, dy, ln) in [(0, -1, 70), (1, 0, 46), (0, 1, 46), (-1, 0, 46)]:
    fill_poly([(RX + dx * ln, RY + dy * ln),
               (RX + dy * 12 - dx * 12, RY - dx * 12 - dy * 12),
               (RX - dy * 12 - dx * 12, RY + dx * 12 - dy * 12)], INK)
text('N', RX - 6, RY - 96, INK, 2)

# ---------------------------------------------------------------- sea monsters
def serpent(x, y, flip=1):
    pts = [(x + i * 14, y + 12 * math.sin(i * 1.1) * flip) for i in range(8)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], INK, t=3)
    hx, hy = pts[-1]
    circle(int(hx), int(hy), 7, INK, fill=True)
    px(int(hx) + 3 * flip, int(hy) - 2, PARCH)
    for i in range(3):
        px(int(hx + 8 * flip), int(hy - 6 + i * 4), RED)

serpent(180, 860)
serpent(880, 700, -1)

# little ship
def ship(x, y):
    fill_poly([(x - 26, y), (x + 26, y), (x + 20, y + 10), (x - 20, y + 10)], (94, 66, 44))
    line(x, y, x, y - 34, INK, t=2)
    fill_poly([(x, y - 34), (x + 22, y - 14), (x, y - 14)], PARCH)
    line(x - 26, y, x + 26, y, INK, t=2)

ship(700, 900)
# waves
for (wx, wy) in [(140, 940), (240, 960), (420, 950), (560, 965), (760, 945),
                 (900, 930), (120, 760), (930, 560), (110, 420), (950, 340)]:
    for i in range(4):
        line(wx + i * 10, wy, wx + i * 10 + 8, wy - 4, INK_SOFT, t=1)

# ---------------------------------------------------------------- labels + route
LABELS = [
 ("PORT UNPROMISING", 300, 300),
 ("MOUNT REGRET & RICOCHET", 430, 430),
 ("THE SIGHING WOODS", 330, 640),
 ("CAPE SECOND THOUGHTS", 640, 640),
 ("BAY OF MILD PERIL", 640, 380),
 ("GROG LAGOON", 600, 730),
]
for s, x, y in LABELS:
    w = text_w(s, 2)
    text(s, min(max(x - w // 2, 8), W - w - 8), y, INK, 2)

# lagoon
circle(600, 680, 26, SEA, fill=True)
circle(600, 680, 26, SEA_D, t=2)

# treasure X and dashed route from port
TX_, TY_ = 690, 545
line(TX_ - 12, TY_ - 12, TX_ + 12, TY_ + 12, RED, t=4)
line(TX_ - 12, TY_ + 12, TX_ + 12, TY_ - 12, RED, t=4)
text("YE BURIED GOLD (PROBABLY)", TX_ - text_w("YE BURIED GOLD (PROBABLY)", 2) // 2, TY_ + 24, RED, 2)
circle(305, 350, 8, INK, t=2)  # port marker

route = [(312, 358), (360, 430), (430, 470), (500, 520), (560, 545), (TX_, TY_)]
for i in range(len(route) - 1):
    dashed(route[i][0], route[i][1], route[i + 1][0], route[i + 1][1], RED, t=1, dash=7, gap=5)

# dotted trail from woods to cape
dashed(340, 560, 700, 620, INK_SOFT, t=1, dash=5, gap=6)

# ---------------------------------------------------------------- title + border
banner("THE ISLE OF ALMOST-ARRR", 70, 4)
banner("A CHART FOR SAILORS OF QUESTIONABLE LUCK", 130, 2, INK_SOFT)
text("HERE BE DOODLES - NO REFUNDS", 30, 968, INK_SOFT, 2)
text("SERPENT'S SNACK BAR", 150, 905, INK, 2)
text("KRAKEN KARAOKE COVE", 755, 770, INK, 2)

for t_ in range(3):
    line(20 + t_, 20 + t_, W - 21 - t_, 20 + t_, INK, t=2)
    line(20 + t_, H - 21 - t_, W - 21 - t_, H - 21 - t_, INK, t=2)
    line(20 + t_, 20 + t_, 20 + t_, H - 21 - t_, INK, t=2)
    line(W - 21 - t_, 20 + t_, W - 21 - t_, H - 21 - t_, INK, t=2)

# corner flourish squiggles
for (fx, fy, sxx, syy) in [(40, 180, 1, 1), (W-60, 180, -1, 1), (40, H-180, 1, -1), (W-60, H-180, -1, -1)]:
    for i in range(24):
        a = i / 24 * 6.28
        px(fx + sxx * int(14 * math.sin(a * 2)), fy + syy * int(i * 4), INK_SOFT)

# ---------------------------------------------------------------- write PNG
os.makedirs(os.path.dirname(OUT), exist_ok=True)

def png_chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

raw = b"".join(b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3]) for y in range(H))
png = (b"\x89PNG\r\n\x1a\n"
       + png_chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
       + png_chunk(b"IDAT", zlib.compress(raw, 9))
       + png_chunk(b"IEND", b""))
with open(OUT, "wb") as f:
    f.write(png)
print("wrote", OUT, len(png), "bytes")
