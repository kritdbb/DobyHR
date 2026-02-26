"""
Bulk update DB references from .png/.jpg to .webp (images already compressed).
Run inside the backend container: python /app/scripts/compress_existing.py
"""
import os
import sys
sys.path.insert(0, "/app")

UPLOAD_ROOT = "/app/uploads"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}


def update_db_references():
    """Update all image paths in DB from .png/.jpg to .webp using raw SQL"""
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        updated = 0

        # Update user images
        rows = conn.execute(text("SELECT id, image FROM users WHERE image IS NOT NULL")).fetchall()
        for row in rows:
            uid, img = row
            if img:
                base, ext = os.path.splitext(img)
                if ext.lower() in EXTENSIONS:
                    new_path = base + ".webp"
                    full_path = UPLOAD_ROOT + new_path.replace("/uploads", "")
                    if os.path.exists(full_path):
                        conn.execute(text("UPDATE users SET image = :img WHERE id = :uid"), {"img": new_path, "uid": uid})
                        updated += 1
                        print(f"  👤 User {uid}: {img} → {new_path}")

        # Update user card_bg
        try:
            rows = conn.execute(text("SELECT id, card_bg FROM users WHERE card_bg IS NOT NULL")).fetchall()
            for row in rows:
                uid, bg = row
                if bg and not bg.startswith("http"):
                    base, ext = os.path.splitext(bg)
                    if ext.lower() in EXTENSIONS:
                        new_path = base + ".webp"
                        full_path = UPLOAD_ROOT + new_path.replace("/uploads", "")
                        if os.path.exists(full_path):
                            conn.execute(text("UPDATE users SET card_bg = :bg WHERE id = :uid"), {"bg": new_path, "uid": uid})
                            updated += 1
                            print(f"  🎨 User {uid} bg: {bg} → {new_path}")
        except Exception as e:
            print(f"  ⚠️ card_bg: {e}")

        # Update reward images
        try:
            rows = conn.execute(text("SELECT id, image FROM rewards WHERE image IS NOT NULL")).fetchall()
            for row in rows:
                rid, img = row
                if img:
                    base, ext = os.path.splitext(img)
                    if ext.lower() in EXTENSIONS:
                        new_path = base + ".webp"
                        full_path = UPLOAD_ROOT + new_path.replace("/uploads", "")
                        if os.path.exists(full_path):
                            conn.execute(text("UPDATE rewards SET image = :img WHERE id = :rid"), {"img": new_path, "rid": rid})
                            updated += 1
                            print(f"  🎁 Reward {rid}: {img} → {new_path}")
        except Exception as e:
            print(f"  ⚠️ Rewards table: {e}")

        # Update badge images
        try:
            rows = conn.execute(text("SELECT id, image FROM badges WHERE image IS NOT NULL")).fetchall()
            for row in rows:
                bid, img = row
                if img:
                    base, ext = os.path.splitext(img)
                    if ext.lower() in EXTENSIONS:
                        new_path = base + ".webp"
                        full_path = UPLOAD_ROOT + new_path.replace("/uploads", "")
                        if os.path.exists(full_path):
                            conn.execute(text("UPDATE badges SET image = :img WHERE id = :bid"), {"img": new_path, "bid": bid})
                            updated += 1
                            print(f"  🏅 Badge {bid}: {img} → {new_path}")
        except Exception as e:
            print(f"  ⚠️ Badges table: {e}")

        # Update fortune wheel images
        try:
            rows = conn.execute(text("SELECT id, image FROM fortune_wheels WHERE image IS NOT NULL")).fetchall()
            for row in rows:
                fid, img = row
                if img:
                    base, ext = os.path.splitext(img)
                    if ext.lower() in EXTENSIONS:
                        new_path = base + ".webp"
                        full_path = UPLOAD_ROOT + new_path.replace("/uploads", "")
                        if os.path.exists(full_path):
                            conn.execute(text("UPDATE fortune_wheels SET image = :img WHERE id = :fid"), {"img": new_path, "fid": fid})
                            updated += 1
                            print(f"  🎡 Wheel {fid}: {img} → {new_path}")
        except Exception as e:
            print(f"  ⚠️ Fortune wheels: {e}")

        # Update badge_shop artifact images  
        try:
            rows = conn.execute(text("SELECT id, image FROM artifacts WHERE image IS NOT NULL")).fetchall()
            for row in rows:
                aid, img = row
                if img:
                    base, ext = os.path.splitext(img)
                    if ext.lower() in EXTENSIONS:
                        new_path = base + ".webp"
                        full_path = UPLOAD_ROOT + new_path.replace("/uploads", "")
                        if os.path.exists(full_path):
                            conn.execute(text("UPDATE artifacts SET image = :img WHERE id = :aid"), {"img": new_path, "aid": aid})
                            updated += 1
                            print(f"  ✨ Artifact {aid}: {img} → {new_path}")
        except Exception as e:
            print(f"  ⚠️ Artifacts table: {e}")

        conn.commit()
        print(f"\n📝 Updated {updated} DB references to .webp")

    # Show final uploads size
    total_size = 0
    for dirpath, _, filenames in os.walk(UPLOAD_ROOT):
        for fname in filenames:
            total_size += os.path.getsize(os.path.join(dirpath, fname))
    print(f"📦 Total uploads size now: {total_size/1024/1024:.1f} MB")


if __name__ == "__main__":
    print("📝 Updating DB references to .webp...")
    update_db_references()
