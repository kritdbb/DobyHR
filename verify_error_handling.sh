#!/bin/bash
BASE_URL="http://localhost:8100"

# 1. Login as Admin
ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin" | jq -r '.access_token')

# 2. Create User (First time - should succeed or fail if exists)
EMAIL="duplicate.test@example.com"
curl -s -X POST "$BASE_URL/api/users/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Duplicate\",
    \"surname\": \"Test\",
    \"email\": \"$EMAIL\",
    \"password\": \"password123\",
    \"role\": \"staff\"
  }" > /dev/null

# 3. Create User AGAIN (Should fail with 400)
echo "Attempting to create duplicate user..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/users/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Duplicate\",
    \"surname\": \"Test\",
    \"email\": \"$EMAIL\",
    \"password\": \"password123\",
    \"role\": \"staff\"
  }")

BODY=$(echo "$RESPONSE" | head -n 1)
CODE=$(echo "$RESPONSE" | tail -n 1)

echo "Status Code: $CODE"
echo "Response Body: $BODY"

if [ "$CODE" == "400" ]; then
    if [[ "$BODY" == *"Email already registered"* ]]; then
        echo "SUCCESS: Caught duplicate email correctly."
        exit 0
    else
        echo "FAILED: Got 400 but wrong message."
        exit 1
    fi
else
    echo "FAILED: Expected 400, got $CODE"
    exit 1
fi
