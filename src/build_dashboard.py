"""
Build the interactive dashboard (docs/index.html) from dashboard_data.py + dashboard_template.html.
All filtering and the risk-cutoff simulator run in the browser, so it works on GitHub Pages.

    python src/build_dashboard.py
"""

import json
from pathlib import Path

from plotly.offline import get_plotlyjs_version

from dashboard_data import build

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "dashboard_template.html"


def main() -> None:
    (ROOT / "docs").mkdir(exist_ok=True)
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__PLOTLY_VERSION__", get_plotlyjs_version()).replace("__DATA__", json.dumps(build(), separators=(",", ":")))
    (ROOT / "docs" / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote docs/index.html ({len(html)/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
