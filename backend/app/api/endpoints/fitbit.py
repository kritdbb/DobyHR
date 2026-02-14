import httpx
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.fitbit import FitbitToken, FitbitSteps
from app.models.company import Company
from app.models.step_rewards import StepReward
from app.models.reward import CoinLog
from datetime import timezone as tz

TZ_BKK = tz(timedelta(hours=7))

router = APIRouter(prefix="/api/fitbit", tags=["fitbit"])

FITBIT_AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_API_BASE = "https://api.fitbit.com"


# ── Helpers ───────────────────────────────────────────────

def _get_basic_auth():
    """Return base64-encoded client_id:client_secret for Fitbit token requests."""
    import base64
    creds = f"{settings.FITBIT_CLIENT_ID}:{settings.FITBIT_CLIENT_SECRET}"
    return base64.b64encode(creds.encode()).decode()


async def _refresh_token_if_needed(db: Session, token: FitbitToken) -> FitbitToken:
    """Refresh Fitbit access token if expired."""
    if token.expires_at > datetime.utcnow():
        return token

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            FITBIT_TOKEN_URL,
            headers={
                "Authorization": f"Basic {_get_basic_auth()}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
            },
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Fitbit token refresh failed. Please re-link your Fitbit account.")

    data = resp.json()
    token.access_token = data["access_token"]
    token.refresh_token = data["refresh_token"]
    token.expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 28800))
    db.commit()
    return token


async def _fitbit_get(token: FitbitToken, path: str):
    """Make authenticated GET request to Fitbit API."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{FITBIT_API_BASE}{path}",
            headers={"Authorization": f"Bearer {token.access_token}"},
        )
    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Fitbit token expired")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Fitbit API error: {resp.text}")
    return resp.json()


# ── Endpoints ─────────────────────────────────────────────

@router.get("/authorize")
def get_authorize_url(current_user: User = Depends(get_current_user)):
    """Return the Fitbit OAuth authorization URL."""
    url = (
        f"{FITBIT_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={settings.FITBIT_CLIENT_ID}"
        f"&redirect_uri={settings.FITBIT_REDIRECT_URI}"
        f"&scope=activity"
        f"&expires_in=604800"
    )
    return {"authorize_url": url}


@router.post("/callback")
async def handle_callback(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exchange authorization code for access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            FITBIT_TOKEN_URL,
            headers={
                "Authorization": f"Basic {_get_basic_auth()}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.FITBIT_REDIRECT_URI,
            },
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Fitbit token exchange failed: {resp.text}")

    data = resp.json()

    # Upsert token
    existing = db.query(FitbitToken).filter(FitbitToken.user_id == current_user.id).first()
    if existing:
        existing.access_token = data["access_token"]
        existing.refresh_token = data["refresh_token"]
        existing.expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 28800))
        existing.fitbit_user_id = data.get("user_id")
        existing.updated_at = datetime.utcnow()
    else:
        new_token = FitbitToken(
            user_id=current_user.id,
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.utcnow() + timedelta(seconds=data.get("expires_in", 28800)),
            fitbit_user_id=data.get("user_id"),
        )
        db.add(new_token)

    db.commit()
    return {"message": "Fitbit linked successfully"}


@router.get("/status")
def get_fitbit_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if the current user has linked their Fitbit account."""
    token = db.query(FitbitToken).filter(FitbitToken.user_id == current_user.id).first()
    return {"connected": token is not None, "fitbit_user_id": token.fitbit_user_id if token else None}


@router.post("/sync")
async def sync_steps(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch the last 7 days of step data from Fitbit and store locally."""
    token = db.query(FitbitToken).filter(FitbitToken.user_id == current_user.id).first()
    if not token:
        raise HTTPException(status_code=400, detail="Fitbit not linked. Please connect your Fitbit first.")

    token = await _refresh_token_if_needed(db, token)

    today = date.today()
    end_date = today.strftime("%Y-%m-%d")
    start_date = (today - timedelta(days=6)).strftime("%Y-%m-%d")

    data = await _fitbit_get(
        token,
        f"/1/user/-/activities/steps/date/{start_date}/{end_date}.json",
    )

    steps_list = data.get("activities-steps", [])
    synced_count = 0

    for entry in steps_list:
        step_date = datetime.strptime(entry["dateTime"], "%Y-%m-%d").date()
        step_count = int(entry["value"])

        existing = db.query(FitbitSteps).filter(
            FitbitSteps.user_id == current_user.id,
            FitbitSteps.date == step_date,
        ).first()

        if existing:
            existing.steps = step_count
            existing.synced_at = datetime.utcnow()
        else:
            db.add(FitbitSteps(
                user_id=current_user.id,
                date=step_date,
                steps=step_count,
            ))
        synced_count += 1

    db.commit()
    return {"message": f"Synced {synced_count} days of step data", "days": synced_count}


@router.get("/my-steps")
def get_my_steps(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's step history."""
    since = date.today() - timedelta(days=days - 1)
    steps = (
        db.query(FitbitSteps)
        .filter(FitbitSteps.user_id == current_user.id, FitbitSteps.date >= since)
        .order_by(FitbitSteps.date.desc())
        .all()
    )
    return [
        {"date": s.date.isoformat(), "steps": s.steps, "synced_at": s.synced_at.isoformat() if s.synced_at else None}
        for s in steps
    ]


@router.get("/leaderboard")
def get_leaderboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return top steppers for the current week (Mon–Sun)."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())

    results = (
        db.query(
            FitbitSteps.user_id,
            func.sum(FitbitSteps.steps).label("total_steps"),
        )
        .filter(FitbitSteps.date >= monday)
        .group_by(FitbitSteps.user_id)
        .order_by(func.sum(FitbitSteps.steps).desc())
        .limit(20)
        .all()
    )

    leaderboard = []
    for rank, (user_id, total_steps) in enumerate(results, 1):
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            leaderboard.append({
                "rank": rank,
                "user_id": user.id,
                "name": f"{user.name} {user.surname}",
                "image": user.image,
                "position": user.position,
                "total_steps": int(total_steps),
            })

    return leaderboard


# ── Daily / Monthly Step Goals ────────────────────────────

def _today_bkk():
    """Return today's date in GMT+7."""
    return datetime.now(TZ_BKK).date()


def _month_start_bkk():
    """Return the 1st day of the current month in GMT+7."""
    today = _today_bkk()
    return today.replace(day=1)


def _get_step_config(db: Session):
    """Load step goal config from Company table."""
    company = db.query(Company).first()
    if not company:
        return {
            "daily_target": 5000, "daily_str": 0, "daily_def": 0, "daily_luk": 0, "daily_gold": 0, "daily_mana": 0,
            "monthly_target": 75000, "monthly_str": 0, "monthly_def": 0, "monthly_luk": 0, "monthly_gold": 1, "monthly_mana": 0,
        }
    return {
        "daily_target": company.step_daily_target or 5000,
        "daily_str": company.step_daily_str or 0,
        "daily_def": company.step_daily_def or 0,
        "daily_luk": company.step_daily_luk or 0,
        "daily_gold": company.step_daily_gold or 0,
        "daily_mana": company.step_daily_mana or 0,
        "monthly_target": company.step_monthly_target or 0,
        "monthly_str": company.step_monthly_str or 0,
        "monthly_def": company.step_monthly_def or 0,
        "monthly_luk": company.step_monthly_luk or 0,
        "monthly_gold": company.step_monthly_gold or 0,
        "monthly_mana": company.step_monthly_mana or 0,
    }


@router.get("/goals")
def get_step_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return current daily and monthly goal status."""
    today = _today_bkk()
    month_start = _month_start_bkk()
    cfg = _get_step_config(db)

    # Today's steps
    today_entry = db.query(FitbitSteps).filter(
        FitbitSteps.user_id == current_user.id,
        FitbitSteps.date == today,
    ).first()
    today_steps = today_entry.steps if today_entry else 0

    # Daily goal
    daily_claimed = db.query(StepReward).filter(
        StepReward.user_id == current_user.id,
        StepReward.reward_date == today,
        StepReward.reward_type == "daily",
    ).first() is not None

    daily_goal = {
        "target": cfg["daily_target"],
        "str": cfg["daily_str"],
        "def": cfg["daily_def"],
        "luk": cfg["daily_luk"],
        "gold": cfg["daily_gold"],
        "mana": cfg["daily_mana"],
        "reached": today_steps >= cfg["daily_target"],
        "claimed": daily_claimed,
    }

    # Monthly total
    monthly_steps_row = db.query(func.coalesce(func.sum(FitbitSteps.steps), 0)).filter(
        FitbitSteps.user_id == current_user.id,
        FitbitSteps.date >= month_start,
    ).scalar()
    monthly_steps = int(monthly_steps_row) if monthly_steps_row else 0

    monthly_claimed = db.query(StepReward).filter(
        StepReward.user_id == current_user.id,
        StepReward.reward_date == month_start,
        StepReward.reward_type == "monthly",
    ).first() is not None

    monthly_goal = {
        "target": cfg["monthly_target"],
        "str": cfg["monthly_str"],
        "def": cfg["monthly_def"],
        "luk": cfg["monthly_luk"],
        "gold": cfg["monthly_gold"],
        "mana": cfg["monthly_mana"],
        "reached": monthly_steps >= cfg["monthly_target"] if cfg["monthly_target"] > 0 else False,
        "claimed": monthly_claimed,
        "enabled": cfg["monthly_target"] > 0,
    }

    return {
        "today_steps": today_steps,
        "today_date": today.isoformat(),
        "daily_goal": daily_goal,
        "monthly_steps": monthly_steps,
        "monthly_goal": monthly_goal,
    }


@router.post("/claim-reward")
def claim_step_reward(
    reward_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Claim a step-based reward (daily or monthly)."""
    today = _today_bkk()
    cfg = _get_step_config(db)

    if reward_type == "daily":
        threshold = cfg["daily_target"]
        reward_date = today
        rewards = {k: cfg[f"daily_{k}"] for k in ["str", "def", "luk", "gold", "mana"]}
    elif reward_type == "monthly":
        threshold = cfg["monthly_target"]
        reward_date = _month_start_bkk()
        rewards = {k: cfg[f"monthly_{k}"] for k in ["str", "def", "luk", "gold", "mana"]}
        if threshold <= 0:
            raise HTTPException(status_code=400, detail="Monthly goal is disabled")
    else:
        raise HTTPException(status_code=400, detail="Invalid reward type (daily or monthly)")

    # Check already claimed
    existing = db.query(StepReward).filter(
        StepReward.user_id == current_user.id,
        StepReward.reward_date == reward_date,
        StepReward.reward_type == reward_type,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Reward already claimed")

    # Check steps meet threshold
    if reward_type == "daily":
        entry = db.query(FitbitSteps).filter(
            FitbitSteps.user_id == current_user.id,
            FitbitSteps.date == today,
        ).first()
        current_steps = entry.steps if entry else 0
    else:
        month_start = _month_start_bkk()
        row = db.query(func.coalesce(func.sum(FitbitSteps.steps), 0)).filter(
            FitbitSteps.user_id == current_user.id,
            FitbitSteps.date >= month_start,
        ).scalar()
        current_steps = int(row) if row else 0

    if current_steps < threshold:
        raise HTTPException(status_code=400, detail=f"Need {threshold:,} steps, currently {current_steps:,}")

    # Grant rewards
    if rewards["str"] > 0:
        current_user.base_str = (current_user.base_str or 10) + rewards["str"]
    if rewards["def"] > 0:
        current_user.base_def = (current_user.base_def or 10) + rewards["def"]
    if rewards["luk"] > 0:
        current_user.base_luk = (current_user.base_luk or 10) + rewards["luk"]
    if rewards["gold"] > 0:
        current_user.coins = (current_user.coins or 0) + rewards["gold"]
        db.add(CoinLog(
            user_id=current_user.id,
            amount=rewards["gold"],
            reason=f"🥾 Step reward — {reward_type} goal ({threshold:,} steps)",
            created_by="System",
        ))
    if rewards["mana"] > 0:
        current_user.angel_coins = (current_user.angel_coins or 0) + rewards["mana"]

    # Record claim
    db.add(StepReward(
        user_id=current_user.id,
        reward_date=reward_date,
        reward_type=reward_type,
        str_granted=rewards["str"],
        coins_granted=rewards["gold"],
    ))

    db.commit()

    # Build message
    parts = []
    for stat, label in [("str", "STR"), ("def", "DEF"), ("luk", "LUK"), ("gold", "Gold"), ("mana", "Mana")]:
        if rewards[stat] > 0:
            parts.append(f"{label} +{rewards[stat]}")

    return {
        "message": f"Reward claimed! {', '.join(parts)}" if parts else "Reward claimed!",
        "rewards": rewards,
    }


@router.post("/disconnect")
def disconnect_fitbit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove Fitbit tokens for the current user."""
    token = db.query(FitbitToken).filter(FitbitToken.user_id == current_user.id).first()
    if token:
        db.delete(token)
        db.commit()
    return {"message": "Fitbit disconnected"}


@router.post("/test-set-steps")
def test_set_steps(
    steps: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """DEV ONLY — manually set today's step count for testing rewards."""
    today = _today_bkk()
    entry = db.query(FitbitSteps).filter(
        FitbitSteps.user_id == current_user.id,
        FitbitSteps.date == today,
    ).first()
    if entry:
        entry.steps = steps
    else:
        entry = FitbitSteps(user_id=current_user.id, date=today, steps=steps)
        db.add(entry)
    db.commit()
    return {"message": f"Set today's steps to {steps:,} for user {current_user.id}", "steps": steps, "date": today.isoformat()}
