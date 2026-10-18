"""Generate static/test.jpg: 320x240, baseline (non-progressive) JPEG."""
import os
import time
import requests
import cairosvg
import io
import re
from datetime import datetime, timezone
from PIL import Image, ImageDraw

W, H = 320, 240
away_spot = 160
home_spot = 20
b = 10
chumby_color = (137,207,240)
logo_size = 130
offset = 10
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(out_dir, exist_ok=True)

BASE = "https://api-web.nhle.com/v1"
# TEAM = "NYR"
CACHE_SECS = 300

_jpeg_cache = {}      # team -> (timestamp, jpeg bytes)
_logo_cache = {}      # logo url -> RGBA image, kept for the life of the worker

def next_game(team):
    data = requests.get(f"{BASE}/club-schedule-season/{team}/now", timeout=10).json()
    now = datetime.now(timezone.utc)
    for g in data["games"]:
        start = datetime.fromisoformat(g["startTimeUTC"].replace("Z", "+00:00"))
        if start > now:
            return g
    return None

def records():
    data = requests.get(f"{BASE}/standings/now", timeout=10).json()
    return {
        t["teamAbbrev"]["default"]: f'{t["wins"]}-{t["losses"]}-{t["otLosses"]}'
        for t in data["standings"]
    }

def paste_logo(img, team, isHome):
    resp = requests.get(team["logo"])
    resp.raise_for_status()
    png_bytes = cairosvg.svg2png(bytestring=resp.content)
    logo = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    logo = logo.resize((logo_size,logo_size))
    if isHome:
        img.paste(logo,(home_spot+offset, (H-logo.height)//2), logo)
    else:
        img.paste(logo,(away_spot+offset, (H-logo.height)//2), logo)

def render(team):
    img = Image.new("RGB", (W, H))
    px = img.load()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W, H], outline=chumby_color, width=14, radius=30)
    game = next_game(team)
    recs = records()
    home, away = game["homeTeam"], game["awayTeam"]

    paste_logo(img, away, False)
    paste_logo(img, home, True)

    venue = game["venue"]["default"]
    away_record = recs.get(away["abbrev"])
    home_record = recs.get(home["abbrev"])

    d.text((42, 2), venue, fill=(0, 0, 0))
    d.text((207, 2), game["gameDate"], fill=(0, 0, 0))
    d.text((away_spot+(logo_size//2), 40), away["abbrev"], fill=(255, 255, 255))
    d.text((home_spot+(logo_size//2), 40), home["abbrev"], fill=(255, 255, 255))
    d.text((away_spot+(logo_size//2), 190), away_record, fill=(255, 255, 255))
    d.text((home_spot+(logo_size//2), 190), home_record, fill=(255, 255, 255))
    d.text((W//2, (H//2)+50), "vs.", fill=(255, 255, 255))

    path = os.path.join(out_dir, "nhl.jpg")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85, progressive=False, optimize=False)
    return buf.getvalue()

def get_nhl_jpeg(team):
    """Return JPEG bytes for a team's next game. Raises ValueError on a bad team code."""
    team = team.upper()
    if not re.fullmatch(r"[A-Z]{3}", team):
        raise ValueError("bad team code")

    now = time.time()
    cached = _jpeg_cache.get(team)
    if cached and now - cached[0] < CACHE_SECS:
        return cached[1]

    try:
        data = render(team)
    except Exception:
        if cached:            # NHL API down? serve the last good image
            return cached[1]
        raise
    _jpeg_cache[team] = (now, data)
    return data