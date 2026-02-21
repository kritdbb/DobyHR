import asyncio
import os
import shutil
import uuid
import sys
from pathlib import Path

# Need to properly initialize SQLAlchemy and FastAPI contexts if we're using the app's models directly
sys.path.append("/app")

from app.core.database import SessionLocal, Base
# Import core application models so SQLAlchemy knows about them
import pkgutil
import importlib
import app.models

# Dynamically import all modules in app.models to ensure relationships are mapped
for _, module_name, _ in pkgutil.iter_modules(app.models.__path__):
    importlib.import_module(f"app.models.{module_name}")

from app.models.badge import Badge
from app.core.config import settings

def process_badges(source_dir):
    source_path = Path(source_dir)
    if not source_path.exists() or not source_path.is_dir():
        print(f"Error: Directory not found at {source_dir}")
        return

    db = SessionLocal()
    try:
        image_files = [f for f in source_path.iterdir() if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']]
        
        if not image_files:
            print(f"No image files found in {source_dir}")
            return
            
        print(f"Found {len(image_files)} images to process.")
        
        for i, file_path in enumerate(image_files, 1):
            # Generate a generic name "S-Badge<Number>"
            # For a more advanced approach, we could use an ML model to caption the image, 
            # but since we're automating via a simple script here, we'll use a sequence.
            badge_name = f"S-Mystic{i:02d}"
            
            # Copy image to uploads
            ext = file_path.suffix
            filename = f"badge_{uuid.uuid4().hex[:8]}{ext}"
            upload_dir = Path(settings.UPLOAD_DIR) / "badges"
            os.makedirs(upload_dir, exist_ok=True)
            dest_path = upload_dir / filename
            
            # Copy first to ensure we have it
            shutil.copy2(file_path, dest_path)
            
            # Add to DB
            image_url = f"/uploads/badges/{filename}"
            badge = Badge(
                name=badge_name,
                description="A freshly forged mystic badge.",
                stat_str=0,
                stat_def=0,
                stat_luk=0,
                image=image_url
            )
            db.add(badge)
            db.commit()
            db.refresh(badge)
            
            print(f"Processed: {file_path.name} -> Badge '{badge_name}' (ID: {badge.id})")
            
            # Delete original
            os.remove(file_path)
            
        print("All badges processed successfully.")
            
    except Exception as e:
        print(f"Error during processing: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process badges from a directory.")
    parser.add_argument("source_dir", help="Directory containing badge images")
    args = parser.parse_args()
    
    process_badges(args.source_dir)
