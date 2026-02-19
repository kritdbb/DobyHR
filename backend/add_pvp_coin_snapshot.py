"""
Migration: Add coin/mana snapshot columns to pvp_battles table.
These store the players' coins and angel_coins at the moment the fight runs,
so the UI shows accurate historical data instead of live values.

Run with:  python add_pvp_coin_snapshot.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

def migrate():
    cols = {
        "a_coins": "INTEGER DEFAULT 0",
        "a_angel_coins": "INTEGER DEFAULT 0",
        "b_coins": "INTEGER DEFAULT 0",
        "b_angel_coins": "INTEGER DEFAULT 0",
    }
    for col_name, col_type in cols.items():
        with engine.connect() as conn:
            try:
                conn.execute(text(f"ALTER TABLE pvp_battles ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"  ✅ Added column: {col_name}")
            except Exception as e:
                conn.rollback()
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"  ⏭️ Column {col_name} already exists, skipping")
                else:
                    raise
    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()
