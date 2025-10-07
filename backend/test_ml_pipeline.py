"""
Test script to verify ML pipeline functions work correctly
Run this from the backend directory: python test_ml_pipeline.py
"""

from ml_pipeline import calculate_severity, estimate_repair_cost, optimize_repair_budget, generate_repair_schedule

print("\n" + "="*60)
print("🧪 TESTING ML PIPELINE")
print("="*60)

# Test 1: Severity Calculation
print("\n1. Testing Severity Calculation:")
print("-" * 40)

test_cases_severity = [
    (55, True, "Low confidence damage"),
    (75, True, "Medium confidence damage"),
    (90, True, "High confidence damage"),
    (98, True, "Very high confidence damage"),
    (50, False, "No damage detected"),
]

for confidence, is_damage, description in test_cases_severity:
    severity = calculate_severity(confidence, is_damage)
    print(f"{description:30} | Confidence: {confidence}% | Severity: {severity}/10")

# Test 2: Cost Estimation
print("\n2. Testing Cost Estimation:")
print("-" * 40)

for severity in range(0, 11):
    cost = estimate_repair_cost(severity, 'Pothole')
    print(f"Severity {severity:2}/10 → ₦{cost:,}")

# Test 3: Budget Optimization
print("\n3. Testing Budget Optimization:")
print("-" * 40)

# Create sample reports
sample_reports = [
    {'id': 1, 'severity': 9, 'cost': 95000, 'location': 'Lekki Phase 1'},
    {'id': 2, 'severity': 5, 'cost': 40000, 'location': 'Victoria Island'},
    {'id': 3, 'severity': 7, 'cost': 60000, 'location': 'Ikeja GRA'},
    {'id': 4, 'severity': 3, 'cost': 25000, 'location': 'Surulere'},
    {'id': 5, 'severity': 8, 'cost': 75000, 'location': 'Yaba'},
    {'id': 6, 'severity': 6, 'cost': 50000, 'location': 'Allen Avenue'},
]

budgets = [100000, 200000, 300000]

for budget in budgets:
    print(f"\nBudget: ₦{budget:,}")
    result = optimize_repair_budget(sample_reports, budget)
    
    print(f"  Status: {result['optimization_status']}")
    print(f"  Repairs scheduled: {result['repairs_count']}")
    print(f"  Total severity addressed: {result['total_severity']}")
    print(f"  Total cost: ₦{result['total_cost']:,}")
    print(f"  Budget utilization: {result['budget_utilization']:.1f}%")
    print(f"  Selected report IDs: {result['selected_repairs']}")

# Test 4: Full Pipeline
print("\n4. Testing Complete Pipeline:")
print("-" * 40)

full_reports = [
    {
        'id': 1,
        'tracking_number': 'RW-001',
        'severity_score': 8,
        'estimated_cost': 75000,
        'location': 'Test Location 1',
        'damage_type': 'Pothole',
        'damage_detected': True
    },
    {
        'id': 2,
        'tracking_number': 'RW-002',
        'severity_score': 5,
        'estimated_cost': 40000,
        'location': 'Test Location 2',
        'damage_type': 'Pothole',
        'damage_detected': True
    },
]

schedule = generate_repair_schedule(full_reports, 100000)

print(f"Scheduled repairs: {schedule['repairs_count']}")
print(f"Total cost: ₦{schedule['total_cost']:,}")
print(f"Budget utilization: {schedule['budget_utilization']:.1f}%")
print(f"\nScheduled reports:")
for report in schedule['scheduled_reports']:
    print(f"  - {report['tracking_number']}: {report['location']} "
          f"(Severity: {report['severity_score']}, Cost: ₦{report['estimated_cost']:,})")

print("\n" + "="*60)
print(" ALL TESTS COMPLETED!")
print("="*60 + "\n")