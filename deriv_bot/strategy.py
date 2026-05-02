import statistics
from typing import List, Tuple, Optional

import logging

logger = logging.getLogger(__name__)

def extract_last_digit(price: float, pip_size: int = 4) -> int:
    """
    Extract the last digit from a price based on its precise pip size.
    Deriv indices have highly specific decimal places (e.g., R_100 has 2, Vol 75 has 4).
    """
    # Format the float explicitly to the symbol's required decimal places.
    # E.g., if price is 123.4 and pip_size is 2 -> "123.40", last digit is 0.
    format_string = f"{{:.{pip_size}f}}"
    price_str = format_string.format(price)

    return int(price_str[-1])

def evaluate_ldp_strategy(prices: List[float], pip_size: int = 4, mode: str = "auto_median") -> Tuple[Optional[str], Optional[str]]:
    """
    Evaluates the Over/Under Strategy based on the selected mode.

    Args:
        prices: List of the latest tick prices.
        pip_size: Number of decimal places the symbol naturally uses.
        mode: The strategy mode ('auto_median', 'strict_over', 'strict_under')

    Returns:
        Tuple of (contract_type, barrier) or (None, None) if no signal.
    """
    if not prices or len(prices) < 5:
        return None, None

    if mode == "auto_median":
        # Calculate Median for mean reversion on all prices.
        last_digits = [extract_last_digit(p, pip_size) for p in prices]
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
        # We only need the last 4 prices to determine the signal.
        recent_digits = [extract_last_digit(p, pip_size) for p in prices[-4:]]
        low_count = sum(1 for d in recent_digits if d <= 3)
        if low_count >= 3:
            return "DIGITOVER", "3"

    elif mode == "strict_under":
        # Strategy: Strict UNDER 6
        # Look for a streak of high numbers (e.g., 3 out of the last 4 ticks were >= 6)
        # We bet on mean reversion (that the next tick will drop back under 6).
        # We only need the last 4 prices to determine the signal.
        recent_digits = [extract_last_digit(p, pip_size) for p in prices[-4:]]
        high_count = sum(1 for d in recent_digits if d >= 6)
        if high_count >= 3:
            return "DIGITUNDER", "6"

    return None, None
