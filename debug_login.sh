#!/bin/bash
BASE_URL="http://localhost:8100"

echo "1. Debugging Admin Login..."
# Remove -s to see errors, print body
RESPONSE=$(curl -v -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin" 2>&1)

echo "--- RAW RESPONSE ---"
echo "$RESPONSE"
echo "--------------------"

# Extract token from the last line (body) if successful
# We'll use a cleaner approach: separate body file
curl -s -o login_response.json -w "%{http_code}" -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=admin" > login_status.txt

CODE=$(cat login_status.txt)
echo "HTTP Status: $CODE"
cat login_response.json

if [ "$CODE" != "200" ]; then
    echo "Login failed with status $CODE"
    exit 1
fi

ADMIN_TOKEN=$(cat login_response.json | jq -r '.access_token')
echo "Token: $ADMIN_TOKEN"

if [ "$ADMIN_TOKEN" == "null" ]; then
    echo "Failed to parse token."
    exit 1
fi

echo "2. Testing /me..."
curl -s -X GET "$BASE_URL/api/users/me" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .
