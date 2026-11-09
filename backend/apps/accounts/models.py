from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from config.validators import validate_image_file


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    biografia = models.CharField(max_length=500, blank=True, default="")
    ubicacion = models.CharField(max_length=120, blank=True)
    reputacion = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    perfil_publico = models.BooleanField(default=True)
    avatar = models.FileField(
        upload_to="profiles/avatars/",
        validators=[validate_image_file],
        blank=True,
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class MetodoPago(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plataforma = models.CharField(max_length=80)
    alias_pago = models.CharField(max_length=120, blank=True)
    correo_pago = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.plataforma} - {self.user.username}"


class Resena(models.Model):
    emisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resenas_emitidas"
    )
    receptor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resenas_recibidas"
    )
    puntuacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["emisor", "receptor"],
                name="unique_review_per_user_pair",
            ),
            models.CheckConstraint(
                check=models.Q(puntuacion__gte=1, puntuacion__lte=5),
                name="review_score_between_1_and_5",
            ),
            models.CheckConstraint(
                check=~models.Q(emisor=models.F("receptor")),
                name="review_users_must_differ",
            ),
        ]

    def __str__(self):
        return f"{self.emisor} -> {self.receptor}: {self.puntuacion}"
