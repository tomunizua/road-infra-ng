"""
Flask API endpoints for budget optimization
Integrate with the main backend application
"""
from flask import Blueprint, request, jsonify
import pandas as pd
from typing import Dict, Any
import traceback
import sys
import os

# Add current directory to path for relative imports
BUDGET_DIR = os.path.dirname(os.path.abspath(__file__))
if BUDGET_DIR not in sys.path:
    sys.path.insert(0, BUDGET_DIR)

from enhanced_budget import (
    EnhancedRepairFinancials,
    BudgetConfig,
    BudgetOptimizationError
)
from data_converter import (
    database_report_to_budget_format,
    batch_convert_reports,
    get_conversion_stats
)

# Create Blueprint for budget optimization routes
budget_bp = Blueprint('budget', __name__, url_prefix='/api/budget')


@budget_bp.route('/optimize', methods=['POST'])
def optimize_budget():
    """
    Optimize budget allocation using specified strategy
    
    Request body:
    {
        "repairs": [
            {
                "tracking_number": "RW...",
                "damage_type": "pothole",
                "severity_score": 7,  (0-10)
                "estimated_cost": 150000,
                "location": "Lagos",
                "urgency": "immediate"  (optional: immediate, urgent, routine)
            },
            ...
        ],
        "total_budget": 5000000,
        "strategy": "priority_weighted"  (priority_weighted, severity_first, proportional, hybrid)
    }
    
    Response:
    {
        "success": true,
        "strategy": "priority_weighted",
        "allocations": {...},
        "report": {...}
    }
    """
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No request body provided"
            }), 400
        
        # Validate required fields
        if "repairs" not in data or "total_budget" not in data:
            return jsonify({
                "success": False,
                "error": "Missing required fields: 'repairs' and 'total_budget'"
            }), 400
        
        repairs = data.get("repairs", [])
        total_budget = data.get("total_budget", 0)
        strategy = data.get("strategy", "priority_weighted")
        
        if not repairs:
            return jsonify({
                "success": False,
                "error": "No repairs provided"
            }), 400
        
        if total_budget <= 0:
            return jsonify({
                "success": False,
                "error": "Total budget must be positive"
            }), 400
        
        # Convert repairs to enhanced format
        enhanced_repairs = _convert_reports_to_repair_format(repairs)
        
        # Create repair objects
        repair_objects = []
        for repair_data in enhanced_repairs:
            try:
                df = pd.DataFrame([repair_data])
                repair_obj = EnhancedRepairFinancials(df)
                repair_objects.append((repair_data.get("tracking_number"), repair_obj))
            except BudgetOptimizationError as e:
                print(f"⚠️  Skipping repair {repair_data.get('tracking_number')}: {e}")
                continue
        
        if not repair_objects:
            return jsonify({
                "success": False,
                "error": "No valid repairs after validation"
            }), 400
        
        # Optimize budget
        try:
            allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
                [obj for _, obj in repair_objects],
                total_budget,
                strategy=strategy
            )
            
            # Generate report
            report = EnhancedRepairFinancials.generate_budget_report(allocation, total_budget)
            
            # Map tracking numbers to allocations
            allocation_with_tracking = {}
            for i, (tracking_number, _) in enumerate(repair_objects, start=1):
                key = f"Repair_{i}"
                if key in allocation:
                    allocation_with_tracking[tracking_number] = allocation[key]
            
            return jsonify({
                "success": True,
                "strategy": strategy,
                "allocations": allocation_with_tracking,
                "report": report
            }), 200
        
        except BudgetOptimizationError as e:
            return jsonify({
                "success": False,
                "error": f"Optimization failed: {str(e)}"
            }), 400
    
    except Exception as e:
        print(f"❌ Error in optimize_budget: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@budget_bp.route('/strategies', methods=['GET'])
def get_available_strategies():
    """Get list of available allocation strategies"""
    
    strategies = {
        "priority_weighted": {
            "name": "Priority-Weighted",
            "description": "Allocate budget based on priority scores combining severity, urgency, size, and depth",
            "best_for": "General purpose optimization"
        },
        "severity_first": {
            "name": "Severity First",
            "description": "Fully fund all Severe repairs first, then Moderate, then Minor",
            "best_for": "Emergency-first approach"
        },
        "proportional": {
            "name": "Proportional",
            "description": "Allocate budget proportionally based on estimated costs",
            "best_for": "Fair and simple allocation"
        },
        "hybrid": {
            "name": "Hybrid",
            "description": "Guarantee critical repairs (Severe + immediate), then optimize remaining",
            "best_for": "Safety-critical repairs + optimization"
        }
    }
    
    return jsonify({
        "success": True,
        "strategies": strategies
    }), 200


@budget_bp.route('/estimate-cost', methods=['POST'])
def estimate_repair_cost():
    """
    Estimate cost for a single repair
    
    Request body:
    {
        "length_cm": 100,
        "breadth_cm": 80,
        "depth_cm": 15,
        "severity": "Moderate",
        "urgency": "routine",
        "image_path": "/path/to/image.jpg"
    }
    
    Response:
    {
        "success": true,
        "cost_estimation": {...},
        "priority_score": {...}
    }
    """
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No request body provided"
            }), 400
        
        # Add required fields if missing
        data.setdefault("image_path", "unknown")
        
        try:
            df = pd.DataFrame([data])
            repair = EnhancedRepairFinancials(df)
            
            return jsonify({
                "success": True,
                "cost_estimation": repair.cost_estimation_data,
                "priority_score": repair.priority_score
            }), 200
        
        except BudgetOptimizationError as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400
    
    except Exception as e:
        print(f"❌ Error in estimate_repair_cost: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@budget_bp.route('/report-statistics', methods=['POST'])
def get_report_statistics():
    """
    Get statistics about reports data for conversion
    
    Request body:
    {
        "reports": [...]  // List of report dictionaries from database
    }
    
    Response:
    {
        "success": true,
        "statistics": {
            "total_reports": 10,
            "severity_distribution": {...},
            "damage_type_distribution": {...},
            ...
        }
    }
    """
    
    try:
        data = request.get_json()
        
        if not data or "reports" not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: 'reports'"
            }), 400
        
        reports = data.get("reports", [])
        
        if not reports:
            return jsonify({
                "success": False,
                "error": "No reports provided"
            }), 400
        
        stats = get_conversion_stats(reports)
        
        return jsonify({
            "success": True,
            "statistics": stats
        }), 200
    
    except Exception as e:
        print(f"❌ Error in get_report_statistics: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@budget_bp.route('/compare-strategies', methods=['POST'])
def compare_strategies():
    """
    Compare all allocation strategies
    
    Request body:
    {
        "repairs": [...],
        "total_budget": 5000000
    }
    
    Response:
    {
        "success": true,
        "comparison": {
            "strategy_name": {
                "allocations": {...},
                "report": {...}
            },
            ...
        }
    }
    """
    
    try:
        data = request.get_json()
        
        if not data or "repairs" not in data or "total_budget" not in data:
            return jsonify({
                "success": False,
                "error": "Missing required fields: 'repairs' and 'total_budget'"
            }), 400
        
        repairs = data.get("repairs", [])
        total_budget = data.get("total_budget", 0)
        
        if not repairs or total_budget <= 0:
            return jsonify({
                "success": False,
                "error": "Valid repairs and positive total_budget required"
            }), 400
        
        # Convert repairs
        enhanced_repairs = _convert_reports_to_repair_format(repairs)
        
        # Create repair objects
        repair_objects = []
        for repair_data in enhanced_repairs:
            try:
                df = pd.DataFrame([repair_data])
                repair_obj = EnhancedRepairFinancials(df)
                repair_objects.append(repair_obj)
            except BudgetOptimizationError:
                continue
        
        if not repair_objects:
            return jsonify({
                "success": False,
                "error": "No valid repairs after validation"
            }), 400
        
        # Compare all strategies
        comparison = {}
        strategies = ["priority_weighted", "severity_first", "proportional", "hybrid"]
        
        for strategy in strategies:
            try:
                allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
                    repair_objects,
                    total_budget,
                    strategy=strategy
                )
                
                report = EnhancedRepairFinancials.generate_budget_report(allocation, total_budget)
                
                comparison[strategy] = {
                    "allocations": allocation,
                    "report": report
                }
            except BudgetOptimizationError as e:
                comparison[strategy] = {
                    "error": str(e)
                }
        
        return jsonify({
            "success": True,
            "comparison": comparison
        }), 200
    
    except Exception as e:
        print(f"❌ Error in compare_strategies: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


def _convert_reports_to_repair_format(reports: list) -> list:
    """
    Convert report objects from database to repair format for optimization
    Uses data_converter module for consistent conversion
    
    Args:
        reports: List of report dictionaries
    
    Returns:
        List of repair dictionaries in optimization format
    """
    converted, skipped = batch_convert_reports(reports)
    
    if skipped:
        print(f"⚠️  Skipped {len(skipped)} reports due to missing data:")
        for skip in skipped:
            print(f"   - {skip['tracking_number']}: {skip['error']}")
    
    return converted


def create_budget_app(app=None):
    """
    Register budget optimization blueprint with Flask app
    
    Usage in main app:
    from budget_api import create_budget_app
    create_budget_app(app)
    """
    if app is not None:
        app.register_blueprint(budget_bp)
        print("✅ Budget optimization API registered")
        print("   Available endpoints:")
        print("   - POST /api/budget/optimize")
        print("   - GET  /api/budget/strategies")
        print("   - POST /api/budget/estimate-cost")
        print("   - POST /api/budget/compare-strategies")
    
    return budget_bp