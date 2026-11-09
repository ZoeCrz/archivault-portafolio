from django.conf import settings
from django.db import models
from apps.catalog.models import ColeccionUsuario, PiezaInventario


class PublicacionMarket(models.Model):
    CONDICIONES = [
        ("NUEVA", "Nueva"),
        ("USADA", "Usada"),
        ("DAÑADA", "Dañada"),
        ("NO_ESPECIFICADA", "No especificada"),
    ]
    ESTADOS = [
        ("ACTIVA", "Activa"),
        ("RESERVADA", "Reservada"),
        ("VENDIDA", "Vendida"),
        ("CANCELADA", "Cancelada"),
    ]

    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="publicaciones_market",
    )
    pieza_inventario = models.OneToOneField(
        PiezaInventario,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    coleccion_usuario = models.OneToOneField(
        ColeccionUsuario,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=500, blank=True, default="")
    condicion = models.CharField(
        max_length=20,
        choices=CONDICIONES,
        default="NO_ESPECIFICADA",
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default="ACTIVA")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(pieza_inventario__isnull=False, coleccion_usuario__isnull=True)
                    | models.Q(pieza_inventario__isnull=True, coleccion_usuario__isnull=False)
                ),
                name="market_publication_exactly_one_target",
            ),
            models.CheckConstraint(
                check=models.Q(estado__in=["ACTIVA", "RESERVADA", "VENDIDA", "CANCELADA"]),
                name="valid_market_publication_status",
            ),
            models.CheckConstraint(
                check=models.Q(
                    condicion__in=["NUEVA", "USADA", "DAÑADA", "NO_ESPECIFICADA"]
                ),
                name="valid_market_publication_condition",
            ),
        ]

    def __str__(self):
        objetivo = self.pieza_inventario or self.coleccion_usuario
        return f"{objetivo} - ${self.precio}"


class Oferta(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("ACEPTADA", "Aceptada"),
        ("RECHAZADA", "Rechazada"),
        ("COMPLETADA", "Completada"),
        ("CANCELADA", "Cancelada"),
    ]

    publicacion = models.ForeignKey(PublicacionMarket, on_delete=models.CASCADE)
    comprador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="PENDIENTE")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["publicacion", "comprador"],
                name="unique_offer_per_buyer_publication",
            ),
            models.CheckConstraint(
                check=models.Q(
                    estado__in=["PENDIENTE", "ACEPTADA", "RECHAZADA", "COMPLETADA", "CANCELADA"]
                ),
                name="valid_market_offer_status",
            ),
        ]

    def __str__(self):
        return f"{self.comprador.username} - {self.monto}"
