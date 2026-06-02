"""
tests/test_api.py — FastAPI endpoint tests.

Run with:  pytest backend/tests/test_api.py -v

MediaPipe and cv2 are heavy; the PostureService is mocked so these tests
run in CI without a camera or GPU.
"""
from __future__ import annotations

import csv
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ── Patch heavy dependencies before importing the app ─────────────────────
# We patch at the module level so MediaPipe never initialises.

@pytest.fixture(scope="session", autouse=True)
def mock_mediapipe():
    """Prevent MediaPipe from loading during tests."""
    with patch.dict("sys.modules", {
        "mediapipe":                           MagicMock(),
        "mediapipe.solutions":                 MagicMock(),
        "mediapipe.solutions.pose":            MagicMock(),
        "mediapipe.solutions.drawing_utils":   MagicMock(),
        "winsound":                            MagicMock(),
        "cv2":                                 MagicMock(),
    }):
        yield


@pytest.fixture(scope="session")
def client(mock_mediapipe, tmp_path_factory):
    """Return a TestClient with session/calibration dirs in a temp folder."""
    tmp = tmp_path_factory.mktemp("data")
    session_dir = tmp / "sessions"
    session_dir.mkdir()

    with patch("app.config.SESSION_DIR", str(session_dir)), \
         patch("app.config.CALIBRATION_FILE", str(tmp / "calibration.json")):
        from app.server import create_app
        app = create_app()
        with TestClient(app) as c:
            yield c


# ── Health ─────────────────────────────────────────────────────────────────

class TestHealth:
    def test_returns_ok(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ── Calibration ────────────────────────────────────────────────────────────

class TestCalibration:
    def test_status_before_calibration(self, client):
        with patch("app.api.deps._posture_service") as mock_svc:
            mock_svc._calibration.is_calibrated    = False
            mock_svc._calibration.baseline_distance = None
            mock_svc._calibration.baseline_angle    = None
            r = client.get("/api/v1/calibration/status")
        assert r.status_code == 200
        assert r.json()["is_calibrated"] is False

    def test_start_calibration(self, client):
        with patch("app.api.deps._posture_service") as mock_svc:
            mock_svc.start_recalibration = MagicMock()
            r = client.post("/api/v1/calibration/start")
        assert r.status_code == 202
        assert "started" in r.json()["message"].lower()


# ── Sessions ───────────────────────────────────────────────────────────────

@pytest.fixture
def sample_session():
    """Write a minimal valid session CSV in the active SESSION_DIR and return its Path."""
    from pathlib import Path
    from app.config import SESSION_DIR
    rows = [
        ["timestamp", "elapsed_s", "ratio", "distance", "angle", "status"],
        ["10:00:00",  "0.0",  "92.0", "120.0", "5.0", "GOOD POSTURE"],
        ["10:00:01",  "1.0",  "88.0", "115.0", "7.0", "GOOD POSTURE"],
        ["10:00:02",  "2.0",  "75.0", "100.0", "12.0", "SLIGHT SLOUCH"],
        ["10:00:03",  "3.0",  "60.0",  "80.0", "20.0", "BAD POSTURE"],
        ["10:00:04",  "4.0",  "90.0", "118.0",  "4.0", "GOOD POSTURE"],
    ]
    path = Path(SESSION_DIR) / "session_20260101_120000.csv"
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    yield path
    if path.exists():
        path.unlink()


class TestSessions:
    def test_list_empty(self, client):
        with patch("app.config.SESSION_DIR", "/tmp/nonexistent_xyz"):
            r = client.get("/api/v1/legacy/sessions")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_stats(self, sample_session):
        from app.reports.parser import load_session
        from app.reports.analytics import compute_stats
        data  = load_session(str(sample_session))
        stats = compute_stats(data)
        assert 0 <= stats.score <= 100
        assert stats.total_frames == 5
        assert stats.good_count == 3
        assert stats.slight_count == 1
        assert stats.bad_count == 1

    def test_timeline_length(self, sample_session):
        from app.reports.parser import load_session
        data = load_session(str(sample_session))
        assert len(data.elapsed) == 5
        assert len(data.statuses) == 5

    def test_404_unknown_session(self, client):
        r = client.get("/api/v1/legacy/sessions/session_00000000_000000/stats")
        assert r.status_code == 404

    def test_delete_session(self, client, sample_session):
        r = client.delete(f"/api/v1/legacy/sessions/{sample_session.stem}")
        assert r.status_code == 204
        assert not sample_session.exists()


# ── Classifier (pure unit test, no HTTP) ───────────────────────────────────

class TestClassifier:
    def test_good(self):
        from app.posture.classifier import PostureStatus, classify
        assert classify(90.0) == PostureStatus.GOOD

    def test_slight(self):
        from app.posture.classifier import PostureStatus, classify
        assert classify(77.0) == PostureStatus.SLIGHT

    def test_bad(self):
        from app.posture.classifier import PostureStatus, classify
        assert classify(60.0) == PostureStatus.BAD

    def test_boundary_good(self):
        from app.posture.classifier import PostureStatus, classify
        assert classify(85.1) == PostureStatus.GOOD

    def test_boundary_slight(self):
        from app.posture.classifier import PostureStatus, classify
        assert classify(85.0) == PostureStatus.SLIGHT


# ── Geometry helpers ───────────────────────────────────────────────────────

class TestGeometry:
    def test_distance(self):
        from app.posture.detector import get_distance
        assert abs(get_distance((0, 0), (3, 4)) - 5.0) < 1e-6

    def test_midpoint(self):
        from app.posture.detector import get_midpoint
        assert get_midpoint((0, 0), (4, 4)) == (2, 2)

    def test_angle_vertical(self):
        """Nose directly above mid-shoulder → 0°."""
        from app.posture.detector import get_angle
        assert get_angle((10, 0), (10, 50)) == pytest.approx(0.0, abs=1e-4)
