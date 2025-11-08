"""Enhanced Budget Optimization with Priority-Based Allocation"""
import math
import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BudgetConfig:
    """Configuration for budget optimization"""
    material_cost_per_m3: float = 150_000  # ₦ per cubic metre
    labour_cost_per_m2: float = 10_000      # ₦ per square metre
    mobilization: float = 20_000            # ₦ fixed per repair
    severity_weights: Dict[str, float] = None
    urgency_multipliers: Dict[str, float] = None
    area_calculation_mode: str = "rectangular"  # "rectangular" or "elliptical"
    
    def __post_init__(self):
        if self.severity_weights is None:
            self.severity_weights = {
                "Severe": 3.0,    # Highest priority
                "Moderate": 2.0,  # Medium priority
                "Minor": 1.0      # Lower priority
            }
        if self.urgency_multipliers is None:
            self.urgency_multipliers = {
                "immediate": 1.5,   # Main roads, high traffic
                "urgent": 1.2,      # Secondary roads
                "routine": 1.0      # Low traffic areas
            }


class BudgetOptimizationError(Exception):
    """Custom exception for budget optimization errors"""
    pass


class EnhancedRepairFinancials:
    """Enhanced version with priority-based budget optimization"""
    
    def __init__(self, df: pd.DataFrame, config: Optional[BudgetConfig] = None):
        """
        Initialize repair financials with input validation
        
        Args:
            df: DataFrame with repair data (single row)
            config: Optional BudgetConfig for customization
        """
        self.config = config or BudgetConfig()
        
        # Validate required columns
        self._validate_input_data(df)
        
        # Extract data
        self.length = df["length_cm"].values[0] if isinstance(df["length_cm"], pd.Series) else df["length_cm"]
        self.breadth = df["breadth_cm"].values[0] if isinstance(df["breadth_cm"], pd.Series) else df["breadth_cm"]
        self.depth = df["depth_cm"].values[0] if isinstance(df["depth_cm"], pd.Series) else df["depth_cm"]
        self.severity = df["severity"].values[0] if isinstance(df["severity"], pd.Series) else df["severity"]
        self.image_path = df["image_path"].values[0] if isinstance(df["image_path"], pd.Series) else df["image_path"]
        
        # Optional urgency field with validation
        if "urgency" in df.columns:
            self.urgency = df["urgency"].values[0] if isinstance(df["urgency"], pd.Series) else df["urgency"]
            if self.urgency not in self.config.urgency_multipliers:
                raise BudgetOptimizationError(
                    f"Invalid urgency '{self.urgency}'. Must be one of: {list(self.config.urgency_multipliers.keys())}"
                )
        else:
            self.urgency = "routine"
        
        # Validate severity
        if self.severity not in self.config.severity_weights:
            raise BudgetOptimizationError(
                f"Invalid severity '{self.severity}'. Must be one of: {list(self.config.severity_weights.keys())}"
            )
        
        # Calculate metrics
        self.cost_estimation_data = self._cost_estimation()
        self.priority_score = self._calculate_priority_score()

    def _validate_input_data(self, df: pd.DataFrame) -> None:
        """Validate that required columns exist and have valid data"""
        required_columns = ["length_cm", "breadth_cm", "depth_cm", "severity", "image_path"]
        missing = [col for col in required_columns if col not in df.columns]
        
        if missing:
            raise BudgetOptimizationError(f"Missing required columns: {missing}")
        
        # Check for null values
        for col in required_columns:
            if df[col].isnull().any():
                raise BudgetOptimizationError(f"Column '{col}' contains null values")
        
        # Check numeric fields are positive
        for col in ["length_cm", "breadth_cm", "depth_cm"]:
            if (df[col] <= 0).any():
                raise BudgetOptimizationError(f"Column '{col}' must contain positive values")

    def _calculate_area(self) -> float:
        """Calculate area in m² using configured method"""
        length_m = self.length / 100.0
        breadth_m = self.breadth / 100.0
        
        if self.config.area_calculation_mode == "elliptical":
            # Elliptical: assumes length/breadth are semi-axes
            area = math.pi * (length_m / 2) * (breadth_m / 2)
        else:  # rectangular (default)
            # Rectangular: full dimensions
            area = length_m * breadth_m
        
        return area

    def _cost_estimation(self) -> Dict[str, Any]:
        """Enhanced cost estimation with urgency factors"""
        severity_multiplier = {
            "Minor": 0.85,
            "Moderate": 1.0,
            "Severe": 1.4
        }
        
        # Area and volume calculations
        area_m2 = self._calculate_area()
        depth_m = self.depth / 100.0
        volume_m3 = area_m2 * depth_m
        
        # Base costs
        material_cost = self.config.material_cost_per_m3 * volume_m3
        labour_cost = self.config.labour_cost_per_m2 * area_m2
        subtotal = material_cost + labour_cost + self.config.mobilization
        
        # Apply severity and urgency multipliers
        severity_mult = severity_multiplier[self.severity]
        urgency_mult = self.config.urgency_multipliers.get(self.urgency, 1.0)
        estimated_cost = subtotal * severity_mult * urgency_mult
        
        return {
            "image_path": self.image_path,
            "Length (cm)": self.length,
            "Breadth (cm)": self.breadth,
            "Depth (cm)": self.depth,
            "Severity": self.severity,
            "Urgency": self.urgency,
            "Area (m²)": round(area_m2, 3),
            "Volume (m³)": round(volume_m3, 3),
            "Material Cost (₦)": int(round(material_cost)),
            "Labour Cost (₦)": int(round(labour_cost)),
            "Base Cost (₦)": int(round(subtotal)),
            "Estimated Cost (₦)": int(round(estimated_cost)),
            "Severity Multiplier": severity_mult,
            "Urgency Multiplier": urgency_mult
        }

    def _calculate_priority_score(self) -> Dict[str, Any]:
        """Calculate priority scores for repair"""
        # Base priority from severity
        severity_weight = self.config.severity_weights[self.severity]
        
        # Urgency factor
        urgency_mult = self.config.urgency_multipliers.get(self.urgency, 1.0)
        
        # Size factor (larger potholes get higher priority)
        area_factor = math.sqrt((self.length * self.breadth) / 10000)  # Normalize
        
        # Safety factor (deeper holes are more dangerous)
        depth_factor = 1 + (self.depth / 100)  # Depth in meters
        
        # Combined priority score
        priority_score = severity_weight * urgency_mult * area_factor * depth_factor
        
        return {
            "Priority_Score": round(priority_score, 3),
            "Severity_Weight": severity_weight,
            "Urgency_Multiplier": urgency_mult,
            "Area_Factor": round(area_factor, 3),
            "Depth_Factor": round(depth_factor, 3)
        }

    @classmethod
    def optimize_budget_with_priorities(cls, repair_objects: List['EnhancedRepairFinancials'], 
                                       total_budget: int,
                                       strategy: str = "priority_weighted") -> Dict[str, Any]:
        """
        Advanced budget optimization with multiple strategies
        
        Args:
            repair_objects: List of EnhancedRepairFinancials objects
            total_budget: Total available budget (₦)
            strategy: "priority_weighted", "severity_first", "proportional", or "hybrid"
            
        Returns:
            Dict with optimized allocations
        """
        
        if not repair_objects:
            raise BudgetOptimizationError("No repair objects provided")
        
        if total_budget <= 0:
            raise BudgetOptimizationError("Total budget must be positive")
        
        if strategy == "priority_weighted":
            return cls._priority_weighted_allocation(repair_objects, total_budget)
        elif strategy == "severity_first":
            return cls._severity_first_allocation(repair_objects, total_budget)
        elif strategy == "proportional":
            return cls._proportional_allocation(repair_objects, total_budget)
        elif strategy == "hybrid":
            return cls._hybrid_allocation(repair_objects, total_budget)
        else:
            raise BudgetOptimizationError(
                f"Unknown strategy: {strategy}. Must be one of: "
                f"priority_weighted, severity_first, proportional, hybrid"
            )

    @classmethod
    def _priority_weighted_allocation(cls, repair_objects: List['EnhancedRepairFinancials'],
                                     total_budget: int) -> Dict[str, Any]:
        """Allocate budget based on priority scores"""
        
        # Calculate total priority-weighted cost
        total_weighted_cost = 0
        repair_data = []
        
        for repair in repair_objects:
            estimated_cost = repair.cost_estimation_data["Estimated Cost (₦)"]
            priority_score = repair.priority_score["Priority_Score"]
            weighted_cost = estimated_cost * priority_score
            
            total_weighted_cost += weighted_cost
            repair_data.append({
                "repair": repair,
                "estimated_cost": estimated_cost,
                "priority_score": priority_score,
                "weighted_cost": weighted_cost,
                "cost_data": repair.cost_estimation_data
            })
        
        if total_weighted_cost == 0:
            raise BudgetOptimizationError("Total weighted cost cannot be zero")
        
        # Allocate budget proportionally to weighted costs
        optimized_allocations = {}
        
        for i, data in enumerate(repair_data, start=1):
            allocation = (data["weighted_cost"] / total_weighted_cost) * total_budget
            funding_ratio = allocation / data["estimated_cost"]
            
            optimized_allocations[f"Repair_{i}"] = {
                "image_path": data["cost_data"]["image_path"],
                "Severity": data["cost_data"]["Severity"],
                "Urgency": data["cost_data"]["Urgency"],
                "Priority_Score": data["priority_score"],
                "Estimated Cost (₦)": data["estimated_cost"],
                "Allocated Budget (₦)": int(round(allocation)),
                "Funding Ratio": round(funding_ratio, 2),
                "Can_Complete": funding_ratio >= 1.0
            }
        
        return optimized_allocations

    @classmethod
    def _severity_first_allocation(cls, repair_objects: List['EnhancedRepairFinancials'],
                                  total_budget: int) -> Dict[str, Any]:
        """Allocate budget by severity level first (Severe → Moderate → Minor)"""
        
        # Group repairs by severity
        severity_groups = {"Severe": [], "Moderate": [], "Minor": []}
        
        for repair in repair_objects:
            severity = repair.cost_estimation_data["Severity"]
            severity_groups[severity].append(repair)
        
        optimized_allocations = {}
        remaining_budget = total_budget
        repair_counter = 1
        
        # Allocate in severity order
        for severity_level in ["Severe", "Moderate", "Minor"]:
            repairs_in_group = severity_groups[severity_level]
            
            if not repairs_in_group or remaining_budget <= 0:
                continue
            
            # Calculate total cost for this severity group
            group_total_cost = sum(
                r.cost_estimation_data["Estimated Cost (₦)"]
                for r in repairs_in_group
            )
            
            # Allocate proportionally within the group
            for repair in repairs_in_group:
                estimated_cost = repair.cost_estimation_data["Estimated Cost (₦)"]
                
                if group_total_cost > 0:
                    allocation = min(
                        (estimated_cost / group_total_cost) * remaining_budget,
                        estimated_cost  # Don't over-allocate
                    )
                else:
                    allocation = 0
                
                funding_ratio = allocation / estimated_cost if estimated_cost > 0 else 0
                
                optimized_allocations[f"Repair_{repair_counter}"] = {
                    "image_path": repair.cost_estimation_data["image_path"],
                    "Severity": repair.cost_estimation_data["Severity"],
                    "Estimated Cost (₦)": estimated_cost,
                    "Allocated Budget (₦)": int(round(allocation)),
                    "Funding Ratio": round(funding_ratio, 2),
                    "Can_Complete": funding_ratio >= 1.0,
                    "Priority_Order": severity_level
                }
                
                remaining_budget -= allocation
                repair_counter += 1
        
        return optimized_allocations

    @classmethod
    def _proportional_allocation(cls, repair_objects: List['EnhancedRepairFinancials'],
                                total_budget: int) -> Dict[str, Any]:
        """Allocate budget proportionally by estimated cost"""
        
        total_cost = sum(
            r.cost_estimation_data["Estimated Cost (₦)"]
            for r in repair_objects
        )
        
        if total_cost == 0:
            raise BudgetOptimizationError("Total estimated cost cannot be zero")
        
        optimized_allocations = {}
        
        for i, repair in enumerate(repair_objects, start=1):
            estimated_cost = repair.cost_estimation_data["Estimated Cost (₦)"]
            allocation = (estimated_cost / total_cost) * total_budget if total_cost > 0 else 0
            funding_ratio = allocation / estimated_cost if estimated_cost > 0 else 0
            
            optimized_allocations[f"Repair_{i}"] = {
                "image_path": repair.cost_estimation_data["image_path"],
                "Severity": repair.cost_estimation_data["Severity"],
                "Estimated Cost (₦)": estimated_cost,
                "Allocated Budget (₦)": int(round(allocation)),
                "Funding Ratio": round(funding_ratio, 2),
                "Can_Complete": funding_ratio >= estimated_cost
            }
        
        return optimized_allocations

    @classmethod
    def _hybrid_allocation(cls, repair_objects: List['EnhancedRepairFinancials'],
                          total_budget: int) -> Dict[str, Any]:
        """Hybrid approach: Guarantee critical repairs, then optimize remaining"""
        
        # Step 1: Identify critical repairs (Severe + immediate urgency)
        critical_repairs = []
        regular_repairs = []
        
        for repair in repair_objects:
            severity = repair.cost_estimation_data["Severity"]
            urgency = repair.cost_estimation_data.get("Urgency", "routine")
            
            if severity == "Severe" and urgency == "immediate":
                critical_repairs.append(repair)
            else:
                regular_repairs.append(repair)
        
        # Step 2: Calculate critical budget
        critical_budget = sum(
            r.cost_estimation_data["Estimated Cost (₦)"]
            for r in critical_repairs
        )
        
        if critical_budget > total_budget:
            raise BudgetOptimizationError(
                f"Critical repairs (₦{critical_budget:,}) exceed total budget (₦{total_budget:,})"
            )
        
        remaining_budget = total_budget - critical_budget
        
        # Step 3: Build allocations
        optimized_allocations = {}
        repair_counter = 1
        
        # Fully fund critical repairs
        for repair in critical_repairs:
            estimated_cost = repair.cost_estimation_data["Estimated Cost (₦)"]
            
            optimized_allocations[f"Repair_{repair_counter}"] = {
                "image_path": repair.cost_estimation_data["image_path"],
                "Severity": repair.cost_estimation_data["Severity"],
                "Category": "Critical",
                "Estimated Cost (₦)": estimated_cost,
                "Allocated Budget (₦)": estimated_cost,
                "Funding Ratio": 1.0,
                "Can_Complete": True
            }
            repair_counter += 1
        
        # Priority-weighted allocation for remaining repairs
        if regular_repairs and remaining_budget > 0:
            regular_allocation = cls._priority_weighted_allocation(regular_repairs, remaining_budget)
            
            for key, value in regular_allocation.items():
                value["Category"] = "Regular"
                optimized_allocations[f"Repair_{repair_counter}"] = value
                repair_counter += 1
        
        return optimized_allocations

    @classmethod
    def generate_budget_report(cls, allocation_data: Dict, total_budget: int) -> Dict[str, Any]:
        """Generate comprehensive budget allocation report"""
        
        total_allocated = sum(v["Allocated Budget (₦)"] for v in allocation_data.values())
        unallocated = total_budget - total_allocated
        
        # Count repairs by completion status
        fully_funded = sum(1 for v in allocation_data.values() if v.get("Can_Complete", False))
        partially_funded = len(allocation_data) - fully_funded
        
        # Group by severity
        severity_summary = {}
        for v in allocation_data.values():
            severity = v.get("Severity", "Unknown")
            if severity not in severity_summary:
                severity_summary[severity] = {
                    "count": 0,
                    "allocated": 0,
                    "estimated": 0
                }
            
            severity_summary[severity]["count"] += 1
            severity_summary[severity]["allocated"] += v["Allocated Budget (₦)"]
            severity_summary[severity]["estimated"] += v["Estimated Cost (₦)"]
        
        report = {
            "budget_summary": {
                "total_budget": total_budget,
                "total_allocated": total_allocated,
                "unallocated": unallocated,
                "allocation_rate": round(total_allocated / total_budget * 100, 1) if total_budget > 0 else 0
            },
            "repair_summary": {
                "total_repairs": len(allocation_data),
                "fully_funded": fully_funded,
                "partially_funded": partially_funded
            },
            "severity_breakdown": severity_summary
        }
        
        return report


def demonstrate_optimization_strategies(repair_list: List[Dict], budget: int = 5_000_000,
                                       config: Optional[BudgetConfig] = None) -> Dict[str, Any]:
    """
    Demonstrate different optimization strategies
    
    Args:
        repair_list: List of repair dictionaries
        budget: Total budget in ₦
        config: Optional BudgetConfig
        
    Returns:
        Dictionary with results from all strategies
    """
    
    if not repair_list:
        raise BudgetOptimizationError("No repairs provided")
    
    config = config or BudgetConfig()
    
    # Create repair objects
    repair_objects = []
    for repair_dict in repair_list:
        df = pd.DataFrame([repair_dict])
        try:
            repair_obj = EnhancedRepairFinancials(df, config)
            repair_objects.append(repair_obj)
        except BudgetOptimizationError as e:
            print(f"⚠️  Skipping repair: {e}")
            continue
    
    if not repair_objects:
        raise BudgetOptimizationError("No valid repairs after validation")
    
    strategies = ["priority_weighted", "severity_first", "proportional", "hybrid"]
    results = {}
    
    for strategy in strategies:
        try:
            allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
                repair_objects, budget, strategy
            )
            report = EnhancedRepairFinancials.generate_budget_report(allocation, budget)
            results[strategy] = {
                "allocation": allocation,
                "report": report
            }
            print(f"✅ {strategy.replace('_', ' ').title()} strategy completed")
        except BudgetOptimizationError as e:
            print(f"❌ {strategy} strategy failed: {e}")
            results[strategy] = {"error": str(e)}
    
    return results