"""
Data converter between database format and budget optimization format
"""
from typing import Dict, List, Any

def database_report_to_budget_format(report: Dict[str, Any]) -> Dict[str, Any]:
    """Convert database Report model to budget optimization input format"""
    
    # Default values if AI hasn't processed it yet
    severity_score = report.get('severity_score', 0)
    damage_type = report.get('damage_type', 'unknown')
    
    # Map severity score (0-100) to categorical severity
    # Note: DB stores 0-100, Logic expects 0-10 scale roughly
    score_norm = severity_score / 10.0 
    
    if severity_score >= 70:
        severity = "Severe"
        urgency = "immediate"
    elif severity_score >= 30:
        severity = "Moderate"
        urgency = "urgent"
    else:
        severity = "Minor"
        urgency = "routine"
    
    # Estimate dimensions based on type (Heuristics)
    if "crack" in str(damage_type).lower():
        length, breadth, depth = 150, 100, 8
    elif "pothole" in str(damage_type).lower():
        length, breadth, depth = 100, 80, 15
    else:
        length, breadth, depth = 80, 60, 10
    
    # Scale by severity
    multiplier = max(0.5, score_norm / 5.0)
    length = int(length * multiplier)
    breadth = int(breadth * multiplier)
    
    return {
        "tracking_number": report.get("tracking_number", "unknown"),
        "length_cm": length,
        "breadth_cm": breadth,
        "depth_cm": depth,
        "severity": severity,
        "urgency": urgency,
        "image_path": report.get("photo_url") or "unknown",
        "damage_type": damage_type
    }

def batch_convert_reports(reports: List[Dict[str, Any]]) -> tuple:
    """Convert multiple database reports"""
    converted = []
    skipped = []
    
    for i, report in enumerate(reports):
        try:
            # Basic validation
            if not report.get('tracking_number'):
                continue
                
            converted_report = database_report_to_budget_format(report)
            converted.append(converted_report)
        except Exception as e:
            skipped.append({
                "index": i,
                "error": str(e)
            })
    
    return converted, skipped

def get_conversion_stats(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get stats about the data"""
    stats = {
        "total_reports": len(reports),
        "severity_breakdown": {"Severe": 0, "Moderate": 0, "Minor": 0}
    }
    for r in reports:
        score = r.get('severity_score', 0)
        if score >= 70: stats["severity_breakdown"]["Severe"] += 1
        elif score >= 30: stats["severity_breakdown"]["Moderate"] += 1
        else: stats["severity_breakdown"]["Minor"] += 1
    return stats