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


scheduler = BackgroundScheduler()


def start_scheduler():
    """Start the background scheduler."""
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
    scheduler.start()
    logger.info("✅ Scheduler started — auto coin/angel at 00:01 UTC+7, lucky draw at 12:30 UTC+7, badge quest eval every 2h")
