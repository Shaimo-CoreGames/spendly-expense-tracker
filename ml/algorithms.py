from typing import List, Dict
from collections import defaultdict
import statistics
# ==================== ML HELPER FUNCTIONS ====================

def simple_linear_regression(x_values: List[float], y_values: List[float]) -> tuple:
    """
    Simple linear regression: y = mx + b
    Returns (slope, intercept)
    """
    if len(x_values) < 2 or len(y_values) < 2:
        return (0, sum(y_values) / len(y_values) if y_values else 0)
    
    n = len(x_values)
    x_mean = sum(x_values) / n
    y_mean = sum(y_values) / n
    
    # Calculate slope (m)
    numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return (0, y_mean)
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    return (slope, intercept)

def moving_average(values: List[float], window: int = 7) -> float:
    """Calculate moving average for the most recent window"""
    if not values:
        return 0.0
    recent = values[-window:] if len(values) >= window else values
    return sum(recent) / len(recent)

def exponential_smoothing(values: List[float], alpha: float = 0.3) -> float:
    """Exponential smoothing for time series prediction"""
    if not values:
        return 0.0
    
    if len(values) == 1:
        return values[0]
    
    # Initialize with first value
    smoothed = values[0]
    
    # Apply exponential smoothing
    for value in values[1:]:
        smoothed = alpha * value + (1 - alpha) * smoothed
    
    return smoothed

def calculate_trend(values: List[float]) -> str:
    """Determine trend direction from historical data"""
    if len(values) < 2:
        return "stable"
    
    # Use linear regression slope to determine trend
    x = list(range(len(values)))
    slope, _ = simple_linear_regression(x, values)
    
    if slope > 0.1:
        return "increasing"
    elif slope < -0.1:
        return "decreasing"
    else:
        return "stable"

def calculate_volatility(values: List[float]) -> str:
    """Calculate spending volatility"""
    if len(values) < 2:
        return "low"
    
    try:
        std_dev = statistics.stdev(values)
        mean = statistics.mean(values)
        
        if mean == 0:
            return "low"
        
        coefficient_of_variation = std_dev / mean
        
        if coefficient_of_variation > 0.5:
            return "high"
        elif coefficient_of_variation > 0.25:
            return "medium"
        else:
            return "low"
    except:
        return "low"

def predict_next_week_expenses(historical_data: List[Dict]) -> Dict[str, float]:
    """
    Predict next week's expenses by category using multiple methods
    """
    predictions = {}
    
    # Group by category
    category_data = defaultdict(list)
    for expense in historical_data:
        category_data[expense['category']].append(expense['amount'])
    
    for category, amounts in category_data.items():
        if not amounts:
            predictions[category] = 0.0
            continue
        
        # Method 1: Moving average (40% weight)
        ma = moving_average(amounts, window=7)
        
        # Method 2: Exponential smoothing (40% weight)
        es = exponential_smoothing(amounts, alpha=0.3)
        
        # Method 3: Linear regression prediction (20% weight)
        x = list(range(len(amounts)))
        slope, intercept = simple_linear_regression(x, amounts)
        lr_pred = slope * len(amounts) + intercept
        
        # Weighted average of predictions
        weighted_pred = (0.4 * ma + 0.4 * es + 0.2 * lr_pred)
        
        # Ensure non-negative prediction
        predictions[category] = max(0, weighted_pred)
    
    return predictions

def calculate_confidence(historical_data: List[float]) -> float:
    """Calculate prediction confidence based on data consistency"""
    if len(historical_data) < 2:
        return 0.3  # Low confidence with little data
    
    try:
        # Calculate coefficient of variation
        mean = statistics.mean(historical_data)
        std_dev = statistics.stdev(historical_data)
        
        if mean == 0:
            return 0.5
        
        cv = std_dev / mean
        
        # More consistent data = higher confidence
        # CV of 0 = 100% confidence, CV of 1+ = 30% confidence
        confidence = max(0.3, min(1.0, 1.0 - cv))
        
        # Adjust based on sample size
        size_factor = min(1.0, len(historical_data) / 30)
        
        return round(confidence * size_factor, 2)
    except:
        return 0.5

