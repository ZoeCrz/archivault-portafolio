from rest_framework import serializers
from .models import PublicacionMarket, Oferta
from apps.webhooks.notifications import notify
from apps.catalog.models import Favorito
from config.media import resolve_media_url
from .services import marketplace_resource_name


class PublicacionMarketSerializer(serializers.ModelSerializer):
    tipo = serializers.SerializerMethodField()
    objetivo_id = serializers.SerializerMethodField()
    nombre = serializers.SerializerMethodField()
    sku = serializers.SerializerMethodField()
    coleccion = serializers.SerializerMethodField()
    imagen = serializers.SerializerMethodField()
    vendedor = serializers.SerializerMethodField()
    categoria = serializers.SerializerMethodField()
    estado_objetivo = serializers.SerializerMethodField()
    es_favorito = serializers.SerializerMethodField()

    def validate(self, attrs):
        pieza = attrs.get("pieza_inventario", getattr(self.instance, "pieza_inventario", None))
        coleccion = attrs.get("coleccion_usuario", getattr(self.instance, "coleccion_usuario", None))

        if (pieza is None) == (coleccion is None):
            raise serializers.ValidationError(
                "La publicación debe incluir exactamente una pieza o una colección."
            )
        request = self.context["request"]
        objetivo = pieza or coleccion
        if objetivo.user_id != request.user.id:
            raise serializers.ValidationError(
                "Sólo puedes publicar piezas o colecciones que te pertenecen."
            )

        description_was_provided = "descripcion" in attrs
        if description_was_provided:
            attrs["descripcion"] = attrs["descripcion"].strip()
        description = attrs.get(
            "descripcion",
            getattr(self.instance, "descripcion", ""),
        )
        condition_was_provided = "condicion" in attrs
        condition = attrs.get(
            "condicion",
            getattr(self.instance, "condicion", None),
        )

        errors = {}
        if self.instance is None:
            if not description:
                errors["descripcion"] = ["Añade una descripción breve para la publicación."]
            if pieza is not None and not condition_was_provided:
                condition = pieza.condicion
                attrs["condicion"] = condition
            elif coleccion is not None and not condition_was_provided:
                errors["condicion"] = ["Selecciona la condición de la colección."]
        else:
            # Los metadatos históricos vacíos no bloquean un PATCH que no los modifica.
            if description_was_provided and not description:
                errors["descripcion"] = ["Añade una descripción breve para la publicación."]

        if condition_was_provided and condition == "NO_ESPECIFICADA":
            errors["condicion"] = [
                "Selecciona una condición válida para la publicación."
            ]
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    class Meta:
        model = PublicacionMarket
        fields = [
            "id",
            "tipo",
            "objetivo_id",
            "nombre",
            "sku",
            "coleccion",
            "descripcion",
            "condicion",
            "imagen",
            "vendedor",
            "precio",
            "categoria",
            "estado",
            "estado_objetivo",
            "es_favorito",
            "fecha_publicacion",
            # Compatibilidad transitoria con clientes de escritura existentes.
            "pieza_inventario",
            "coleccion_usuario",
        ]
        read_only_fields = ["vendedor", "estado"]

    def get_tipo(self, obj):
        return "PIEZA" if obj.pieza_inventario_id else "COLECCION"

    def get_objetivo_id(self, obj):
        return obj.pieza_inventario_id or obj.coleccion_usuario_id

    def get_nombre(self, obj):
        return marketplace_resource_name(obj)

    def get_sku(self, obj):
        return obj.pieza_inventario.sku if obj.pieza_inventario_id else None

    def _master_collection(self, obj):
        if obj.pieza_inventario_id:
            return obj.pieza_inventario.pieza_catalogo.coleccion
        return obj.coleccion_usuario.coleccion

    def _user_collection_id(self, obj):
        if obj.pieza_inventario_id:
            return obj.pieza_inventario.coleccion_usuario_id
        return obj.coleccion_usuario_id

    def get_coleccion(self, obj):
        collection = self._master_collection(obj)
        return {
            "id": collection.id,
            "coleccion_usuario_id": self._user_collection_id(obj),
            "nombre": collection.nombre,
        }

    def get_imagen(self, obj):
        request = self.context.get("request")
        candidates = []
        if obj.pieza_inventario_id:
            photos = getattr(obj.pieza_inventario, "marketplace_photos", None)
            if photos is None:
                photos = obj.pieza_inventario.piezafoto_set.order_by("id")
            for photo in photos:
                if photo.archivo:
                    candidates.append(resolve_media_url(photo.archivo, request=request))
                if photo.url:
                    candidates.append(photo.url)
        else:
            image = self._master_collection(obj).imagen
            if image:
                candidates.append(resolve_media_url(image, request=request))
        return list(dict.fromkeys(candidate for candidate in candidates if candidate))

    def get_vendedor(self, obj):
        return {"id": obj.vendedor_id, "nombre": obj.vendedor.username}

    def get_categoria(self, obj):
        return self._master_collection(obj).categoria

    def get_estado_objetivo(self, obj):
        if obj.pieza_inventario_id:
            return obj.pieza_inventario.estado_adquisicion
        return None

    def get_es_favorito(self, obj):
        annotated = getattr(obj, "es_favorito", None)
        if annotated is not None:
            return annotated
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        filters = {"user": request.user}
        if obj.pieza_inventario_id:
            filters["pieza_inventario_id"] = obj.pieza_inventario_id
        else:
            filters["coleccion_maestra_id"] = obj.coleccion_usuario.coleccion_id
        return Favorito.objects.filter(**filters).exists()


class OfertaSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        offer = super().create(validated_data)
        resource_name = marketplace_resource_name(offer.publicacion)
        notify(
            offer.publicacion.vendedor,
            "oferta",
            f"{offer.comprador.username} hizo una oferta de ${offer.monto} por {resource_name}.",
            evento="OFFER_RECEIVED",
            destino_tipo="MARKETPLACE_PUBLICATION",
            destino_id=offer.publicacion_id,
            metadata={
                "actor_id": offer.comprador_id,
                "actor_name": offer.comprador.username,
                "resource_type": "PIEZA" if offer.publicacion.pieza_inventario_id else "COLECCION",
                "resource_name": resource_name,
                "offer_id": offer.id,
                "amount": str(offer.monto),
            },
        )
        return offer

    def validate(self, attrs):
        request = self.context["request"]
        publicacion = attrs.get("publicacion", getattr(self.instance, "publicacion", None))
        monto = attrs.get("monto", getattr(self.instance, "monto", None))

        if monto is not None and monto <= 0:
            raise serializers.ValidationError("El monto debe ser mayor que cero.")
        if self.instance is None:
            if publicacion.estado != "ACTIVA":
                raise serializers.ValidationError("La publicación no está activa.")
            if publicacion.vendedor_id == request.user.id:
                raise serializers.ValidationError("No puedes ofertar sobre tu propia publicación.")
            if Oferta.objects.filter(
                publicacion=publicacion,
                comprador=request.user,
            ).exists():
                raise serializers.ValidationError("Ya realizaste una oferta para esta publicación.")
        return attrs

    class Meta:
        model = Oferta
        fields = "__all__"
        read_only_fields = ["comprador", "estado"]
