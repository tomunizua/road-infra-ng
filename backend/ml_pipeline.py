"""
Enhanced ML Pipeline with Realistic Budget and Human Capital Analysis
Based on Lagos State road maintenance budget and socioeconomic impact
"""

import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus

# ========================
# LAGOS STATE CONSTANTS
# ========================

# Realistic annual budget for Lagos State road maintenance
LAGOS_ANNUAL_BUDGET = 25_000_000_000  # ₦25 billion (conservative estimate)
QUARTERLY_BUDGET = LAGOS_ANNUAL_BUDGET / 4  # ₦6.25 billion per quarter
MONTHLY_BUDGET = LAGOS_ANNUAL_BUDGET / 12  # ₦2.08 billion per month

# Cost breakdown by severity (in Naira)
REPAIR_COST_MAPPING = {
    0: 0, 1: 50_000, 2: 75_000, 3: 150_000, 4: 250_000, 5: 400_000,
    6: 600_000, 7: 900_000, 8: 1_500_000, 9: 2_500_000, 10: 4_000_000
}


def calculate_severity(confidence, damage_detected):
    """
    Convert ML confidence into severity score (0-10)
    Enhanced with more granular levels
    """
    if not damage_detected:
        return 0
    
    # More nuanced severity mapping
    if confidence < 55:
        return 1  # Minimal damage
    elif confidence < 62:
        return 2
    elif confidence < 68:
        return 3
    elif confidence < 74:
        return 4
    elif confidence < 80:
        return 5  # Moderate damage
    elif confidence < 85:
        return 6
    elif confidence < 90:
        return 7
    elif confidence < 93:
        return 8
    elif confidence < 97:
        return 9
    else:
        return 10  # Critical damage
    

def estimate_repair_cost(severity_score, damage_type='Pothole', location_factor=1.0):
    """
    Estimate repair cost with Lagos-specific factors
    
    Args:
        severity_score: 0-10 scale
        damage_type: Type of damage
        location_factor: Multiplier for high-traffic areas (1.0-1.5)
    """
    if severity_score == 0:
        return 0
    
    base_cost = REPAIR_COST_MAPPING.get(severity_score, 500_000)
    
    # Add realistic variation (±15%)
    variation = np.random.uniform(0.85, 1.15)
    
    # Apply location factor (high-traffic areas cost more)
    final_cost = int(base_cost * variation * location_factor)
    
    return final_cost


def optimize_repair_budget(reports, total_budget):
    """
    Optimize repair schedule using linear programming (Knapsack problem).
    
    Args:
        reports: List of repair reports with severity and cost
        total_budget: Available budget in Naira
    """
    if not reports or total_budget <= 0:
        return {
            'selected_repairs': [],
            'total_cost': 0,
            'total_severity': 0,
            'budget_utilization': 0,
            'repairs_count': 0,
            'optimization_status': 'NoReportsOrBudget'
        }
    
    # Filter valid reports
    actionable_reports = [r for r in reports 
                         if r.get('severity', r.get('severity_score', 0)) > 0]
    
    if not actionable_reports:
        return {**optimize_repair_budget([], 0), 'optimization_status': 'NoActionableReports'}
    
    # Create optimization problem
    problem = LpProblem("Road_Repair_Optimization", LpMaximize)
    
    # Decision variables: binary for each repair
    repair_vars = {
        i: LpVariable(f"repair_{i}", cat='Binary')
        for i in range(len(actionable_reports))
    }
    
    # Objective: Maximize total severity score
    objective = lpSum([
        actionable_reports[i].get('severity', actionable_reports[i].get('severity_score', 0)) * repair_vars[i]
        for i in range(len(actionable_reports))
    ])
    
    problem += objective, "Maximize_Total_Severity"
    
    # Constraint 1: Budget
    problem += lpSum([
        actionable_reports[i].get('cost', 
        actionable_reports[i].get('estimated_cost', 0)) * repair_vars[i]
        for i in range(len(actionable_reports))
    ]) <= total_budget, "Budget_Constraint"
    
    # Solve
    problem.solve()
    
    # Extract results
    selected_indices = [
        i for i in range(len(actionable_reports))
        if repair_vars[i].value() == 1
    ]
    
    selected_repairs = [actionable_reports[i]['id'] for i in selected_indices]
    
    total_cost = sum([
        actionable_reports[i].get('cost', 
        actionable_reports[i].get('estimated_cost', 0))
        for i in selected_indices
    ])
    
    total_severity = sum([
        actionable_reports[i].get('severity', 
        actionable_reports[i].get('severity_score', 0))
        for i in selected_indices
    ])
    
    budget_utilization = (total_cost / total_budget * 100) if total_budget > 0 else 0
    
    return {
        'selected_repairs': selected_repairs,
        'total_cost': total_cost,
        'total_severity': total_severity,
        'budget_utilization': round(budget_utilization, 2),
        'repairs_count': len(selected_repairs),
        'optimization_status': LpStatus[problem.status],
        'budget_context': {
            'budget_used': total_cost,
            'budget_available': total_budget,
            'budget_remaining': total_budget - total_cost,
            'percentage_of_monthly_budget': round((total_cost / MONTHLY_BUDGET) * 100, 2),
            'percentage_of_quarterly_budget': round((total_cost / QUARTERLY_BUDGET) * 100, 2),
            'percentage_of_annual_budget': round((total_cost / LAGOS_ANNUAL_BUDGET) * 100, 2),
        }
    }


def generate_repair_schedule(reports, budget, time_period='monthly'):
    """
    Complete pipeline for budget optimization.
    
    Args:
        reports: List of reports
        budget: Available budget (or use default based on time_period)
        time_period: 'monthly', 'quarterly', or 'annual'
    """
    # Use realistic budget if not specified
    if budget is None or budget == 0:
        if time_period == 'monthly':
            budget = MONTHLY_BUDGET
        elif time_period == 'quarterly':
            budget = QUARTERLY_BUDGET
        else:
            budget = LAGOS_ANNUAL_BUDGET
    
    # Prepare optimization input
    optimization_input = []
    for report in reports:
        if report.get('damage_detected', False):
            optimization_input.append({
                'id': report['id'],
                'severity': report.get('severity_score', 0),
                'cost': report.get('estimated_cost', 0),
                'location': report.get('location', 'Unknown')
            })
    
    # Run optimization
    schedule = optimize_repair_budget(optimization_input, budget)
    
    # Add detailed report info
    scheduled_reports = []
    for report in reports:
        if report['id'] in schedule['selected_repairs']:
            scheduled_reports.append(report)
    
    schedule['scheduled_reports'] = scheduled_reports
    schedule['time_period'] = time_period
    
    return schedule