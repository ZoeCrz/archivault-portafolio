from rest_framework.permissions import IsAuthenticated, SAFE_METHODS


class IsResourceOwnerOrReadOnly(IsAuthenticated):
    """Permite lectura; delega las mutaciones a la regla de propiedad del viewset."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff or view.is_owner(obj, request.user)
