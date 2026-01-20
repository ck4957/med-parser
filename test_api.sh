#!/bin/bash

# Quick test script for MLX Django API endpoints
# Run this after: python manage.py runserver

BASE_URL="http://localhost:8000"

echo "========================================================================"
echo "🧪 Testing MLX Medical Parser API"
echo "========================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "📋 Test 1: Health Check"
echo "   GET ${BASE_URL}/api/health/"
echo ""
response=$(curl -s -w "\n%{http_code}" "${BASE_URL}/api/health/")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo -e "   ${GREEN}✅ Status: $http_code${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "   ${RED}❌ Status: $http_code${NC}"
    echo "$body"
fi
echo ""
echo "------------------------------------------------------------------------"
echo ""

# Test 2: Model Info
echo "📋 Test 2: Model Information"
echo "   GET ${BASE_URL}/api/model-info/"
echo ""
response=$(curl -s -w "\n%{http_code}" "${BASE_URL}/api/model-info/")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo -e "   ${GREEN}✅ Status: $http_code${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "   ${RED}❌ Status: $http_code${NC}"
    echo "$body"
fi
echo ""
echo "------------------------------------------------------------------------"
echo ""

# Test 3: Process Medical Text (Basic)
echo "📋 Test 3: Process Medical Text (Basic)"
echo "   POST ${BASE_URL}/api/process-medical-text/"
echo ""

payload=$(cat <<'EOF'
{
  "transcript": "Patient is a 58-year-old male with hypertension. Started on Lisinopril 10mg once daily.",
  "validate_fhir": true,
  "use_fallback": false
}
EOF
)

echo "   Request Body:"
echo "$payload" | python3 -m json.tool
echo ""
echo "   ${YELLOW}⏳ Processing... (this may take 30-60 seconds on first run)${NC}"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/process-medical-text/" \
  -H "Content-Type: application/json" \
  -d "$payload")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo -e "   ${GREEN}✅ Status: $http_code${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "   ${RED}❌ Status: $http_code${NC}"
    echo "$body"
fi
echo ""
echo "------------------------------------------------------------------------"
echo ""

# Test 4: Process Medical Text (Advanced with Fallback)
echo "📋 Test 4: Process Medical Text (with Fallback)"
echo "   POST ${BASE_URL}/api/process-medical-text/"
echo ""

payload=$(cat <<'EOF'
{
  "transcript": "Patient has type 2 diabetes mellitus and essential HTN. Current medications: Metformin 1000mg BID, Lisinopril 20mg QD. Adding Atorvastatin 40mg at bedtime for hyperlipidemia.",
  "validate_fhir": true,
  "use_fallback": true
}
EOF
)

echo "   Request Body:"
echo "$payload" | python3 -m json.tool
echo ""
echo "   ${YELLOW}⏳ Processing with self-correction and fallback...${NC}"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/process-medical-text/" \
  -H "Content-Type: application/json" \
  -d "$payload")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo -e "   ${GREEN}✅ Status: $http_code${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "   ${RED}❌ Status: $http_code${NC}"
    echo "$body"
fi
echo ""
echo "------------------------------------------------------------------------"
echo ""

# Test 5: Error Handling (Empty Transcript)
echo "📋 Test 5: Error Handling (Empty Transcript)"
echo "   POST ${BASE_URL}/api/process-medical-text/"
echo ""

payload='{"transcript": "", "validate_fhir": true}'
echo "   Request Body: $payload"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/process-medical-text/" \
  -H "Content-Type: application/json" \
  -d "$payload")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 400 ]; then
    echo -e "   ${GREEN}✅ Status: $http_code (expected error)${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "   ${YELLOW}⚠️  Status: $http_code (expected 400)${NC}"
    echo "$body"
fi
echo ""
echo "------------------------------------------------------------------------"
echo ""

# Summary
echo "========================================================================"
echo "🎉 Test Suite Complete"
echo "========================================================================"
echo ""
echo "💡 Tips:"
echo "   - First request is slow (model loading)"
echo "   - Subsequent requests are much faster"
echo "   - Check terminal logs for detailed MLX output"
echo ""
echo "🔗 API Documentation:"
echo "   Health: GET  ${BASE_URL}/api/health/"
echo "   Info:   GET  ${BASE_URL}/api/model-info/"
echo "   Parse:  POST ${BASE_URL}/api/process-medical-text/"
echo ""
echo "========================================================================"
