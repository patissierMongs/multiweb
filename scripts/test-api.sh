#!/bin/bash

# Simple API test script

API_URL="${1:-http://localhost:8000}"

echo "Testing MultiWeb API at $API_URL"
echo "=========================================="
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
response=$(curl -s -w "\n%{http_code}" "$API_URL/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo "✓ Health check passed"
    echo "  Response: $body"
else
    echo "✗ Health check failed (HTTP $http_code)"
    exit 1
fi

echo ""

# Test ready endpoint
echo "2. Testing readiness endpoint..."
response=$(curl -s -w "\n%{http_code}" "$API_URL/health/ready")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" = "200" ]; then
    echo "✓ Readiness check passed"
else
    echo "⚠️  Readiness check failed (HTTP $http_code)"
    echo "  This may indicate database or cache connectivity issues"
fi

echo ""

# Test API docs
echo "3. Testing API documentation..."
response=$(curl -s -w "\n%{http_code}" "$API_URL/docs")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" = "200" ]; then
    echo "✓ API docs accessible at $API_URL/docs"
else
    echo "⚠️  API docs not accessible"
fi

echo ""

# Test product list endpoint
echo "4. Testing product list endpoint..."
response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/products/")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" = "200" ]; then
    echo "✓ Product list endpoint working"
else
    echo "✗ Product list endpoint failed (HTTP $http_code)"
fi

echo ""
echo "=========================================="
echo "API test completed!"
echo "=========================================="
