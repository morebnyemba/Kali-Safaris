# whatsappcrm_backend/customer_data/traveler_validation.py
"""
Single source of truth for what counts as a complete traveler record.

Customer-facing booking channels (WhatsApp booking flow, website checkout)
must not create a Booking until every booked passenger passes these checks,
so every booking reaches the park manifest with full passenger details.
"""

MAX_AGE = 120
_EMPTY = {'', 'none', 'null', 'undefined', 'n/a', 'na'}
_GENDERS = {'m': 'Male', 'male': 'Male', 'f': 'Female', 'female': 'Female', 'other': 'Other'}
_NO_MEDICAL = {'', 'none', 'no', 'n/a', 'na', 'nil', 'no special requirements'}


def _text(value):
    text = '' if value is None else str(value).strip()
    return '' if text.lower() in _EMPTY else text


def normalize_traveler(data, label='Traveler'):
    """
    Returns (cleaned, error). `cleaned` holds model-ready values
    (name, age, nationality, gender, id_number, traveler_type,
    medical_dietary_requirements); `error` is a customer-safe message.
    Age 0 (infant under one) is valid.
    """
    if not isinstance(data, dict):
        return None, f"{label}: details are missing."

    name = _text(data.get('name'))
    nationality = _text(data.get('nationality'))
    gender_raw = _text(data.get('gender'))
    id_number = _text(data.get('id_number'))
    traveler_type = _text(data.get('type')).lower() or 'adult'
    medical = _text(data.get('medical'))

    if len(name) < 2:
        return None, f"{label}: full name is required."

    try:
        age_value = float(_text(data.get('age')))
    except (TypeError, ValueError):
        age_value = -1.0
    if not age_value.is_integer() or not 0 <= age_value <= MAX_AGE:
        return None, f"{name}: a valid age is required (0 for infants under one)."
    age = int(age_value)

    if not nationality:
        return None, f"{name}: nationality is required."
    gender = _GENDERS.get(gender_raw.lower())
    if not gender:
        return None, f"{name}: gender must be Male, Female or Other."
    if len(id_number) < 3:
        return None, f"{name}: ID or passport number is required."
    if traveler_type not in ('adult', 'child'):
        traveler_type = 'adult'

    return {
        'name': name,
        'age': age,
        'nationality': nationality,
        'gender': gender,
        'id_number': id_number,
        'traveler_type': traveler_type,
        'medical_dietary_requirements': '' if medical.lower() in _NO_MEDICAL else medical,
    }, None


def validate_traveler_list(travelers, expected_count):
    """
    Returns (cleaned_list, error). Requires exactly `expected_count`
    complete, distinct travelers (same name + ID twice is a duplicate).
    """
    if not isinstance(travelers, (list, tuple)):
        travelers = []
    if expected_count < 1:
        return [], "At least one traveler is required."
    if len(travelers) != expected_count:
        return [], (
            f"Traveler details are required for all {expected_count} passenger(s); "
            f"received {len(travelers)}."
        )

    cleaned, seen = [], set()
    for idx, data in enumerate(travelers, start=1):
        traveler, error = normalize_traveler(data, label=f"Traveler {idx}")
        if error:
            return [], error
        key = (traveler['name'].lower(), traveler['id_number'].lower())
        if key in seen:
            return [], f"{traveler['name']} ({traveler['id_number']}) was entered twice."
        seen.add(key)
        cleaned.append(traveler)
    return cleaned, None
