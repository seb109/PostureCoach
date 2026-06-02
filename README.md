# PostureCoach

Real-time posture monitoring via webcam + MediaPipe, with a FastAPI backend,
session logging, and PNG reports.

---

## Project structure

```
backend/
├── app/
│   ├── server.py             # FastAPI application factory  ← uvicorn entry point
│   ├── main.py               # CLI entry point (session | serve | report)
│   ├── config.py             # All tuneable constants (thresholds, paths, colours)
│   │
│   ├── api/
│   │   ├── schemas.py        # All Pydantic request / response models
│   │   ├── deps.py           # FastAPI Depends() providers (singleton service)
│   │   └── v1/
│   │       ├── router.py     # Mounts all endpoint routers under /api/v1
│   │       └── endpoints/
│   │           ├── health.py        GET  /health
│   │           ├── calibration.py   GET  /calibration/status
│   │           │                    POST /calibration/start
│   │           ├── sessions.py      GET  /sessions
│   │           │                    GET  /sessions/{id}/stats
│   │           │                    GET  /sessions/{id}/timeline
│   │           │                    GET  /sessions/{id}/report
│   │           │                    GET  /sessions/{id}/report/image
│   │           │                    GET  /sessions/{id}/download
│   │           │                    DELETE /sessions/{id}
│   │           └── stream.py        WS   /stream  (real-time frame analysis)
│   │
│   ├── posture/
│   │   ├── detector.py       MediaPipe inference + landmark geometry helpers
│   │   ├── classifier.py     Ratio → PostureStatus enum
│   │   ├── calibration.py    Two-phase quick-cal state machine + JSON persistence
│   │   ├── alerts.py         Streak timers, cooldown, sound playback
│   │   ├── session_logger.py Throttled CSV writer
│   │   └── visualization.py  All OpenCV HUD drawing helpers
│   │
│   ├── reports/
│   │   ├── parser.py         CSV discovery + loading → SessionData
│   │   ├── analytics.py      Pure statistics → SessionStats
│   │   ├── charts.py         Individual matplotlib panel builders
│   │   └── report_generator.py  Figure assembly + PNG output
│   │
│   ├── services/
│   │   ├── posture_service.py   Per-frame orchestration (detector + alert + log)
│   │   └── session_service.py   Session file management (list, stats, timeline)
│   │
│   └── routes/
│       └── posture.py           CLI sub-command dispatchers (OpenCV loop + report)
│
tests/
└── test_api.py               pytest suite (mocks MediaPipe — runs in CI)

data/                         ← auto-created at runtime
├── calibration.json
└── sessions/
    └── session_YYYYMMDD_HHMMSS.csv
```

---

## Quick start

```bash
pip install -r requirements.txt
```

### Start the API server

```bash
python app/main.py serve              # production
python app/main.py serve --reload     # dev (hot-reload)
python app/main.py serve --port 9000  # custom port
```

Then open **http://localhost:8000/docs** for the interactive Swagger UI.

### Live webcam session (OpenCV window)

```bash
python app/main.py session
```

### Generate a report

```bash
python app/main.py report
python app/main.py report data/sessions/session_20260329_203405.csv
```

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Liveness probe |
| `GET` | `/api/v1/calibration/status` | Is the model calibrated? |
| `POST` | `/api/v1/calibration/start` | Start / restart calibration |
| `WS` | `/api/v1/stream` | Real-time frame analysis |
| `GET` | `/api/v1/sessions` | List all sessions |
| `GET` | `/api/v1/sessions/{id}/stats` | Full analytics for one session |
| `GET` | `/api/v1/sessions/{id}/timeline` | Raw time-series data |
| `GET` | `/api/v1/sessions/{id}/report` | Generate PNG report (JSON) |
| `GET` | `/api/v1/sessions/{id}/report/image` | Download PNG report |
| `GET` | `/api/v1/sessions/{id}/download` | Download raw CSV |
| `DELETE` | `/api/v1/sessions/{id}` | Delete session |

### WebSocket protocol (`/api/v1/stream`)

**Client → Server**
- **Binary**: raw JPEG bytes of one video frame
- **Text**: `"recalibrate"` to trigger a new calibration sequence

**Server → Client**
- **Text / JSON**: `FrameAnalysisResponse`

```json
{
  "cal_phase": "DONE",
  "cal_progress": 1.0,
  "cal_seconds_left": 0,
  "status": "GOOD POSTURE",
  "ratio": 91.2,
  "distance": 118.4,
  "angle": 4.1,
  "pose_visible": true,
  "alert_progress": 0.0,
  "alert_seconds_left": 0,
  "is_flashing": false,
  "cooldown_seconds": 0
}
```

---

## Configuration

Edit `app/config.py` — no other file needs to change.

| Key | Default | Meaning |
|-----|---------|---------|
| `RATIO_GOOD_THRESHOLD` | `85.0` | ratio % above which posture is GOOD |
| `RATIO_SLIGHT_THRESHOLD` | `70.0` | ratio % above which posture is SLIGHT |
| `ALERT_DELAY_BAD_SECONDS` | `10` | seconds of BAD before alert fires |
| `ALERT_DELAY_SLIGHT_SECONDS` | `20` | seconds of SLIGHT before alert fires |
| `ALERT_COOLDOWN_SECONDS` | `20` | minimum gap between alerts |
| `CORS_ORIGINS` env var | `"*"` | comma-separated allowed origins |

---

## Running tests

```bash
pytest backend/tests/ -v
```

Tests mock MediaPipe and cv2 so they run in CI without a camera.

---

## Platform note

The audible alert uses `winsound` (Windows only). On macOS/Linux a terminal
bell is used instead. Swap `play_alert()` in `app/posture/alerts.py` for any
cross-platform sound library if needed.
