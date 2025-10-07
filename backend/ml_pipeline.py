import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus

def calculate_severity(confidence, damage_detected):
    """
    Convert ML confidence into severity score (1-10)
    Based on model's certainty about damage presence
    
    Logic:
    - No damage detected → 0
    - Low confidence (50-60%) → Minor damage (3-4)
    - Medium confidence (60-80%) → Moderate damage (5-7)
    - High confidence (80-95%) → Severe damage (8-9)
    - Very high confidence (95-100%) → Critical damage (10)
    """
    if not damage_detected:
        return 0
    
    # Map confidence percentage to severity scale
    if confidence < 60:
        severity = 3
    elif confidence < 70:
        severity = 5
    elif confidence < 80:
        severity = 6
    elif confidence < 85:
        severity = 7
    elif confidence < 90:
        severity = 8
    elif confidence < 95:
        severity = 9
    else:
        severity = 10
    
    return severity


def estimate_repair_cost(severity_score, damage_type='Pothole'):
    """
    Estimate repair cost based on severity and damage type
    
    Cost breakdown (Nigerian Naira):
    - Severity 0: ₦0 (no damage)
    - Severity 1-3: ₦15,000-25,000 (minor repairs)
    - Severity 4-6: ₦30,000-50,000 (moderate repairs)
    - Severity 7-8: ₦60,000-80,000 (major repairs)
    - Severity 9-10: ₦90,000-120,000 (critical repairs)
    """
    if severity_score == 0:
        return 0
    
    cost_mapping = {
        1: 15000, 2: 18000, 3: 25000,
        4: 30000, 5: 40000, 6: 50000,
        7: 60000, 8: 75000,
        9: 95000, 10: 115000
    }
    
    base_cost = cost_mapping.get(severity_score, 50000)
    
    # Add some randomness to make it realistic (±10%)
    variation = np.random.uniform(-0.1, 0.1)
    final_cost = int(base_cost * (1 + variation))
    
    return final_cost


def optimize_repair_budget(reports, total_budget):
    """
    Optimize repair schedule using linear programming
    
    Objective: Maximize total severity score addressed
    Constraint: Total cost <= available budget
    
    Args:
        reports: List of dicts with keys: 'id', 'severity', 'cost', 'location'
        total_budget: Total available budget in Naira
    
    Returns:
        dict with:
            - selected_repairs: List of report IDs to repair
            - total_cost: Total cost of selected repairs
            - total_severity: Total severity addressed
            - budget_utilization: Percentage of budget used
            - repairs_count: Number of repairs scheduled
    """
    
    if not reports or total_budget <= 0:
        return {
            'selected_repairs': [],
            'total_cost': 0,
            'total_severity': 0,
            'budget_utilization': 0,
            'repairs_count': 0
        }
    
    # Filter out reports with no damage
    actionable_reports = [r for r in reports if r['severity'] > 0]
    
    if not actionable_reports:
        return {
            'selected_repairs': [],
            'total_cost': 0,
            'total_severity': 0,
            'budget_utilization': 0,
            'repairs_count': 0
        }
    
    # Create optimization problem
    problem = LpProblem("Road_Repair_Optimization", LpMaximize)
    
    # Decision variables: binary (0 or 1) for each repair
    repair_vars = {
        report['id']: LpVariable(f"repair_{report['id']}", cat='Binary')
        for report in actionable_reports
    }
    
    # Objective function: Maximize sum of severity scores
    problem += lpSum([
        report['severity'] * repair_vars[report['id']]
        for report in actionable_reports
    ]), "Total_Severity_Addressed"
    
    # Budget constraint
    problem += lpSum([
        report['cost'] * repair_vars[report['id']]
        for report in actionable_reports
    ]) <= total_budget, "Budget_Constraint"
    
    # Solve the problem
    problem.solve()
    
    # Extract results
    selected_repairs = [
        report['id'] 
        for report in actionable_reports 
        if repair_vars[report['id']].value() == 1
    ]
    
    total_cost = sum([
        report['cost'] 
        for report in actionable_reports 
        if repair_vars[report['id']].value() == 1
    ])
    
    total_severity = sum([
        report['severity'] 
        for report in actionable_reports 
        if repair_vars[report['id']].value() == 1
    ])
    
    budget_utilization = (total_cost / total_budget * 100) if total_budget > 0 else 0
    
    return {
        'selected_repairs': selected_repairs,
        'total_cost': total_cost,
        'total_severity': total_severity,
        'budget_utilization': round(budget_utilization, 2),
        'repairs_count': len(selected_repairs),
        'optimization_status': LpStatus[problem.status]
    }


def generate_repair_schedule(reports, budget):
    """
    Complete pipeline: takes reports, runs optimization, returns schedule
    
    This demonstrates the full research contribution:
    1. ML model classifies damage
    2. Severity calculation from confidence
    3. Cost estimation based on severity
    4. Optimization to maximize impact within budget
    """
    
    # Prepare data for optimization
    optimization_input = []
    for report in reports:
        if report.get('damage_detected', False):
            optimization_input.append({
                'id': report['id'],
                'severity': report['severity_score'],
                'cost': report['estimated_cost'],
                'location': report.get('location', 'Unknown')
            })
    
    # Run optimization
    schedule = optimize_repair_budget(optimization_input, budget)
    
    # Add report details to schedule
    scheduled_reports = [
        report for report in reports 
        if report['id'] in schedule['selected_repairs']
    ]
    
    schedule['scheduled_reports'] = scheduled_reports
    
    return schedule