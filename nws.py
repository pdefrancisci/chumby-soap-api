"""Generate static/test.jpg: 320x240, baseline (non-progressive) JPEG."""
import os
import time
import requests
import cairosvg
import io
import re
import urllib.request
from datetime import datetime, timezone
from PIL import Image, ImageDraw

W, H = 320, 240
b=5
chumby_color = (137,207,240)
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(out_dir, exist_ok=True)

BASE = "https://radar.weather.gov/ridge/standard/"
SUFFIX = "_0.gif"
CACHE_SECS = 300
_jpeg_cache = {}      # team -> (timestamp, jpeg bytes)

def render(station):
    img = Image.new("RGB", (W, H))
    px = img.load()
    d = ImageDraw.Draw(img)
    resp = requests.get(f"{BASE}{station}{SUFFIX}", timeout=10)
    resp.raise_for_status()
    url = f"{BASE}{station}{SUFFIX}"
    print("PATRICK request at: "+url)

    img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    urllib.request.urlretrieve(url, "radar.png")
    bg = Image.new("RGBA", img.size, (0, 0, 0, 255))

    img = Image.alpha_composite(bg, img).convert("RGB")
    (left, upper, right, lower) = (0, H/8, W*2, H/8+(H*2))
    img = img.crop((left, upper, right, lower)).resize((W,H))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85, progressive=False, optimize=False)
    return buf.getvalue()

def get_nws_jpeg(station):
    """Return JPEG bytes for a station's next game. Raises ValueError on a bad station code."""
    station = station.upper()
    if not re.fullmatch(r"[A-Z]{4}", station):
        raise ValueError("bad station code")

    now = time.time()
    cached = _jpeg_cache.get(station)
    print("PATRICK staysh: "+station)
    if cached and now - cached[0] < CACHE_SECS:
        print("PATRICK loaded cache")
        return cached[1]

    try:
        data = render(station)
    except Exception:
        if cached:            # NHL API down? serve the last good image
            return cached[1]
        raise
    _jpeg_cache[station] = (now, data)
    return data