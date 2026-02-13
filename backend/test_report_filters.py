import sys
import os
from datetime import date, datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.core.database import SessionLocal
from app.api.endpoints.reports import get_attendance_report, get_coin_report, get_leave_summary_report
from app.models.user import User
from app.models.approval import ApprovalFlow

# Mock Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_reports():
    db = SessionLocal()
    try:
        print("Testing Reports Logic...")
        
        # 1. Get Admin User for dependency
        admin = db.query(User).filter(User.email == "admin@admin.com").first()
        if not admin:
            print("Admin not found!")
            return

        # 2. Test Attendance Report (Last 7 Days)
        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        
        print(f"\n--- Attendance Report ({seven_days_ago} to {today}) ---")
        att_report = get_attendance_report(
            start_date=seven_days_ago, 
            end_date=today, 
            user_id=None, 
            db=db, 
            current_user=admin
        )
        print(f"Total Records: {len(att_report)}")
        if att_report:
            print(f"Sample: {att_report[0]}")
            
        # 3. Test Coin Report
        print(f"\n--- Coin Report ---")
        coin_report = get_coin_report(
            start_date=None, 
            end_date=None, 
            user_id=None, 
            db=db, 
            current_user=admin
        )
        print(f"Total Records: {len(coin_report)}")
        if coin_report:
            print(f"Sample: {coin_report[0]}")

        # 4. Test Leave Summary
        print(f"\n--- Leave Summary ---")
        leave_report = get_leave_summary_report(db=db, current_user=admin)
        print(f"Total Users: {len(leave_report)}")
        for item in leave_report:
            print(f"User: {item.user_name}, Sick: {item.sick_taken}, Business: {item.business_taken}, Vacation: {item.vacation_taken}, Pending: {item.total_pending}")

    except Exception as e:
        print(f"Error testing: {e}")
    finally:
        db.close()

# We need to import the function, but it's decorated as a router. 
# We can call the underlying function directly if we import it correctly.
# But wait, endpoint functions expect dependencies to be injected.
# In the script, we passed `db` and `current_user` manually.
# However, `get_leave_summary_report` call above uses `get_leave_summary` name imported?
# I imported `get_leave_summary` but called `get_leave_summary_report`. 
# Let me fix the call name.

if __name__ == "__main__":
    from app.api.endpoints.reports import get_leave_summary_report # Import the function name exactly
    
    # Re-define to correct function call
    def test_reports_fixed():
        db = SessionLocal()
        try:
            print("Testing Reports Logic...")
            
            # 1. Get Admin User
            admin = db.query(User).filter(User.email == "admin@admin.com").first()
            
            # 2. Attendance
            today = date.today()
            seven_days_ago = today - timedelta(days=7)
            
            print(f"\n--- Attendance Report ({seven_days_ago} to {today}) ---")
            att_report = get_attendance_report(
                start_date=seven_days_ago, 
                end_date=today, 
                user_id=None, 
                db=db, 
                current_user=admin
            )
            print(f"Total Records: {len(att_report)}")
            for r in att_report[:3]:
                print(f" - {r['timestamp']} | {r['user_name']} | {r['status']}")

            # 3. Coins
            print(f"\n--- Coin Report (All time) ---")
            coin_report = get_coin_report(
                start_date=None, 
                end_date=None, 
                user_id=None, 
                db=db, 
                current_user=admin
            )
            print(f"Total Records: {len(coin_report)}")
            for r in coin_report[:3]:
                 print(f" - {r['created_at']} | {r['user_name']} | {r['amount']} | {r['reason']}")

            # 4. Leaves
            print(f"\n--- Leave Summary ---")
            leave_report = get_leave_summary_report(db=db, current_user=admin)
            for item in leave_report:
                # Item is Pydantic model or dict? Endpoint returns list of Pydantic models (LeaveSummaryItem)
                # But the function implementation returns a LIST OF DICTS.
                # However, response_model=List[LeaveSummaryItem] converts it.
                # When calling directly, it returns list of dicts.
                print(f"User: {item['user_name']}")
                print(f"  Sick: {item['sick_taken']}/{item['sick_quota']}")
                print(f"  Business: {item['business_taken']}/{item['business_quota']}")
                print(f"  Vacation: {item['vacation_taken']}/{item['vacation_quota']}")
                print(f"  Pending: {item['total_pending']}")

        except Exception as e:
            print(f"Error testing: {e}")
        finally:
            db.close()

    test_reports_fixed()
