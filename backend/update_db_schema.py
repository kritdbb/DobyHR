from app.core.database import SessionLocal, engine
from sqlalchemy import text

def update_schema():
    db = SessionLocal()
    try:
        # 1. Add coins to users
        print("Checking users table...")
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0"))
            print("Added 'coins' to users.")
        except Exception as e:
            print(f"Skipping users update (likely exists): {e}")
            db.rollback()

        # 2. Add settings to companies
        print("Checking companies table...")
        try:
            db.execute(text("ALTER TABLE companies ADD COLUMN coin_on_time INTEGER DEFAULT 10"))
            print("Added 'coin_on_time' to companies.")
        except Exception as e:
            print(f"Skipping companies update: {e}")
            db.rollback()
            
        try:
            db.execute(text("ALTER TABLE companies ADD COLUMN coin_late_penalty INTEGER DEFAULT 5"))
            print("Added 'coin_late_penalty' to companies.")
        except Exception as e:
            print(f"Skipping companies update: {e}")
            db.rollback()

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    update_schema()
