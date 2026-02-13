#!/bin/bash
BASE_URL="http://localhost:8100"
EMAIL="real.final@example.com"

# 1. Login as Admin
echo "Logging in as Admin..."
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin" | jq -r '.access_token')

# 2. Get Staff ID
echo "Getting Staff ID..."
STAFF_ID=$(curl -s -X GET "$BASE_URL/api/users/?skip=0&limit=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r ".[] | select(.email==\"$EMAIL\") | .id")
echo "Staff ID: $STAFF_ID"

# 3. Add 100 Coins
echo "Adding 100 Coins..."
ADJUST_RES=$(curl -s -X POST "$BASE_URL/api/users/$STAFF_ID/coins" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100,
    "reason": "Performance Bonus"
  }')
echo "Adjust Response Coins: $(echo $ADJUST_RES | jq '.coins')"

# 4. Check Logs
echo "Checking Logs..."
LOGS_RES=$(curl -s -X GET "$BASE_URL/api/users/$STAFF_ID/coin-logs" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
  
echo "Logs Count: $(echo $LOGS_RES | jq 'length')"
LAST_LOG=$(echo $LOGS_RES | jq '.[0]')
echo "Last Log Reason: $(echo $LAST_LOG | jq -r '.reason')"
echo "Last Log Amount: $(echo $LAST_LOG | jq '.amount')"

EXPECTED_REASON="Performance Bonus"
ACTUAL_REASON=$(echo $LAST_LOG | jq -r '.reason')

if [ "$ACTUAL_REASON" == "$EXPECTED_REASON" ]; then
    echo "SUCCESS: Coin adjustment and logging verified."
else
    echo "FAILED: Log verification failed."
fi
