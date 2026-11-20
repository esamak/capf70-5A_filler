# CAPF 70-5A Filler

A check-pilot tool for grading a CAP Pilot Flight Evaluation (Airplane) on a tablet or phone and stamping the results onto the official **CAPF 70-5A (8 JUN 20)** PDF.

## Use it

Open `docs/index.html` (or the GitHub Pages URL) in any modern browser (Safari on iPad works). It's one self-contained file: no install, no network, nothing leaves the device. AirDrop it, email it, or drop it in Files.

1. **Evaluation**: Annual/Abbreviated, date, member, CAP ID, aircraft, class, sortie time, and the endorsements being evaluated. Your initials print in the box for each endorsement you check.
2. **Tasks**: tap Q / QT / U / V / NP for each task. Only the grades the form allows appear (the form prints a dash in the others). Sections 3–10 open only for the endorsements you checked. ASES/AMEL-only tasks are dimmed unless the class matches. Grading a task QT or U opens a note box; notes can be added to Comments.
3. **Certification**: certificate review, qualifications to renew, CAP IDs, comments, and optional finger-drawn signatures (leave them blank to wet-sign).
4. **Review & PDF**: flags ungraded tasks, U grades, QT grades with no note, and comments that won't fit. Then it downloads `CAPF70-5A_<name>_<date>.pdf`.

The app autosaves a draft in the browser. **Save draft file** / **Open draft file** move an evaluation between devices.

## Layout

| Path | What |
|---|---|
| `form/CAPF_70-5A.pdf` | Blank official form (from gocivilairpatrol.com forms page) |
| `tools/extract_layout.py` | Reads the PDF's checkbox glyphs, then writes every task, its allowed grades, and the box coordinates to `web/layout.json` |
| `web/app.html` | App source |
| `vendor/pdf-lib.min.js` | pdf-lib 1.17.1 |
| `tools/build.py` | Inlines pdf-lib, the layout and the PDF into `docs/index.html` |

## Deploy (GitHub Pages)

In the repo's Settings → Pages, set Source to **Deploy from a branch**, branch `main`, folder `/docs`. After that, each update is: edit `web/app.html`, run `python3 tools/build.py`, commit, push.

## Rebuild

```bash
python3 -m venv .venv && .venv/bin/pip install pymupdf
.venv/bin/python tools/extract_layout.py form/CAPF_70-5A.pdf web/layout.json   # only if the form changes
python3 tools/build.py
```

If CAP issues a new edition of the form, replace `form/CAPF_70-5A.pdf`, re-run the extractor, and check its output. Header/certification field positions are hand-measured constants in `extract_layout.py` (`TEXT_FIELDS`, `SIGNATURES`, `ENDORSEMENTS`).
