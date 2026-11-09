import logging
import uuid

from django.db import IntegrityError
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


logger = logging.getLogger("archivault.api")

VALIDATION_MESSAGE = "Revisa los datos indicados e inténtalo nuevamente."
AUTHENTICATION_MESSAGE = "Tu sesión ha expirado. Inicia sesión nuevamente."
INVALID_CREDENTIALS_MESSAGE = "El usuario o la contraseña no son correctos."
PERMISSION_MESSAGE = "No tienes permiso para realizar esta acción."
NOT_FOUND_MESSAGE = "El contenido solicitado ya no está disponible o no existe."
CONFLICT_MESSAGE = "La operación entra en conflicto con el estado actual del contenido."
INTERNAL_ERROR_MESSAGE = (
    "No pudimos completar la operación por un problema interno. "
    "Inténtalo nuevamente y, si continúa, contacta con soporte."
)


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = CONFLICT_MESSAGE
    default_code = "conflict"


class InvalidCredentials(AuthenticationFailed):
    default_detail = INVALID_CREDENTIALS_MESSAGE
    default_code = "invalid_credentials"


def get_request_id(request=None):
    if request is not None and getattr(request, "error_request_id", None):
        return request.error_request_id
    request_id = uuid.uuid4().hex
    if request is not None:
        request.error_request_id = request_id
    return request_id


def normalize_error_fields(detail):
    if isinstance(detail, dict):
        return {
            str(field): normalize_error_fields(value)
            for field, value in detail.items()
        }
    if isinstance(detail, (list, tuple)):
        return [normalize_error_fields(value) for value in detail]
    return str(detail)


def error_response(code, message, request_id, *, fields=None, status_code=400):
    public_error = {
        "code": code,
        "message": message,
        "request_id": request_id,
    }
    if fields:
        public_error["fields"] = fields
    response = Response({"error": public_error}, status=status_code)
    response["X-Request-ID"] = request_id
    return response


def _request_log_context(request, request_id, code):
    user = getattr(request, "user", None)
    return {
        "request_id": request_id,
        "error_code": code,
        "request_path": getattr(request, "path", ""),
        "request_method": getattr(request, "method", ""),
        "user_id": getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None,
    }


def api_exception_handler(exc, context):
    request = context.get("request")
    request_id = get_request_id(request)

    if isinstance(exc, IntegrityError):
        logger.warning(
            "Database constraint conflict",
            extra=_request_log_context(request, request_id, "conflict"),
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return error_response(
            "conflict",
            "El contenido cambió o ya existe. Actualiza la página e inténtalo nuevamente.",
            request_id,
            status_code=status.HTTP_409_CONFLICT,
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        logger.exception(
            "Unhandled API exception",
            extra=_request_log_context(request, request_id, "internal_error"),
        )
        return error_response(
            "internal_error",
            INTERNAL_ERROR_MESSAGE,
            request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, InvalidCredentials):
        code, message = "invalid_credentials", INVALID_CREDENTIALS_MESSAGE
    elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        code, message = "authentication_required", AUTHENTICATION_MESSAGE
    elif isinstance(exc, PermissionDenied):
        code, message = "permission_denied", PERMISSION_MESSAGE
    elif isinstance(exc, NotFound):
        code, message = "not_found", NOT_FOUND_MESSAGE
    elif isinstance(exc, Conflict):
        code, message = "conflict", str(exc.detail)
    elif isinstance(exc, ValidationError):
        fields = normalize_error_fields(response.data)
        return error_response(
            "validation_error",
            VALIDATION_MESSAGE,
            request_id,
            fields=fields,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    elif response.status_code == status.HTTP_401_UNAUTHORIZED:
        code, message = "authentication_required", AUTHENTICATION_MESSAGE
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        code, message = "permission_denied", PERMISSION_MESSAGE
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        code, message = "not_found", NOT_FOUND_MESSAGE
    elif response.status_code == status.HTTP_409_CONFLICT:
        code, message = "conflict", CONFLICT_MESSAGE
    elif response.status_code >= 500:
        logger.error(
            "Internal API exception",
            extra=_request_log_context(request, request_id, "internal_error"),
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        code, message = "internal_error", INTERNAL_ERROR_MESSAGE
    else:
        code = "request_error"
        message = "No pudimos completar la solicitud. Revisa los datos e inténtalo nuevamente."

    return error_response(code, message, request_id, status_code=response.status_code)
