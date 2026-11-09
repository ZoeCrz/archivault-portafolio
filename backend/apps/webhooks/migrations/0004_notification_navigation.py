from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webhooks", "0003_alter_notificacion_tipo"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificacion",
            name="evento",
            field=models.CharField(
                choices=[
                    ("POST_LIKE", "Reacción a publicación"),
                    ("POST_COMMENT", "Comentario en publicación"),
                    ("CHAT_MESSAGE", "Mensaje de chat"),
                    ("OFFER_RECEIVED", "Oferta recibida"),
                    ("OFFER_ACCEPTED", "Oferta aceptada"),
                    ("OFFER_REJECTED", "Oferta rechazada"),
                    ("SALE_COMPLETED_BUYER", "Compra completada"),
                    ("SALE_COMPLETED_SELLER", "Venta completada"),
                    ("GENERAL", "General"),
                ],
                default="GENERAL",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="notificacion",
            name="destino_tipo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("COMMUNITY_POST", "Publicación de comunidad"),
                    ("CHAT", "Chat"),
                    ("MARKETPLACE_PUBLICATION", "Publicación de marketplace"),
                ],
                max_length=32,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="notificacion",
            name="destino_id",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="notificacion",
            name="metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddConstraint(
            model_name="notificacion",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(destino_tipo__isnull=True, destino_id__isnull=True)
                    | models.Q(destino_tipo__isnull=False, destino_id__isnull=False)
                ),
                name="notification_destination_complete",
            ),
        ),
    ]
