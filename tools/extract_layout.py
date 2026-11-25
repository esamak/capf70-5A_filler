"""Extract the task grid from the official CAPF 70-5A PDF into web/layout.json.

The form has no AcroForm fields: every grade box is a SymbolMT glyph ("\x00")
and every disallowed grade is a SymbolMT minus sign. This script finds those
glyphs, groups them into task rows, pairs each row with its task label, and
records coordinates in PDF user space (origin bottom-left of the MediaBox) so
the browser can stamp marks with pdf-lib.

Usage:  .venv/bin/python tools/extract_layout.py form/CAPF_70-5A.pdf web/layout.json
"""
import json
import re
import sys
from collections import defaultdict

import pymupdf

GRADES = ["Q", "QT", "U", "V", "NP"]
MID_X = 310  # left / right column split on pages 1-2
ROMAN = re.compile(r"^(X{0,3}(?:IX|IV|V?I{0,3}))\.\s+(.*)$")
TASK = re.compile(r"^([A-Z])\.\s+(.*)$")


def to_pdf(page, x, y):
    """PyMuPDF page coords (top-left origin) -> PDF user space."""
    p = pymupdf.Point(x, y) * ~page.transformation_matrix
    return round(p.x, 2), round(p.y, 2)


def lines_of(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            spans = [s for s in l["spans"] if s["font"] != "SymbolMT"]
            text = "".join(s["text"] for s in spans).strip()
            if not text:
                continue
            out.append({
                "bbox": l["bbox"],
                "text": re.sub(r"\s+", " ", text),
                "italic": any("Italic" in s["font"] and s["text"].strip() for s in spans),
                "bold": any("Bold" in s["font"] and s["text"].strip() for s in spans),
            })
    return out


def marks_of(page):
    rows = defaultdict(list)
    for b in page.get_text("rawdict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if s["font"] != "SymbolMT":
                    continue
                for c in s["chars"]:
                    if c["c"] in ("\x00", "−"):
                        x0, y0, x1, y1 = c["bbox"]
                        rows[(round(y0, 1), x0 > MID_X)].append((x0, y0, x1, y1, c["c"] == "\x00"))
    return rows


# Free-text fields, measured from the printed cell borders (PyMuPDF coords:
# x, text baseline y, max width). Converted to PDF space in main().
TEXT_FIELDS = {
    0: {
        "date":              (447, 64.5, 139),
        "memberName":        (90, 83.5, 350),
        "capId":             (474, 83.5, 112),
        "aircraft":          (447, 107.5, 139),
        "airplaneClass":     (447, 131.5, 139),
        "sortieTime":        (447, 155.5, 139),
        "otherEndorsements": (105, 155.5, 336),
    },
    2: {
        "pilotSignDate":     (45, 129.5, 46),
        "faaCert":           (22, 168.5, 288),
        "medical":           (318, 168.5, 268),
        "flightReview":      (22, 192.5, 288),
        "cfiExp":            (318, 192.5, 268),
        "qualsToRenew":      (148, 284.5, 438),
        "qualsToRenew2":     (22, 297.5, 564),
        "evalCapId":         (62, 316.5, 62),
        "extCapId":          (62, 379.5, 62),
    },
}
# Signature boxes: (x0, y0, x1, y1) in PyMuPDF coords.
SIGNATURES = {
    "pilotSignature": (2, (322, 107, 495, 131.5)),
    "evalSignature":  (2, (400, 296, 544, 318.5)),
    "extSignature":   (2, (360, 359, 505, 381.5)),
}
COMMENTS = (2, (22, 400, 586, 694))
# Ops Quals endorsement initial boxes: centre x, centre y.
ENDORSEMENTS = [
    ("instrumentDemo", "Instrument Demo", 35.6, 103.7),
    ("highPerfDemo", "High Performance Demo", 35.6, 115.7),
    ("complexDemo", "Complex Demo", 35.6, 127.7),
    ("turbo", "Turbo Aircraft", 35.6, 139.7),
    ("g1000Vfr", "G1000 VFR", 218.7, 103.7),
    ("g1000Ifr", "G1000 IFR", 218.7, 115.7),
    ("g1000Ip", "G1000 IP", 218.7, 127.7),
    ("mountain", "Mountain Flight", 218.7, 139.7),
    ("orientation", "Orientation Pilot", 330.1, 103.7),
    ("instructor", "Instructor Pilot", 330.1, 115.7),
    ("checkPilot", "Check Pilot", 330.1, 127.7),
]


def main(src, dst):
    doc = pymupdf.open(src)
    tasks = []
    for pno in (0, 1):
        page = doc[pno]
        lines = lines_of(page)
        for (y, right), marks in sorted(marks_of(page).items()):
            if pno == 0 and y < 60:
                continue  # Annual / Abbreviated boxes, handled separately
            marks.sort()
            assert len(marks) == 5, (pno, y, right, marks)
            ymid = y + 5.6
            label = None
            for ln in lines:
                bx0, by0, bx1, by1 = ln["bbox"]
                if (bx0 > MID_X) == right and by0 - 1 <= ymid <= by1 + 1 and TASK.match(ln["text"]):
                    label = ln
                    break
            assert label, (pno, y, right)
            letter, name = TASK.match(label["text"]).groups()
            boxes = {}
            allowed = []
            for g, (x0, y0, x1, y1, is_box) in zip(GRADES, marks):
                # The visible square is the centre of the glyph cell.
                cx, cy = to_pdf(page, (x0 + x1) / 2, y0 + (y1 - y0) * 0.56)
                boxes[g] = [cx, cy]
                if is_box:
                    allowed.append(g)
            tasks.append({
                "page": pno, "y": y, "right": right, "letter": letter, "name": name,
                # CAPS 72-5: tasks that must be performed and graded are in italics.
                "required": label["italic"],
                "allowed": allowed, "boxes": boxes,
            })

    # Each area starts on a band carrying a "Q QT U V NP" column header. The
    # band's title is in the same column, or - for continuation bands such as
    # V.B and XIII.F-I - in the opposite column on the same band.
    bands = []
    for pno in (0, 1):
        lns = lines_of(doc[pno])
        heads = [ln for ln in lns if "Q QT U V NP" in ln["text"]]
        sections = [ln for ln in lns if ln["text"].startswith("Section")]
        for h in heads:
            right = h["bbox"][0] > MID_X + 150 or (h["bbox"][0] > MID_X and h["bbox"][0] < 330)
            hy = (h["bbox"][1] + h["bbox"][3]) / 2
            titles = [ln for ln in lns if ln["bbox"][1] - 2 <= hy <= ln["bbox"][3] + 2
                      and (ln["bbox"][0] < 30 or 314 < ln["bbox"][0] < 322)]
            def side(ln):
                return ln["bbox"][0] > MID_X
            mine = [ln for ln in titles if side(ln) == right]
            title = (mine or titles)[0]
            m = ROMAN.match(re.sub(r"\s*Q QT U V NP.*$", "", title["text"]).strip())
            sec = max((sc for sc in sections if sc["bbox"][1] < hy), key=lambda sc: sc["bbox"][1], default=None)
            bands.append({"page": pno, "y": hy, "right": right, "roman": m.group(1), "name": m.group(2).strip(),
                          "section": sec["text"] if sec else bands[-1]["section"]})

    ases = {}
    for pno in (0, 1):
        for ln in lines_of(doc[pno]):
            for tag in ("ASES", "AMEL"):
                if f"({tag} only)" in ln["text"]:
                    ases[(pno, round((ln["bbox"][1] + ln["bbox"][3]) / 2), ln["bbox"][0] > MID_X)] = tag

    out = []
    for t in tasks:
        cy = t["y"] + 5.6
        b = max((b for b in bands if b["page"] == t["page"] and b["right"] == t["right"] and b["y"] < cy),
                key=lambda b: b["y"])
        t["area"] = f'{b["roman"]}. {b["name"]}'
        t["roman"] = b["roman"]
        t["section"] = b["section"]
        t["id"] = f'{b["roman"]}.{t["letter"]}'
        t["only"] = None
        for (pno, y, right), tag in ases.items():
            if pno == t["page"] and right == t["right"] and abs(y - cy) < 4:
                t["only"] = tag
        if "(AMEL only)" in t["area"]:
            t["only"] = "AMEL"
        t["name"] = re.sub(r"\s*\((ASES|AMEL) only\)", "", t["name"]).strip()
        out.append(t)

    # Labels that wrap onto a second printed line.
    fixups = {
        "XXII.D": "Demonstrate an instructional scenario for the briefed maneuver",
        "XXIII.C": "Evaluate the left seat check pilot flying one inflight maneuver and one landing",
        "XV.G": "Circling Approach (verbal at a minimum)",
    }
    for t in out:
        t["name"] = fixups.get(t["id"], t["name"])

    order = {r: i for i, r in enumerate(
        "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX XXI XXII XXIII XXIV".split())}
    out.sort(key=lambda t: (order[t["roman"]], t["letter"]))
    for t in out:
        for k in ("y", "right", "roman"):
            t.pop(k)

    page0 = doc[0]
    annual = {}
    for (y, right), marks in marks_of(page0).items():
        if y < 60:
            for (x0, y0, x1, y1, _), key in zip(sorted(marks), ("annual", "abbreviated")):
                annual[key] = list(to_pdf(page0, (x0 + x1) / 2, y0 + (y1 - y0) * 0.56))

    layout = {
        "source": "CAPF 70-5A, 8 JUN 20",
        "grades": GRADES,
        "checktype": annual,
        "tasks": out,
        "text": {k: {"page": pno, "x": to_pdf(doc[pno], x, y)[0], "y": to_pdf(doc[pno], x, y)[1], "w": w}
                 for pno, fs in TEXT_FIELDS.items() for k, (x, y, w) in fs.items()},
        "signatures": {k: {"page": pno, "x0": to_pdf(doc[pno], r[0], r[3])[0], "y0": to_pdf(doc[pno], r[0], r[3])[1],
                           "x1": to_pdf(doc[pno], r[2], r[1])[0], "y1": to_pdf(doc[pno], r[2], r[1])[1]}
                       for k, (pno, r) in SIGNATURES.items()},
        "comments": {"page": COMMENTS[0],
                     "x0": to_pdf(doc[COMMENTS[0]], COMMENTS[1][0], COMMENTS[1][3])[0],
                     "y0": to_pdf(doc[COMMENTS[0]], COMMENTS[1][0], COMMENTS[1][3])[1],
                     "x1": to_pdf(doc[COMMENTS[0]], COMMENTS[1][2], COMMENTS[1][1])[0],
                     "y1": to_pdf(doc[COMMENTS[0]], COMMENTS[1][2], COMMENTS[1][1])[1]},
        "endorsements": [{"key": k, "label": lbl, "page": 0, "x": to_pdf(doc[0], x, y)[0], "y": to_pdf(doc[0], x, y)[1]}
                         for k, lbl, x, y in ENDORSEMENTS],
    }
    with open(dst, "w") as f:
        json.dump(layout, f, indent=1)
    print(f"{len(out)} tasks -> {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
