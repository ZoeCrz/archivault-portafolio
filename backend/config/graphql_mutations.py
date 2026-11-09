from graphql import GraphQLError

from config.exceptions import (
    PERMISSION_MESSAGE,
    VALIDATION_MESSAGE,
    get_request_id,
    normalize_error_fields,
)


def serializer_save(serializer_class, info, data, instance=None, **save_kwargs):
    serializer = serializer_class(
        instance=instance,
        data=dict(data),
        partial=instance is not None,
        context={"request": info.context},
    )
    if not serializer.is_valid():
        raise GraphQLError(
            VALIDATION_MESSAGE,
            extensions={
                "code": "VALIDATION_ERROR",
                "fields": normalize_error_fields(serializer.errors),
                "request_id": get_request_id(info.context),
            },
        )
    return serializer.save(**save_kwargs)


def require_owner(condition, message="No tienes permiso para modificar este recurso."):
    if not condition:
        raise GraphQLError(
            message or PERMISSION_MESSAGE,
            extensions={"code": "PERMISSION_DENIED"},
        )
