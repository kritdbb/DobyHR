import requests
import sys
import json

BASE_URL = "http://localhost:8100"

def test_api():
    print("1. Testing Admin Login...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", data={
            "username": "admin@admin.com",
            "password": "admin"
        })
        if resp.status_code != 200:
            print(f"FAILED: Admin login returned {resp.status_code}: {resp.text}")
            return
        
        admin_token = resp.json()["access_token"]
        print(f"SUCCESS: Admin logged in.")
        
        # Test /api/users/me
        print("\n2. Testing /api/users/me for Admin...")
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        if resp.status_code != 200:
             print(f"FAILED: /me returned {resp.status_code}: {resp.text}")
             return
        print(f"SUCCESS: /me returned: {resp.json()['email']}")

        print("\n3. Creating Staff User...")
        staff_data = {
            "name": "Me",
            "surname": "Tester",
            "email": "me.test@example.com",
            "password": "password123",
            "role": "staff",
            "sick_leave_days": 5,
            "business_leave_days": 5,
            "vacation_leave_days": 5
        }
        
        # Check if user exists
        users_resp = requests.get(f"{BASE_URL}/api/users/", headers=headers) # Test list endpoint too
        if users_resp.status_code == 200:
            print(f"SUCCESS: /api/users/ list returned {len(users_resp.json())} users")
            for u in users_resp.json():
                if u["email"] == staff_data["email"]:
                    print("User already exists, deleting...")
                    requests.delete(f"{BASE_URL}/api/users/{u['id']}", headers=headers)
        else:
             print(f"FAILED: /api/users/ returned {users_resp.status_code}")

        resp = requests.post(f"{BASE_URL}/api/users/", json=staff_data, headers=headers)
        if resp.status_code != 200:
            print(f"FAILED: Create user returned {resp.status_code}: {resp.text}")
            return
        
        print("SUCCESS: Staff user created.")
        
        print("\n4. Testing Staff Login & /me...")
        resp = requests.post(f"{BASE_URL}/auth/login", data={
            "username": staff_data["email"],
            "password": staff_data["password"]
        })
        if resp.status_code != 200:
            print(f"FAILED: Staff login returned {resp.status_code}: {resp.text}")
            return
            
        staff_token = resp.json()["access_token"]
        print("SUCCESS: Staff logged in.")
        
        # Test /me as staff
        headers = {"Authorization": f"Bearer {staff_token}"}
        resp = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        if resp.status_code != 200:
             print(f"FAILED: Staff /me returned {resp.status_code}: {resp.text}")
             return
        
        data = resp.json()
        print(f"SUCCESS: Staff /me returned email: {data['email']}")
        print(f"Sick Leave: {data['sick_leave_days']}")
        
        if data['sick_leave_days'] == 5:
            print("PASSED: Leave quota is correct.")
        else:
            print(f"FAILED: Expected 5, got {data['sick_leave_days']}")

        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_api()
