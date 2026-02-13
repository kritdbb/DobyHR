#!/bin/bash
BASE_URL="http://localhost:8100"

# Login as Staff
EMAIL="real.final@example.com"
PASSWORD="password123"

# Or admin to create if not exists
echo "Logging in as Admin to ensure user exists..."
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin" | jq -r '.access_token')

# Ensure staff exists (idempotent-ish)
curl -s -X POST "$BASE_URL/api/users/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Real\",
    \"surname\": \"Final\",
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\",
    \"role\": \"staff\",
    \"sick_leave_days\": 5,
    \"business_leave_days\": 5,
    \"vacation_leave_days\": 5
  }" > /dev/null

echo "Logging in as Staff ($EMAIL)..."
STAFF_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD" | jq -r '.access_token')

if [ "$STAFF_TOKEN" == "null" ] || [ -z "$STAFF_TOKEN" ]; then
    echo "FAILED: Staff login."
    exit 1
fi

echo "Testing /leaves/quota..."
RESPONSE=$(curl -s -X GET "$BASE_URL/leaves/quota" \
  -H "Authorization: Bearer $STAFF_TOKEN")

echo "Response Body:"
echo "$RESPONSE"

# Check if valid JSON
echo "$RESPONSE" | jq . > /dev/null
if [ $? -eq 0 ]; then
    echo "Valid JSON received."
else
    echo "Invalid JSON received."
fi
