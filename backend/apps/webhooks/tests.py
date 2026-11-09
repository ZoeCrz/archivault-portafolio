import hashlib
import hmac
import json
import time

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.catalog.models import (
    ColeccionMaestra,
    ColeccionUsuario,
    PiezaCatalogo,
    PiezaInventario,
)
from apps.marketplace.models import Oferta, PublicacionMarket
from .models import Notificacion, WebhookEvent


@override_settings(WEBHOOK_SECRET="test-webhook-secret", WEBHOOK_TOLERANCE_SECONDS=300)
class SignedWebhookTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(username="seller", password="password")
        self.buyer = user_model.objects.create_user(username="buyer", password="password")
        master = ColeccionMaestra.objects.create(
            nombre="Webhook", categoria="General", propietario=self.seller
        )
        participation = ColeccionUsuario.objects.create(user=self.seller, coleccion=master)
        catalog_piece = PiezaCatalogo.objects.create(
            coleccion=master,
            numero_item="1",
            nombre="Pieza webhook",
            sku_base="WEBHOOK-BASE",
        )
        self.piece = PiezaInventario.objects.create(
            user=self.seller,
            coleccion_usuario=participation,
            pieza_catalogo=catalog_piece,
            sku="WEBHOOK-SKU",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PUBLICA",
            condicion="NUEVA",
        )
        publication = PublicacionMarket.objects.create(
            vendedor=self.seller,
            pieza_inventario=self.piece,
            precio="100.00",
            estado="RESERVADA",
        )
        self.offer = Oferta.objects.create(
            publicacion=publication,
            comprador=self.buyer,
            monto="100.00",
            estado="ACEPTADA",
        )
        self.client = APIClient()

    def signed_request(self, delivery="delivery-1", timestamp=None, signature=None):
        timestamp = str(timestamp or int(time.time()))
        body = json.dumps(
            {"evento": "pago_exitoso", "datos": {"oferta_id": self.offer.id}},
            separators=(",", ":"),
        ).encode()
        if signature is None:
            signature = hmac.new(
                b"test-webhook-secret",
                timestamp.encode() + b"." + body,
                hashlib.sha256,
            ).hexdigest()
        return self.client.post(
            "/api/v1/webhooks/receive/",
            data=body,
            content_type="application/json",
            HTTP_X_ARCHIVAULT_TIMESTAMP=timestamp,
            HTTP_X_ARCHIVAULT_SIGNATURE=f"sha256={signature}",
            HTTP_X_ARCHIVAULT_DELIVERY=delivery,
        )

    def test_rechaza_webhook_sin_firma(self):
        response = self.client.post(
            "/api/v1/webhooks/receive/",
            {"evento": "pago_exitoso", "datos": {"oferta_id": self.offer.id}},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_rechaza_firma_invalida(self):
        response = self.signed_request(signature="0" * 64)

        self.assertEqual(response.status_code, 401)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.estado, "ACEPTADA")

    def test_rechaza_timestamp_vencido(self):
        response = self.signed_request(timestamp=int(time.time()) - 301)

        self.assertEqual(response.status_code, 401)

    def test_firma_valida_completa_venta(self):
        response = self.signed_request()

        self.assertEqual(response.status_code, 200)
        self.offer.refresh_from_db()
        self.piece.refresh_from_db()
        self.assertEqual(self.offer.estado, "COMPLETADA")
        self.assertEqual(self.piece.user, self.buyer)
        self.assertTrue(WebhookEvent.objects.get(delivery_id="delivery-1").procesado)
        self.assertEqual(Notificacion.objects.filter(user=self.buyer).count(), 1)

    def test_entrega_duplicada_no_se_procesa_dos_veces(self):
        first = self.signed_request()
        second = self.signed_request()

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()["duplicado"])
        self.assertEqual(Notificacion.objects.filter(user=self.buyer).count(), 1)


class WebhookPublicErrorTests(TestCase):
    @override_settings(WEBHOOK_SECRET="")
    def test_configuracion_interna_no_se_expone(self):
        response = APIClient().post(
            "/api/v1/webhooks/receive/",
            {"evento": "pago_exitoso", "datos": {"oferta_id": 1}},
            format="json",
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["error"]["code"], "internal_error")
        self.assertNotIn("secreto", str(response.data).lower())

class PersistentNotificationApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="notified", password="password")
        self.other = user_model.objects.create_user(username="other", password="password")
        self.own_notification = Notificacion.objects.create(
            user=self.user,
            tipo="general",
            mensaje="Notificación propia",
        )
        Notificacion.objects.create(
            user=self.other,
            tipo="general",
            mensaje="Notificación ajena",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_listado_solo_devuelve_notificaciones_propias(self):
        response = self.client.get("/api/v1/webhooks/notificaciones/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [self.own_notification.id])

    def test_marcado_de_lectura_es_persistente(self):
        response = self.client.post(
            "/api/v1/webhooks/notificaciones/marcar-leidas/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["actualizadas"], 1)
        self.own_notification.refresh_from_db()
        self.assertTrue(self.own_notification.leido)

    def test_no_permite_marcar_notificacion_ajena(self):
        foreign = Notificacion.objects.get(user=self.other)

        response = self.client.post(
            f"/api/v1/webhooks/notificaciones/{foreign.id}/marcar-leida/"
        )

        self.assertEqual(response.status_code, 404)
