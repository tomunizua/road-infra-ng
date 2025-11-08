"""
Data converter between database format and budget optimization format
Handles mapping between Report model and EnhancedRepairFinancials requirements
"""
from typing import Dict, List, Any


def database_report_to_budget_format(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert database Report model to budget optimization input format
    
    Args:
        report: Dictionary from database with fields like:
                {damage_type, severity_score, estimated_cost, tracking_number, ...}
    
    Returns:
        Dictionary in budget optimization format with fields like:
        {length_cm, breadth_cm, depth_cm, severity, urgency, image_path}
    
    Raises:
        ValueError: If required fields are missing
    """
    
    # Validate required fields
    required_fields = ['damage_type', 'severity_score', 'tracking_number']
    missing = [f for f in required_fields if f not in report]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    
    severity_score = report.get('severity_score', 5)
    damage_type = report.get('damage_type', 'unknown')
    
    # Map severity score (0-10) to categorical severity
    if severity_score >= 8:
        severity = "Severe"
    elif severity_score >= 5:
        severity = "Moderate"
    else:
        severity = "Minor"
    
    # Estimate dimensions from damage type and severity if not provided
    # These are heuristic defaults based on typical road damage patterns
    if "crack" in damage_type.lower():
        length, breadth, depth = 150, 100, 8
    elif "pothole" in damage_type.lower():
        length, breadth, depth = 100, 80, 15
    elif "rut" in damage_type.lower():
        length, breadth, depth = 200, 50, 12
    elif "spalling" in damage_type.lower():
        length, breadth, depth = 120, 90, 10
    else:
        length, breadth, depth = 80, 60, 10
    
    # Scale dimensions by normalized severity (0-10 -> 0.5-1.5 multiplier)
    severity_multiplier = (severity_score / 5)  # 0-10 -> 0-2 range
    length = int(length * severity_multiplier)
    breadth = int(breadth * severity_multiplier)
    depth = int(depth * severity_multiplier)
    
    # Ensure minimum dimensions
    length = max(length, 50)
    breadth = max(breadth, 30)
    depth = max(depth, 5)
    
    # Determine urgency based on severity (can be overridden by report urgency field)
    if "urgency" in report and report["urgency"] in ["immediate", "urgent", "routine"]:
        urgency = report["urgency"]
    else:
        # Default urgency based on severity
        if severity_score >= 8:
            urgency = "immediate"
        elif severity_score >= 5:
            urgency = "urgent"
        else:
            urgency = "routine"
    
    return {
        "tracking_number": report.get("tracking_number", "unknown"),
        "length_cm": length,
        "breadth_cm": breadth,
        "depth_cm": depth,
        "severity": severity,
        "urgency": urgency,
        "image_path": report.get("image_filename", f"report_{report.get('tracking_number', 'unknown')}.jpg"),
        "damage_type": damage_type
    }


def batch_convert_reports(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert multiple database reports to budget format
    
    Args:
        reports: List of database report dictionaries
    
    Returns:
        List of converted report dictionaries
    """
    converted = []
    skipped = []
    
    for i, report in enumerate(reports):
        try:
            converted_report = database_report_to_budget_format(report)
            converted.append(converted_report)
        except ValueError as e:
            skipped.append({
                "index": i,
                "tracking_number": report.get("tracking_number", "unknown"),
                "error": str(e)
            })
    
    return converted, skipped


def get_conversion_stats(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get statistics about report data before and after conversion
    
    Args:
        reports: List of database reports
    
    Returns:
        Dictionary with conversion statistics
    """
    
    stats = {
        "total_reports": len(reports),
        "severity_distribution": {"Severe": 0, "Moderate": 0, "Minor": 0},
        "damage_type_distribution": {},
        "total_estimated_cost": 0,
        "avg_severity_score": 0
    }
    
    total_severity = 0
    
    for report in reports:
        # Severity distribution
        severity_score = report.get('severity_score', 5)
        if severity_score >= 8:
            stats["severity_distribution"]["Severe"] += 1
        elif severity_score >= 5:
            stats["severity_distribution"]["Moderate"] += 1
        else:
            stats["severity_distribution"]["Minor"] += 1
        
        total_severity += severity_score
        
        # Damage type distribution
        damage_type = report.get('damage_type', 'unknown')
        stats["damage_type_distribution"][damage_type] = \
            stats["damage_type_distribution"].get(damage_type, 0) + 1
        
        # Total cost
        stats["total_estimated_cost"] += report.get('estimated_cost', 0)
    
    # Average severity
    if stats["total_reports"] > 0:
        stats["avg_severity_score"] = total_severity / stats["total_reports"]
    
    return stats