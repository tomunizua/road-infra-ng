"""
Test script for the enhanced but focused budget pipeline.
Run from the backend directory: python test_budget_pipeline.py
"""

from pipeline import (
    calculate_severity,
    estimate_repair_cost,
    optimize_repair_budget,
    generate_repair_schedule,
    MONTHLY_BUDGET
)

print("\n" + "="*60)
print("🧪 TESTING ENHANCED BUDGET PIPELINE")
print("="*60)

# Test 1: Severity Calculation (Granular)
print("\n1. Testing Granular Severity Calculation:")
print("-" * 40)
test_cases_severity = [
    (52, True, "Minimal damage"),
    (65, True, "Low-moderate damage"),
    (78, True, "Moderate damage"),
    (91, True, "Severe damage"),
    (98, True, "Critical damage"),
]
for confidence, is_damage, description in test_cases_severity:
    severity = calculate_severity(confidence, is_damage)
    print(f"{description:30} | Confidence: {confidence}% | Severity: {severity}/10")

# Test 2: Cost Estimation (Lagos-specific)
print("\n2. Testing Realistic Cost Estimation:")
print("-" * 40)
for severity in range(1, 11):
    cost = estimate_repair_cost(severity, 'Pothole')
    print(f"Severity {severity:2}/10 → Estimated Cost: ₦{cost:,}")

# Test 3: Budget Optimization (Focused)
print("\n3. Testing Focused Budget Optimization:")
print("-" * 40)

sample_reports = [
    {'id': 1, 'severity': 9, 'cost': 2_500_000, 'location': 'Lekki Phase 1'},
    {'id': 2, 'severity': 5, 'cost': 400_000, 'location': 'Victoria Island'},
    {'id': 3, 'severity': 7, 'cost': 900_000, 'location': 'Ikeja GRA'},
    {'id': 4, 'severity': 8, 'cost': 1_500_000, 'location': 'Yaba'},
    {'id': 5, 'severity': 6, 'cost': 600_000, 'location': 'Allen Avenue'},
]

budget = 3_000_000  # ₦3 Million budget

print(f"\nBudget: ₦{budget:,}")
result = optimize_repair_budget(sample_reports, budget)

print(f"  Status: {result['optimization_status']}")
print(f"  Repairs scheduled: {result['repairs_count']}")
print(f"  Total severity addressed: {result['total_severity']}")
print(f"  Total cost: ₦{result['total_cost']:,}")
print(f"  Budget utilization: {result['budget_utilization']:.1f}%")
print(f"  Selected report IDs: {result['selected_repairs']}")

# Test 4: Full Schedule Generation
print("\n4. Testing Full Repair Schedule Generation:")
print("-" * 40)

full_reports_input = [
    {'id': 101, 'damage_detected': True, 'severity_score': 8, 'estimated_cost': 1_500_000, 'location': 'Apapa'},
    {'id': 102, 'damage_detected': True, 'severity_score': 9, 'estimated_cost': 2_500_000, 'location': 'Oshodi'},
    {'id': 103, 'damage_detected': False, 'severity_score': 0, 'estimated_cost': 0, 'location': 'Ikoyi'},
    {'id': 104, 'damage_detected': True, 'severity_score': 7, 'estimated_cost': 900_000, 'location': 'Festac'},
]

schedule = generate_repair_schedule(full_reports_input, 4_000_000)

print(f"Schedule for a ₦4,000,000 budget:")
print(f"  - Total repairs: {schedule['repairs_count']}")
print(f"  - Total cost: ₦{schedule['total_cost']:,} ({schedule['budget_utilization']:.1f}% utilization)")
print(f"  - Scheduled Reports (IDs): {[r['id'] for r in schedule['scheduled_reports']]}")

print("\n" + "="*60)
print(" ALL BUDGET PIPELINE TESTS COMPLETED!")
print("="*60 + "\n")