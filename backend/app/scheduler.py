"""
Scheduler for automatic coin/angel distribution and Lucky Draw.
Uses APScheduler with two cron jobs:
  - Auto coin/angel at 00:01 UTC+7 (17:01 UTC)
  - Lucky Draw at 12:30 UTC+7 (05:30 UTC)
"""
import logging
import random
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.database import SessionLocal
from app.models.company import Company
from app.models.user import User, UserRole
from app.models.reward import CoinLog
from app.models.badge import Badge, UserBadge

logger = logging.getLogger("hr-api")

DAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}


def auto_give_coins_and_angels():
    """Run daily: check if today matches auto_coin_day / auto_angel_day and distribute."""
    db = SessionLocal()
    try:
        now_local = datetime.utcnow() + timedelta(hours=7)
        today_code = DAY_MAP.get(now_local.weekday(), "")
        logger.info(f"⏰ Auto-giver check running for {today_code.upper()} ({now_local.strftime('%Y-%m-%d %H:%M')})")

        company = db.query(Company).first()
        if not company:
            logger.warning("No company found, skipping auto-giver")
            return

        # Get all active staff
        staff = db.query(User).filter(User.role == UserRole.PLAYER).all()
        if not staff:
            logger.info("No active staff found, skipping auto-giver")
            return

        # --- Auto Coin ---
        if company.auto_coin_day and company.auto_coin_amount and company.auto_coin_amount > 0:
            coin_days = [d.strip().lower() for d in company.auto_coin_day.split(",")]
            if today_code in coin_days:
                count = 0
                for user in staff:
                    user.coins += company.auto_coin_amount
                    log = CoinLog(
                        user_id=user.id,
                        amount=company.auto_coin_amount,
                        reason=f"🪙 Auto Coin ({today_code.upper()})",
                        created_by="System"
                    )
                    db.add(log)
                    count += 1
                logger.info(f"🪙 Auto Coin: +{company.auto_coin_amount} to {count} staff")

        # --- Auto Angel ---
        if company.auto_angel_day and company.auto_angel_amount and company.auto_angel_amount > 0:
            angel_days = [d.strip().lower() for d in company.auto_angel_day.split(",")]
            if today_code in angel_days:
                count = 0
                for user in staff:
                    user.angel_coins += company.auto_angel_amount
                    log = CoinLog(
                        user_id=user.id,
                        amount=company.auto_angel_amount,
                        reason=f"🪽 Auto Angel Coins ({today_code.upper()})",
                        created_by="System"
                    )
                    db.add(log)
                    count += 1
                logger.info(f"🪽 Auto Angel: +{company.auto_angel_amount} to {count} staff")

        db.commit()
    except Exception as e:
        logger.error(f"Auto-giver error: {e}")
        db.rollback()
    finally:
        db.close()


def lucky_draw():
    """Run daily at 12:30 UTC+7: weighted random coin draw based on LUK stats."""
    db = SessionLocal()
    try:
        now_local = datetime.utcnow() + timedelta(hours=7)
        today_code = DAY_MAP.get(now_local.weekday(), "")
        logger.info(f"🎰 Lucky Draw check for {today_code.upper()} ({now_local.strftime('%Y-%m-%d %H:%M')})")

        company = db.query(Company).first()
        if not company:
            return

        if not company.lucky_draw_day or not company.lucky_draw_amount or company.lucky_draw_amount <= 0:
            logger.info("Lucky Draw not configured, skipping")
            return

        draw_days = [d.strip().lower() for d in company.lucky_draw_day.split(",")]
        if today_code not in draw_days:
            logger.info(f"Lucky Draw not scheduled for {today_code.upper()}, skipping")
            return

        # Get all active staff
        staff = db.query(User).filter(User.role == UserRole.PLAYER).all()
        if not staff:
            logger.info("No active staff for lucky draw")
            return

        # Build weighted pool: each user gets tickets = total_luk
        pool = []
        for user in staff:
            # Compute total LUK = base_luk + sum of badge luk bonuses
            base_luk = user.base_luk if hasattr(user, 'base_luk') and user.base_luk else 1
            badge_luk = 0
            user_badges = db.query(UserBadge).filter(UserBadge.user_id == user.id).all()
            for ub in user_badges:
                badge = db.query(Badge).filter(Badge.id == ub.badge_id).first()
                if badge and badge.stat_luk:
                    badge_luk += badge.stat_luk
            total_luk = base_luk + badge_luk
            # Add `total_luk` tickets for this user
            for _ in range(max(1, total_luk)):
                pool.append(user)

        if not pool:
            logger.info("Empty lucky draw pool")
            return

        # Draw one winner
        winner = random.choice(pool)
        winner.coins += company.lucky_draw_amount

        user_name = f"{winner.name} {winner.surname or ''}".strip()
        log = CoinLog(
            user_id=winner.id,
            amount=company.lucky_draw_amount,
            reason=f"🎰 Lucky Draw! Won {company.lucky_draw_amount} Gold ({today_code.upper()})",
            created_by="System"
        )
        db.add(log)
        db.commit()
        logger.info(f"🎰 Lucky Draw winner: {user_name} (+{company.lucky_draw_amount} Gold)")
    except Exception as e:
        logger.error(f"Lucky draw error: {e}")
        db.rollback()
    finally:
        db.close()


def evaluate_badge_quests():
    """Run daily: evaluate all active badge quests and auto-award badges."""
    db = SessionLocal()
    try:
        from app.api.endpoints.badge_quests import _run_evaluation
        result = _run_evaluation(db)
        logger.info(f"🏅 Badge Quest evaluation: {result['awarded']} badges awarded")
    except Exception as e:
        logger.error(f"Badge Quest evaluation error: {e}")
        db.rollback()
    finally:
        db.close()


def auto_process_absent_penalties():
    """Run daily at 12:00 UTC+7 (noon): deduct coins from users who didn't check in today."""
    db = SessionLocal()
    try:
        now_local = datetime.utcnow() + timedelta(hours=7)
        target_date = now_local.date()  # Today
        today_code = DAY_MAP.get(target_date.weekday(), "")
        logger.info(f"🚨 Auto absent penalty check for {target_date.isoformat()} ({today_code.upper()})")

        company = db.query(Company).first()
        if not company or not company.coin_absent_penalty:
            logger.info("No absent penalty configured, skipping")
            return

        from app.models.attendance import Attendance
        from app.models.leave import LeaveRequest, LeaveStatus
        from app.models.work_request import WorkRequest, WorkRequestStatus

        penalty_amount = company.coin_absent_penalty
        staff = db.query(User).filter(User.role == UserRole.PLAYER).all()

        penalized_count = 0
        for user in staff:
            # Check if it's a working day for this user
            user_working_days = []
            if user.working_days:
                user_working_days = [d.strip().lower() for d in user.working_days.split(",")]
            if today_code not in user_working_days:
                continue

            # Check if user checked in today with a valid status
            day_start_utc = datetime.combine(target_date, datetime.min.time()) - timedelta(hours=7)
            day_end_utc = datetime.combine(target_date, datetime.max.time()) - timedelta(hours=7)
            attendance = db.query(Attendance).filter(
                Attendance.user_id == user.id,
                Attendance.timestamp >= day_start_utc,
                Attendance.timestamp <= day_end_utc,
                Attendance.status.in_(["present", "late", "absent"])
            ).first()
            if attendance:
                continue

            # Skip users with pending remote/work requests (not yet decided)
            pending_request = db.query(WorkRequest).filter(
                WorkRequest.user_id == user.id,
                WorkRequest.status == WorkRequestStatus.PENDING,
                WorkRequest.created_at >= day_start_utc,
                WorkRequest.created_at <= day_end_utc
            ).first()
            if pending_request:
                continue

            # Check if user has approved leave
            approved_leave = db.query(LeaveRequest).filter(
                LeaveRequest.user_id == user.id,
                LeaveRequest.status == LeaveStatus.APPROVED,
                LeaveRequest.start_date <= target_date,
                LeaveRequest.end_date >= target_date
            ).first()
            if approved_leave:
                continue

            # Apply penalty
            user.coins -= penalty_amount
            log = CoinLog(
                user_id=user.id,
                amount=-penalty_amount,
                reason=f"Absent penalty ({target_date.isoformat()})",
                created_by="System"
            )
            db.add(log)
            penalized_count += 1

        db.commit()
        logger.info(f"🚨 Absent penalties: {penalized_count} users penalized for {target_date.isoformat()}")
    except Exception as e:
        logger.error(f"Absent penalty error: {e}")
        db.rollback()
    finally:
        db.close()


scheduler = BackgroundScheduler()


def start_scheduler():
    """Start the background scheduler."""
    # Load FAISS index at startup
    try:
        from app.services.face_service import load_index
        load_index()
    except Exception as e:
        logger.warning(f"⚠️ FAISS index load skipped: {e}")

    # Auto coin/angel giver at 00:01 UTC+7 (17:01 UTC)
    scheduler.add_job(
        auto_give_coins_and_angels,
        "cron",
        hour=17,
        minute=1,
        id="auto_coin_angel_giver",
        replace_existing=True,
    )
    # Lucky Draw at 12:30 UTC+7 (05:30 UTC)
    scheduler.add_job(
        lucky_draw,
        "cron",
        hour=5,
        minute=30,
        id="lucky_draw",
        replace_existing=True,
    )
    # Badge Quest evaluation every 2 hours
    scheduler.add_job(
        evaluate_badge_quests,
        "interval",
        hours=2,
        id="badge_quest_eval",
        replace_existing=True,
    )
    # Auto absent penalties at 12:00 UTC+7 (05:00 UTC) — noon check
    scheduler.add_job(
        auto_process_absent_penalties,
        "cron",
        hour=5,
        minute=0,
        id="auto_absent_penalty",
        replace_existing=True,
    )
    # Face Recognition check-in worker — every 60 seconds
    # The worker itself checks the time window (06:00–10:30 UTC+7) and exits if outside
    scheduler.add_job(
        _run_face_recognition,
        "interval",
        seconds=60,
        id="face_recognition_worker",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("✅ Scheduler started — auto coin/angel at 00:01, lucky draw at 12:30, absent penalty at 23:00, face recognition check, badge quest eval every 2h")


def _run_face_recognition():
    """Wrapper to run the face check-in worker safely."""
    try:
        from app.services.face_checkin_worker import run
        run()
    except Exception as e:
        logger.error(f"❌ Face recognition worker error: {e}")
