import sys
sys.path.append("/app")
from app.core.database import SessionLocal, Base
import pkgutil
import importlib
import app.models

for _, module_name, _ in pkgutil.iter_modules(app.models.__path__):
    importlib.import_module(f"app.models.{module_name}")

from app.models.badge import Badge
import json

db = SessionLocal()
try:
    badges = db.query(Badge).filter(Badge.name.like('S-Mystic%')).all()
    out = []
    for b in badges:
        out.append({"id": b.id, "name": b.name, "image": b.image})
    
    with open("/app/recent_badges.json", "w") as f:
        json.dump(out, f, indent=2)
finally:
    db.close()
