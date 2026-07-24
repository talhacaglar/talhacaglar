#!/usr/bin/env python3
"""Typing-animasyonlu banner GIF ureticisi.
Arka plan koyu kahve (#4D2C12), yazi acik mavi (#9CC9E8).
Her satir karakter karakter yazilir, yanip sonen imlec eslik eder.
Cikti: assets/banner.gif
"""
import os
import subprocess
import shutil
import html

# --- Ayarlar ---
W, H = 900, 260
BG = "#4D2C12"          # koyu kahve arka plan
FG = "#9CC9E8"          # acik mavi yazi
DIM = "#B48A6A"         # sonmus/ipucu tonu (arka plandan bir tik acik)
FONT = "JetBrainsMono Nerd Font"   # kalin monospace
FONT_WEIGHT = "ExtraBold"

LINES = [
    ("Hi, I'm Talha Caglar", 40, 78),
    ("Cybersecurity * Linux & Automation", 26, 138),
    ("Python  JavaScript  Java  Bash  F#  CSS", 24, 196),
]
# gorsel dogruluk icin ozel karakterler
LINES = [
    ("Hi, I'm Talha \u00c7a\u011flar", 40, 78),
    ("Cybersecurity \u00b7 Linux & Automation", 26, 138),
    ("Python \u00b7 JavaScript \u00b7 Java \u00b7 Bash \u00b7 F# \u00b7 CSS", 24, 196),
]

CURSOR = "\u2588"       # dolu blok imlec
LEFT = 60               # sol kenar bosluk
FRAME_DIR = "/tmp/banner_frames"
OUT = "assets/banner.gif"


def esc(s):
    return html.escape(s, quote=True)


def svg_frame(states, cursor_line, cursor_on):
    """states: her satir icin (tam_metin, gorunen_karakter_sayisi, size, y)."""
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" rx="18" fill="{BG}"/>',
        # ince ust vurgu cizgisi
        f'<rect x="0" y="0" width="{W}" height="4" fill="{FG}" fill-opacity="0.35"/>',
    ]
    for idx, (text, n, size, y) in enumerate(states):
        shown = text[:n]
        style = (
            f'font-family="{FONT}" font-weight="{FONT_WEIGHT}" '
            f'font-size="{size}" fill="{FG}"'
        )
        line = f'<text x="{LEFT}" y="{y}" {style}>{esc(shown)}</text>'
        parts.append(line)
        # imlec: sadece o an yazilan satirin sonunda, yanip sonerek
        if idx == cursor_line and cursor_on:
            # imleci gorunen metnin sonuna yaklasik yerlestir (monospace)
            cx = LEFT + int(len(shown) * size * 0.60) + 6
            parts.append(
                f'<text x="{cx}" y="{y}" {style}>{CURSOR}</text>'
            )
    parts.append('</svg>')
    return "\n".join(parts)


def render(svg, png_path):
    subprocess.run(
        ["rsvg-convert", "-o", png_path, "-w", str(W), "-h", str(H)],
        input=svg.encode(), check=True,
    )


def main():
    if os.path.isdir(FRAME_DIR):
        shutil.rmtree(FRAME_DIR)
    os.makedirs(FRAME_DIR)

    frames = []            # (png_path, delay_centisec)
    fi = 0

    def add(svg, delay):
        nonlocal fi
        p = os.path.join(FRAME_DIR, f"f{fi:04d}.png")
        render(svg, p)
        frames.append((p, delay))
        fi += 1

    # baslangic: tum satirlar bos
    counts = [0, 0, 0]

    # her satiri sirayla yaz
    for li, (text, size, y) in enumerate(LINES):
        for c in range(1, len(text) + 1):
            counts[li] = c
            states = [(LINES[k][0], counts[k], LINES[k][1], LINES[k][2])
                      for k in range(len(LINES))]
            # imlec yaziliyorken surekli acik
            svg = svg_frame(states, li, True)
            add(svg, 4)     # 40ms/karakter -> akici typing
        # satir bitince kisa bekleme + imlec yanip sonme
        for blink in range(2):
            states = [(LINES[k][0], counts[k], LINES[k][1], LINES[k][2])
                      for k in range(len(LINES))]
            add(svg_frame(states, li, blink % 2 == 0), 22)

    # final: tam metin, imlec son satirda yanip sonuyor (uzun tutus)
    states = [(LINES[k][0], len(LINES[k][0]), LINES[k][1], LINES[k][2])
              for k in range(len(LINES))]
    for blink in range(6):
        add(svg_frame(states, len(LINES) - 1, blink % 2 == 0), 45)

    # GIF birlestir
    cmd = ["magick", "-loop", "0"]
    for p, d in frames:
        cmd += ["-delay", str(d), p]
    cmd += ["-layers", "optimize", OUT]
    subprocess.run(cmd, check=True)
    print(f"OK: {OUT}  ({len(frames)} frame)")


if __name__ == "__main__":
    main()
