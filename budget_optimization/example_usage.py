"""
Quick-Start Example: Budget Optimization Usage
Run this script to see the module in action
"""
import pandas as pd
import sys
import os

# Add current directory to path
BUDGET_DIR = os.path.dirname(os.path.abspath(__file__))
if BUDGET_DIR not in sys.path:
    sys.path.insert(0, BUDGET_DIR)

from enhanced_budget import (
    EnhancedRepairFinancials,
    BudgetConfig
)
from utility import format_currency


def example_1_single_repair_cost():
    """Example 1: Estimate cost for a single repair"""
    print("\n" + "="*70)
    print("📍 EXAMPLE 1: Single Repair Cost Estimation")
    print("="*70)
    
    repair_data = {
        "length_cm": 120,
        "breadth_cm": 90,
        "depth_cm": 18,
        "severity": "Severe",
        "urgency": "immediate",
        "image_path": "/uploads/severe_pothole.jpg"
    }
    
    df = pd.DataFrame([repair_data])
    repair = EnhancedRepairFinancials(df)
    
    print(f"\n🔧 Repair Details:")
    print(f"   Damage Type: Pothole (Severe)")
    print(f"   Dimensions: {repair_data['length_cm']}cm × {repair_data['breadth_cm']}cm × {repair_data['depth_cm']}cm")
    print(f"   Urgency: {repair_data['urgency'].upper()}")
    
    print(f"\n💰 Cost Breakdown:")
    cost_data = repair.cost_estimation_data
    print(f"   Material Cost:  {format_currency(cost_data['Material Cost (₦)'])}")
    print(f"   Labour Cost:    {format_currency(cost_data['Labour Cost (₦)'])}")
    print(f"   Mobilization:   {format_currency(20000)}")  # From config
    print(f"   Base Cost:      {format_currency(cost_data['Base Cost (₦)'])}")
    print(f"   ├─ Severity Multiplier: {cost_data['Severity Multiplier']}x")
    print(f"   └─ Urgency Multiplier:  {cost_data['Urgency Multiplier']}x")
    print(f"   \n   TOTAL ESTIMATED COST: {format_currency(cost_data['Estimated Cost (₦)'])}")
    
    print(f"\n⭐ Priority Score: {repair.priority_score['Priority_Score']}")
    print(f"   ├─ Severity Weight:    {repair.priority_score['Severity_Weight']}")
    print(f"   ├─ Urgency Multiplier: {repair.priority_score['Urgency_Multiplier']}")
    print(f"   ├─ Area Factor:        {repair.priority_score['Area_Factor']}")
    print(f"   └─ Depth Factor:       {repair.priority_score['Depth_Factor']}")


def example_2_cost_comparison():
    """Example 2: Compare costs for different severity levels"""
    print("\n" + "="*70)
    print("📊 EXAMPLE 2: Cost Comparison by Severity")
    print("="*70)
    
    severities = ["Minor", "Moderate", "Severe"]
    
    print("\nComparing repair costs with same dimensions but different severity:\n")
    
    costs = {}
    for severity in severities:
        repair_data = {
            "length_cm": 100,
            "breadth_cm": 80,
            "depth_cm": 15,
            "severity": severity,
            "urgency": "routine",
            "image_path": f"/uploads/{severity.lower()}_damage.jpg"
        }
        
        df = pd.DataFrame([repair_data])
        repair = EnhancedRepairFinancials(df)
        cost = repair.cost_estimation_data["Estimated Cost (₦)"]
        costs[severity] = cost
    
    # Print comparison
    for severity in severities:
        cost = costs[severity]
        percentage = (cost / costs["Moderate"]) * 100
        print(f"{severity:.<15} {format_currency(cost):>20} ({percentage:.0f}% vs Moderate)")


def example_3_budget_allocation():
    """Example 3: Allocate budget across multiple repairs"""
    print("\n" + "="*70)
    print("🎯 EXAMPLE 3: Budget Allocation Strategies")
    print("="*70)
    
    # Define multiple repairs
    repairs_data = [
        {
            "length_cm": 200,
            "breadth_cm": 150,
            "depth_cm": 25,
            "severity": "Severe",
            "urgency": "immediate",
            "image_path": "/uploads/1.jpg",
            "description": "Large pothole on main highway"
        },
        {
            "length_cm": 150,
            "breadth_cm": 120,
            "depth_cm": 20,
            "severity": "Severe",
            "urgency": "immediate",
            "image_path": "/uploads/2.jpg",
            "description": "Severe crack in downtown area"
        },
        {
            "length_cm": 80,
            "breadth_cm": 60,
            "depth_cm": 12,
            "severity": "Moderate",
            "urgency": "urgent",
            "image_path": "/uploads/3.jpg",
            "description": "Moderate pothole on secondary road"
        },
        {
            "length_cm": 100,
            "breadth_cm": 70,
            "depth_cm": 10,
            "severity": "Moderate",
            "urgency": "routine",
            "image_path": "/uploads/4.jpg",
            "description": "Moderate crack on residential street"
        },
        {
            "length_cm": 50,
            "breadth_cm": 40,
            "depth_cm": 8,
            "severity": "Minor",
            "urgency": "routine",
            "image_path": "/uploads/5.jpg",
            "description": "Small pothole in residential area"
        }
    ]
    
    # Create repair objects
    repair_objects = []
    print("\nCreating repair objects...")
    for i, repair_data in enumerate(repairs_data, start=1):
        df = pd.DataFrame([repair_data])
        repair = EnhancedRepairFinancials(df)
        repair_objects.append(repair)
        print(f"  ✓ Repair {i}: {repair_data['description']}")
    
    # Budget
    total_budget = 5_000_000  # ₦5 million
    print(f"\nTotal Available Budget: {format_currency(total_budget)}")
    
    # Test each strategy
    strategies = ["priority_weighted", "severity_first", "proportional", "hybrid"]
    
    for strategy in strategies:
        print(f"\n{'─'*70}")
        print(f"🎲 Strategy: {strategy.upper().replace('_', ' ')}")
        print(f"{'─'*70}")
        
        try:
            # Allocate budget
            allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
                repair_objects,
                total_budget,
                strategy=strategy
            )
            
            # Generate report
            report = EnhancedRepairFinancials.generate_budget_report(allocation, total_budget)
            
            # Display results
            budget_summary = report['budget_summary']
            repair_summary = report['repair_summary']
            
            print(f"\nBudget Summary:")
            print(f"  Total Allocated:  {format_currency(budget_summary['total_allocated'])}")
            print(f"  Unallocated:      {format_currency(budget_summary['unallocated'])}")
            print(f"  Allocation Rate:  {budget_summary['allocation_rate']}%")
            
            print(f"\nRepair Summary:")
            print(f"  Total Repairs:      {repair_summary['total_repairs']}")
            print(f"  Fully Funded:       {repair_summary['fully_funded']}")
            print(f"  Partially Funded:   {repair_summary['partially_funded']}")
            
            print(f"\nSeverity Breakdown:")
            for severity, data in report['severity_breakdown'].items():
                print(f"  {severity}:")
                print(f"    Count:     {data['count']}")
                print(f"    Allocated: {format_currency(data['allocated'])}")
                print(f"    Estimated: {format_currency(data['estimated'])}")
            
            # Show allocations table
            print(f"\nDetailed Allocations:")
            print(f"{'Repair':<10} {'Severity':<12} {'Estimated':<15} {'Allocated':<15} {'Ratio':<8} {'Status':<10}")
            print("─" * 70)
            
            for i, (key, alloc) in enumerate(allocation.items(), start=1):
                status = "✓" if alloc['Can_Complete'] else "✗"
                print(
                    f"{i:<10} "
                    f"{alloc['Severity']:<12} "
                    f"{format_currency(alloc['Estimated Cost (₦)']):<15} "
                    f"{format_currency(alloc['Allocated Budget (₦)']):<15} "
                    f"{alloc['Funding Ratio']:<8} "
                    f"{status:<10}"
                )
        
        except Exception as e:
            print(f"❌ Error: {e}")


def example_4_custom_configuration():
    """Example 4: Use custom configuration"""
    print("\n" + "="*70)
    print("⚙️  EXAMPLE 4: Custom Configuration")
    print("="*70)
    
    # Create custom config
    custom_config = BudgetConfig(
        material_cost_per_m3=160_000,      # Increased from 150k
        labour_cost_per_m2=12_000,         # Increased from 10k
        area_calculation_mode="elliptical",  # For circular damage
        severity_weights={
            "Severe": 4.0,     # Higher weight
            "Moderate": 2.0,
            "Minor": 0.5       # Lower weight
        },
        urgency_multipliers={
            "immediate": 2.0,  # Doubled from 1.5
            "urgent": 1.3,
            "routine": 1.0
        }
    )
    
    repair_data = {
        "length_cm": 100,
        "breadth_cm": 80,
        "depth_cm": 15,
        "severity": "Severe",
        "urgency": "immediate",
        "image_path": "/uploads/damage.jpg"
    }
    
    print("\nDefault Configuration:")
    df = pd.DataFrame([repair_data])
    repair_default = EnhancedRepairFinancials(df)
    cost_default = repair_default.cost_estimation_data["Estimated Cost (₦)"]
    print(f"  Estimated Cost: {format_currency(cost_default)}")
    
    print("\nCustom Configuration:")
    repair_custom = EnhancedRepairFinancials(df, custom_config)
    cost_custom = repair_custom.cost_estimation_data["Estimated Cost (₦)"]
    print(f"  Estimated Cost: {format_currency(cost_custom)}")
    
    difference = cost_custom - cost_default
    percentage = (difference / cost_default) * 100
    print(f"\nDifference: {format_currency(difference)} ({percentage:+.1f}%)")


def example_5_area_calculation_modes():
    """Example 5: Compare area calculation modes"""
    print("\n" + "="*70)
    print("📐 EXAMPLE 5: Area Calculation Modes")
    print("="*70)
    
    repair_data = {
        "length_cm": 100,
        "breadth_cm": 80,
        "depth_cm": 15,
        "severity": "Moderate",
        "urgency": "routine",
        "image_path": "/uploads/damage.jpg"
    }
    
    print("\nRectangular Mode (Default):")
    print("  Area = length × breadth")
    
    config_rect = BudgetConfig(area_calculation_mode="rectangular")
    df = pd.DataFrame([repair_data])
    repair_rect = EnhancedRepairFinancials(df, config_rect)
    
    print(f"  Area: {repair_rect.cost_estimation_data['Area (m²)']} m²")
    print(f"  Cost: {format_currency(repair_rect.cost_estimation_data['Estimated Cost (₦)'])}")
    
    print("\nElliptical Mode (Circular Damage):")
    print("  Area = π × (length/2) × (breadth/2)")
    
    config_ellip = BudgetConfig(area_calculation_mode="elliptical")
    repair_ellip = EnhancedRepairFinancials(df, config_ellip)
    
    print(f"  Area: {repair_ellip.cost_estimation_data['Area (m²)']} m²")
    print(f"  Cost: {format_currency(repair_ellip.cost_estimation_data['Estimated Cost (₦)'])}")


def main():
    """Run all examples"""
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*10 + "🚀 BUDGET OPTIMIZATION - EXAMPLES" + " "*25 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        example_1_single_repair_cost()
        example_2_cost_comparison()
        example_3_budget_allocation()
        example_4_custom_configuration()
        example_5_area_calculation_modes()
        
        print("\n" + "="*70)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\n📚 Next steps:")
        print("   1. Check README.md for detailed documentation")
        print("   2. Run: python test_budget_optimization.py")
        print("   3. Review INTEGRATION_GUIDE.md for backend integration")
        print("   4. See budget_api.py for Flask endpoint specifications")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()