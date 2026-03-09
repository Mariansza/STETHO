import type { VizMessage } from "@/types";

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
 * Parse a JSON viz message from the backend.
 */
export function parseVizMessage(data: string): VizMessage | null {
  try {
    const msg = JSON.parse(data);
    if (msg.type === "viz") {
      return msg as VizMessage;
    }
    return null;
  } catch {
    return null;
  }
}
