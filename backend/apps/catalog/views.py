from rest_framework import mixins, serializers, viewsets
from django.db.models import Q
from config.permissions import IsResourceOwnerOrReadOnly
from .models import (
    ColeccionMaestra,
    PiezaCatalogo,
    ColeccionUsuario,
    PiezaInventario,
    PiezaFoto,
    Favorito,
)
from .serializers import (
    ColeccionMaestraSerializer,
    PiezaCatalogoSerializer,
    ColeccionUsuarioSerializer,
    PiezaInventarioSerializer,
    PiezaFotoSerializer,
    FavoritoSerializer,
)


class ColeccionMaestraViewSet(viewsets.ModelViewSet):
    queryset = ColeccionMaestra.objects.all()
    serializer_class = ColeccionMaestraSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def get_queryset(self):
        return ColeccionMaestra.objects.filter(
            Q(tipo="global")
            | Q(propietario=self.request.user)
            | Q(coleccionusuario__user=self.request.user)
            | Q(coleccionusuario__publicacionmarket__isnull=False)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(propietario=self.request.user)

    def is_owner(self, obj, user):
        return obj.propietario_id == user.id


class PiezaCatalogoViewSet(viewsets.ModelViewSet):
    queryset = PiezaCatalogo.objects.all()
    serializer_class = PiezaCatalogoSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def get_queryset(self):
        return PiezaCatalogo.objects.filter(
            Q(coleccion__tipo="global")
            | Q(coleccion__propietario=self.request.user)
            | Q(coleccion__coleccionusuario__user=self.request.user)
            | Q(piezainventario__publicacionmarket__isnull=False)
            | Q(coleccion__coleccionusuario__publicacionmarket__isnull=False)
        ).distinct()

    def is_owner(self, obj, user):
        return obj.coleccion.propietario_id == user.id


class ColeccionUsuarioViewSet(viewsets.ModelViewSet):
    queryset = ColeccionUsuario.objects.all()
    serializer_class = ColeccionUsuarioSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def get_queryset(self):
        return ColeccionUsuario.objects.filter(
            Q(user=self.request.user) | Q(publicacionmarket__isnull=False)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def is_owner(self, obj, user):
        return obj.user_id == user.id


class PiezaInventarioViewSet(viewsets.ModelViewSet):
    queryset = PiezaInventario.objects.all()
    serializer_class = PiezaInventarioSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def get_queryset(self):
        return PiezaInventario.objects.filter(
            Q(user=self.request.user) | Q(publicacionmarket__isnull=False)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def is_owner(self, obj, user):
        return obj.user_id == user.id


class PiezaFotoViewSet(viewsets.ModelViewSet):
    queryset = PiezaFoto.objects.all()
    serializer_class = PiezaFotoSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def get_queryset(self):
        return PiezaFoto.objects.filter(
            Q(pieza_inventario__user=self.request.user)
            | Q(pieza_inventario__publicacionmarket__isnull=False)
        ).distinct()

    def is_owner(self, obj, user):
        return obj.pieza_inventario.user_id == user.id


class FavoritoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Favorito.objects.all()
    serializer_class = FavoritoSerializer

    def get_queryset(self):
        queryset = Favorito.objects.filter(user=self.request.user).select_related(
            "pieza_inventario",
            "coleccion_maestra",
        )
        favorite_type = self.request.query_params.get("tipo")
        if favorite_type == "PIEZA":
            return queryset.filter(pieza_inventario__isnull=False)
        if favorite_type == "COLECCION":
            return queryset.filter(coleccion_maestra__isnull=False)
        if favorite_type:
            raise serializers.ValidationError(
                {"tipo": ["Selecciona un tipo de favorito válido."]}
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
