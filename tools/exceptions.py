from rest_framework.views import exception_handler
from rest_framework import serializers

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and isinstance(response.data, dict):
        first_error = None

        def extract_first_error(errors):
            if isinstance(errors, dict):
                for v in errors.values():
                    msg = extract_first_error(v)
                    if msg:
                        return msg
            elif isinstance(errors, list) and errors:
                return extract_first_error(errors[0])
            elif isinstance(errors, (str, serializers.ErrorDetail)):
                return str(errors)
            return None

        first_error = extract_first_error(response.data)
        response.data = {"detail": first_error or "Invalid request"}

    return response
