import statistics
from typing import List, Tuple, Optional

def extract_last_digit(price: float) -> int:
    """
    Extract the last digit from a price.
    Usually Deriv indices have prices with 2, 3 or 4 decimal places.
    We convert the float to string, remove the decimal point, and take the last character.
    """
    # Converting to string based on how it's naturally represented,
    # but forcing a clean decimal structure. For ticks like 1000.0,
    # the last digit of the price is actually 0.
    price_str = f"{price:.4f}".rstrip('0')
    if price_str.endswith('.'):
        # E.g. 123.0000 -> 123. -> 123
        price_str = price_str[:-1]

    return int(price_str[-1])

def evaluate_ldp_strategy(prices: List[float]) -> Tuple[Optional[str], Optional[str]]:
    """
    Evaluates the Over/Under Median Strategy on a list of prices.

    Args:
        prices: List of the latest tick prices (e.g., 500 ticks)

    Returns:
        Tuple of (contract_type, barrier) or (None, None) if no signal.
    """
    if not prices:
        return None, None

    last_digits = [extract_last_digit(p) for p in prices]

    # Calculate Median
    median_val = statistics.median(last_digits)

    # Strategy Rules:
    # If Median > 4.5 -> OPEN OVER 2
    # If Median < 4.5 -> OPEN UNDER 7

    if median_val > 4.5:
        return "DIGITOVER", "2"
    elif median_val < 4.5:
        return "DIGITUNDER", "7"

    # If exactly 4.5, no clear signal
    return None, None
