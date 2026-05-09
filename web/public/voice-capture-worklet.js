// AudioWorklet that captures mic input, downsamples to 24 kHz, converts
// to int16 PCM, and posts ~40 ms frames back to the main thread.
//
// Bridge expects pcm_24000 mono int16 base64 frames per the 46elks
// protocol; this worklet produces the wire-format the main thread can
// trivially base64-encode and ship.

class VoiceCaptureProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    const target = (options.processorOptions && options.processorOptions.targetRate) || 24000;
    this.targetRate = target;
    this.frameSamples = Math.floor(target * 0.04); // 40 ms = 960 samples at 24 kHz
    this.ratio = sampleRate / target;
    this.buffer = [];
    this._enabled = true;
    this.port.onmessage = (e) => {
      if (e.data && typeof e.data.enabled === "boolean") this._enabled = e.data.enabled;
    };
  }

  process(inputs) {
    if (!this._enabled) return true;
    const input = inputs[0];
    if (!input || !input[0]) return true;
    const ch0 = input[0];

    // Linear-interpolation resample from sampleRate (typically 48 kHz) to targetRate.
    // Cheap and good enough for voice; replace with polyphase if quality matters.
    const ratio = this.ratio;
    let i = 0;
    while (i + 1 < ch0.length) {
      const idx = i;
      const idxFloor = Math.floor(idx);
      const idxNext = idxFloor + 1 < ch0.length ? idxFloor + 1 : idxFloor;
      const frac = idx - idxFloor;
      const v = ch0[idxFloor] * (1 - frac) + ch0[idxNext] * frac;
      this.buffer.push(v);
      i += ratio;
    }

    while (this.buffer.length >= this.frameSamples) {
      const slice = this.buffer.splice(0, this.frameSamples);
      const int16 = new Int16Array(this.frameSamples);
      for (let j = 0; j < this.frameSamples; j++) {
        const s = Math.max(-1, Math.min(1, slice[j]));
        int16[j] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      this.port.postMessage(int16.buffer, [int16.buffer]);
    }
    return true;
  }
}

registerProcessor("voice-capture", VoiceCaptureProcessor);
