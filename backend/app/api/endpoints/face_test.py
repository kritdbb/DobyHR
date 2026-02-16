"""
CCTV Test Stream — MJPEG endpoint for previewing RTSP cameras with face annotations.
"""
import time
import logging

import cv2
import numpy as np
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger("hr-api")
router = APIRouter(prefix="/api/face", tags=["face-test"])


def _verify_token(token: str):
    """Verify JWT token passed as query param (needed because <img src> can't set headers)."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def _generate_frames(rtsp_url: str):
    """Generator yielding MJPEG frames with face bounding boxes and annotations."""
    from app.services.face_service import get_face_app, search

    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        # Return a single error frame
        err = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(err, "Cannot connect to RTSP stream", (30, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        _, buf = cv2.imencode('.jpg', err)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
        return

    app = get_face_app()
    target_interval = 1.0 / 6  # 6 FPS

    try:
        while True:
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                break

            # Detect faces
            faces = app.get(frame)

            for face in faces:
                bbox = face.bbox.astype(int)
                x1, y1, x2, y2 = bbox
                face_h = y2 - y1

                # Recognise against FAISS index
                name = "Unknown"
                confidence = 0.0
                if face.embedding is not None:
                    result = search(face.embedding, threshold=0.3)
                    if result is not None:
                        _uid, confidence, name = result

                # Colours: green=known, orange=unknown
                color = (0, 255, 0) if name != "Unknown" else (0, 165, 255)

                # Bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                # Name label above the box
                cv2.putText(frame, name, (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

                # Confidence | height label below the box
                info_text = f"{confidence:.2f} | {face_h}px"
                cv2.putText(frame, info_text, (x1, y2 + 18),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # Encode & yield
            _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')

            # Throttle to target FPS
            elapsed = time.time() - t0
            if elapsed < target_interval:
                time.sleep(target_interval - elapsed)
    finally:
        cap.release()
        logger.info(f"📹 Test stream closed for {rtsp_url}")


@router.get("/test-stream")
async def test_stream(rtsp_url: str = Query(...), token: str = Query(...)):
    """
    MJPEG stream for testing an RTSP camera with live face annotations.
    Token is passed as a query param because <img src> cannot set headers.
    """
    _verify_token(token)
    logger.info(f"📹 Starting test stream for {rtsp_url}")
    return StreamingResponse(
        _generate_frames(rtsp_url),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
