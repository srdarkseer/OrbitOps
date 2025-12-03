"""
Utility functions for cost calculations and conversions
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta


def calculate_monthly_to_annual(monthly_cost: float) -> float:
    """Convert monthly cost to annual"""
    return monthly_cost * 12


def calculate_annual_to_monthly(annual_cost: float) -> float:
    """Convert annual cost to monthly"""
    return annual_cost / 12


def calculate_daily_cost(monthly_cost: float) -> float:
    """Calculate daily cost from monthly"""
    return monthly_cost / 30.0


def calculate_hourly_cost(monthly_cost: float) -> float:
    """Calculate hourly cost from monthly"""
    return monthly_cost / (30.0 * 24.0)


def apply_percentage_change(base_cost: float, percentage: float) -> float:
    """
    Apply a percentage change to a cost.
    
    Args:
        base_cost: Base cost amount
        percentage: Percentage change (positive for increase, negative for decrease)
        
    Returns:
        New cost after percentage change
    """
    return base_cost * (1 + percentage / 100.0)


def calculate_savings_percentage(original: float, new: float) -> float:
    """
    Calculate percentage savings.
    
    Args:
        original: Original cost
        new: New cost
        
    Returns:
        Percentage savings (positive if new < original)
    """
    if original == 0:
        return 0.0
    return ((original - new) / original) * 100.0


def format_cost(cost: float, currency: str = "USD", decimal_places: int = 2) -> str:
    """
    Format cost with currency symbol.
    
    Args:
        cost: Cost amount
        currency: Currency code
        decimal_places: Number of decimal places
        
    Returns:
        Formatted cost string
    """
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CAD": "C$",
        "AUD": "A$"
    }
    
    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{cost:,.{decimal_places}f}"


def calculate_total_cost_breakdown(breakdown: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculate totals and percentages from a cost breakdown.
    
    Args:
        breakdown: Dictionary of category -> cost
        
    Returns:
        Dictionary with totals and percentages
    """
    total = sum(breakdown.values())
    
    percentages = {
        category: (cost / total * 100) if total > 0 else 0
        for category, cost in breakdown.items()
    }
    
    return {
        "total": total,
        "breakdown": breakdown,
        "percentages": percentages,
        "largest_category": max(breakdown.items(), key=lambda x: x[1])[0] if breakdown else None
    }


def project_costs_over_time(
    base_monthly_cost: float,
    months: int,
    growth_rate: Optional[float] = None
) -> Dict[str, Any]:
    """
    Project costs over multiple months with optional growth.
    
    Args:
        base_monthly_cost: Starting monthly cost
        months: Number of months to project
        growth_rate: Optional monthly growth rate (as decimal, e.g., 0.01 for 1%)
        
    Returns:
        Dictionary with monthly projections and totals
    """
    monthly_costs = []
    current_cost = base_monthly_cost
    
    for month in range(months):
        monthly_costs.append({
            "month": month + 1,
            "cost": current_cost
        })
        if growth_rate:
            current_cost = current_cost * (1 + growth_rate)
    
    total_cost = sum(m["cost"] for m in monthly_costs)
    
    return {
        "monthly_projections": monthly_costs,
        "total_cost": total_cost,
        "average_monthly": total_cost / months if months > 0 else 0,
        "growth_rate": growth_rate or 0
    }


def apply_discount(cost: float, discount_percentage: float) -> float:
    """
    Apply a discount percentage to a cost.
    
    Args:
        cost: Original cost
        discount_percentage: Discount percentage (e.g., 30 for 30% off)
        
    Returns:
        Cost after discount
    """
    return cost * (1 - discount_percentage / 100.0)


def calculate_roi(
    initial_investment: float,
    monthly_savings: float,
    months: int
) -> Dict[str, Any]:
    """
    Calculate ROI for an optimization investment.
    
    Args:
        initial_investment: One-time cost to implement
        monthly_savings: Monthly savings after implementation
        months: Number of months to calculate ROI for
        
    Returns:
        Dictionary with ROI metrics
    """
    total_savings = monthly_savings * months
    net_benefit = total_savings - initial_investment
    roi_percentage = (net_benefit / initial_investment * 100) if initial_investment > 0 else float('inf')
    payback_months = initial_investment / monthly_savings if monthly_savings > 0 else float('inf')
    
    return {
        "initial_investment": initial_investment,
        "total_savings": total_savings,
        "net_benefit": net_benefit,
        "roi_percentage": roi_percentage,
        "payback_months": payback_months,
        "is_profitable": net_benefit > 0
    }

