"""Render the profile's work and record cards from live GitHub data.

Everything is emitted as self-contained SVG committed into assets/, so the
profile never depends on a third-party card service being up.
"""

import json
import os
import urllib.request

USER = "talhacaglar"
FEATURED = ["Lexis", "printhub", "Clar-Corp-Security-Lab", "Clar-Focus"]

BLURBS = {
    "Lexis": "AI-supported, personalized dictionary application.",
    "printhub": "Printer fleet management: toner cost, stock,\nActive Directory, ISO 27001.",
    "Clar-Corp-Security-Lab": "Security experiments, notes, and\nlab-style development.",
    "Clar-Focus": "Terminal-native productivity tooling\nfor Linux.",
}

BLUE = "#A6AFCC"
BLUE_SOFT = "#7C859E"
BROWN = "#B08D6A"
INK = "#EAEBF0"
MUTED = "#9A9EB0"
FAINT = "#5E6270"
CARD = "#14151A"
LINE = "#2A2C33"

# Apple San Francisco first, graceful fallback everywhere else.
SF = "'SF Pro Display','SF Pro Text',-apple-system,BlinkMacSystemFont,ui-sans-serif,'Helvetica Neue',Arial,sans-serif"
SF_TEXT = "'SF Pro Text',-apple-system,BlinkMacSystemFont,ui-sans-serif,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"

LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#F1E05A",
    "Java": "#B07219",
    "Dart": "#00B4AB",
    "Shell": "#89E051",
    "CSS": "#563D7C",
    "HTML": "#E34C26",
    "C": "#555555",
    "C++": "#F34B7D",
    "ShaderLab": "#222C37",
    "F#": "#B845FC",
    "TypeScript": "#3178C6",
}


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-card-renderer",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def esc(s):
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def fetch():
    user = api(f"/users/{USER}")
    repos = []
    page = 1
    while True:
        chunk = api(f"/users/{USER}/repos?per_page=100&page={page}")
        repos.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1

    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in own)

    # Weight each repository equally: raw byte totals let a single repo full of
    # generated or vendored files dominate the whole mix.
    lang_bytes = {}
    for r in own:
        try:
            langs = api(f"/repos/{USER}/{r['name']}/languages")
        except Exception:
            continue
        total = sum(langs.values())
        if not total:
            continue
        for lang, size in langs.items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + (size / total) / len(own)

    by_name = {r["name"]: r for r in repos}
    return user, own, stars, lang_bytes, by_name


def work_card(by_name):
    """2x2 grid of framed project cards."""
    W, H = 900, 320
    cw, ch = 424, 140
    gap_x, gap_y = 452, 168
    out = []
    for i, name in enumerate(FEATURED):
        repo = by_name.get(name, {})
        x = 8 + (i % 2) * gap_x
        y = 6 + (i // 2) * gap_y
        stars = repo.get("stargazers_count", 0)
        lang = repo.get("language") or "—"
        dot = LANG_COLORS.get(lang, BROWN)
        blurb = BLURBS.get(name, "")

        lines = "".join(
            f'<tspan x="{x + 22}" dy="{18 if j else 0}">{esc(line)}</tspan>'
            for j, line in enumerate(blurb.split("\n"))
        )

        out.append(f'''  <g>
    <rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="4" fill="{CARD}" stroke="{LINE}"/>
    <rect x="{x}" y="{y}" width="3" height="{ch}" rx="1.5" fill="{BROWN}" fill-opacity="0.7"/>
    <text x="{x + 22}" y="{y + 38}" font-family="{SF}" font-weight="700" font-size="19" letter-spacing="0.4" fill="{BLUE}">{esc(name)}</text>
    <text x="{x + 22}" y="{y + 68}" font-family="{SF_TEXT}" font-weight="500" font-size="13" fill="{MUTED}">{lines}</text>
    <circle cx="{x + 25}" cy="{y + ch - 22}" r="4.5" fill="{dot}"/>
    <text x="{x + 37}" y="{y + ch - 18}" font-family="{SF_TEXT}" font-weight="500" font-size="12" fill="{FAINT}">{esc(lang)}</text>
    <text x="{x + cw - 22}" y="{y + ch - 18}" text-anchor="end" font-family="{MONO}" font-weight="500" font-size="12" fill="{FAINT}">&#9733; {stars}</text>
  </g>''')

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Selected work">
{chr(10).join(out)}
</svg>
'''


def record_card(user, own, stars, lang_bytes):
    W, H = 900, 250
    total = sum(lang_bytes.values()) or 1
    top = sorted(lang_bytes.items(), key=lambda kv: -kv[1])[:6]

    stats = [
        ("REPOSITORIES", str(len(own))),
        ("STARS EARNED", str(stars)),
        ("FOLLOWERS", str(user["followers"])),
        ("LANGUAGES", str(len(lang_bytes))),
    ]

    out = []
    for i, (label, value) in enumerate(stats):
        x = 60 + i * 200
        out.append(f'''  <g text-anchor="middle">
    <text x="{x}" y="{74}" font-family="{SF}" font-weight="700" font-size="34" fill="{INK}">{value}</text>
    <text x="{x}" y="{98}" font-family="{SF_TEXT}" font-weight="600" font-size="10" letter-spacing="2.4" fill="{FAINT}">{label}</text>
  </g>''')
        if i < len(stats) - 1:
            out.append(
                f'  <rect x="{x + 100}" y="46" width="1" height="60" fill="{LINE}"/>'
            )

    # stacked language bar
    bx, bw = 60, 780
    cursor = bx
    bar, legend = [], []
    shown = sum(v for _, v in top)
    for i, (lang, size) in enumerate(top):
        frac = size / shown
        seg = bw * frac
        color = LANG_COLORS.get(lang, BROWN)
        r_left = "4" if i == 0 else "0"
        bar.append(
            f'  <rect x="{cursor:.1f}" y="146" width="{seg:.1f}" height="9" fill="{color}"/>'
        )
        cursor += seg

        lx = 60 + (i % 3) * 270
        ly = 190 + (i // 3) * 26
        pct = 100 * size / total
        legend.append(f'''  <g>
    <circle cx="{lx}" cy="{ly - 4}" r="4.5" fill="{color}"/>
    <text x="{lx + 13}" y="{ly}" font-family="{SF_TEXT}" font-weight="500" font-size="12.5" fill="{MUTED}">{esc(lang)}</text>
    <text x="{lx + 240}" y="{ly}" text-anchor="end" font-family="{MONO}" font-weight="500" font-size="12" fill="{FAINT}">{pct:.1f}%</text>
  </g>''')

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub record">
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="4" fill="{CARD}" stroke="{LINE}"/>
  <rect x="0" y="0" width="{W}" height="2" rx="1" fill="{BROWN}" fill-opacity="0.6"/>
{chr(10).join(out)}
  <text x="{bx}" y="136" font-family="{SF_TEXT}" font-weight="600" font-size="10" letter-spacing="2.4" fill="{FAINT}">LANGUAGE MIX &#183; WEIGHTED BY REPOSITORY</text>
  <rect x="{bx}" y="146" width="{bw}" height="9" rx="4" fill="#16161A"/>
{chr(10).join(bar)}
{chr(10).join(legend)}
</svg>
'''


def main():
    user, own, stars, lang_bytes, by_name = fetch()
    root = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
    with open(os.path.join(root, "work.svg"), "w") as f:
        f.write(work_card(by_name))
    with open(os.path.join(root, "record.svg"), "w") as f:
        f.write(record_card(user, own, stars, lang_bytes))
    print(f"repos={len(own)} stars={stars} langs={len(lang_bytes)}")


if __name__ == "__main__":
    main()
