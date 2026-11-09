from rest_framework import serializers
from .models import (
    ColeccionMaestra,
    PiezaCatalogo,
    ColeccionUsuario,
    PiezaInventario,
    PiezaFoto,
    Favorito,
)
from config.serializer_fields import MediaFileField
from config.exceptions import Conflict
from rest_framework.exceptions import NotFound
from .favorites import (
    can_access_favorite_collection,
    can_access_favorite_piece,
    favorite_is_available,
)


class ColeccionMaestraSerializer(serializers.ModelSerializer):
    imagen = MediaFileField(required=False, allow_null=True)

    class Meta:
        model = ColeccionMaestra
        fields = "__all__"
        read_only_fields = ["propietario"]


class PiezaCatalogoSerializer(serializers.ModelSerializer):
    def validate_coleccion(self, coleccion):
        request = self.context["request"]
        if not request.user.is_staff and coleccion.propietario_id != request.user.id:
            raise serializers.ValidationError("No puedes modificar el catálogo de esta colección.")
        return coleccion

    class Meta:
        model = PiezaCatalogo
        fields = "__all__"


class ColeccionUsuarioSerializer(serializers.ModelSerializer):
    def validate_coleccion(self, coleccion):
        if coleccion.tipo != "global" and coleccion.propietario_id != self.context["request"].user.id:
            raise serializers.ValidationError("No puedes participar en una colección personal ajena.")
        return coleccion

    class Meta:
        model = ColeccionUsuario
        fields = "__all__"
        read_only_fields = ["user", "progreso"]


class PiezaInventarioSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        coleccion_usuario = attrs.get(
            "coleccion_usuario",
            getattr(self.instance, "coleccion_usuario", None),
        )
        pieza_catalogo = attrs.get(
            "pieza_catalogo",
            getattr(self.instance, "pieza_catalogo", None),
        )
        request = self.context["request"]
        if coleccion_usuario and coleccion_usuario.user_id != request.user.id:
            raise serializers.ValidationError("La colección no pertenece al usuario autenticado.")
        if (
            coleccion_usuario
            and pieza_catalogo
            and pieza_catalogo.coleccion_id != coleccion_usuario.coleccion_id
        ):
            raise serializers.ValidationError("La pieza no pertenece a la colección indicada.")
        return attrs

    class Meta:
        model = PiezaInventario
        fields = "__all__"
        read_only_fields = ["user"]


class PiezaFotoSerializer(serializers.ModelSerializer):
    archivo = MediaFileField(required=False, allow_null=True)

    def validate(self, attrs):
        url = attrs.get("url", getattr(self.instance, "url", ""))
        archivo = attrs.get("archivo", getattr(self.instance, "archivo", None))
        if not url and not archivo:
            raise serializers.ValidationError("Debes proporcionar un archivo o una URL.")
        return attrs

    def validate_pieza_inventario(self, pieza):
        if pieza.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("La pieza no pertenece al usuario autenticado.")
        return pieza

    class Meta:
        model = PiezaFoto
        fields = "__all__"


class FavoritoSerializer(serializers.ModelSerializer):
    tipo = serializers.SerializerMethodField()
    objetivo_id = serializers.SerializerMethodField()
    disponible = serializers.SerializerMethodField()

    def validate(self, attrs):
        user = self.context["request"].user
        pieza = attrs.get("pieza_inventario")
        coleccion = attrs.get("coleccion_maestra")
        if (pieza is None) == (coleccion is None):
            raise serializers.ValidationError(
                "Selecciona exactamente una pieza o una colección."
            )
        duplicate = Favorito.objects.filter(user=user)
        if pieza and duplicate.filter(pieza_inventario=pieza).exists():
            raise Conflict("Esta pieza ya está en tus favoritos.")
        if coleccion and duplicate.filter(coleccion_maestra=coleccion).exists():
            raise Conflict("Esta colección ya está en tus favoritos.")
        return attrs

    def validate_pieza_inventario(self, pieza):
        if not can_access_favorite_piece(self.context["request"].user, pieza):
            raise NotFound()
        return pieza

    def validate_coleccion_maestra(self, coleccion):
        if not can_access_favorite_collection(
            self.context["request"].user, coleccion
        ):
            raise NotFound()
        return coleccion

    def get_tipo(self, obj):
        return "PIEZA" if obj.pieza_inventario_id else "COLECCION"

    def get_objetivo_id(self, obj):
        return obj.pieza_inventario_id or obj.coleccion_maestra_id

    def get_disponible(self, obj):
        return favorite_is_available(obj, self.context["request"].user)

    class Meta:
        model = Favorito
        fields = [
            "id",
            "tipo",
            "objetivo_id",
            "pieza_inventario",
            "coleccion_maestra",
            "disponible",
        ]
