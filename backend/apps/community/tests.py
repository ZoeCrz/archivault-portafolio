from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Chat, Mensaje, Post
from apps.webhooks.models import Notificacion


class CommunityOwnershipApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="user", password="password")
        self.other = user_model.objects.create_user(username="other", password="password")
        self.third = user_model.objects.create_user(username="third", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_autor_del_post_proviene_del_token(self):
        response = self.client.post(
            "/api/v1/community/posts/",
            {"user": self.other.id, "contenido": "Nuevo hallazgo"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"], self.user.id)

    def test_no_permite_modificar_post_ajeno(self):
        post = Post.objects.create(user=self.other, contenido="Original")

        response = self.client.patch(
            f"/api/v1/community/posts/{post.id}/",
            {"contenido": "Alterado"},
        )

        self.assertEqual(response.status_code, 403)
        post.refresh_from_db()
        self.assertEqual(post.contenido, "Original")

    def test_listado_de_chats_solo_incluye_al_usuario(self):
        own_chat = Chat.objects.create()
        own_chat.usuarios.add(self.user, self.other)
        foreign_chat = Chat.objects.create()
        foreign_chat.usuarios.add(self.other, self.third)

        response = self.client.get("/api/v1/community/chats/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [own_chat.id])

    def test_detalle_de_chat_aplica_pertenencia(self):
        own_chat = Chat.objects.create()
        own_chat.usuarios.add(self.user, self.other)
        foreign_chat = Chat.objects.create()
        foreign_chat.usuarios.add(self.other, self.third)

        self.assertEqual(self.client.get(f"/api/v1/community/chats/{own_chat.id}/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/community/chats/{foreign_chat.id}/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/community/chats/999999/").status_code, 404)

    def test_detalle_de_post_admite_apertura_directa(self):
        post = Post.objects.create(user=self.other, contenido="Enlace estable")

        self.assertEqual(self.client.get(f"/api/v1/community/posts/{post.id}/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/community/posts/999999/").status_code, 404)

    def test_participante_no_puede_editar_mensaje_ajeno(self):
        chat = Chat.objects.create()
        chat.usuarios.add(self.user, self.other)
        message = Mensaje.objects.create(chat=chat, user=self.other, contenido="Original")

        response = self.client.patch(
            f"/api/v1/community/mensajes/{message.id}/",
            {"contenido": "Alterado"},
        )

        self.assertEqual(response.status_code, 403)

    def test_graphql_crea_post_con_autor_del_token(self):
        access = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.post(
            "/graphql/",
            {"query": 'mutation { createPost(contenido: "Hallazgo") { post { id } } }'},
            format="json",
        )

        self.assertNotIn("errors", response.json())
        post_id = response.json()["data"]["createPost"]["post"]["id"]
        self.assertTrue(Post.objects.filter(id=post_id, user=self.user).exists())

    def test_comentario_genera_notificacion_persistente(self):
        post = Post.objects.create(user=self.other, contenido="Hallazgo")

        response = self.client.post(
            "/api/v1/community/comentarios/",
            {"post": post.id, "contenido": "Gran pieza"},
        )

        self.assertEqual(response.status_code, 201)
        notification = Notificacion.objects.get(user=self.other)
        self.assertEqual(notification.tipo, "comentario")
        self.assertFalse(notification.leido)

    def test_no_permite_reaccionar_dos_veces_al_mismo_post(self):
        post = Post.objects.create(user=self.other, contenido="Hallazgo")
        first = self.client.post("/api/v1/community/likes/", {"post": post.id})
        duplicate = self.client.post("/api/v1/community/likes/", {"post": post.id})

        self.assertEqual(first.status_code, 201)
        self.assertEqual(duplicate.status_code, 400)

    def test_mensaje_notifica_a_los_otros_participantes(self):
        chat = Chat.objects.create()
        chat.usuarios.add(self.user, self.other, self.third)

        response = self.client.post(
            "/api/v1/community/mensajes/",
            {"chat": chat.id, "contenido": "Hola"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notificacion.objects.filter(tipo="mensaje").count(), 2)
        self.assertFalse(Notificacion.objects.filter(user=self.user).exists())

    def test_polling_incremental_devuelve_solo_mensajes_nuevos_y_ordenados(self):
        chat = Chat.objects.create()
        chat.usuarios.add(self.user, self.other)
        first = Mensaje.objects.create(chat=chat, user=self.other, contenido="Primero")
        second = Mensaje.objects.create(chat=chat, user=self.user, contenido="Segundo")
        third = Mensaje.objects.create(chat=chat, user=self.other, contenido="Tercero")

        response = self.client.get(
            f"/api/v1/community/mensajes/?chat={chat.id}&after={first.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [message["id"] for message in response.data],
            [second.id, third.id],
        )

    def test_polling_rechaza_cursor_invalido(self):
        chat = Chat.objects.create()
        chat.usuarios.add(self.user, self.other)

        response = self.client.get(
            f"/api/v1/community/mensajes/?chat={chat.id}&after=invalid"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("after", response.data["error"]["fields"])
