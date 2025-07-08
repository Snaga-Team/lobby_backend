from django.core.exceptions import ValidationError

import re

def validate_hex_color(value: str) -> None:
    """
    Validates that the given string is a proper HEX color code.

    Accepts:
        - 3-digit (e.g. "#fff")
        - 6-digit (e.g. "#ffffff")

    Args:
        value (str): The value to validate.

    Raises:
        ValidationError: If the value is not a valid HEX color.
    """
    
    if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', value):
        raise ValidationError(
            "Invalid HEX color code. Example: #fff or #ffffff.",
            code="invalid_hex"
        )
