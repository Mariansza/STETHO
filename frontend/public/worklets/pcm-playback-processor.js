/**
 * AudioWorkletProcessor for gapless PCM playback.
 * Receives Float32Array chunks via the port, buffers them,
 * and outputs continuous audio.
 */
class PCMPlaybackProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._buffer = new Float32Array(0);
    this.port.onmessage = (event) => {
      if (event.data instanceof Float32Array) {
        // Append to buffer
        const newBuf = new Float32Array(this._buffer.length + event.data.length);
        newBuf.set(this._buffer, 0);
        newBuf.set(event.data, this._buffer.length);
        this._buffer = newBuf;

        // Prevent buffer from growing too large (keep max ~0.5s @ 44100)
        const maxLen = 22050;
        if (this._buffer.length > maxLen) {
          this._buffer = this._buffer.slice(this._buffer.length - maxLen);
        }
      }
    };
  }

  process(inputs, outputs, parameters) {
    const output = outputs[0];
    if (!output || output.length === 0) return true;

    const channel = output[0];
    const needed = channel.length; // typically 128

    if (this._buffer.length >= needed) {
      channel.set(this._buffer.subarray(0, needed));
      this._buffer = this._buffer.slice(needed);
    } else {
      // Underrun — output silence for missing samples
      channel.set(this._buffer);
      for (let i = this._buffer.length; i < needed; i++) {
        channel[i] = 0;
      }
      this._buffer = new Float32Array(0);
    }

    return true;
  }
}

registerProcessor("pcm-playback-processor", PCMPlaybackProcessor);
