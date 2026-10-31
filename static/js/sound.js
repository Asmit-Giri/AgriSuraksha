// Procedural Web Audio API Siren & Alert Chime Synthesizer
class AlertAudioPlayer {
  constructor() {
    this.audioCtx = null;
    this.soundEnabled = false;
  }

  init() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioContext();
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  toggleSound() {
    this.soundEnabled = !this.soundEnabled;
    if (this.soundEnabled) {
      this.init();
      this.playChime(660, 0.2);
    }
    return this.soundEnabled;
  }

  playChime(freq = 587.33, duration = 0.3) {
    if (!this.soundEnabled) return;
    this.init();
    try {
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime);

      gain.gain.setValueAtTime(0.2, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start();
      osc.stop(this.audioCtx.currentTime + duration);
    } catch (e) {
      console.warn("Audio playback error:", e);
    }
  }

  playEmergencySiren(repeats = 3) {
    if (!this.soundEnabled) return;
    this.init();
    try {
      let now = this.audioCtx.currentTime;
      for (let i = 0; i < repeats; i++) {
        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();

        osc.type = 'sawtooth';
        // Siren warble between 700Hz and 1000Hz
        osc.frequency.setValueAtTime(700, now + (i * 0.4));
        osc.frequency.linearRampToValueAtTime(1050, now + (i * 0.4) + 0.2);
        osc.frequency.linearRampToValueAtTime(700, now + (i * 0.4) + 0.38);

        gain.gain.setValueAtTime(0.25, now + (i * 0.4));
        gain.gain.exponentialRampToValueAtTime(0.01, now + (i * 0.4) + 0.38);

        osc.connect(gain);
        gain.connect(this.audioCtx.destination);

        osc.start(now + (i * 0.4));
        osc.stop(now + (i * 0.4) + 0.4);
      }
    } catch (e) {
      console.warn("Siren audio error:", e);
    }
  }
}

window.alertAudio = new AlertAudioPlayer();

