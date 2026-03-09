export const WS_URL = "ws://localhost:8000/ws/audio";
export const API_URL = "http://localhost:8000/api";
export const SAMPLE_RATE = 44100;
export const CHUNK_SIZE = 1024;

export const MODE_LABELS: Record<string, string> = {
  cardiac: "Cardiaque",
  respiratory: "Respiratoire",
  raw: "Brut",
};

export const MODE_COLORS: Record<string, string> = {
  cardiac: "#ef4444",
  respiratory: "#3b82f6",
  raw: "#a3a3a3",
};
