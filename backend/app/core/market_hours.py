"""Market hours detection and utilities."""
from datetime import datetime, time
from zoneinfo import ZoneInfo

# US market holidays 2025 (NYSE/NASDAQ)
MARKET_HOLIDAYS_2025 = [
    "2025-01-01",  # New Year's Day
    "2025-01-20",  # MLK Day
    "2025-02-17",  # Presidents Day
    "2025-04-18",  # Good Friday
    "2025-05-26",  # Memorial Day
    "2025-07-04",  # Independence Day
    "2025-09-01",  # Labor Day
    "2025-11-27",  # Thanksgiving
    "2025-12-25",  # Christmas
]


def is_market_hours() -> bool:
    """
    Check if current time is during US market hours.
    
    Market hours: 9:30 AM - 4:00 PM ET, Monday-Friday, excluding holidays.
    
    Returns:
        True if market is currently open, False otherwise
    """
    # Get current time in ET
    et_tz = ZoneInfo("America/New_York")
    now_et = datetime.now(et_tz)
    
    # Check if weekend
    if now_et.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    
    # Check if holiday
    date_str = now_et.strftime("%Y-%m-%d")
    if date_str in MARKET_HOLIDAYS_2025:
        return False
    
    # Check if within trading hours (9:30 AM - 4:00 PM ET)
    market_open = time(9, 30)
    market_close = time(16, 0)
    current_time = now_et.time()
    
    return market_open <= current_time < market_close


def get_market_status() -> dict:
    """
    Get detailed market status information.
    
    Returns:
        Dict with:
        - is_open: bool
        - current_time_et: str (ISO format)
        - next_open: str (description)
        - next_close: str (description)
    """
    et_tz = ZoneInfo("America/New_York")
    now_et = datetime.now(et_tz)
    
    is_open = is_market_hours()
    
    # Simple next open/close messages
    if is_open:
        next_event = "Market closes at 4:00 PM ET"
    elif now_et.weekday() >= 5:
        next_event = "Market opens Monday at 9:30 AM ET"
    else:
        next_event = "Market opens at 9:30 AM ET"
    
    return {
        "is_open": is_open,
        "current_time_et": now_et.isoformat(),
        "status": "OPEN" if is_open else "CLOSED",
        "next_event": next_event,
    }

