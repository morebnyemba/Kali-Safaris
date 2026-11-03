# customer_data/reference_generator.py

import random
import string
from typing import Literal
from datetime import date, time
from typing import Optional


def generate_reference_id(prefix: Literal['BK', 'TQ']) -> str:
    """
    Generates an 8-digit reference code with the specified prefix.
    
    Args:
        prefix: Either 'BK' for bookings or 'TQ' for tour inquiries
        
    Returns:
        A reference string in the format: {prefix}12345678 (prefix + 8 digits)
        
    Examples:
        - generate_reference_id('BK') -> 'BK87654321'
        - generate_reference_id('TQ') -> 'TQ12345678'
    """
    # Generate 8 random digits
    digits = ''.join(random.choices(string.digits, k=8))
    return f"{prefix}{digits}"


def generate_booking_reference() -> str:
    """
    Generates a unique booking reference with BK prefix.
    
    Returns:
        A booking reference string like 'BK12345678'
    """
    return generate_reference_id('BK')


def generate_shared_booking_reference(tour_id: int, start_date: date, start_time: Optional[time] = None) -> str:
    """
    Generates a shared booking reference for a specific tour departure.
    All travelers on the same tour, date (and departure time, when the tour
    has fixed departures) share this reference — it's the manifest key, so
    the 06:00 and 16:00 groups of one tour must not be merged.

    Returns e.g. 'BK-T001-20231225', or 'BK-T001-20231225-1600' with a time.
    """
    ref = f"BK-T{tour_id:03d}-{start_date.strftime('%Y%m%d')}"
    if start_time:
        ref += f"-{start_time.strftime('%H%M')}"
    return ref


def generate_inquiry_reference() -> str:
    """
    Generates a unique tour inquiry reference with TQ prefix.
    
    Returns:
        A tour inquiry reference string like 'TQ12345678'
    """
    return generate_reference_id('TQ')
