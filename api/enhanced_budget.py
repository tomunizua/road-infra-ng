import math
import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class BudgetConfig:
    material_cost_per_m3: float = 150_000
    labour_cost_per_m2: float = 10_000
    mobilization: float = 20_000
    severity_weights: Dict[str, float] = None
    urgency_multipliers: Dict[str, float] = None
    
    def __post_init__(self):
        if self.severity_weights is None:
            self.severity_weights = {"Severe": 3.0, "Moderate": 2.0, "Minor": 1.0}
        if self.urgency_multipliers is None:
            self.urgency_multipliers = {"immediate": 1.5, "urgent": 1.2, "routine": 1.0}

class BudgetOptimizationError(Exception): pass

class EnhancedRepairFinancials:
    def __init__(self, df: pd.DataFrame, config: Optional[BudgetConfig] = None):
        self.config = config or BudgetConfig()
        self.length = df["length_cm"].values[0] if isinstance(df["length_cm"], pd.Series) else df["length_cm"]
        self.breadth = df["breadth_cm"].values[0] if isinstance(df["breadth_cm"], pd.Series) else df["breadth_cm"]
        self.depth = df["depth_cm"].values[0] if isinstance(df["depth_cm"], pd.Series) else df["depth_cm"]
        self.severity = df["severity"].values[0] if isinstance(df["severity"], pd.Series) else df["severity"]
        self.urgency = df["urgency"].values[0] if "urgency" in df.columns and isinstance(df["urgency"], pd.Series) else "routine"
        
        self.cost_estimation_data = self._cost_estimation()
        self.priority_score = self._calculate_priority_score()

    def _cost_estimation(self) -> Dict[str, Any]:
        area_m2 = (self.length / 100.0) * (self.breadth / 100.0)
        volume_m3 = area_m2 * (self.depth / 100.0)
        
        base_cost = (self.config.material_cost_per_m3 * volume_m3) + \
                    (self.config.labour_cost_per_m2 * area_m2) + \
                    self.config.mobilization
                    
        severity_mult = {"Minor": 0.85, "Moderate": 1.0, "Severe": 1.4}.get(self.severity, 1.0)
        urgency_mult = self.config.urgency_multipliers.get(self.urgency, 1.0)
        
        return {
            "Estimated Cost (₦)": int(base_cost * severity_mult * urgency_mult),
            "Severity": self.severity,
            "Urgency": self.urgency
        }

    def _calculate_priority_score(self) -> Dict[str, Any]:
        severity_weight = self.config.severity_weights.get(self.severity, 1.0)
        urgency_mult = self.config.urgency_multipliers.get(self.urgency, 1.0)
        area_factor = math.sqrt((self.length * self.breadth) / 10000)
        
        priority_score = severity_weight * urgency_mult * area_factor
        return {"Priority_Score": round(priority_score, 3)}

    @classmethod
    def optimize_budget_with_priorities(cls, repair_objects, total_budget, strategy="priority_weighted"):
        # Priority Weighted Strategy
        allocations = {}
        repair_data = []
        total_weighted_cost = 0
        
        for repair in repair_objects:
            cost = repair.cost_estimation_data["Estimated Cost (₦)"]
            score = repair.priority_score["Priority_Score"]
            weighted = cost * score
            total_weighted_cost += weighted
            repair_data.append({"obj": repair, "cost": cost, "score": score, "weighted": weighted})
            
        if total_weighted_cost == 0: return {}
        
        for i, data in enumerate(repair_data, 1):
            allocation = (data["weighted"] / total_weighted_cost) * total_budget
            funding_ratio = allocation / data["cost"] if data["cost"] > 0 else 0
            
            allocations[f"Repair_{i}"] = {
                "Estimated Cost (₦)": data["cost"],
                "Allocated Budget (₦)": int(allocation),
                "Can_Complete": funding_ratio >= 1.0,
                "Priority_Score": data["score"]
            }
        return allocations

    @classmethod
    def generate_budget_report(cls, allocations, total_budget):
        allocated = sum(v["Allocated Budget (₦)"] for v in allocations.values())
        return {
            "budget_summary": {
                "total_budget": total_budget,
                "total_allocated": allocated,
                "unallocated": total_budget - allocated
            }
        }