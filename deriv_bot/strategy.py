import statistics
from typing import List, Tuple, Optional

import logging

logger = logging.getLogger(__name__)

def extract_last_digit(price: float, pip_size: int = 4) -> int:
    """
    Return the final decimal digit of a price when formatted to the specified pip precision.
    
    Parameters:
        price (float): The price value to inspect.
        pip_size (int): Number of decimal places to format the price to before extracting the digit.
    
    Returns:
        int: The last decimal digit of the formatted price (0–9).
    """
    # Format the float explicitly to the symbol's required decimal places.
    # E.g., if price is 123.4 and pip_size is 2 -> "123.40", last digit is 0.
    format_string = f"{{:.{pip_size}f}}"
    price_str = format_string.format(price)

    return int(price_str[-1])

def evaluate_ldp_strategy(prices: List[float], pip_size: int = 4, mode: str = "auto_median") -> Tuple[Optional[str], Optional[str]]:
    """
    Determine an Over/Under contract signal and barrier from recent tick prices using the selected mode.
    
    Parameters:
    	prices (List[float]): Recent tick prices (must contain at least 5 entries).
    	pip_size (int): Number of decimal places the symbol uses.
    	mode (str): Strategy mode; one of "auto_median", "strict_over", or "strict_under".
    		- "auto_median": use the median of last digits to pick DIGITOVER ("3") if median > 4.5 or DIGITUNDER ("6") if median < 4.5.
    		- "strict_over": if at least 3 of the last 4 digits are <= 3, signal DIGITOVER ("3").
    		- "strict_under": if at least 3 of the last 4 digits are >= 6, signal DIGITUNDER ("6").
    
    Returns:
    	tuple: `(contract_type, barrier)` where `contract_type` is `"DIGITOVER"` or `"DIGITUNDER"` and `barrier` is the barrier digit as a string; returns `(None, None)` when no signal is produced.
    """
    if not prices or len(prices) < 5:
        return None, None

    last_digits = [extract_last_digit(p, pip_size) for p in prices]

    if mode == "auto_median":
        # Calculate Median for mean reversion.
        median_val = statistics.median(last_digits)

        # We use Over 3 (wins on 4,5,6,7,8,9 -> 60% chance)
        # and Under 6 (wins on 0,1,2,3,4,5 -> 60% chance)
        # This requires a higher Martingale multiplier (~2.5x) but wins much more frequently.
        if median_val > 4.5:
            return "DIGITOVER", "3"
        elif median_val < 4.5:
            return "DIGITUNDER", "6"

    elif mode == "strict_over":
        # Strategy: Strict OVER 3
        # Look for a streak of low numbers (e.g., 3 out of the last 4 ticks were <= 3)
        # We bet on mean reversion (that the next tick will pop back over 3).
        recent_digits = last_digits[-4:]
        low_count = sum(1 for d in recent_digits if d <= 3)
        if low_count >= 3:
            return "DIGITOVER", "3"

    elif mode == "strict_under":
        # Strategy: Strict UNDER 6
        # Look for a streak of high numbers (e.g., 3 out of the last 4 ticks were >= 6)
        # We bet on mean reversion (that the next tick will drop back under 6).
        recent_digits = last_digits[-4:]
        high_count = sum(1 for d in recent_digits if d >= 6)
        if high_count >= 3:
            return "DIGITUNDER", "6"

    return None, None
