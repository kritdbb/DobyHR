"""
FAISS Index Management for Face Recognition
Builds and searches the FAISS index from UserFaceImage records.
"""

import os
import json
import logging
import numpy as np

logger = logging.getLogger("hr-api")

DIMENSION = 512  # ArcFace embedding dimension
FAISS_DIR = "/app/uploads/faiss"
FAISS_INDEX_PATH = os.path.join(FAISS_DIR, "faiss_index.bin")
FAISS_METADATA_PATH = os.path.join(FAISS_DIR, "faiss_metadata.json")

# Global state — loaded once, rebuilt on face image upload/delete
_index = None
_metadata = {}
_face_app = None


def _get_face_app():
    """Lazy-load InsightFace model (heavy, only load once)."""
    global _face_app
    if _face_app is None:
        logger.info("📦 Loading ArcFace model (buffalo_l)...")
        from insightface.app import FaceAnalysis
        _face_app = FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
        logger.info("✅ ArcFace model loaded")
    return _face_app


def rebuild_index():
    """
    Rebuild FAISS index from all UserFaceImage records in the database.
    Called after face image upload or delete.
    """
    global _index, _metadata
    import faiss
    import cv2
    from app.core.database import SessionLocal
    from app.models.face_image import UserFaceImage
    from app.models.user import User
    from app.core.config import settings

    logger.info("🔨 Rebuilding FAISS index...")

    db = SessionLocal()
    try:
        face_images = db.query(UserFaceImage).all()
        if not face_images:
            logger.info("⚠️ No face images found, creating empty index")
            _index = faiss.IndexFlatIP(DIMENSION)
            _metadata = {}
            _save_index()
            return

        app = _get_face_app()
        index = faiss.IndexFlatIP(DIMENSION)
        metadata = {}
        face_id = 0

        for face_img in face_images:
            # Resolve absolute path
            rel_path = face_img.image_path.lstrip("/uploads/")
            abs_path = os.path.join(settings.UPLOAD_DIR, rel_path)

            if not os.path.exists(abs_path):
                logger.warning(f"  ❌ File not found: {abs_path}")
                continue

            img = cv2.imread(abs_path)
            if img is None:
                logger.warning(f"  ❌ Cannot read image: {abs_path}")
                continue

            faces = app.get(img)
            if len(faces) == 0:
                logger.warning(f"  ❌ No face detected in: {abs_path}")
                continue

            # Use first face found
            embedding = faces[0].embedding
            embedding = embedding / np.linalg.norm(embedding)
            embedding = embedding.astype('float32').reshape(1, -1)

            index.add(embedding)

            # Get user info
            user = db.query(User).filter(User.id == face_img.user_id).first()
            user_name = f"{user.name} {user.surname}" if user else f"User#{face_img.user_id}"

            metadata[str(face_id)] = {
                "user_id": face_img.user_id,
                "name": user_name,
                "image_path": face_img.image_path,
            }

            logger.info(f"  ✅ [{face_id}] {user_name} ({face_img.image_path})")
            face_id += 1

        _index = index
        _metadata = metadata
        _save_index()
        logger.info(f"✅ FAISS index rebuilt: {index.ntotal} face embeddings")

    except Exception as e:
        logger.error(f"❌ FAISS rebuild error: {e}", exc_info=True)
    finally:
        db.close()


def _save_index():
    """Save FAISS index and metadata to disk."""
    import faiss
    os.makedirs(FAISS_DIR, exist_ok=True)
    if _index is not None:
        faiss.write_index(_index, FAISS_INDEX_PATH)
    with open(FAISS_METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(_metadata, f, ensure_ascii=False, indent=2)


def load_index():
    """Load FAISS index from disk (called on startup)."""
    global _index, _metadata
    import faiss

    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FAISS_METADATA_PATH):
        try:
            _index = faiss.read_index(FAISS_INDEX_PATH)
            with open(FAISS_METADATA_PATH, 'r', encoding='utf-8') as f:
                _metadata = json.load(f)
            logger.info(f"📂 FAISS index loaded: {_index.ntotal} faces")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load FAISS index: {e}")
            _index = faiss.IndexFlatIP(DIMENSION)
            _metadata = {}
    else:
        logger.info("📂 No existing FAISS index found, will build on first face upload")
        _index = faiss.IndexFlatIP(DIMENSION)
        _metadata = {}


def search(embedding, threshold=0.5):
    """
    Search FAISS index for matching face.

    Args:
        embedding: 512-dim face embedding from InsightFace
        threshold: minimum cosine similarity (0.0 - 1.0)

    Returns:
        (user_id, confidence, name) or None if no match
    """
    if _index is None or _index.ntotal == 0:
        return None

    emb = embedding / np.linalg.norm(embedding)
    emb = emb.astype('float32').reshape(1, -1)

    scores, indices = _index.search(emb, k=1)
    score = float(scores[0][0])
    idx = int(indices[0][0])

    if score > threshold and idx >= 0:
        face_data = _metadata.get(str(idx), {})
        user_id = face_data.get("user_id")
        name = face_data.get("name", "Unknown")
        if user_id is not None:
            return user_id, score, name

    return None


def get_face_app():
    """Public accessor for the InsightFace app instance."""
    return _get_face_app()
