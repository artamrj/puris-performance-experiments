#!/usr/bin/env python3
"""Terminal output with ANSI colours → SVG image of a terminal window (stdlib only).

Used for the screenshots in docs/img/ (see docs/img/README.md). Every text run is placed at its
column and stretched to its exact width (textLength), so boxes and bars stay aligned in any
monospace font. Only the SGR codes that `reproduce` prints are interpreted: 0, 1, 2, 22, 30–37, 39.

  python3 tools/ansi2svg.py in.ans out.svg --title "./reproduce status" [--cmd "./reproduce status"] [--cols 104]
"""
import argparse
import re
from xml.sax.saxutils import escape

FONT, CW, LH = 13, 7.8, 17          # font size, cell width, line height (px)
PAD, BAR = 16, 30                   # inner padding, title bar height
THEME = {"bg": "#0d1117", "frame": "#30363d", "bar": "#161b22", "fg": "#c9d1d9", "dim": "#8b949e",
         "title": "#8b949e", "prompt": "#3fb950"}
FG = {30: "#6e7681", 31: "#f85149", 32: "#3fb950", 33: "#d29922", 34: "#58a6ff", 35: "#bc8cff", 36: "#39c5cf", 37: "#c9d1d9"}
SGR = re.compile(r"\x1b\[([0-9;]*)m")
OTHER = re.compile(r"\x1b\[[0-9;?]*[A-Za-ln-z]|\x1b\][^\x07]*\x07")


def parse(line):
    """one line → [(column, text, style)] with style = (fg, bold, dim)"""
    out, col, st = [], 0, [None, False, False]
    line = OTHER.sub("", line)
    pos = 0
    for m in list(SGR.finditer(line)) + [None]:
        text = line[pos:m.start() if m else len(line)]
        # words with single spaces, and symbols on their own: each run starts at its exact column
        for r in re.finditer(r"[\x21-\x7e]+(?: [\x21-\x7e]+)*|[^\x00-\x7e]+", text):
            out.append((col + r.start(), r.group(), tuple(st)))
        col += len(text)
        if not m: break
        pos = m.end()
        for c in [int(x) if x else 0 for x in m.group(1).split(";")]:
            if c == 0: st = [None, False, False]
            elif c == 1: st[1] = True
            elif c == 2: st[2] = True
            elif c == 22: st[1] = st[2] = False
            elif 30 <= c <= 37: st[0] = c
            elif c == 39: st[0] = None
    return out, col


def render(text, title, cmd=None, cols=None):
    lines = text.rstrip("\n").split("\n")
    if cmd: lines = ["\x1b[32m$\x1b[0m " + cmd] + lines
    parsed = [parse(l) for l in lines]
    if cols:    # longer lines end with "…" at the window edge, like in a terminal of that width
        clip = lambda runs: [(c, t if c + len(t) <= cols else t[:max(0, cols - c - 1)] + "…", st) for c, t, st in runs if c < cols - 1]
        parsed = [(clip(r), min(w, cols)) for r, w in parsed]
    cols = cols or max([w for _, w in parsed] + [40])
    W = int(PAD * 2 + cols * CW); H = int(BAR + PAD * 2 + len(lines) * LH)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s" xml:space="preserve">'
         % (W, H, W, H, escape(title, {'"': "&quot;"})),
         "<title>%s</title>" % escape(title),
         "<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace;"
         "font-size:%dpx;white-space:pre}.b{font-weight:700}</style>" % FONT,
         '<rect x="0.5" y="0.5" width="%d" height="%d" rx="8" fill="%s" stroke="%s"/>' % (W - 1, H - 1, THEME["bg"], THEME["frame"]),
         '<path d="M0.5 %d V8.5 A8 8 0 0 1 8.5 0.5 H%.1f A8 8 0 0 1 %.1f 8.5 V%d Z" fill="%s"/>' % (BAR, W - 8.5, W - 0.5, BAR, THEME["bar"]),
         '<line x1="0.5" y1="%d.5" x2="%.1f" y2="%d.5" stroke="%s"/>' % (BAR, W - 0.5, BAR, THEME["frame"])]
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        o.append('<circle cx="%d" cy="%d" r="6" fill="%s"/>' % (18 + i * 20, BAR // 2, c))
    o.append('<text x="%d" y="%d" fill="%s" text-anchor="middle" style="font-size:12px">%s</text>' % (W // 2, BAR // 2 + 4, THEME["title"], escape(title)))
    for n, (runs, _) in enumerate(parsed):
        y = BAR + PAD + n * LH + FONT
        for col, run, (fg, bold, dim) in runs:
            colour = FG.get(fg, THEME["fg"]) if fg else (THEME["dim"] if dim else THEME["fg"])
            attrs = 'x="%.1f" y="%d" fill="%s" textLength="%.1f" lengthAdjust="spacingAndGlyphs"' % (PAD + col * CW, y, colour, len(run) * CW)
            if dim and fg: attrs += ' fill-opacity="0.65"'
            o.append('<text %s%s>%s</text>' % (attrs, ' class="b"' if bold else "", escape(run)))
    o.append("</svg>")
    return "\n".join(o) + "\n"


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("src"); a.add_argument("dst"); a.add_argument("--title", required=True)
    a.add_argument("--cmd"); a.add_argument("--cols", type=int)
    x = a.parse_args()
    open(x.dst, "w", encoding="utf-8").write(render(open(x.src, encoding="utf-8").read(), x.title, x.cmd, x.cols))
