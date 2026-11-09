import logging

from django.http import JsonResponse
from graphql import GraphQLError
from graphene_django.views import GraphQLView
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.exceptions import (
    AUTHENTICATION_MESSAGE,
    CONFLICT_MESSAGE,
    INTERNAL_ERROR_MESSAGE,
    NOT_FOUND_MESSAGE,
    PERMISSION_MESSAGE,
    VALIDATION_MESSAGE,
    Conflict,
    get_request_id,
    normalize_error_fields,
)


logger = logging.getLogger("archivault.graphql")


class AuthenticatedGraphQLView(GraphQLView):
    def dispatch(self, request, *args, **kwargs):
        self._error_request = request
        try:
            authentication = JWTAuthentication().authenticate(request)
        except AuthenticationFailed:
            return self._authentication_error(request)
        if authentication is None:
            return self._authentication_error(request)
        request.user, request.auth = authentication
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _authentication_error(request):
        request_id = get_request_id(request)
        response = JsonResponse(
            {
                "error": {
                    "code": "authentication_required",
                    "message": AUTHENTICATION_MESSAGE,
                    "request_id": request_id,
                }
            },
            status=401,
        )
        response["X-Request-ID"] = request_id
        return response

    def format_error(self, error):
        if isinstance(error, GraphQLError) and error.extensions:
            formatted = error.formatted
            formatted["extensions"].setdefault(
                "request_id", get_request_id(getattr(self, "_error_request", None))
            )
            return formatted

        original_error = getattr(error, "original_error", None)
        request = getattr(self, "_error_request", None)
        request_id = get_request_id(request)
        if isinstance(original_error, Conflict):
            return {
                "message": str(original_error.detail) or CONFLICT_MESSAGE,
                "extensions": {"code": "CONFLICT", "request_id": request_id},
            }
        if isinstance(original_error, PermissionDenied):
            return {
                "message": PERMISSION_MESSAGE,
                "extensions": {"code": "PERMISSION_DENIED", "request_id": request_id},
            }
        if isinstance(original_error, NotFound):
            return {
                "message": NOT_FOUND_MESSAGE,
                "extensions": {"code": "NOT_FOUND", "request_id": request_id},
            }
        if isinstance(original_error, ValidationError):
            return {
                "message": VALIDATION_MESSAGE,
                "extensions": {
                    "code": "VALIDATION_ERROR",
                    "fields": normalize_error_fields(original_error.detail),
                    "request_id": request_id,
                },
            }
        if original_error is not None:
            logger.error(
                "Unhandled GraphQL exception",
                extra={
                    "request_id": request_id,
                    "error_code": "internal_error",
                    "request_path": getattr(request, "path", ""),
                    "request_method": getattr(request, "method", ""),
                    "user_id": getattr(getattr(request, "user", None), "id", None),
                },
                exc_info=(
                    type(original_error),
                    original_error,
                    original_error.__traceback__,
                ),
            )
            return {
                "message": INTERNAL_ERROR_MESSAGE,
                "extensions": {
                    "code": "INTERNAL_ERROR",
                    "request_id": request_id,
                },
            }

        return super().format_error(error)
