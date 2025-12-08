#!/bin/bash

# JWT Authentication Test Script
# This script tests the complete JWT authentication flow

set -e  # Exit on error

echo "======================================================================"
echo "JWT Authentication Test"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AUTH_URL="http://localhost/auth"
INTERVIEW_URL="http://localhost/interview"
TEST_EMAIL="test_jwt_$(date +%s)@example.com"
TEST_USERNAME="testuser_$(date +%s)"
TEST_PASSWORD="TestPass123!"

echo -e "${YELLOW}Step 1: Registering a new user...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "${AUTH_URL}/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"username\": \"${TEST_USERNAME}\",
    \"password\": \"${TEST_PASSWORD}\",
    \"role\": \"candidate\",
    \"date_of_birth\": \"1990-01-01\"
  }")

echo "Response: ${REGISTER_RESPONSE}"

if echo "${REGISTER_RESPONSE}" | grep -q "User registered successfully"; then
    echo -e "${GREEN}✓ User registered successfully${NC}"
else
    echo -e "${RED}✗ Failed to register user${NC}"
    echo "Response: ${REGISTER_RESPONSE}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 2: Logging in to get JWT token...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "${AUTH_URL}/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"${TEST_PASSWORD}\"
  }")

echo "Response: ${LOGIN_RESPONSE}"

# Extract access token
ACCESS_TOKEN=$(echo "${LOGIN_RESPONSE}" | grep -o '"access":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}✗ Failed to get access token${NC}"
    echo "Response: ${LOGIN_RESPONSE}"
    exit 1
fi

echo -e "${GREEN}✓ Login successful${NC}"
echo "Access Token (first 50 chars): ${ACCESS_TOKEN:0:50}..."

echo ""
echo -e "${YELLOW}Step 3: Waiting 3 seconds for Kafka sync...${NC}"
sleep 3

echo ""
echo -e "${YELLOW}Step 4: Testing authenticated request to interview_service...${NC}"
PROFILE_RESPONSE=$(curl -s -X GET "${INTERVIEW_URL}/api/v1/profiles/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

echo "Response: ${PROFILE_RESPONSE}"

if echo "${PROFILE_RESPONSE}" | grep -q "data"; then
    echo -e "${GREEN}✓ Authenticated request successful!${NC}"
    echo -e "${GREEN}✓ JWT authentication is working correctly across services!${NC}"
else
    echo -e "${RED}✗ Authenticated request failed${NC}"
    echo "This might mean:"
    echo "  1. JWT_SIGNING_KEY mismatch between services"
    echo "  2. User not synced via Kafka yet (wait longer)"
    echo "  3. interview_service authentication not configured correctly"
    exit 1
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}All JWT authentication tests passed!${NC}"
echo "======================================================================"
echo ""
echo "Summary:"
echo "  - User registered in auth_service: ${TEST_EMAIL}"
echo "  - JWT token generated and validated"
echo "  - Token successfully used in interview_service"
echo "  - Cross-service authentication working!"
