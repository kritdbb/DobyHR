import sys
sys.path.append("/app")

from app.core.database import SessionLocal, Base
import pkgutil
import importlib
import app.models

for _, module_name, _ in pkgutil.iter_modules(app.models.__path__):
    importlib.import_module(f"app.models.{module_name}")

from app.models.badge import Badge

# Map of ID to new name
badge_names = {
    11: "S-Necromancer",
    12: "S-Forest Druid",
    13: "S-Sorceress",
    14: "S-Hellfire Warden",
    15: "S-Void Relic",
    16: "S-Crimson Skull",
    17: "S-Hydra Hunter",
    18: "S-Inferno Blade",
    19: "S-Dragon Slayer",
    20: "S-Frost Crystal",
    21: "S-Golden Aegis",
    22: "S-Pot of Gold",
    23: "S-Dark Rider",
    24: "S-Archangel",
    25: "S-World Tree"
}

db = SessionLocal()
try:
    updated = 0
    for b_id, b_name in badge_names.items():
        # Using S-Mystic as a fallback check but we know the IDs
        badge = db.query(Badge).filter(Badge.id == b_id).first()
        if badge:
            badge.name = b_name
            updated += 1
            print(f"Updated badge ID {b_id} to {b_name}")
        else:
            print(f"Badge ID {b_id} not found!")

    db.commit()
    print(f"Successfully updated {updated} badges.")
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
