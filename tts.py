"""Speech clips for the games, made with the Windows built-in voices (SAPI).

Some tablet browsers (e.g. Amazon Silk) have no working text-to-speech, so the
server renders each phrase to a WAV once, caches it on disk, and the games play
it like any other sound.
"""
import array
import hashlib
import os
import threading
import wave
from xml.sax.saxutils import escape

try:
    import pythoncom
    import win32com.client
    AVAILABLE = True
except ImportError:  # not on Windows / pywin32 missing: games fall back to browser speech
    AVAILABLE = False

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tts_cache")
VOICE = "Zira"      # part of the Windows voice name to use ("Zira" or "David")
MAX_CHARS = 200

_lock = threading.Lock()


def clip_path(text):
    """Path of the WAV for `text`, rendered on first use, or None if it can't be made.

    Cached clips are served on any platform, so a cache built on Windows can be
    deployed to a Linux host (e.g. PythonAnywhere) where SAPI doesn't exist.
    """
    key = hashlib.sha1(f"{VOICE}|{text}".encode("utf-8")).hexdigest()
    path = os.path.join(CACHE_DIR, key + ".wav")
    if not os.path.exists(path):
        if not AVAILABLE:
            return None
        with _lock:  # SAPI calls are serialized; also avoids rendering twice
            if not os.path.exists(path):
                _render(text, path)
    return path


def _to_xml(text):
    # A lone letter is spelled so it's read by its name ("A" -> "ay", not "uh").
    body = f"<spell>{text}</spell>" if len(text) == 1 and text.isalpha() else escape(text)
    return f'<rate absspeed="-1"><pitch absmiddle="3">{body}</pitch></rate>'


def _render(text, path):
    os.makedirs(CACHE_DIR, exist_ok=True)
    raw = path + ".raw.wav"
    pythoncom.CoInitialize()
    try:
        voice = win32com.client.Dispatch("SAPI.SpVoice")
        for token in voice.GetVoices():
            if VOICE.lower() in token.GetDescription().lower():
                voice.Voice = token
                break
        fmt = win32com.client.Dispatch("SAPI.SpAudioFormat")
        fmt.Type = 22  # SAFT22kHz16BitMono
        stream = win32com.client.Dispatch("SAPI.SpFileStream")
        stream.Format = fmt
        stream.Open(raw, 3)  # SSFMCreateForWrite
        voice.AudioOutputStream = stream
        voice.Speak(_to_xml(text), 8)  # SVSFIsXML, synchronous
        stream.Close()
    finally:
        pythoncom.CoUninitialize()
    _trim_silence(raw, path)
    os.remove(raw)


def _trim_silence(src, dst, threshold=250, pad_ms=40):
    """Cut the silence SAPI leaves around speech so clips chain without long gaps."""
    with wave.open(src, "rb") as w:
        params = w.getparams()
        samples = array.array("h", w.readframes(w.getnframes()))
    start = next((i for i, s in enumerate(samples) if abs(s) > threshold), None)
    if start is not None:
        end = next(i for i in range(len(samples) - 1, -1, -1) if abs(samples[i]) > threshold)
        pad = params.framerate * pad_ms // 1000
        samples = samples[max(0, start - pad):end + pad]
    part = dst + ".part"
    with wave.open(part, "wb") as w:
        w.setparams(params)
        w.writeframes(samples.tobytes())
    os.replace(part, dst)
