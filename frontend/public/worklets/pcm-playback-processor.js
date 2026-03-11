/**
 * Kept as a no-op placeholder. Playback now uses scheduled AudioBufferSourceNodes
 * in use-audio-playback.ts for click-free output.
 */
class PCMPlaybackProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.port.onmessage = () => {};
  }
  process() {
    return true;
  }
}
registerProcessor("pcm-playback-processor", PCMPlaybackProcessor);
