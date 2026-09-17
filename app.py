"""Kid Games - a tiny Flask site for playing games on the home network.

Run:  python app.py        then open the printed address on the tablet.

Adding a game: make a folder in games/<slug>/ with an index.html,
then add an entry to GAMES below.
"""
import os
import socket

from flask import Flask, abort, render_template, request, send_file, send_from_directory

import tts

ROOT = os.path.dirname(os.path.abspath(__file__))
GAMES_DIR = os.path.join(ROOT, "games")
PORT = int(os.environ.get("PORT", 8080))

GAMES = [
    {"slug": "number-race", "name": "Number Race", "icon": "🏎️"},
    {"slug": "rescue-letters", "name": "Rescue Letters", "icon": "🚒"},
    {"slug": "build-it", "name": "Build It!", "icon": "🚧"},
    {"slug": "shape-train", "name": "Shape Train", "icon": "🚂"},
]

app = Flask(__name__)


@app.after_request
def no_cache(response):
    # Always serve fresh files so edits show up on the tablet right away.
    # Speech clips never change for the same text, so those may be cached.
    if request.path != "/tts":
        response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/")
def home():
    return render_template("home.html", games=GAMES)


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/tts")
def speech():
    text = request.args.get("text", "").strip()
    if not text or len(text) > tts.MAX_CHARS:
        abort(400)
    path = tts.clip_path(text)  # cached clips work anywhere; new ones need Windows voices
    if path is None:
        abort(503)
    return send_file(path, mimetype="audio/wav", max_age=31536000)


@app.route("/games/<slug>/")
@app.route("/games/<slug>/<path:filename>")
def game(slug, filename="index.html"):
    if slug not in {g["slug"] for g in GAMES}:
        abort(404)
    return send_from_directory(os.path.join(GAMES_DIR, slug), filename)


def lan_ips():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))  # no packets are sent
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    return sorted(ip for ip in ips if not ip.startswith(("127.", "169.254.")))


if __name__ == "__main__":
    print("\nKid Games is running! On the tablet, open one of these:")
    for ip in lan_ips():
        print(f"    http://{ip}:{PORT}/")
    print()
    app.run(host="0.0.0.0", port=PORT, debug=False)
