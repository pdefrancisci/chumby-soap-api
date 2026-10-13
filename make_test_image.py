"""Generate static/test.jpg: 320x240, baseline (non-progressive) JPEG."""
import os
import time
from PIL import Image, ImageDraw

W, H = 320, 240
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(out_dir, exist_ok=True)

img = Image.new("RGB", (W, H))
px = img.load()
for y in range(H):
    for x in range(W):
        px[x, y] = (int(255 * x / W), int(255 * y / H), 160)

d = ImageDraw.Draw(img)
d.rectangle([0, 0, W - 1, H - 1], outline=(255, 255, 255), width=3)
d.line([0, 0, W - 1, H - 1], fill=(255, 255, 255), width=1)
d.line([0, H - 1, W - 1, 0], fill=(255, 255, 255), width=1)
d.rectangle([60, 90, 260, 150], fill=(0, 0, 0))
d.text((72, 98), "FUNNY MOMENTS", fill=(255, 255, 255))
d.text((72, 114), "320x240 test image", fill=(255, 255, 255))
d.text((72, 130), time.strftime("%Y-%m-%d %H:%M"), fill=(255, 255, 255))

path = os.path.join(out_dir, "test.jpg")
img.save(path, "JPEG", quality=85, progressive=False, optimize=False)
print("wrote", path)
