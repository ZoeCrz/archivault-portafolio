from django.conf import settings
from django.db import models
from config.validators import validate_image_file


class ColeccionMaestra(models.Model):
    TIPOS = [
        ("personal", "Personal"),
        ("global", "Global"),
    ]

    nombre = models.CharField(max_length=120)
    categoria = models.CharField(max_length=80)
    total_piezas = models.PositiveIntegerField(default=0)
    tipo = models.CharField(max_length=20, choices=TIPOS, default="personal")
    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="colecciones_creadas",
        null=True,
        blank=True,
    )
    imagen = models.FileField(
        upload_to="collections/",
        validators=[validate_image_file],
        blank=True,
    )

    def __str__(self):
        return self.nombre


class PiezaCatalogo(models.Model):
    coleccion = models.ForeignKey(ColeccionMaestra, on_delete=models.CASCADE)
    numero_item = models.CharField(max_length=50)
    nombre = models.CharField(max_length=120)
    sku_base = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.nombre


class ColeccionUsuario(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coleccion = models.ForeignKey(ColeccionMaestra, on_delete=models.CASCADE)
    progreso = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fecha_inicio = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "coleccion"],
                name="unique_user_collection",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.coleccion.nombre}"


class PiezaInventario(models.Model):
    ESTADOS_ADQUISICION = [
        ("ADQUIRIDA", "Adquirida"),
        ("DESEADA", "Deseada"),
    ]
    VISIBILIDADES = [
        ("PUBLICA", "Pública"),
        ("PRIVADA", "Privada"),
    ]
    CONDICIONES = [
        ("NUEVA", "Nueva"),
        ("USADA", "Usada"),
        ("DAÑADA", "Dañada"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coleccion_usuario = models.ForeignKey(ColeccionUsuario, on_delete=models.CASCADE)
    pieza_catalogo = models.ForeignKey(PiezaCatalogo, on_delete=models.CASCADE)
    nombre_personalizado = models.CharField(max_length=120, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    estado_adquisicion = models.CharField(max_length=80, choices=ESTADOS_ADQUISICION)
    visibilidad = models.CharField(max_length=80, choices=VISIBILIDADES)
    condicion = models.CharField(max_length=80, choices=CONDICIONES)
    talla = models.CharField(max_length=50, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(estado_adquisicion__in=["ADQUIRIDA", "DESEADA"]),
                name="valid_inventory_acquisition_status",
            ),
            models.CheckConstraint(
                check=models.Q(visibilidad__in=["PUBLICA", "PRIVADA"]),
                name="valid_inventory_visibility",
            ),
            models.CheckConstraint(
                check=models.Q(condicion__in=["NUEVA", "USADA", "DAÑADA"]),
                name="valid_inventory_condition",
            ),
        ]

    def __str__(self):
        return self.nombre_personalizado or self.pieza_catalogo.nombre


class PiezaFoto(models.Model):
    pieza_inventario = models.ForeignKey(PiezaInventario, on_delete=models.CASCADE)
    url = models.URLField(blank=True)
    archivo = models.FileField(
        upload_to="pieces/",
        validators=[validate_image_file],
        blank=True,
    )

    def __str__(self):
        return self.url or self.archivo.name


class Favorito(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pieza_inventario = models.ForeignKey(
        PiezaInventario,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="favoritos",
    )
    coleccion_maestra = models.ForeignKey(
        ColeccionMaestra,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="favoritos",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(
                        pieza_inventario__isnull=False,
                        coleccion_maestra__isnull=True,
                    )
                    | models.Q(
                        pieza_inventario__isnull=True,
                        coleccion_maestra__isnull=False,
                    )
                ),
                name="favorite_exactly_one_target",
            ),
            models.UniqueConstraint(
                fields=["user", "pieza_inventario"],
                name="unique_user_piece_favorite",
            ),
            models.UniqueConstraint(
                fields=["user", "coleccion_maestra"],
                name="unique_user_master_collection_favorite",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.pieza_inventario or self.coleccion_maestra}"
