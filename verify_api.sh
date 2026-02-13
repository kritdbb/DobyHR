#!/bin/bash
BASE_URL="http://localhost:8100"

echo "1. Testing Admin Login..."
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo "FAILED: Admin login. Response:"
    curl -v -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=admin@admin.com&password=admin"
    exit 1
fi
echo "SUCCESS: Admin Token received."

echo "2. Creating Staff User..."
# Randomize email to verify creation logic
EMAIL="staff_$(date +%s)@example.com"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/users/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test\",
    \"surname\": \"Staff\",
    \"email\": \"$EMAIL\",
    \"password\": \"password123\",
    \"role\": \"staff\",
    \"sick_leave_days\": 5,
    \"business_leave_days\": 5,
    \"vacation_leave_days\": 5
  }")

BODY=$(echo "$RESPONSE" | head -n 1)
CODE=$(echo "$RESPONSE" | tail -n 1)

if [ "$CODE" != "200" ]; then
    echo "FAILED: Create user returned $CODE"
    echo "Body: $BODY"
    exit 1
fi
echo "SUCCESS: Staff user created ($EMAIL)."

echo "3. Testing Staff Login..."
STAFF_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=password123" | jq -r '.access_token')

if [ "$STAFF_TOKEN" == "null" ] || [ -z "$STAFF_TOKEN" ]; then
    echo "FAILED: Staff login."
    exit 1
fi
echo "SUCCESS: Staff Token received."

echo "ALL CHECKS PASSED"
