#!/usr/bin/env python3
"""Ring / mobile parity guard for theacademiagroup.com index.html.

The capability ring (SVG, desktop) and the .mrow list (mobile sheet) are two
independent hand-maintained renderings of the SAME ten divisions. They have
drifted twice: Pools appeared in one and not the other, then Permitting did,
and Restoration advertised POOLS on a link pointing at /restoration/.

Nothing enforced agreement, so this does. Exit 1 on any divergence.

Run:  python3 check-parity.py [path-to-index.html]

Parse note, learned the hard way: parse each <a> block INDIVIDUALLY. A regex
with .*? spanning blocks silently mismaps sub-labels between neighbouring nodes
and reports a confident wrong answer (real-estate carrying Recertification's
sub-label). Compare slugs to slugs, never labels to slugs.
"""
import re, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "index.html"
NODE = re.compile(r'<a href="https://academiadevelopment\.com/([a-z\-]+)/"><title>.*?</a>', re.S)
SUB  = re.compile(r'class="mono dim" font-size="9"[^>]*>([^<]*)</text>')
ROW  = re.compile(r'<a class="mrow" href="https://academiadevelopment\.com/([a-z\-]+)/">'
                  r'<b>([^<]*)</b><span>([^<]*)</span>')


def parse(html):
    ring = {}
    for m in NODE.finditer(html):
        block = m.group(0)
        if 'class="dia"' not in block:       # only capability-ring nodes carry a diamond
            continue
        sub = SUB.search(block)
        if sub:
            ring[m.group(1)] = sub.group(1).strip()
    rows = {slug: span.strip() for slug, _label, span in ROW.findall(html)}
    return ring, rows


def main():
    ring, rows = parse(open(SRC, encoding="utf-8").read())
    problems = []

    for slug in sorted(set(ring) - set(rows)):
        problems.append(f"in ring, MISSING from mobile: /{slug}/")
    for slug in sorted(set(rows) - set(ring)):
        problems.append(f"in mobile, MISSING from ring: /{slug}/")
    for slug in sorted(set(ring) & set(rows)):
        if ring[slug].upper() != rows[slug].upper():
            problems.append(f"sub-label differs on /{slug}/:\n"
                            f"      ring:   {ring[slug]}\n"
                            f"      mobile: {rows[slug]}")

    # A sub-label must not advertise a division that owns its own node — that is
    # how "CONCRETE · FAÇADE · POOLS" ended up pointing pool traffic at /restoration/.
    for slug, sub in ring.items():
        for other in ring:
            if other == slug:
                continue
            word = other.split("-")[0].upper()
            # WORD BOUNDARIES, not substring. The first version of this check used
            # `word in sub` and immediately fired on WATERPROOFING, because it
            # contains ROOFING. A guard written to prevent sloppy matching must not
            # itself match sloppily.
            if len(word) > 4 and re.search(rf"\b{re.escape(word)}\b", sub.upper()):
                problems.append(f"/{slug}/ sub-label advertises {word}, which has its "
                                f"own node at /{other}/ — it will send that traffic to "
                                f"the wrong page:\n      {sub}")

    print(f"ring nodes: {len(ring)}   mobile rows: {len(rows)}")
    if problems:
        print(f"\nFAIL — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("OK — ring and mobile agree on every slug and every sub-label.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
