#!/bin/bash
BASE_URL="http://localhost:8100"
EMAIL="real.final@example.com"
PASSWORD="password123"

# 1. Login as Admin
echo "Logging in as Admin..."
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin" | jq -r '.access_token')

# 2. Create Reward
echo "Creating Reward 'Test Gift' (Cost 50)..."
REWARD_RES=$(curl -s -X POST "$BASE_URL/rewards/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Gift",
    "description": "A test reward",
    "point_cost": 50
  }')
REWARD_ID=$(echo $REWARD_RES | jq '.id')
echo "Reward ID: $REWARD_ID"

if [ "$REWARD_ID" == "null" ]; then
    echo "FAILED: Create Reward"
    exit 1
fi

# 3. Login as Staff
echo "Logging in as Staff..."
STAFF_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD" | jq -r '.access_token')

# 4. Check Coins Before
echo "Checking Initial Coins..."
INIT_COINS=$(curl -s -X GET "$BASE_URL/api/users/me" \
  -H "Authorization: Bearer $STAFF_TOKEN" | jq '.coins')
echo "Initial Coins: $INIT_COINS"

if [ "$INIT_COINS" -lt 50 ]; then
    echo "WARNING: Not enough coins. Adding 100 via Admin..."
    STAFF_ID=$(curl -s -X GET "$BASE_URL/api/users/me" \
        -H "Authorization: Bearer $STAFF_TOKEN" | jq '.id')
    curl -s -X POST "$BASE_URL/api/users/$STAFF_ID/coins" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"amount": 100, "reason": "Test Topup"}' > /dev/null
    INIT_COINS=$((INIT_COINS + 100))
fi

# 5. Redeem Reward
echo "Redeeming Reward..."
REDEEM_RES=$(curl -s -X POST "$BASE_URL/rewards/redeem" \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"reward_id\": $REWARD_ID
  }")

REDEMPTION_ID=$(echo $REDEEM_RES | jq '.id')
UUID=$(echo $REDEEM_RES | jq -r '.qr_code')
STATUS=$(echo $REDEEM_RES | jq -r '.status')

echo "Redemption ID: $REDEMPTION_ID, UUID: $UUID, Status: $STATUS"

if [ "$STATUS" != "pending" ]; then
    echo "FAILED: Redemption status not pending"
fi

# 6. Admin Verify (Look up)
echo "Admin Loading Redemption by UUID..."
VERIFY_RES=$(curl -s -X GET "$BASE_URL/rewards/verify/$UUID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
VERIFY_ID=$(echo $VERIFY_RES | jq '.id')

if [ "$VERIFY_ID" != "$REDEMPTION_ID" ]; then
    echo "FAILED: Admin lookup mismatch"
fi

# 7. Admin Approve (Manual endpoint I added)
echo "Admin Approving..."
APPROVE_RES=$(curl -s -X POST "$BASE_URL/rewards/$REDEMPTION_ID/approve" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
APPROVED_STATUS=$(echo $APPROVE_RES | jq -r '.status')
echo "Approved Status: $APPROVED_STATUS"

if [ "$APPROVED_STATUS" != "ready" ]; then
    echo "FAILED: Approve failed"
fi

# 8. Admin Handover
echo "Admin Handover..."
HANDOVER_RES=$(curl -s -X POST "$BASE_URL/rewards/verify/$UUID/handover" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
FINAL_STATUS=$(echo $HANDOVER_RES | jq -r '.status')

echo "Final Status: $FINAL_STATUS"

if [ "$FINAL_STATUS" == "completed" ]; then
    echo "SUCCESS: Full Redemption Flow Verified"
else
    echo "FAILED: Handover failed"
fi
