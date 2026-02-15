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
from app.api.endpoints import company, users, approval, auth, attendance, leaves, rewards, reports, absent_check, approval_pattern, work_requests, badges, fitbit, badge_quests, fortune_wheel, expenses
from app.models import user as user_model, company as company_model, approval as approval_model, attendance as attendance_model, leave as leave_model, reward as reward_model, approval_pattern as approval_pattern_model, work_request as work_request_model, badge as badge_model, fitbit as fitbit_model, step_rewards as step_rewards_model, badge_quest as badge_quest_model, fortune_wheel as fortune_wheel_model, expense as expense_model
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

# Create all tables
Base.metadata.create_all(bind=engine)

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
