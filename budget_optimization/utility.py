"""Utility functions for budget optimization"""
import json
import os
from datetime import datetime
from typing import Dict, Any


def get_data(data: Any, file_name: str = 'output', output_dir: str = None) -> Any:
    """
    Save data to JSON file and return the data
    
    Args:
        data: Data to save and return
        file_name: Name of output file (without extension)
        output_dir: Directory to save file (default: current directory)
    
    Returns:
        The input data (unchanged)
    """
    
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(output_dir, f"{file_name}_{timestamp}.json")
    
    try:
        # Convert data to JSON-serializable format
        json_data = _make_serializable(data)
        
        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"✅ Data saved to: {file_path}")
    
    except Exception as e:
        print(f"⚠️  Could not save to file: {e}")
    
    return data


def _make_serializable(obj: Any) -> Any:
    """
    Convert non-JSON-serializable objects to serializable format
    
    Args:
        obj: Object to convert
    
    Returns:
        JSON-serializable version of object
    """
    
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)


def format_currency(amount: float, currency_symbol: str = "₦") -> str:
    """
    Format amount as currency string
    
    Args:
        amount: Amount to format
        currency_symbol: Currency symbol to use
    
    Returns:
        Formatted currency string
    """
    return f"{currency_symbol}{amount:,.0f}"


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """
    Format value as percentage string
    
    Args:
        value: Value to format (0-100)
        decimal_places: Number of decimal places
    
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimal_places}f}%"


def calculate_statistics(allocations: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics from allocation data
    
    Args:
        allocations: Dictionary of allocations
    
    Returns:
        Dictionary with statistics
    """
    
    allocated_amounts = [
        v.get("Allocated Budget (₦)", 0)
        for v in allocations.values()
    ]
    
    estimated_amounts = [
        v.get("Estimated Cost (₦)", 0)
        for v in allocations.values()
    ]
    
    funding_ratios = [
        v.get("Funding Ratio", 0)
        for v in allocations.values()
    ]
    
    return {
        "total_allocated": sum(allocated_amounts),
        "total_estimated": sum(estimated_amounts),
        "average_allocated": sum(allocated_amounts) / len(allocated_amounts) if allocated_amounts else 0,
        "average_estimated": sum(estimated_amounts) / len(estimated_amounts) if estimated_amounts else 0,
        "min_funding_ratio": min(funding_ratios) if funding_ratios else 0,
        "max_funding_ratio": max(funding_ratios) if funding_ratios else 0,
        "average_funding_ratio": sum(funding_ratios) / len(funding_ratios) if funding_ratios else 0,
        "fully_funded_count": sum(1 for v in allocations.values() if v.get("Can_Complete", False)),
        "partially_funded_count": len(allocations) - sum(1 for v in allocations.values() if v.get("Can_Complete", False))
    }


def print_allocation_summary(allocation: Dict[str, Any], total_budget: int) -> None:
    """
    Print a formatted summary of allocation
    
    Args:
        allocation: Allocation dictionary
        total_budget: Total budget amount
    """
    
    stats = calculate_statistics(allocation)
    
    print("\n" + "="*70)
    print("📊 ALLOCATION SUMMARY")
    print("="*70)
    print(f"Total Budget:           {format_currency(total_budget)}")
    print(f"Total Allocated:        {format_currency(stats['total_allocated'])}")
    print(f"Allocation Rate:        {format_percentage(stats['total_allocated']/total_budget*100)}")
    print(f"Fully Funded:           {stats['fully_funded_count']} repairs")
    print(f"Partially Funded:       {stats['partially_funded_count']} repairs")
    print(f"Average Funding Ratio:  {stats['average_funding_ratio']:.2f}")
    print("="*70 + "\n")


def print_repair_details(repair_data: Dict[str, Any]) -> None:
    """
    Print formatted repair details
    
    Args:
        repair_data: Repair data dictionary
    """
    
    print("\n" + "-"*70)
    print("🔧 REPAIR DETAILS")
    print("-"*70)
    
    fields_to_print = [
        ("Severity", "Severity"),
        ("Urgency", "Urgency"),
        ("Length (cm)", "Length (cm)"),
        ("Breadth (cm)", "Breadth (cm)"),
        ("Depth (cm)", "Depth (cm)"),
        ("Area (m²)", "Area (m²)"),
        ("Volume (m³)", "Volume (m³)"),
        ("Estimated Cost", "Estimated Cost (₦)"),
        ("Allocated Budget", "Allocated Budget (₦)"),
        ("Funding Ratio", "Funding Ratio"),
        ("Can Complete", "Can_Complete")
    ]
    
    for label, key in fields_to_print:
        if key in repair_data:
            value = repair_data[key]
            if "Cost" in label or "Budget" in label:
                print(f"{label:.<30} {format_currency(value)}")
            else:
                print(f"{label:.<30} {value}")
    
    print("-"*70 + "\n")