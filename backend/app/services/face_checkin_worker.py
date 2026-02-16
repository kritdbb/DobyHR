"""
Face Check-in Worker — RTSP stream processing with face tracking.

Connects to RTSP cameras, detects/recognizes faces, and triggers
check-in when a face is seen for N consecutive frames.
"""

import os
import json
import time
import base64
import logging
import threading
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger("hr-api")

# Track which users already checked in today (reset daily)
_checked_in_today = set()
_checked_in_date = None

# Global stop flag
_stop_event = threading.Event()
_worker_threads = []


def _reset_daily_tracker():
    """Reset the daily check-in tracker if it's a new day."""
    global _checked_in_today, _checked_in_date
    now_local = datetime.utcnow() + timedelta(hours=7)
    today = now_local.date()
    if _checked_in_date != today:
        _checked_in_today = set()
        _checked_in_date = today
        logger.info(f"🔄 Face check-in tracker reset for {today}")


def _is_frontal_face(face):
    """
    Check if face is roughly frontal using landmark positions.
    Returns False if face appears to be a side profile.
    """
    if face.landmark_2d_106 is not None:
        landmarks = face.landmark_2d_106
        # Use nose tip and face edges to estimate yaw
        # landmarks[38] = nose tip, landmarks[0] = left face edge, landmarks[32] = right face edge
        nose_x = landmarks[86][0]   # nose tip
        left_x = landmarks[0][0]    # left contour
        right_x = landmarks[32][0]  # right contour
        face_width = right_x - left_x
        if face_width < 1:
            return False
        # Nose position ratio (0.5 = perfectly frontal)
        nose_ratio = (nose_x - left_x) / face_width
        # Allow ~30 degree yaw: ratio between 0.3 and 0.7
        return 0.3 <= nose_ratio <= 0.7

    # Fallback: use 5-point landmarks if available
    if face.landmark_3d_68 is not None or (hasattr(face, 'kps') and face.kps is not None):
        kps = face.kps if hasattr(face, 'kps') and face.kps is not None else None
        if kps is not None and len(kps) >= 5:
            # kps: [left_eye, right_eye, nose, left_mouth, right_mouth]
            left_eye_x = kps[0][0]
            right_eye_x = kps[1][0]
            nose_x = kps[2][0]
            eye_width = right_eye_x - left_eye_x
            if eye_width < 1:
                return False
            nose_ratio = (nose_x - left_eye_x) / eye_width
            return 0.2 <= nose_ratio <= 0.8

    # Can't determine — assume frontal
    return True


def _process_rtsp_stream(rtsp_url, stream_idx, settings):
    """
    Process a single RTSP stream. Run in a dedicated thread.

    Args:
        rtsp_url: RTSP URL string
        stream_idx: Index for logging
        settings: dict with threshold, min_frames, min_height, end_time
    """
    import cv2
    from app.services.face_service import get_face_app, search

    threshold = settings["threshold"]
    min_consecutive = settings["min_frames"]
    min_height = settings["min_height"]
    end_time_str = settings["end_time"]

    logger.info(f"📹 [Stream {stream_idx}] Connecting to {rtsp_url}")

    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        logger.error(f"❌ [Stream {stream_idx}] Cannot open RTSP: {rtsp_url}")
        return

    logger.info(f"✅ [Stream {stream_idx}] Connected. Processing faces...")

    app = get_face_app()
    inference_interval = 1.0 / 6  # 6 fps
    last_inference_time = 0

    # Face tracking: user_id -> { consecutive_count, last_seen_frame, best_frame, best_score }
    face_tracker = {}
    frame_number = 0
    miss_tolerance = 3  # Allow 3 frames gap before resetting

    try:
        while not _stop_event.is_set():
            # Check time window
            now_local = datetime.utcnow() + timedelta(hours=7)
            end_parts = end_time_str.split(":")
            end_hour, end_minute = int(end_parts[0]), int(end_parts[1])
            if now_local.hour > end_hour or (now_local.hour == end_hour and now_local.minute > end_minute):
                logger.info(f"⏰ [Stream {stream_idx}] End time reached ({end_time_str}). Stopping.")
                break

            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.5)
                continue

            current_time = time.time()
            if (current_time - last_inference_time) < inference_interval:
                continue

            last_inference_time = current_time
            frame_number += 1
            _reset_daily_tracker()

            # Detect faces
            try:
                faces = app.get(frame)
            except Exception as e:
                logger.warning(f"⚠️ [Stream {stream_idx}] Face detection error: {e}")
                continue

            seen_user_ids = set()

            for face in faces:
                x1, y1, x2, y2 = face.bbox.astype(int)
                face_height = y2 - y1

                # Filter: face height
                if face_height < min_height:
                    continue

                # Filter: frontal face
                if not _is_frontal_face(face):
                    continue

                # Recognize face
                result = search(face.embedding, threshold)
                if result is None:
                    continue

                user_id, confidence, name = result
                seen_user_ids.add(user_id)

                # Skip if already checked in today
                if user_id in _checked_in_today:
                    continue

                # Update tracker
                if user_id not in face_tracker:
                    face_tracker[user_id] = {
                        "consecutive_count": 0,
                        "last_seen_frame": frame_number,
                        "best_frame": None,
                        "best_score": 0.0,
                        "name": name,
                    }

                tracker = face_tracker[user_id]

                # Check if consecutive (allow miss_tolerance gap)
                if frame_number - tracker["last_seen_frame"] <= miss_tolerance:
                    tracker["consecutive_count"] += 1
                else:
                    tracker["consecutive_count"] = 1  # Reset

                tracker["last_seen_frame"] = frame_number

                # Keep best frame (highest confidence)
                if confidence > tracker["best_score"]:
                    tracker["best_score"] = confidence
                    # Crop and encode face region from frame
                    h_pad = int(face_height * 0.3)
                    w_pad = int((x2 - x1) * 0.3)
                    cy1 = max(0, y1 - h_pad)
                    cy2 = min(frame.shape[0], y2 + h_pad)
                    cx1 = max(0, x1 - w_pad)
                    cx2 = min(frame.shape[1], x2 + w_pad)
                    face_crop = frame[cy1:cy2, cx1:cx2]
                    _, buffer = cv2.imencode('.jpg', face_crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    tracker["best_frame"] = base64.b64encode(buffer).decode('utf-8')

                # Check if threshold met for check-in
                if tracker["consecutive_count"] >= min_consecutive:
                    logger.info(
                        f"✅ [Stream {stream_idx}] CHECK-IN triggered: "
                        f"{name} (user_id={user_id}, confidence={confidence:.3f}, "
                        f"frames={tracker['consecutive_count']})"
                    )

                    # Trigger check-in
                    _do_face_checkin(
                        user_id=user_id,
                        confidence=tracker["best_score"],
                        snapshot_b64=tracker["best_frame"],
                    )
                    _checked_in_today.add(user_id)
                    del face_tracker[user_id]

            # Clean up stale trackers (not seen for too long)
            stale = [
                uid for uid, t in face_tracker.items()
                if frame_number - t["last_seen_frame"] > miss_tolerance * 2
            ]
            for uid in stale:
                del face_tracker[uid]

    except Exception as e:
        logger.error(f"❌ [Stream {stream_idx}] Worker error: {e}", exc_info=True)
    finally:
        cap.release()
        logger.info(f"📹 [Stream {stream_idx}] Stream closed.")


def _do_face_checkin(user_id, confidence, snapshot_b64):
    """Call the face check-in endpoint internally."""
    from app.core.database import SessionLocal
    from app.models.attendance import Attendance
    from app.models.company import Company
    from app.models.user import User
    from app.models.reward import CoinLog
    from app.core.config import settings
    import uuid

    db = SessionLocal()
    try:
        now_local = datetime.utcnow() + timedelta(hours=7)
        today_local = now_local.date()

        # Check duplicate
        day_start_utc = datetime.combine(today_local, datetime.min.time()) - timedelta(hours=7)
        day_end_utc = datetime.combine(today_local, datetime.max.time()) - timedelta(hours=7)

        existing = db.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.timestamp >= day_start_utc,
            Attendance.timestamp <= day_end_utc
        ).first()

        if existing:
            logger.info(f"  ⏭️ User {user_id} already checked in today, skipping")
            return

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"  ⚠️ User {user_id} not found")
            return

        # Check working day
        DAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
        if user.working_days:
            day_code = DAY_MAP.get(today_local.weekday(), "")
            user_working_days = [d.strip().lower() for d in user.working_days.split(",")]
            if day_code not in user_working_days:
                logger.info(f"  ⏭️ Not a working day for {user.name}")
                return

        # Save snapshot
        snapshot_path = None
        if snapshot_b64:
            try:
                img_data = base64.b64decode(snapshot_b64)
                snapshot_filename = f"face_checkin_{user_id}_{uuid.uuid4().hex[:8]}.jpg"
                snapshot_dir = os.path.join(settings.UPLOAD_DIR, "face_checkins")
                os.makedirs(snapshot_dir, exist_ok=True)
                with open(os.path.join(snapshot_dir, snapshot_filename), "wb") as f:
                    f.write(img_data)
                snapshot_path = f"/uploads/face_checkins/{snapshot_filename}"
            except Exception as e:
                logger.warning(f"  ⚠️ Failed to save snapshot: {e}")

        # Determine status
        from datetime import time as dt_time
        check_in_time = now_local.time()
        status = "present"
        start = user.work_start_time or dt_time(9, 0)
        start_minutes = start.hour * 60 + start.minute
        checkin_minutes = check_in_time.hour * 60 + check_in_time.minute
        diff = checkin_minutes - start_minutes

        if diff > 60:
            status = "absent"
        elif diff > 0:
            status = "late"

        # Get company location
        company = db.query(Company).first()
        lat = company.latitude if company else 0.0
        lon = company.longitude if company else 0.0

        attendance = Attendance(
            user_id=user_id,
            timestamp=datetime.utcnow(),
            latitude=lat,
            longitude=lon,
            status=status,
            check_in_method="face",
            face_image_path=snapshot_path,
            face_confidence=confidence,
        )
        db.add(attendance)

        # Coin logic
        coin_change = 0
        coin_reason = ""
        if company:
            if status == "absent" and company.coin_absent_penalty:
                coin_change = -company.coin_absent_penalty
                coin_reason = "Absent (face check-in >1hr late)"
            elif status == "late" and company.coin_late_penalty:
                coin_change = -company.coin_late_penalty
                coin_reason = "Late (face check-in)"
            elif status == "present" and company.coin_on_time:
                coin_change = company.coin_on_time
                coin_reason = "On-time (face check-in)"

            if coin_change != 0:
                user.coins += coin_change
                db.add(CoinLog(
                    user_id=user_id,
                    amount=coin_change,
                    reason=coin_reason,
                    created_by="Face Recognition"
                ))

        db.commit()
        logger.info(
            f"📸 Face check-in recorded: {user.name} {user.surname} — "
            f"{status} (confidence: {confidence:.3f}, coins: {coin_change:+d})"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Face check-in DB error: {e}", exc_info=True)
    finally:
        db.close()


def run():
    """
    Main entry point. Called by the scheduler.
    Reads RTSP URLs and settings from DB, starts worker threads.
    """
    global _worker_threads
    from app.core.database import SessionLocal
    from app.models.company import Company
    from app.services.face_service import load_index, _index

    # Check if already running
    if _worker_threads and any(t.is_alive() for t in _worker_threads):
        return  # Already running

    _stop_event.clear()
    _reset_daily_tracker()

    db = SessionLocal()
    try:
        company = db.query(Company).first()
        if not company:
            return

        # Check time window
        now_local = datetime.utcnow() + timedelta(hours=7)
        start_time_str = company.face_start_time or "06:00"
        end_time_str = company.face_end_time or "10:30"

        start_parts = start_time_str.split(":")
        end_parts = end_time_str.split(":")
        start_hour, start_minute = int(start_parts[0]), int(start_parts[1])
        end_hour, end_minute = int(end_parts[0]), int(end_parts[1])

        current_minutes = now_local.hour * 60 + now_local.minute
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute

        if current_minutes < start_minutes or current_minutes > end_minutes:
            return  # Outside time window

        # Get RTSP URLs
        rtsp_urls_raw = company.face_rtsp_urls
        if not rtsp_urls_raw:
            return

        try:
            rtsp_urls = json.loads(rtsp_urls_raw)
            if not isinstance(rtsp_urls, list) or len(rtsp_urls) == 0:
                return
        except (json.JSONDecodeError, TypeError):
            return

        # Load FAISS index if not loaded
        if _index is None or _index.ntotal == 0:
            load_index()
            from app.services.face_service import _index as loaded_index
            if loaded_index is None or loaded_index.ntotal == 0:
                logger.info("⚠️ FAISS index empty, skipping face recognition")
                return

        settings = {
            "threshold": company.face_confidence_threshold or 0.5,
            "min_frames": company.face_min_consecutive_frames or 20,
            "min_height": company.face_min_face_height or 50,
            "end_time": end_time_str,
        }

        logger.info(f"🚀 Starting face recognition on {len(rtsp_urls)} stream(s)...")

        _worker_threads = []
        for idx, url in enumerate(rtsp_urls):
            url = url.strip()
            if not url:
                continue
            t = threading.Thread(
                target=_process_rtsp_stream,
                args=(url, idx, settings),
                daemon=True,
                name=f"face-stream-{idx}"
            )
            t.start()
            _worker_threads.append(t)

    finally:
        db.close()


def stop():
    """Stop all running worker threads."""
    _stop_event.set()
    for t in _worker_threads:
        t.join(timeout=5)
    _worker_threads.clear()
    logger.info("🛑 Face recognition workers stopped")
