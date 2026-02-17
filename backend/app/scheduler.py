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
from app.models.social import ThankYouCard
from app.models.attendance import Attendance
from app.models.social import AnonymousPraise

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



def weekly_thank_you_badge_eval():
    """Every Monday: find last week's top Thank You Card recipient, award temp badge + LUK 10."""
    BADGE_NAME = "💌 Thank You Star"
    LUK_BONUS = 10
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        now_local = datetime.utcnow() + timedelta(hours=7)
        prev = now_local - timedelta(weeks=1)
        prev_week_key = f"{prev.isocalendar()[0]}-W{prev.isocalendar()[1]:02d}"
        logger.info(f"🌟 Weekly Thank You evaluation for {prev_week_key}")

        # Ensure badge exists (auto-create once)
        badge = db.query(Badge).filter(Badge.name == BADGE_NAME).first()
        if not badge:
            badge = Badge(
                name=BADGE_NAME,
                description="Awarded weekly to the person who received the most Thank You Cards. LUK +10 for the week!",
                stat_luk=0,  # We manage LUK directly via base_luk
                stat_str=0,
                stat_def=0,
                image="/uploads/badges/thank_you_star.png",
            )
            db.add(badge)
            db.commit()
            db.refresh(badge)
            logger.info(f"🌟 Auto-created '{BADGE_NAME}' badge (id={badge.id})")

        # Step 1: Revoke last week's holders and remove LUK bonus
        old_holders = db.query(UserBadge).filter(UserBadge.badge_id == badge.id).all()
        for ub in old_holders:
            user = db.query(User).filter(User.id == ub.user_id).first()
            if user:
                user.base_luk = max(10, (user.base_luk or 10) - LUK_BONUS)
                logger.info(f"   Revoked from {user.name}, LUK back to {user.base_luk}")
            db.delete(ub)
        db.commit()

        # Step 2: Find top recipient(s) from last week
        from sqlalchemy import func as sqlfunc
        top_recipients = (
            db.query(
                ThankYouCard.recipient_id,
                sqlfunc.count(ThankYouCard.id).label("card_count"),
            )
            .filter(ThankYouCard.week_key == prev_week_key)
            .group_by(ThankYouCard.recipient_id)
            .order_by(sqlfunc.count(ThankYouCard.id).desc())
            .all()
        )

        if not top_recipients:
            logger.info("🌟 No Thank You Cards sent last week, skipping.")
            return

        max_count = top_recipients[0].card_count
        winners = [r for r in top_recipients if r.card_count == max_count]

        # Step 3: Award badge + LUK bonus to all winners
        winner_names = []
        for winner in winners:
            user = db.query(User).filter(User.id == winner.recipient_id).first()
            if not user:
                continue
            ub = UserBadge(
                user_id=user.id,
                badge_id=badge.id,
                awarded_by="Weekly Thank You Star",
            )
            db.add(ub)
            user.base_luk = (user.base_luk or 10) + LUK_BONUS
            winner_names.append(f"{user.name} {user.surname or ''}".strip())
            logger.info(f"   🌟 Awarded to {user.name} ({max_count} cards), LUK → {user.base_luk}")

        db.commit()

        # Announce in Town Crier
        if winner_names:
            try:
                from app.services.notifications import send_town_crier_webhook
                names = ", ".join(winner_names)
                send_town_crier_webhook(
                    f"🌟 *{names}* ได้รับเหรียญ Thank You Star ประจำสัปดาห์! "
                    f"(ได้รับ Thank You Card มากที่สุด {max_count} ใบ — LUK +{LUK_BONUS} ตลอดสัปดาห์!)"
                )
            except Exception as e:
                logger.warning(f"Town Crier webhook failed: {e}")

        logger.info(f"🌟 Thank You Star awarded to {len(winners)} user(s)")
    except Exception as e:
        logger.error(f"❌ Weekly Thank You badge eval error: {e}")
        db.rollback()
    finally:
        db.close()


def distribute_motm_rewards():
    """Distribute Man of the Month rewards on the 1st of each month for the previous month."""
    import json
    from sqlalchemy import func, or_
    db = SessionLocal()
    try:
        company = db.query(Company).first()
        if not company or not company.motm_rewards:
            logger.info("🏆 MOTM: No rewards configured, skipping")
            return

        try:
            rewards_config = json.loads(company.motm_rewards)
        except Exception:
            logger.error("🏆 MOTM: Invalid JSON in motm_rewards")
            return

        if not rewards_config:
            return

        # Previous month window
        now_local = datetime.utcnow() + timedelta(hours=7)
        first_of_this_month = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = first_of_this_month - timedelta(seconds=1)
        first_of_last_month = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_label = first_of_last_month.strftime("%B %Y")

        # Convert to UTC for DB queries
        pm_start_utc = first_of_last_month - timedelta(hours=7)
        pm_end_utc = first_of_this_month - timedelta(hours=7)

        # Find winners for each category
        category_winners = {}

        # 1. Most Mana Received
        mana_winner = (
            db.query(CoinLog.user_id, func.sum(CoinLog.amount).label("total"))
            .filter(
                CoinLog.created_at >= pm_start_utc,
                CoinLog.created_at < pm_end_utc,
                or_(
                    CoinLog.reason.ilike("%Received Angel Coins%"),
                    CoinLog.reason.ilike("%Received Gold from%"),
                    CoinLog.reason.ilike("%Received Mana from%"),
                ),
            )
            .group_by(CoinLog.user_id)
            .order_by(func.sum(CoinLog.amount).desc(), func.min(CoinLog.created_at).asc())
            .first()
        )
        if mana_winner:
            category_winners["motm_mana"] = mana_winner.user_id

        # 2. Most Steps
        try:
            from app.models.fitbit import FitbitSteps
            pm_start_date = first_of_last_month.date()
            pm_end_date = first_of_this_month.date()
            steps_winner = (
                db.query(FitbitSteps.user_id, func.sum(FitbitSteps.steps).label("total"))
                .filter(FitbitSteps.date >= pm_start_date, FitbitSteps.date < pm_end_date)
                .group_by(FitbitSteps.user_id)
                .order_by(func.sum(FitbitSteps.steps).desc(), func.min(FitbitSteps.date).asc())
                .first()
            )
            if steps_winner:
                category_winners["motm_steps"] = steps_winner.user_id
        except Exception as e:
            logger.warning(f"🏆 MOTM steps query error: {e}")

        # 3. Most On-Time
        ontime_winner = (
            db.query(Attendance.user_id, func.count(Attendance.id).label("cnt"))
            .filter(
                Attendance.timestamp >= pm_start_utc,
                Attendance.timestamp < pm_end_utc,
                Attendance.status == "present",
            )
            .group_by(Attendance.user_id)
            .order_by(func.count(Attendance.id).desc(), func.min(Attendance.timestamp).asc())
            .first()
        )
        if ontime_winner:
            category_winners["motm_ontime"] = ontime_winner.user_id

        # 4. Most Gold Spent
        gold_winner = (
            db.query(CoinLog.user_id, func.sum(func.abs(CoinLog.amount)).label("total"))
            .filter(
                CoinLog.created_at >= pm_start_utc,
                CoinLog.created_at < pm_end_utc,
                CoinLog.amount < 0,
                ~CoinLog.reason.ilike("%penalty%"),
                ~CoinLog.reason.ilike("%Late%"),
                ~CoinLog.reason.ilike("%Absent%"),
            )
            .group_by(CoinLog.user_id)
            .order_by(func.sum(func.abs(CoinLog.amount)).desc(), func.min(CoinLog.created_at).asc())
            .first()
        )
        if gold_winner:
            category_winners["motm_gold_spent"] = gold_winner.user_id

        # 5. Most Anonymous Praises
        pm_month_str = first_of_last_month.strftime("%Y-%m")
        praise_winner = (
            db.query(AnonymousPraise.recipient_id, func.count(AnonymousPraise.id).label("cnt"))
            .filter(AnonymousPraise.date_key.startswith(pm_month_str))
            .group_by(AnonymousPraise.recipient_id)
            .order_by(func.count(AnonymousPraise.id).desc(), func.min(AnonymousPraise.id).asc())
            .first()
        )
        if praise_winner:
            category_winners["motm_praises"] = praise_winner.recipient_id

        # Apply rewards
        category_labels = {
            "motm_mana": "✨ Most Mana Received",
            "motm_steps": "🥾 Most Steps",
            "motm_ontime": "⏰ Most On-Time",
            "motm_gold_spent": "💰 Most Gold Spent",
            "motm_praises": "💬 Most Anonymous Praises",
        }

        for cat_key, winner_id in category_winners.items():
            config = rewards_config.get(cat_key, {})
            if not config:
                continue

            user = db.query(User).filter(User.id == winner_id).first()
            if not user:
                continue

            label = category_labels.get(cat_key, cat_key)
            applied = []

            # Gold
            gold_amt = int(config.get("gold", 0) or 0)
            if gold_amt > 0:
                user.coins = (user.coins or 0) + gold_amt
                db.add(CoinLog(user_id=user.id, amount=gold_amt, reason=f"🏆 MOTM {month_label}: {label} — Gold +{gold_amt}", created_by="system"))
                applied.append(f"Gold +{gold_amt}")

            # Mana
            mana_amt = int(config.get("mana", 0) or 0)
            if mana_amt > 0:
                user.angel_coins = (user.angel_coins or 0) + mana_amt
                db.add(CoinLog(user_id=user.id, amount=mana_amt, reason=f"🏆 MOTM {month_label}: {label} — Mana +{mana_amt}", created_by="system"))
                applied.append(f"Mana +{mana_amt}")

            # Stats
            for stat_name in ["str", "def", "luk"]:
                stat_amt = int(config.get(stat_name, 0) or 0)
                if stat_amt > 0:
                    attr = f"base_{stat_name}"
                    current = getattr(user, attr, None) or 10
                    setattr(user, attr, current + stat_amt)
                    applied.append(f"{stat_name.upper()} +{stat_amt}")

            # Badge
            badge_id = config.get("badge_id")
            if badge_id:
                badge_id = int(badge_id)
                existing = db.query(UserBadge).filter(UserBadge.user_id == user.id, UserBadge.badge_id == badge_id).first()
                if not existing:
                    db.add(UserBadge(user_id=user.id, badge_id=badge_id))
                    badge = db.query(Badge).filter(Badge.id == badge_id).first()
                    badge_name = badge.name if badge else f"Badge #{badge_id}"
                    applied.append(f"Badge: {badge_name}")

            if applied:
                user_full = f"{user.name} {user.surname or ''}".strip()
                logger.info(f"🏆 MOTM {month_label}: {label} winner = {user_full} → {', '.join(applied)}")
                from app.services.notifications import send_town_crier_webhook
                send_town_crier_webhook(f"🏆 *{user_full}* ได้รับรางวัล Man of the Month ({label}) — {', '.join(applied)}")

        db.commit()
        logger.info(f"🏆 MOTM rewards distributed for {month_label}: {len(category_winners)} categories")

    except Exception as e:
        logger.error(f"❌ MOTM distribute error: {e}")
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
    # Weekly Thank You Star badge — every Monday 00:05 UTC+7 (17:05 UTC Sunday)
    scheduler.add_job(
        weekly_thank_you_badge_eval,
        "cron",
        day_of_week="sun",
        hour=17,
        minute=5,
        id="weekly_thank_you_star",
        replace_existing=True,
    )
    # Man of the Month rewards — 1st of each month at 00:10 UTC+7 (17:10 UTC)
    scheduler.add_job(
        distribute_motm_rewards,
        "cron",
        day=1,
        hour=17,
        minute=10,
        id="motm_rewards",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("✅ Scheduler started — auto coin/angel at 00:01, lucky draw at 12:30, absent penalty at 23:00, face recognition check, badge quest eval every 2h, thank you star Mon 00:05, MOTM rewards 1st 00:10")


def _run_face_recognition():
    """Wrapper to run the face check-in worker safely."""
    try:
        from app.services.face_checkin_worker import run
        run()
    except Exception as e:
        logger.error(f"❌ Face recognition worker error: {e}")
