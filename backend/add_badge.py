import os
import sys
import shutil
import uuid
from app.core.database import SessionLocal
from app.models.badge import Badge
from app.core.config import settings

def add_badge(image_path, name, description=""):
    db = SessionLocal()
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"Error: Image not found at {image_path}")
            return
            
        # Copy image to uploads
        ext = os.path.splitext(image_path)[1]
        filename = f"badge_{uuid.uuid4().hex[:8]}{ext}"
        upload_dir = os.path.join(settings.UPLOAD_DIR, "badges")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        shutil.copy2(image_path, filepath)
        
        # Add to DB
        image_url = f"/uploads/badges/{filename}"
        badge = Badge(
            name=name,
            description=description,
            stat_str=0,
            stat_def=0,
            stat_luk=0,
            image=image_url
        )
        db.add(badge)
        db.commit()
        db.refresh(badge)
        print(f"Success! Badge '{name}' added with ID {badge.id}")
        print(f"Image URL: {image_url}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python add_badge.py <image_path> <badge_name> [description]")
        sys.exit(1)
        
    img_path = sys.argv[1]
    b_name = sys.argv[2]
    b_desc = sys.argv[3] if len(sys.argv) > 3 else ""
    
    add_badge(img_path, b_name, b_desc)
