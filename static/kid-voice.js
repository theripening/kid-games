/* Kid Games voice.
 *
 * Plays speech clips rendered by the Flask server (/tts) through Web Audio, so it
 * works on browsers with no working text-to-speech (e.g. Amazon Silk on Fire
 * tablets). Falls back to the browser's own speechSynthesis if the server can't
 * make a clip.
 *
 *   KidVoice.init(function () { return audioContext; });
 *   KidVoice.preload(["Find number 3!", "A", "B"]);
 *   KidVoice.speak(["Find the letter", "A"], function (i) { ...part i started... });
 *
 * Pass letters as their own part: the server spells a lone letter by name.
 */
(function () {
  "use strict";

  var getCtx = function () { return null; };
  var clips = {};      // text -> Promise<AudioBuffer|null>
  var token = 0;       // bumped by stop(); stale playback chains check it and bail
  var current = null;  // the AudioBufferSourceNode playing now

  function load(text) {
    if (!clips[text]) {
      clips[text] = fetch("/tts?text=" + encodeURIComponent(text))
        .then(function (r) { if (!r.ok) throw new Error("tts " + r.status); return r.arrayBuffer(); })
        .then(function (data) {
          var ctx = getCtx();
          if (!ctx) throw new Error("no audio context");
          // Callback form: older Chromium builds don't return a promise here.
          return new Promise(function (resolve, reject) { ctx.decodeAudioData(data, resolve, reject); });
        })
        .catch(function () { delete clips[text]; return null; });
    }
    return clips[text];
  }

  function stop() {
    token++;
    if (current) {
      current.onended = null;
      try { current.stop(); } catch (e) {}
      current = null;
    }
    if (window.speechSynthesis) speechSynthesis.cancel();
  }

  function speak(parts, onPart) {
    stop();
    parts = [].concat(parts);
    var mine = token;
    Promise.all(parts.map(load)).then(function (buffers) {
      if (mine !== token) return;
      if (buffers.some(function (b) { return !b; })) { browserSpeak(parts, onPart, mine); return; }
      var ctx = getCtx();
      (function play(i) {
        if (mine !== token || i >= buffers.length) return;
        var src = ctx.createBufferSource();
        src.buffer = buffers[i];
        src.connect(ctx.destination);
        src.onended = function () { if (current === src) current = null; play(i + 1); };
        current = src;
        src.start();
        if (onPart) onPart(i);
      })(0);
    });
  }

  function browserSpeak(parts, onPart, mine) {
    if (!window.speechSynthesis) return;
    // Chromium on Android drops an utterance queued right after cancel(), so wait a beat.
    setTimeout(function () {
      if (mine !== token) return;
      parts.forEach(function (text, i) {
        var u = new SpeechSynthesisUtterance(text);
        u.rate = 0.85; u.pitch = 1.25;
        if (onPart) u.onstart = function () { onPart(i); };
        speechSynthesis.speak(u);
      });
    }, 150);
  }

  window.KidVoice = {
    init: function (fn) { getCtx = fn; },
    preload: function (list) { list.forEach(load); },
    speak: speak,
    stop: stop
  };
})();
