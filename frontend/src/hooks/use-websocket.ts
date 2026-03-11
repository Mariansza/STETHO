"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ClientMessage, ConfigMessage, ConnectionStatus, VizMessage } from "@/types";
import { WS_URL } from "@/lib/constants";
import { parseAudioFrame, parseJsonMessage } from "@/lib/ws-protocol";

interface UseWebSocketOptions {
  onAudioFrame?: (pcm: Float32Array, seq: number) => void;
  onVizMessage?: (viz: VizMessage) => void;
  onConfig?: (config: ConfigMessage) => void;
}

export function useWebSocket({ onAudioFrame, onVizMessage, onConfig }: UseWebSocketOptions = {}) {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const onAudioFrameRef = useRef(onAudioFrame);
  const onVizMessageRef = useRef(onVizMessage);
  const onConfigRef = useRef(onConfig);

  onAudioFrameRef.current = onAudioFrame;
  onVizMessageRef.current = onVizMessage;
  onConfigRef.current = onConfig;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const ws = new WebSocket(WS_URL);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      setStatus("connected");
    };

    ws.onclose = () => {
      setStatus("disconnected");
      wsRef.current = null;
    };

    ws.onerror = () => {
      setStatus("error");
    };

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        const { seq, pcm } = parseAudioFrame(event.data);
        onAudioFrameRef.current?.(pcm, seq);
      } else if (typeof event.data === "string") {
        const msg = parseJsonMessage(event.data);
        if (!msg) return;
        if (msg.type === "viz") {
          onVizMessageRef.current?.(msg);
        } else if (msg.type === "config") {
          onConfigRef.current?.(msg);
        }
      }
    };

    wsRef.current = ws;
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setStatus("disconnected");
  }, []);

  const send = useCallback((msg: ClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  // Auto-reconnect
  useEffect(() => {
    if (status === "error" || status === "disconnected") {
      const timer = setTimeout(() => {
        if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
          connect();
        }
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [status, connect]);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return { status, connect, disconnect, send };
}
