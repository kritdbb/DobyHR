#!/bin/bash
BASE_URL="http://localhost:8100"
EMAIL="real.final@example.com"
PASSWORD="password123"

# 1. Login as Admin
echo "Logging in as Admin..."
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin" | jq -r '.access_token')

# 2. Update Company Settings (Lat/Lon, Coin Rules)
echo "Updating Company Settings..."
curl -s -X PUT "$BASE_URL/api/company/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Corp",
    "latitude": 13.7563,
    "longitude": 100.5018,
    "coin_on_time": 10,
    "coin_late_penalty": 5
  }' > /dev/null

# 3. Get Staff ID (Assuming we know email)
echo "Getting Staff ID..."
STAFF_ID=$(curl -s -X GET "$BASE_URL/api/users/?skip=0&limit=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r ".[] | select(.email==\"$EMAIL\") | .id")

echo "Staff ID: $STAFF_ID"

# 4. Update Staff Work Start Time
echo "Updating Staff Work Time to 08:30..."
curl -s -X PUT "$BASE_URL/api/users/$STAFF_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "work_start_time": "08:30:00"
  }' > /dev/null

# 5. Login as Staff
echo "Logging in as Staff..."
STAFF_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD" | jq -r '.access_token')

# 6. Check Initial Coins (Should be 0 if new column)
echo "Checking Initial /me..."
INITIAL_COINS=$(curl -s -X GET "$BASE_URL/api/users/me" \
  -H "Authorization: Bearer $STAFF_TOKEN" | jq '.coins')
echo "Initial Coins: $INITIAL_COINS"

# 7. Check In (At Company Location)
echo "Checking In (Simulating 13.7563, 100.5018)..."
CHECKIN_RES=$(curl -s -X POST "$BASE_URL/attendance/check-in" \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 13.7563,
    "longitude": 100.5018
  }')

echo "Check-in Response: $CHECKIN_RES"

# 8. Verify Coins Increased
echo "Verifying Coins..."
FINAL_COINS=$(curl -s -X GET "$BASE_URL/api/users/me" \
  -H "Authorization: Bearer $STAFF_TOKEN" | jq '.coins')
echo "Final Coins: $FINAL_COINS"

EXPECTED=$((INITIAL_COINS + 10))
if [ "$FINAL_COINS" -eq "$EXPECTED" ]; then
    echo "SUCCESS: Coins increased by 10 (On Time)."
else
    echo "FAILED: Coins did not increase correctly. Expected $EXPECTED, got $FINAL_COINS"
fi
