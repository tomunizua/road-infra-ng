# 💰 Budget Optimization Module

Advanced budget allocation system for road infrastructure repair prioritization in the RoadWatch Nigeria platform.

## Overview

The budget optimization module provides intelligent allocation of limited repair budgets across multiple road damage reports. It uses priority-weighted algorithms to ensure critical repairs are funded first while maximizing overall infrastructure health.

## Key Features

### 🎯 Multiple Allocation Strategies

1. **Priority-Weighted** (Recommended)
   - Allocates budget based on priority scores combining severity, urgency, damage size, and depth
   - Best for general-purpose optimization
   - Balances critical safety with overall coverage

2. **Severity First**
   - Fully funds all Severe repairs first, then Moderate, then Minor
   - Best for emergency-first approach
   - Ensures all high-risk damage is addressed

3. **Proportional**
   - Allocates budget proportionally based on estimated costs
   - Simple and fair allocation
   - Good for predictable funding patterns

4. **Hybrid**
   - Guarantees critical repairs (Severe + immediate urgency)
   - Optimizes remaining budget using priority weighting
   - Best for safety-critical repairs + optimization

### 📊 Cost Estimation

Calculates repair costs based on:
- **Damage dimensions**: length, breadth, depth (in cm)
- **Material costs**: ₦150,000/m³ (configurable)
- **Labour costs**: ₦10,000/m² (configurable)
- **Mobilization fee**: ₦20,000 per repair (configurable)
- **Severity multiplier**: Increases cost for Severe repairs
- **Urgency multiplier**: Increases cost for immediate/urgent repairs

### ⭐ Priority Scoring

Combines multiple factors:
- Severity weight (Minor: 1.0, Moderate: 2.0, Severe: 3.0)
- Urgency multiplier (Routine: 1.0, Urgent: 1.2, Immediate: 1.5)
- Area factor (larger damages = higher priority)
- Depth factor (deeper damages = higher priority)

## Installation

### Prerequisites
- Python 3.8+
- pandas
- numpy

### Setup

```bash
# Install required packages
pip install pandas numpy

# Navigate to budget_optimization directory
cd budget_optimization

# Run example usage
python example_usage.py
```

## Module Structure

```
budget_optimization/
├── enhanced_budget.py          # Core optimization engine
├── budget_api.py               # Flask API endpoints
├── data_converter.py           # Database ↔ Budget format conversion
├── utility.py                  # Utility functions
├── example_usage.py            # Demonstration examples
├── test_budget_optimization.py # Test suite
└── README.md                   # This file
```

## Core Modules

### enhanced_budget.py

**Main Classes:**

- **BudgetConfig**: Configuration dataclass
  - `material_cost_per_m3`: Cost per cubic metre (default: ₦150,000)
  - `labour_cost_per_m2`: Cost per square metre (default: ₦10,000)
  - `mobilization`: Fixed cost per repair (default: ₦20,000)
  - `severity_weights`: Priority weights for each severity level
  - `urgency_multipliers`: Cost multipliers for each urgency level
  - `area_calculation_mode`: "rectangular" or "elliptical"

- **EnhancedRepairFinancials**: Main repair financials class
  - Validates input data
  - Calculates cost estimation
  - Computes priority scores
  - Static methods for budget optimization

**Key Methods:**

```python
# Create repair object
repair = EnhancedRepairFinancials(df)

# Access calculated data
cost_data = repair.cost_estimation_data
priority_score = repair.priority_score

# Optimize budget (static method)
allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
    repairs=[repair1, repair2, ...],
    total_budget=5_000_000,
    strategy="priority_weighted"
)

# Generate report
report = EnhancedRepairFinancials.generate_budget_report(
    allocation,
    total_budget
)
```

### data_converter.py

Handles conversion between database format (Report model) and budget optimization format.

**Key Functions:**

```python
# Convert single report
budget_format = database_report_to_budget_format(report_dict)

# Batch convert with error handling
converted, skipped = batch_convert_reports(reports_list)

# Get conversion statistics
stats = get_conversion_stats(reports_list)
```

**Data Format Mapping:**

| Database Field | Budget Field | Notes |
|---|---|---|
| `severity_score` (0-10) | `severity` (categorical) | 0-4→Minor, 5-7→Moderate, 8-10→Severe |
| `damage_type` | `damage_type` | Used to estimate dimensions |
| `image_filename` | `image_path` | File path or URL |
| `tracking_number` | `tracking_number` | Unique identifier |
| (calculated) | `length_cm`, `breadth_cm`, `depth_cm` | Estimated from damage type & severity |

### budget_api.py

Flask Blueprint providing REST API endpoints for budget optimization.

**Endpoints:**

- `POST /api/budget/optimize` - Optimize budget with specified strategy
- `GET /api/budget/strategies` - List available strategies
- `POST /api/budget/estimate-cost` - Estimate single repair cost
- `POST /api/budget/compare-strategies` - Compare all strategies
- `POST /api/budget/report-statistics` - Get report statistics

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for detailed endpoint specifications.

## Usage Examples

### Example 1: Single Repair Cost

```python
import pandas as pd
from enhanced_budget import EnhancedRepairFinancials

repair_data = {
    "length_cm": 120,
    "breadth_cm": 90,
    "depth_cm": 18,
    "severity": "Severe",
    "urgency": "immediate",
    "image_path": "/uploads/damage.jpg"
}

df = pd.DataFrame([repair_data])
repair = EnhancedRepairFinancials(df)

print(f"Estimated Cost: ₦{repair.cost_estimation_data['Estimated Cost (₦)']}")
print(f"Priority Score: {repair.priority_score['Priority_Score']}")
```

### Example 2: Budget Allocation

```python
# Prepare repairs
repairs = [repair1, repair2, repair3, ...]
total_budget = 5_000_000

# Allocate budget
allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
    repairs,
    total_budget,
    strategy="priority_weighted"
)

# Generate report
report = EnhancedRepairFinancials.generate_budget_report(
    allocation,
    total_budget
)

print(f"Total Allocated: ₦{report['budget_summary']['total_allocated']}")
print(f"Fully Funded: {report['repair_summary']['fully_funded']} repairs")
```

### Example 3: Custom Configuration

```python
from enhanced_budget import BudgetConfig

custom_config = BudgetConfig(
    material_cost_per_m3=160_000,
    labour_cost_per_m2=12_000,
    severity_weights={
        "Severe": 4.0,
        "Moderate": 2.0,
        "Minor": 0.5
    }
)

repair = EnhancedRepairFinancials(df, custom_config)
```

## API Usage

### Optimize Budget Endpoint

**Request:**
```json
POST /api/budget/optimize
{
    "repairs": [
        {
            "tracking_number": "RW20251001ABC123",
            "damage_type": "pothole",
            "severity_score": 7,
            "estimated_cost": 150000,
            "location": "Lagos",
            "urgency": "immediate"
        }
    ],
    "total_budget": 5000000,
    "strategy": "priority_weighted"
}
```

**Response:**
```json
{
    "success": true,
    "strategy": "priority_weighted",
    "allocations": {
        "RW20251001ABC123": {
            "Allocated Budget (₦)": 150000,
            "Can_Complete": true,
            "Funding Ratio": 1.0
        }
    },
    "report": {
        "budget_summary": {...},
        "repair_summary": {...}
    }
}
```

## Testing

```bash
# Run all tests
python -m pytest test_budget_optimization.py -v

# Run specific test
python -m pytest test_budget_optimization.py::TestEnhancedRepairFinancials -v

# Run with coverage
python -m pytest test_budget_optimization.py --cov=.
```

## Configuration Guide

### Adjusting Cost Parameters

```python
config = BudgetConfig(
    material_cost_per_m3=160_000,  # Adjust for material price changes
    labour_cost_per_m2=12_000,     # Adjust for wage changes
    mobilization=25_000            # Adjust fixed costs
)
```

### Adjusting Priority Weights

Increase/decrease to prioritize certain conditions:

```python
config = BudgetConfig(
    severity_weights={
        "Severe": 5.0,     # Increase to prioritize Severe more
        "Moderate": 2.0,
        "Minor": 0.5
    }
)
```

### Adjusting Urgency Multipliers

Increase for urgent routes (main roads, high traffic):

```python
config = BudgetConfig(
    urgency_multipliers={
        "immediate": 2.0,  # Main roads
        "urgent": 1.5,     # Secondary roads
        "routine": 1.0     # Low traffic
    }
)
```

## Data Format Reference

### Repair Input Format

```python
{
    "tracking_number": str,     # Unique identifier
    "length_cm": int,           # Length in centimeters
    "breadth_cm": int,          # Width in centimeters  
    "depth_cm": int,            # Depth in centimeters
    "severity": str,            # "Severe", "Moderate", or "Minor"
    "urgency": str,             # "immediate", "urgent", or "routine"
    "image_path": str,          # Path to damage image
    "damage_type": str          # Optional: "pothole", "crack", "rut", etc.
}
```

### Cost Estimation Output

```python
{
    "Area (m²)": float,
    "Material Cost (₦)": float,
    "Labour Cost (₦)": float,
    "Base Cost (₦)": float,
    "Severity Multiplier": float,
    "Urgency Multiplier": float,
    "Estimated Cost (₦)": float
}
```

### Priority Score Output

```python
{
    "Priority_Score": float,
    "Severity_Weight": float,
    "Urgency_Multiplier": float,
    "Area_Factor": float,
    "Depth_Factor": float
}
```

## Error Handling

All functions provide detailed error messages:

```python
from enhanced_budget import BudgetOptimizationError

try:
    repair = EnhancedRepairFinancials(df)
except BudgetOptimizationError as e:
    print(f"Validation error: {e}")
```

Common errors:
- **Missing required columns**: Ensure all required fields are in DataFrame
- **Invalid severity**: Must be "Severe", "Moderate", or "Minor"
- **Invalid urgency**: Must be "immediate", "urgent", or "routine"
- **Invalid dimensions**: Must be positive numbers

## Performance Notes

- Optimizing 100 repairs: ~50-100ms
- Optimizing 1,000 repairs: ~500-1,000ms
- Memory usage scales linearly with number of repairs

## Future Enhancements

- [ ] Contractor availability integration
- [ ] Seasonal constraints (rainy season, etc.)
- [ ] Traffic impact analysis
- [ ] Environmental impact scoring
- [ ] Community feedback weighting
- [ ] Real-time budget adjustment
- [ ] Schedule optimization (timing, sequencing)
- [ ] Machine learning-based cost estimation

## Support & Troubleshooting

**Question**: Why are dimensions estimated instead of provided?
**Answer**: The database stores `severity_score` and `damage_type`, but repair costs require physical dimensions. The converter uses historical patterns to estimate dimensions based on damage type and severity.

**Question**: Can I override urgency?
**Answer**: Yes! Pass `urgency` in the report data. If not provided, it defaults based on severity_score.

**Question**: How are multiple repairs compared?
**Answer**: Each repair gets a priority score combining severity, urgency, area, and depth. Higher scores get allocated budget first.

## Contributing

Please see the main project's CONTRIBUTING.md for guidelines.

## License

Part of RoadWatch Nigeria infrastructure project.

---

**Last Updated**: 2024
**Module Version**: 1.0.0
**Status**: Production Ready