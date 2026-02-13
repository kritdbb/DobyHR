#!/bin/bash
BASE_URL="http://localhost:8100"

# 1. Login as Admin to get a token (or create a staff user and login as them)
echo "Logging in as Admin..."
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    echo "FAILED: Admin login."
    exit 1
fi

# 2. Test /me endpoint as Admin
echo "Testing /api/users/me as Admin..."
RESPONSE=$(curl -s -X GET "$BASE_URL/api/users/me" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

EMAIL=$(echo "$RESPONSE" | jq -r '.email')
echo "Admin /me returned email: $EMAIL"

if [ "$EMAIL" != "admin@admin.com" ]; then
    echo "FAILED: /me did not return admin email. Got: $EMAIL"
    echo "Response: $RESPONSE"
    exit 1
fi

# 3. Create a Staff User for testing
echo "Creating Staff user..."
EMAIL="me.test.$(date +%s)@example.com"
curl -s -X POST "$BASE_URL/api/users/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Me\",
    \"surname\": \"Tester\",
    \"email\": \"$EMAIL\",
    \"password\": \"password123\",
    \"role\": \"staff\",
    \"sick_leave_days\": 5,
    \"business_leave_days\": 5,
    \"vacation_leave_days\": 5
  }" > /dev/null

# 4. Login as Staff
echo "Logging in as Staff ($EMAIL)..."
STAFF_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=password123" | jq -r '.access_token')

if [ "$STAFF_TOKEN" == "null" ] || [ -z "$STAFF_TOKEN" ]; then
    echo "FAILED: Staff login."
    exit 1
fi

# 5. Test /me endpoint as Staff
echo "Testing /api/users/me as Staff..."
RESPONSE=$(curl -s -X GET "$BASE_URL/api/users/me" \
  -H "Authorization: Bearer $STAFF_TOKEN")

STAFF_EMAIL=$(echo "$RESPONSE" | jq -r '.email')
SICK_LEAVE=$(echo "$RESPONSE" | jq -r '.sick_leave_days')

echo "Staff /me returned email: $STAFF_EMAIL"
echo "Sick Leave Days: $SICK_LEAVE"

if [ "$STAFF_EMAIL" == "$EMAIL" ] && [ "$SICK_LEAVE" == "5" ]; then
    echo "SUCCESS: /me works correctly."
    exit 0
else
    echo "FAILED: /me response incorrect."
    echo "Response: $RESPONSE"
    exit 1
fi
