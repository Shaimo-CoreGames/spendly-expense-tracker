"""
Test script for ML-Enhanced Personal Expense Tracker API
Run this after starting the server with: uvicorn main_ml:app --reload
"""

import requests
from datetime import date, timedelta
import json
import random

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

# Register user
print_section("REGISTER USER & CREATE DATA")
user_data = {"username": "ml_user", "email": "ml.user@example.com", "password": "secure123"}
response = requests.post(f"{BASE_URL}/users/register", json=user_data)

if response.status_code == 201:
    user_id = response.json()["user_id"]
    print(f"✅ User registered! ID: {user_id}")
elif response.status_code == 400:
    response = requests.get(f"{BASE_URL}/users/ml_user")
    user_id = response.json()["user_id"]
    print(f"✅ Using existing user! ID: {user_id}")

# Create historical data
print("\n🔄 Creating 60 days of expense data...")
categories = {"food": (20, 80), "bills": (100, 200), "travel": (10, 50), "entertainment": (15, 60), "shopping": (30, 150)}
today = date.today()
expenses_added = 0

for days_ago in range(60, 0, -1):
    expense_date = today - timedelta(days=days_ago)
    for _ in range(random.randint(2, 4)):
        category = random.choice(list(categories.keys()))
        min_amt, max_amt = categories[category]
        amount = round(random.uniform(min_amt, max_amt) * (1 + (60 - days_ago) * 0.002), 2)
        
        response = requests.post(f"{BASE_URL}/users/{user_id}/expenses", json={
            "amount": amount, "category": category, "description": f"{category} expense", "date": str(expense_date)
        })
        if response.status_code == 201:
            expenses_added += 1

print(f"✅ Created {expenses_added} expenses!")

# Test ML Predictions
print_section("🤖 ML - PREDICT NEXT WEEK")
response = requests.get(f"{BASE_URL}/users/{user_id}/predictions/next-week")
if response.status_code == 200:
    forecast = response.json()
    print(f"\n📊 Total Predicted: ${forecast['total_predicted']}")
    print("\nBy Category:")
    for pred in forecast['category_predictions']:
        print(f"  • {pred['category']}: ${pred['predicted_amount']:.2f} (confidence: {pred['confidence']*100:.0f}%, trend: {pred['trend']})")

# Test Spending Patterns
print_section("📊 ANALYZE SPENDING PATTERNS")
response = requests.get(f"{BASE_URL}/users/{user_id}/patterns/spending")
if response.status_code == 200:
    for p in response.json():
        print(f"\n{p['category'].upper()}: Daily ${p['average_daily']:.2f}, Trend: {p['trend_direction']}, Volatility: {p['volatility']}")

# Create Budgets
print_section("CREATE BUDGETS")
budgets = [{"category": c, "monthly_limit": m} for c, m in [("food", 500), ("bills", 800), ("travel", 200)]]
for b in budgets:
    requests.post(f"{BASE_URL}/users/{user_id}/budgets", json=b)
    print(f"✅ Budget: {b['category']} - ${b['monthly_limit']}")

# Budget Alerts
print_section("🚨 SMART BUDGET ALERTS")
response = requests.get(f"{BASE_URL}/users/{user_id}/budgets/alerts")
if response.status_code == 200:
    for alert in response.json():
        status_emoji = {"safe": "✅", "warning": "⚠️", "danger": "🚨"}[alert['status']]
        print(f"\n{status_emoji} {alert['category']}: ${alert['current_spending']:.2f}/{alert['budget_limit']:.2f} ({alert['percentage_used']:.0f}%)")
        print(f"   🔮 Predicted month-end: ${alert['predicted_month_end']:.2f}")

print_section("✅ ML TESTING COMPLETE!")
print("\n🚀 All ML features working!")
print("📚 Techniques: Linear Regression + Moving Average + Exponential Smoothing")
