from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import (
    ColeccionMaestra,
    ColeccionUsuario,
    PiezaCatalogo,
    PiezaInventario,
)
from apps.community.models import Chat, Post
from apps.marketplace.models import Oferta, PublicacionMarket
from apps.marketplace.services import accept_offer, complete_offer, reject_offer
from .models import Notificacion
from .notifications import notify


class NotificationContractTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="owner", password="password")
        self.actor = User.objects.create_user(username="actor", password="password")
        self.other = User.objects.create_user(username="other", password="password")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_llamada_historica_y_serializer_sin_destino(self):
        notification = notify(self.user, "general", "Mensaje histórico")
        response = self.client.get("/api/v1/webhooks/notificaciones/")

        self.assertEqual(notification.evento, "GENERAL")
        self.assertEqual(notification.metadata, {})
        self.assertIsNone(response.data[0]["destino"])
        self.assertNotIn("metadata", response.data[0])

    def test_helper_valida_destino_y_metadata(self):
        with self.assertRaises(ValueError):
            notify(self.user, "general", "Inválida", destino_tipo="CHAT")
        with self.assertRaises(ValueError):
            notify(
                self.user,
                "general",
                "Inválida",
                destino_tipo="EXTERNAL_URL",
                destino_id=1,
            )
        with self.assertRaises(ValueError):
            notify(self.user, "general", "Inválida", metadata={"password": "secret"})

    def test_restriccion_impide_destino_incompleto(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Notificacion.objects.create(
                user=self.user,
                tipo="general",
                mensaje="Inválida",
                destino_tipo="CHAT",
            )

    def test_like_comentario_y_mensaje_guardan_destino_correcto(self):
        post = Post.objects.create(user=self.user, contenido="Hallazgo")
        self.client.force_authenticate(self.actor)
        self.client.post("/api/v1/community/likes/", {"post": post.id})
        self.client.post(
            "/api/v1/community/comentarios/",
            {"post": post.id, "contenido": "Interesante"},
        )
        chat = Chat.objects.create()
        chat.usuarios.add(self.user, self.actor)
        self.client.post(
            "/api/v1/community/mensajes/",
            {"chat": chat.id, "contenido": "Hola"},
        )

        like = Notificacion.objects.get(user=self.user, evento="POST_LIKE")
        comment = Notificacion.objects.get(user=self.user, evento="POST_COMMENT")
        message = Notificacion.objects.get(user=self.user, evento="CHAT_MESSAGE")
        self.assertEqual((like.destino_tipo, like.destino_id), ("COMMUNITY_POST", post.id))
        self.assertEqual((comment.destino_tipo, comment.destino_id), ("COMMUNITY_POST", post.id))
        self.assertEqual((message.destino_tipo, message.destino_id), ("CHAT", chat.id))
        self.assertEqual(message.mensaje, "Recibiste un nuevo mensaje de actor.")

    def test_borrar_recurso_no_borra_notificacion(self):
        post = Post.objects.create(user=self.user, contenido="Temporal")
        notification = notify(
            self.user,
            "comentario",
            "Comentario",
            evento="POST_COMMENT",
            destino_tipo="COMMUNITY_POST",
            destino_id=post.id,
        )
        post.delete()
        self.assertTrue(Notificacion.objects.filter(pk=notification.id).exists())

    def test_destino_serializado_no_amplia_autorizacion(self):
        foreign_chat = Chat.objects.create()
        foreign_chat.usuarios.add(self.actor, self.other)
        notify(
            self.user,
            "mensaje",
            "Chat ya no disponible",
            evento="CHAT_MESSAGE",
            destino_tipo="CHAT",
            destino_id=foreign_chat.id,
        )

        notifications = self.client.get("/api/v1/webhooks/notificaciones/")
        self.assertEqual(
            notifications.data[0]["destino"],
            {
                "tipo": "CHAT",
                "id": foreign_chat.id,
                "url": f"/app/chats/{foreign_chat.id}",
            },
        )
        self.assertEqual(
            self.client.get(f"/api/v1/community/chats/{foreign_chat.id}/").status_code,
            404,
        )


class MarketplaceNotificationEventTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.seller = User.objects.create_user(username="seller", password="password")
        self.buyer = User.objects.create_user(username="buyer", password="password")
        self.other_buyer = User.objects.create_user(username="other", password="password")
        self.master = ColeccionMaestra.objects.create(
            nombre="Colección humana", categoria="General", propietario=self.seller
        )
        self.user_collection = ColeccionUsuario.objects.create(
            user=self.seller, coleccion=self.master
        )
        catalog = PiezaCatalogo.objects.create(
            coleccion=self.master,
            numero_item="1",
            nombre="Nombre de catálogo",
            sku_base="NOTIF-BASE",
        )
        self.piece = PiezaInventario.objects.create(
            user=self.seller,
            coleccion_usuario=self.user_collection,
            pieza_catalogo=catalog,
            nombre_personalizado="Nombre personalizado",
            sku="NOTIF-SKU",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PUBLICA",
            condicion="NUEVA",
        )
        self.publication = PublicacionMarket.objects.create(
            vendedor=self.seller,
            pieza_inventario=self.piece,
            precio="100.00",
            descripcion="Publicación",
            condicion="NUEVA",
        )
        self.client = APIClient()

    def create_offer(self, buyer, amount="90.00"):
        self.client.force_authenticate(buyer)
        response = self.client.post(
            "/api/v1/marketplace/ofertas/",
            {"publicacion": self.publication.id, "monto": amount},
        )
        return Oferta.objects.get(pk=response.data["id"])

    def assert_market_destination(self, notification, event):
        self.assertEqual(notification.evento, event)
        self.assertEqual(notification.destino_tipo, "MARKETPLACE_PUBLICATION")
        self.assertEqual(notification.destino_id, self.publication.id)
        self.assertEqual(notification.metadata["resource_name"], "Nombre personalizado")
        self.assertNotIn("#", notification.mensaje)

    def test_nueva_oferta_usa_nombre_y_metadata_minima(self):
        offer = self.create_offer(self.buyer)
        notification = Notificacion.objects.get(user=self.seller, evento="OFFER_RECEIVED")
        self.assert_market_destination(notification, "OFFER_RECEIVED")
        self.assertIn("Nombre personalizado", notification.mensaje)
        self.assertEqual(notification.metadata["offer_id"], offer.id)
        self.assertNotIn("email", notification.metadata)

    def test_aceptada_y_rechazos_directo_y_automatico(self):
        accepted = self.create_offer(self.buyer)
        rejected_automatically = self.create_offer(self.other_buyer, "80.00")
        accept_offer(accepted.id, self.seller)
        accepted_notification = Notificacion.objects.get(
            user=self.buyer, evento="OFFER_ACCEPTED"
        )
        automatic_notification = Notificacion.objects.get(
            user=self.other_buyer, evento="OFFER_REJECTED"
        )
        self.assert_market_destination(accepted_notification, "OFFER_ACCEPTED")
        self.assert_market_destination(automatic_notification, "OFFER_REJECTED")
        self.assertIn("se aceptó otra propuesta", automatic_notification.mensaje)

        second_publication = PublicacionMarket.objects.create(
            vendedor=self.seller,
            coleccion_usuario=self.user_collection,
            precio="200.00",
            descripcion="Colección",
            condicion="USADA",
        )
        self.client.force_authenticate(self.buyer)
        response = self.client.post(
            "/api/v1/marketplace/ofertas/",
            {"publicacion": second_publication.id, "monto": "180.00"},
        )
        direct = Oferta.objects.get(pk=response.data["id"])
        reject_offer(direct.id, self.seller)
        direct_notification = Notificacion.objects.filter(
            user=self.buyer, evento="OFFER_REJECTED"
        ).latest("id")
        self.assertIn("Colección humana", direct_notification.mensaje)
        self.assertNotIn("#", direct_notification.mensaje)

    def test_compra_y_venta_completadas(self):
        offer = self.create_offer(self.buyer)
        accept_offer(offer.id, self.seller)
        complete_offer(offer.id, self.seller)

        buyer_notice = Notificacion.objects.get(
            user=self.buyer, evento="SALE_COMPLETED_BUYER"
        )
        seller_notice = Notificacion.objects.get(
            user=self.seller, evento="SALE_COMPLETED_SELLER"
        )
        self.assert_market_destination(buyer_notice, "SALE_COMPLETED_BUYER")
        self.assert_market_destination(seller_notice, "SALE_COMPLETED_SELLER")
        self.assertIn("La compra de Nombre personalizado", buyer_notice.mensaje)
        self.assertIn("La venta de Nombre personalizado", seller_notice.mensaje)

    def test_fallback_a_catalogo(self):
        self.piece.nombre_personalizado = "   "
        self.piece.save(update_fields=["nombre_personalizado"])
        self.create_offer(self.buyer)
        notification = Notificacion.objects.get(user=self.seller, evento="OFFER_RECEIVED")
        self.assertIn("Nombre de catálogo", notification.mensaje)
