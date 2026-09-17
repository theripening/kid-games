# Kid Games

Simple browser games for a three-year-old, served from a small Flask site on the
home network. Built to be played on an Amazon Fire tablet in the Silk browser:
big touch targets, a spoken voice instead of text to read, no timers and no way
to lose.

| Game | What it teaches |
|---|---|
| **Number Race** (`games/number-race/`) | Recognising numerals 1–20, and counting |
| **Rescue Letters** (`games/rescue-letters/`) | Recognising letters A–Z, upper or lower case |
| **Build It!** (`games/build-it/`) | Adding and taking away, as loads of rocks and bricks |

Each game is one self-contained `index.html` with no internet dependencies.

## Running it

```
pip install -r requirements.txt
python app.py
```

It prints the addresses to open on the tablet, e.g. `http://192.168.1.10:8080/`.
On Windows, `start.bat` does the same by double-click, and the first run asks to
allow the firewall on **private** networks — without that the tablet can't
connect. Set `PORT` to use a different port.

## The games

**Number Race** — *Find it!*: three numbered cars, a voice asks for one, and the
right car races off. *Count!*: tap each parked car to count it out loud. A menu
setting picks numbers up to 5, 10 or 20.

**Rescue Letters** — *Find it!*: a fire truck, ambulance and police car carry
letters, and the right one drives off with lights and siren. *Letter Garage*:
26 garage doors, each opening a card like "B is for Boat 🚤". Menu settings pick
A–F / A–M / A–Z and upper or lower case, plus **🔈 Test voice** to hear every
letter on the device itself.

**Build It!** — *Load it!*: rocks sit in a dump truck, the digger tips in more,
and the child counts the new total by tapping. *Dump it!*: a crane lifts bricks
off a pallet, and they count what's left. *Build a tower!*: free play, stacking
bricks while the voice counts up and the wrecking ball counts down.

Arithmetic here is deliberately concrete — "three rocks and one more", counted
by tapping — because symbolic sums are beyond a three-year-old. Menu settings
pick totals up to 5 or 10, counting alone or counting then picking the total
from three signs, and an off-by-default `3 + 1 = 4` line for when they're older.
Totals never exceed the chosen maximum, and taking away always leaves at least
one brick.

Each game gives a star per correct answer and a trophy every five.

## The voice

Silk on Fire tablets has no reliable text-to-speech, so the browser's own
`speechSynthesis` is only a fallback. Instead `/tts?text=...` renders a phrase
with a Windows SAPI voice, trims the silence around it, and caches the WAV in
`tts_cache/`; `static/kid-voice.js` plays those clips through Web Audio, which
works everywhere the game's sound effects do.

Two things this depends on:

- **Letters are passed as their own phrase** (`["Find the letter", "A"]`), and a
  lone letter is rendered with SAPI's `<spell>`, so it is read by name. Letters
  inside a sentence, or spelled phonetically ("ay", "eff"), get misread as "I"
  or "E-F-F".
- **Rendering needs Windows** (`pywin32` + SAPI). Cached clips are served on any
  platform, so a cache built on Windows can be deployed to Linux. Opening each
  game once locally preloads every phrase it uses into the cache.

`VOICE` at the top of `tts.py` chooses the Windows voice (e.g. `Zira`, `David`).

## Hosting on PythonAnywhere

The app is a plain WSGI app, so point the web app's WSGI file at it:

```python
import sys
sys.path.insert(0, "/home/<user>/KidGames")
from app import app as application
```

`tts_cache/` is committed for this reason: Linux has no SAPI, so the site serves
the clips as recorded. After changing any spoken phrase, run the game locally on
Windows to render the new clips, then commit them.

## Adding a game

1. Create `games/<slug>/index.html`.
2. Add `{"slug": "<slug>", "name": "...", "icon": "<emoji>"}` to `GAMES` in
   `app.py` — the home page is built from that list.
3. Restart the server; the games themselves are served fresh with no caching.
