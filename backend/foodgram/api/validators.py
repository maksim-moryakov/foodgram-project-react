from re import compile

from django.core.exceptions import ValidationError


def validate_username(value):
    pattern = compile(r"^[\w.@+-]+\Z")
    if not pattern.match(value):
        raise ValidationError(
            'username должен соответствовать шаблону ^[\\w.@+-]+\\z'
        )
    if value.lower() == 'me':
        raise ValidationError(
            'username не может быть me.'
        )
    return value
