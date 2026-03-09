---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications.
---

Create distinctive, production-grade frontend interfaces for the Stetho real-time auscultation app.

## Design System

- **Theme**: Dark medical UI — background #0a0a0a, surfaces #141414/#1a1a1a
- **Primary accent**: Emerald (#10b981) for active/positive states
- **Mode colors**: Cardiac = red (#ef4444), Respiratory = blue (#3b82f6), Raw = neutral (#a3a3a3)
- **Typography**: Inter, clean and minimal
- **Borders**: Subtle neutral-800, rounded-lg/rounded-xl
- **Spacing**: Generous, breathable layouts

## Principles

1. **Medical-grade clarity** — information hierarchy must be instantly readable
2. **Real-time feel** — smooth transitions, no layout shifts, Canvas-based visualizations
3. **Dark-first** — optimized for low-light clinical environments
4. **Minimal chrome** — focus on the data (waveforms, spectrogram, metrics)
5. **Accessible controls** — large touch targets for sliders and buttons

## Stack

- Tailwind CSS for styling (no CSS-in-JS, no external UI libraries beyond what exists)
- Canvas 2D for real-time visualizations (waveform, spectrogram)
- React functional components + hooks

## Files to edit

Components are in `frontend/src/components/`:
- `header.tsx`, `control-panel.tsx`, `device-selector.tsx`
- `waveform-canvas.tsx`, `spectrogram-canvas.tsx`
- `status-bar.tsx`, `audio-player.tsx`

Main page: `frontend/src/app/page.tsx`
Global styles: `frontend/src/app/globals.css`
