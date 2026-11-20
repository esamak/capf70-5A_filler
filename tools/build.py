"""Bundle the app into one self-contained, offline HTML file.

Inlines pdf-lib, the task layout, and the official blank CAPF 70-5A so the
result can be emailed, AirDropped, or opened from Files on an iPad with no
network connection.

Usage:  python3 tools/build.py   ->  docs/index.html (served by GitHub Pages)
"""
import base64
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    html = (ROOT / "web/app.html").read_text()
    pdflib = (ROOT / "vendor/pdf-lib.min.js").read_text().replace("</script", "<\\/script")
    layout = (ROOT / "web/layout.json").read_text()
    pdf = base64.b64encode((ROOT / "form/CAPF_70-5A.pdf").read_bytes()).decode()

    for marker in ("/*__PDFLIB__*/", "/*__LAYOUT__*/null", "__PDF_B64__"):
        assert html.count(marker) == 1, marker
    html = html.replace("/*__PDFLIB__*/", pdflib)
    html = html.replace("/*__LAYOUT__*/null", layout)
    html = html.replace("__PDF_B64__", pdf)

    out = ROOT / "docs/index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
