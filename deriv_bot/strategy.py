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

def evaluate_ldp_strategy(prices: List[float], pip_size: int = 4) -> Tuple[Optional[str], Optional[str]]:
    """
    Evaluates the Over/Under Median Strategy on a list of prices.

    Args:
        prices: List of the latest tick prices (e.g., 500 ticks)
        pip_size: Number of decimal places the symbol naturally uses.

    Returns:
        Tuple of (contract_type, barrier) or (None, None) if no signal.
    """
    if not prices:
        return None, None

    last_digits = [extract_last_digit(p, pip_size) for p in prices]

    # Calculate Median
    median_val = statistics.median(last_digits)

    logger.info(f"Strategy: Median calculated as {median_val:.2f} across {len(prices)} ticks.")

    # Strategy Rules:
    # If Median > 4.5 -> OPEN OVER 2
    # If Median < 4.5 -> OPEN UNDER 7

    if median_val > 4.5:
        logger.info("Median > 4.5: Signaling DIGITOVER 2")
        return "DIGITOVER", "2"
    elif median_val < 4.5:
        logger.info("Median < 4.5: Signaling DIGITUNDER 7")
        return "DIGITUNDER", "7"

    # If exactly 4.5, no clear signal
    return None, None
