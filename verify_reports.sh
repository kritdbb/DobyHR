#!/bin/bash
BASE_URL="http://localhost:8100"

# 1. Login as Admin
echo "Logging in as Admin..."
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin" | jq -r '.access_token')

# 2. Test Attendance Report
echo "Testing Attendance Report..."
ATT_RES=$(curl -s -X GET "$BASE_URL/reports/attendance" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
ATT_COUNT=$(echo $ATT_RES | jq 'length')
echo "Attendance Records: $ATT_COUNT"

# 3. Test Coin Report
echo "Testing Coin Report..."
COIN_RES=$(curl -s -X GET "$BASE_URL/reports/coins" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
COIN_COUNT=$(echo $COIN_RES | jq 'length')
echo "Coin Records: $COIN_COUNT"

# 4. Test Leave Summary
echo "Testing Leave Summary..."
LEAVE_RES=$(curl -s -X GET "$BASE_URL/reports/leaves" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
LEAVE_COUNT=$(echo $LEAVE_RES | jq 'length')
echo "Users in Summary: $LEAVE_COUNT"

if [ "$ATT_COUNT" -gt 0 ] && [ "$COIN_COUNT" -gt 0 ]; then
    echo "SUCCESS: Reports return data"
else
    echo "WARNING: Reports empty (may be expected if fresh db)"
fi
