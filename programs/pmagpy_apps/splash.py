"""
The splash screen: what the window shows while Python, the libraries and the
server come up behind it.

It is one self-contained HTML page — the magpie embedded as a data URI, the
styles inline — so the window can show it before anything else has loaded, and
a ``setStatus`` function the host calls as each stage passes ("Loading PmagPy
…", "Starting the local server …"). The colours are the family's: the header
blue of the hub and the teal of PmagPy Directions.
"""
from __future__ import annotations

import base64
import html
import os

from pmagpy_panel import FAMILY_COLOR, app_color

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
MAGPIE = os.path.join(ASSETS, "pmagpy_logo_white.png")          # the white magpie, on nothing


def _data_uri(path: str) -> str:
    with open(path, "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode("ascii")


def splash_html(title: str, subtitle: str = "", status: str = "Starting …", version: str = "",
                accent: str = "") -> str:
    """The page.

    Args:
        title: the product's name, large ("PmagPy Directions").
        subtitle: one line under it, what this edition is for.
        status: the first status line; :func:`status_js` changes it later.
        version: shown small in a corner (the pmagpy version).
        accent: the colour of the progress bar and the glow; PmagPy Directions'
            teal by default.
    """
    accent = accent or app_color("pmagpy_directions")
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
  html, body {{ height: 100%; margin: 0; }}
  body {{ display: flex; align-items: center; justify-content: center; overflow: hidden;
          font-family: "Inter", "Helvetica Neue", Helvetica, Arial, sans-serif; color: #fff;
          background: radial-gradient(ellipse at 30% 20%, {accent} 0%, {FAMILY_COLOR} 48%, #0b1f3f 100%); }}
  .card {{ text-align: center; width: min(560px, 80vw); animation: rise .7s ease-out both; }}
  .bird {{ width: min(360px, 60vw); height: auto; display: block; margin: 0 auto 10px;
           filter: drop-shadow(0 12px 30px rgba(0,0,0,.35)); animation: float 3.2s ease-in-out infinite; }}
  h1 {{ font-size: clamp(30px, 4.6vw, 44px); font-weight: 650; letter-spacing: -.01em; margin: 0 0 6px; }}
  .sub {{ font-size: 15px; opacity: .85; margin: 0 0 30px; line-height: 1.45; }}
  .bar {{ position: relative; height: 4px; width: 62%; margin: 0 auto 14px; border-radius: 2px;
          background: rgba(255,255,255,.22); overflow: hidden; }}
  .bar::after {{ content: ""; position: absolute; top: 0; left: -40%; width: 40%; height: 100%; border-radius: 2px;
                 background: #fff; animation: sweep 1.6s ease-in-out infinite; }}
  .status {{ font-size: 13.5px; opacity: .9; min-height: 1.4em; font-variant-numeric: tabular-nums; }}
  .version {{ position: fixed; right: 16px; bottom: 12px; font-size: 11.5px; opacity: .55; }}
  .family {{ position: fixed; left: 16px; bottom: 12px; font-size: 11.5px; opacity: .55; }}
  @keyframes sweep {{ 0% {{ left: -40%; }} 60% {{ left: 100%; }} 100% {{ left: 100%; }} }}
  @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-7px); }} }}
  @keyframes rise {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
</style></head>
<body>
  <div class="card">
    <img class="bird" alt="" src="{_data_uri(MAGPIE)}">
    <h1>{html.escape(title)}</h1>
    <p class="sub">{html.escape(subtitle)}</p>
    <div class="bar"></div>
    <div class="status" id="status">{html.escape(status)}</div>
  </div>
  <div class="family">PmagPy Apps</div>
  <div class="version">{html.escape(version)}</div>
  <script>
    function setStatus(text) {{ var el = document.getElementById('status'); if (el) el.textContent = text; }}
  </script>
</body></html>"""


def status_js(text: str) -> str:
    """The JavaScript that puts `text` on the splash's status line."""
    import json
    return f"setStatus({json.dumps(text)})"
