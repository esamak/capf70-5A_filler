# CAPF 70-5A Filler

A check-pilot tool for grading a CAP Pilot Flight Evaluation (Airplane) on a tablet or phone and stamping the results onto the official **CAPF 70-5A (8 JUN 20)** PDF.

## Use it

Open `docs/index.html` (or the GitHub Pages URL) in any modern browser (including Safari on iPhone). It's one self-contained file: no install, no network, nothing leaves the device. AirDrop it, email it, or drop it in Files.

1. **Evaluation**: Annual/Abbreviated, date, member, CAP ID, aircraft, class, sortie time, and the endorsements being evaluated. Your initials print in the box for each endorsement you check.
2. **Tasks**: tap Q / QT / U / V / NP for each task. Only the grades the form allows appear (the form prints a dash in the others). Grading a task QT or U opens a note box; notes can be added to Comments.
   - **Required** tasks are the italicized ones on the form (CAPS 72-5, "Mandatory Items for Annual Evaluation"). On an annual they need a grade other than NP. On an abbreviated evaluation they're only flagged, because CAPR 70-1 ¶7.3 leaves the maneuvers to the check pilot.
   - Seaplanes substitute confined area (IV.G/H) for short field (IV.E/F); multi-engine substitutes IX.G for IX.B. Instrument Demo needs at least one flown approach, with circling at least verbal. Check Pilot also requires area XXII.
   - **IPC:** with an FAA IPC in the preceding six calendar months, Instrument Demo can be verbal (CAPR 70-1 ¶7.6.3). XV.A-D print NP (the form has no V for them), XV.G needs at least V, and a comment is added.
   - **Failures:** a U in Section 1 or 2, or the check pilot's switch on the Review tab, makes the ride unsatisfactory: the required-task block lifts, no initials, other endorsements or renewals print, and "UNSATISFACTORY" prints in the evaluator's signature block. A U in an endorsement's tasks drops only that endorsement's initials and lifts only its requirements. A U in XXII counts against both Instructor Pilot and Check Pilot (our reading; CAPS 72-5 doesn't say).
   - Tasks outside the aircraft class or checked endorsements are locked to NP. Any other task left ungraded prints NP, so every row on the form is marked.
3. **Certification**: always required: FAA cert, medical, flight review, the evaluated pilot's date and signature, and the evaluator's CAP ID. CFI expiration is required when Instructor Pilot, Check Pilot or G1000 IP is checked, pass or fail. The evaluator's signature is required unless the ride is unsatisfactory. When a checked endorsement fails, a checkbox by the signature lets the check pilot mark the whole ride unsatisfactory instead of signing (same setting as the one on Review). It's locked on when Section 1 or 2 has a U.
   - **Debrief:** every form section with a U needs a note on at least one of its U tasks (or general comments, if the ride is failed on judgment with no U). U notes always print, first in Comments.
4. **Review & PDF**: the PDF can't be made until every required item is graded, unless the ride has failed. Also flags U grades, QT grades with no note, tasks that will print NP, and comments that won't fit. Then it downloads `CAPF70-5A_<name>_<date>.pdf`.

   - **Mishap question:** before any failed ride (whole ride or any endorsement) downloads, the check pilot is asked whether the failure was associated with aircraft damage or another occurrence needing a mishap report and CAPSIS entry. Yes: a message asks them to report it through the proper channels, then the PDF downloads. No: it downloads. The answer is never saved or printed.

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
