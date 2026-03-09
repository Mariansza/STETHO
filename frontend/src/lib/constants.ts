export const WS_URL = "ws://localhost:8001/ws/audio";
export const API_URL = "http://localhost:8001/api";
export const SAMPLE_RATE = 44100;
export const CHUNK_SIZE = 1024;

export const MODE_LABELS: Record<string, string> = {
  cardiac: "Cardiaque",
  respiratory: "Respiratoire",
  raw: "Brut",
};

export const MODE_COLORS: Record<string, string> = {
  cardiac: "#f87171",
  respiratory: "#60a5fa",
  raw: "#a1a1aa",
};
