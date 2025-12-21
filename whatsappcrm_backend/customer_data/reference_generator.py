# customer_data/reference_generator.py

import random
import string
from typing import Literal
from datetime import date


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


def generate_shared_booking_reference(tour_id: int, start_date: date) -> str:
    """
    Generates a shared booking reference for a specific tour and date.
    All travelers on the same tour and date will share this reference.
    
    Args:
        tour_id: The ID of the tour package
        start_date: The start date of the tour
    
    Returns:
        A booking reference string like 'BK-T001-20231225'
    """
    # Format: BK-T{tour_id}-{YYYYMMDD}
    date_str = start_date.strftime('%Y%m%d')
    return f"BK-T{tour_id:03d}-{date_str}"


def generate_inquiry_reference() -> str:
    """
    Generates a unique tour inquiry reference with TQ prefix.
    
    Returns:
        A tour inquiry reference string like 'TQ12345678'
    """
    return generate_reference_id('TQ')
