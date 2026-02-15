import sys
import os
from datetime import datetime, timedelta
import random

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.attendance import Attendance
from app.models.reward import CoinLog, Reward, Redemption, RedemptionStatus
from app.models.leave import LeaveRequest
from app.models.approval import ApprovalFlow
from app.core.security import get_password_hash

def seed_data():
    db = SessionLocal()
    try:
        print("Seeding data for Report Testing...")

        # 1. Ensure Users Exist
        admin = db.query(User).filter(User.email == "admin@admin.com").first()
        
        # Create a few staff users
        staff_users = []
        for i in range(1, 4):
            email = f"staff{i}@test.com"
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    name=f"Staff",
                    surname=f"{i}",
                    email=email,
                    hashed_password=get_password_hash("password"),
                    role=UserRole.PLAYER,
                    coins=100 + (i*10),
                    sick_leave_days=30,
                    business_leave_days=30,
                    vacation_leave_days=30
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"Created user: {email}")
            staff_users.append(user)
            
        # 2. Generate Attendance Data (Last 7 days)
        print("Generating Attendance...")
        base_time = datetime.now()
        for user in staff_users:
            for day_offset in range(7):
                # Morning Check-in
                check_in_time = base_time - timedelta(days=day_offset)
                check_in_time = check_in_time.replace(hour=8, minute=random.randint(0, 59))
                
                att = Attendance(
                    user_id=user.id,
                    timestamp=check_in_time,
                    latitude=13.7563,
                    longitude=100.5018,
                    status="on_time" if check_in_time.minute < 30 else "late"
                )
                db.add(att)
                
                # Add Coin Log for attendance
                coin_amount = 10 if att.status == "on_time" else -5
                log = CoinLog(
                    user_id=user.id,
                    amount=coin_amount,
                    reason=f"Attendance: {att.status}",
                    created_by="System"
                )
                # Hack to set created_at back in time
                log.created_at = check_in_time 
                db.add(log)

        # 3. Generate Leave Requests
        print("Generating Leaves...")
        leave_types = ['sick', 'vacation', 'business']
        statuses = ['pending', 'approved', 'rejected']
        
        for user in staff_users:
            for _ in range(3):
                l_type = random.choice(leave_types)
                status = random.choice(statuses)
                days = random.randint(1, 5)
                start_date = (base_time + timedelta(days=random.randint(1, 30))).date()
                end_date = start_date + timedelta(days=days-1)
                
                leave = LeaveRequest(
                    user_id=user.id,
                    leave_type=l_type,
                    start_date=start_date,
                    end_date=end_date,
                    reason="Test leave",
                    status=status
                )
                db.add(leave)

        # 4. Generate Redemptions & Coin Logs
        print("Generating Redemptions...")
        # Assume reward exists or create one
        reward = db.query(Reward).first()
        if not reward:
            reward = Reward(name="Test Reward", description="Desc", point_cost=50, is_active=True)
            db.add(reward)
            db.commit()
            
        for user in staff_users:
            # Redeem
            redemption = Redemption(
                user_id=user.id,
                reward_id=reward.id,
                status=RedemptionStatus.COMPLETED,
                qr_code=f"QR-{user.id}-{random.randint(1000,9999)}"
            )
            db.add(redemption)
            
            # Log deduction
            log = CoinLog(
                user_id=user.id,
                amount=-reward.point_cost,
                reason=f"Redeemed {reward.name}",
                created_by="System"
            )
            db.add(log)

        db.commit()
        print("Seed Complete!")

    except Exception as e:
        print(f"Error seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
