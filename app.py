"""Funny Moments - Chumby image server (step 1: test image)."""
import os
from nhl import get_nhl_jpeg
from nws import get_nws_jpeg
from flask import Flask, Response, abort, send_file

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Hardcoded for now. Later, each endpoint renders its own image.
TEST_IMAGE_PATH = os.path.join(BASE_DIR, "static", "test.jpg")

# name -> file path. /chumby/image/<name>.jpg looks things up here.
IMAGES = {
    "test": TEST_IMAGE_PATH,
}

CROSSDOMAIN = """<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.adobe.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
  <allow-access-from domain="*"/>
</cross-domain-policy>
"""


@app.route("/crossdomain.xml")
def crossdomain():
    # Flash fetches this before letting a widget load data from our domain.
    return Response(CROSSDOMAIN, mimetype="text/xml")


@app.route("/chumby/ping.xml")
def ping():
    # Tiny XML health check, handy for testing from the device.
    return Response("<?xml version=\"1.0\"?><status>ok</status>", mimetype="text/xml")


@app.route("/chumby/image/<name>.jpg")
def chumby_image(name):
    path = IMAGES.get(name)
    print(path)
    if not path or not os.path.exists(path):
        abort(404)
    resp = send_file(path, mimetype="image/jpeg", conditional=False)
    # Chumby should always fetch a fresh copy.
    resp.headers["Cache-Control"] = "no-store, max-age=0"
    return resp

@app.route("/chumby/nhl/<team>")
def chumby_nhl(team):
    try:
        data = get_nhl_jpeg(team)
    except ValueError:
        abort(404)
    except Exception:
        app.logger.exception("nhl render failed")
        abort(502)
    resp = Response(data, mimetype="image/jpeg")
    resp.headers["Cache-Control"] = "no-store, max-age=0"
    return resp

@app.route("/chumby/radar/<station>")
def chumby_radar(station):
    try:
        data = get_nws_jpeg(station)
    except Exception:
        app.logger.exception("nhl render failed")
        abort(502)
    resp = Response(data, mimetype="image/jpeg")
    resp.headers["Cache-Control"] = "no-store, max-age=0"
    return resp

if __name__ == "__main__":
    # Dev only. In production use gunicorn behind nginx.
    app.run(host="0.0.0.0", port=5000, debug=True)
