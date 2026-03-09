---
name: dev
description: Launch the development environment
disable-model-invocation: true
---

Launch both the backend and frontend dev servers for the Stetho project.

## Steps

1. Check if ports 8001 (backend) and 3001 (frontend) are already in use
2. Start the backend:
   ```bash
   cd C:/Users/Medhi Souai/Desktop/stetho && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
   ```
   Run this in the background.

3. Start the frontend:
   ```bash
   cd C:/Users/Medhi Souai/Desktop/stetho/frontend && npm run dev -- -p 3001
   ```
   Run this in the background.

4. Wait a few seconds, then verify both are running:
   - Backend: curl http://localhost:8001/api/health
   - Frontend: curl http://localhost:3001

5. Report status to the user with the URLs:
   - Backend API: http://localhost:8001
   - Frontend: http://localhost:3001
