from flask import Blueprint, request, jsonify
import pandas as pd
import traceback
from enhanced_budget import EnhancedRepairFinancials, BudgetOptimizationError
from data_converter import get_conversion_stats, batch_convert_reports

budget_bp = Blueprint('budget', __name__, url_prefix='/api/budget')

@budget_bp.route('/optimize', methods=['POST'])
def optimize_budget():
    try:
        data = request.get_json()
        if not data: return jsonify({"success": False, "error": "No request body"}), 400
        
        repairs = data.get("repairs", [])
        total_budget = float(data.get("total_budget", 0))
        strategy = data.get("strategy", "priority_weighted")
        
        if not repairs: return jsonify({"success": False, "error": "No repairs"}), 400
        if total_budget <= 0: return jsonify({"success": False, "error": "Budget must be positive"}), 400
        
        # Convert repairs to format needed for calculation
        enhanced_repairs, skipped = batch_convert_reports(repairs)
        
        repair_objects = []
        for repair_data in enhanced_repairs:
            try:
                df = pd.DataFrame([repair_data])
                repair_obj = EnhancedRepairFinancials(df)
                repair_objects.append((repair_data.get("tracking_number"), repair_obj))
            except Exception:
                continue
        
        if not repair_objects:
            return jsonify({"success": False, "error": "No valid repairs found"}), 400
        
        # Perform Optimization
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            [obj for _, obj in repair_objects],
            total_budget,
            strategy=strategy
        )
        
        report = EnhancedRepairFinancials.generate_budget_report(allocation, total_budget)
        
        # Re-map to tracking numbers
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
    
    except Exception as e:
        print(f"Budget Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def create_budget_app(app=None):
    if app is not None:
        app.register_blueprint(budget_bp)