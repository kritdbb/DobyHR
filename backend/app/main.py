import os
import sys
import time
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.database import engine, Base
from app.core.config import settings
from app.api.endpoints import company, users, approval, auth, attendance, leaves, rewards, reports, absent_check, approval_pattern, work_requests, badges, fitbit, badge_quests, fortune_wheel, expenses, face_test, social, pvp, badge_shop, sync, holidays, locations
from app.models import user as user_model, company as company_model, approval as approval_model, attendance as attendance_model, leave as leave_model, reward as reward_model, approval_pattern as approval_pattern_model, work_request as work_request_model, badge as badge_model, fitbit as fitbit_model, step_rewards as step_rewards_model, badge_quest as badge_quest_model, fortune_wheel as fortune_wheel_model, expense as expense_model, face_image as face_image_model, social as social_model, pvp as pvp_model, artifact as artifact_model, badge_shop as badge_shop_model, holiday as holiday_model, location as location_model
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.scheduler import start_scheduler

# ── Logging Setup ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("hr-api")

# Create all tables (with retry)
for _attempt in range(10):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables ready")
        break
    except Exception as _e:
        logger.warning(f"⏳ create_all failed (attempt {_attempt+1}/10): {_e}")
        time.sleep(3)



def auto_migrate():
    """
    Model-driven auto-migration: reads all SQLAlchemy models registered on Base,
    compares their columns with the actual database, and ADDs any missing columns.

    SAFE: Only ADDs columns, never DROPs or renames anything.
    IDEMPOTENT: Can run any number of times without issues.
    """
    from sqlalchemy import text, inspect as sa_inspect
    import sqlalchemy as sa

    def _sa_type_to_ddl(col):
        """Convert a SQLAlchemy column type to a PostgreSQL DDL type string."""
        t = col.type
        if isinstance(t, sa.String):
            return f"VARCHAR({t.length})" if t.length else "VARCHAR"
        if isinstance(t, sa.Text):
            return "TEXT"
        if isinstance(t, sa.Integer):
            return "INTEGER"
        if isinstance(t, sa.BigInteger):
            return "BIGINT"
        if isinstance(t, sa.Float):
            return "FLOAT"
        if isinstance(t, sa.Boolean):
            return "BOOLEAN"
        if isinstance(t, sa.Date):
            return "DATE"
        if isinstance(t, sa.Time):
            return "TIME"
        if isinstance(t, sa.DateTime):
            return "TIMESTAMP"
        if isinstance(t, sa.Enum):
            return t.name if t.name else "VARCHAR"
        if isinstance(t, sa.JSON):
            return "JSON"
        if isinstance(t, sa.Numeric):
            return f"NUMERIC({t.precision},{t.scale})" if t.precision else "NUMERIC"
        # Fallback
        return str(t)

    def _default_clause(col):
        """Build DEFAULT clause for a column if it has a server_default or default."""
        if col.server_default is not None:
            return f" DEFAULT {col.server_default.arg}"
        if col.default is not None and col.default.is_scalar:
            val = col.default.arg
            if isinstance(val, bool):
                return f" DEFAULT {'TRUE' if val else 'FALSE'}"
            if isinstance(val, (int, float)):
                return f" DEFAULT {val}"
            if isinstance(val, str):
                return f" DEFAULT '{val}'"
        return ""

    try:
        inspector = sa_inspect(engine)
        db_tables = set(inspector.get_table_names())
        added = 0

        # Iterate over all models registered on Base
        for mapper in Base.registry.mappers:
            model = mapper.class_
            table = model.__table__

            if table.name not in db_tables:
                # Table doesn't exist — create_all should handle it, skip
                continue

            # Get existing column names from the actual database
            db_columns = {col["name"] for col in inspector.get_columns(table.name)}

            # Compare with model columns
            for col_name, col_obj in table.columns.items():
                if col_name not in db_columns:
                    ddl_type = _sa_type_to_ddl(col_obj)
                    default = _default_clause(col_obj)
                    sql = f'ALTER TABLE {table.name} ADD COLUMN IF NOT EXISTS "{col_name}" {ddl_type}{default}'
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(sql))
                            conn.commit()
                        logger.info(f"  ➕ {table.name}.{col_name} ({ddl_type})")
                        added += 1
                    except Exception as col_err:
                        logger.warning(f"  ⚠️ Failed to add {table.name}.{col_name}: {col_err}")

        # Extra migrations that can't be auto-detected (nullable changes, enum values, etc.)
        extra_migrations = [
            "ALTER TABLE badge_quests ALTER COLUMN badge_id DROP NOT NULL",
            "ALTER TYPE expensetype ADD VALUE IF NOT EXISTS 'CENTER'",
            "ALTER TABLE attendance ALTER COLUMN latitude DROP NOT NULL",
            "ALTER TABLE attendance ALTER COLUMN longitude DROP NOT NULL",
            "ALTER TYPE leavestatus ADD VALUE IF NOT EXISTS 'pending_evidence'",
            "ALTER TYPE leavestatus ADD VALUE IF NOT EXISTS 'PENDING_EVIDENCE'",
        ]
        with engine.connect() as conn:
            for sql in extra_migrations:
                try:
                    conn.execute(text(sql))
                except Exception:
                    pass  # Already applied or not applicable
            conn.commit()

        logger.info(f"✅ Auto-migration complete — {added} columns added")
    except Exception as e:
        logger.warning(f"⚠️ Auto-migration error: {e}")


auto_migrate()

app = FastAPI(title="HR System API", version="1.0.0")


# ── Request Logging Middleware ─────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    method = request.method
    path = request.url.path
    query = str(request.url.query)
    full_path = f"{path}?{query}" if query else path

    try:
        response = await call_next(request)
        duration = round((time.time() - start) * 1000)
        status = response.status_code

        if status >= 500:
            logger.error(f"❌ {method} {full_path} → {status} ({duration}ms)")
        elif status >= 400:
            logger.warning(f"⚠️  {method} {full_path} → {status} ({duration}ms)")
        else:
            logger.info(f"✅ {method} {full_path} → {status} ({duration}ms)")

        return response
    except Exception as exc:
        duration = round((time.time() - start) * 1000)
        logger.error(f"💥 {method} {full_path} → EXCEPTION ({duration}ms)")
        logger.error(traceback.format_exc())
        return JSONResponse(status_code=500, content={"detail": str(exc)})


# ── Global Exception Handler ──────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"💥 Unhandled exception on {request.method} {request.url.path}")
    logger.error(traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(company.router)
app.include_router(users.router)
app.include_router(approval.router)
app.include_router(attendance.router)
app.include_router(leaves.router)
app.include_router(rewards.router)
app.include_router(reports.router)
app.include_router(absent_check.router)
app.include_router(approval_pattern.router)
app.include_router(work_requests.router)
app.include_router(badges.router)
app.include_router(fitbit.router)
app.include_router(badge_quests.router)
app.include_router(fortune_wheel.router)
app.include_router(expenses.router)
app.include_router(face_test.router)
app.include_router(social.router)
app.include_router(pvp.router)
app.include_router(badge_shop.router)
app.include_router(sync.router)
app.include_router(holidays.router)
app.include_router(locations.router)


@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        # Create default admin if not exists
        user = db.query(user_model.User).filter(user_model.User.email == "admin@admin.com").first()
        if not user:
            print("Creating default admin user...")
            admin_user = user_model.User(
                name="Admin",
                surname="User",
                email="admin@admin.com",
                hashed_password=get_password_hash("admin"),
                role=user_model.UserRole.GOD,
                position="System Admin",
                sick_leave_days=30,
                business_leave_days=30,
                vacation_leave_days=30
            )
            db.add(admin_user)
            db.commit()
            print("Default admin created: admin@admin.com / admin")
    except Exception as e:
        print(f"Error creating default admin: {e}")
    finally:
        db.close()
    
    # Start scheduler for auto coin/angel distribution
    start_scheduler()



@app.get("/")
def read_root():
    return {"message": "Welcome to HR System API", "version": "1.0.0"}
