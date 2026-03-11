import type { VizMessage, ConfigMessage } from "@/types";

/**
 * Parse a binary audio frame from the backend.
 * Format: [4 bytes seq uint32 LE] + [N × 4 bytes float32 LE PCM]
 */
export function parseAudioFrame(data: ArrayBuffer): {
  seq: number;
  pcm: Float32Array;
} {
  const view = new DataView(data);
  const seq = view.getUint32(0, true); // little-endian
  const pcm = new Float32Array(data, 4);
  return { seq, pcm };
}

/**
 * Parse a JSON message from the backend (viz or config).
 */
export function parseJsonMessage(data: string): VizMessage | ConfigMessage | null {
  try {
    const msg = JSON.parse(data);
    if (msg.type === "viz" || msg.type === "config") {
      return msg;
    }
    return null;
  } catch {
    return null;
  }
}
