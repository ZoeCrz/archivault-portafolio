from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Profile
from apps.community.models import Comentario, Post, PostMedia
from config.media import resolve_media_url
from .models import (
    ColeccionMaestra,
    ColeccionUsuario,
    PiezaCatalogo,
    PiezaFoto,
    PiezaInventario,
)


class MediaUrlResolverTests(SimpleTestCase):
    @override_settings(ALLOWED_HOSTS=["api.example"])
    def test_resuelve_formatos_locales_y_conserva_url_externa(self):
        request = RequestFactory().get("/", secure=True, HTTP_HOST="api.example")

        self.assertEqual(
            resolve_media_url("/media/pieces/item.png", request),
            "https://api.example/media/pieces/item.png",
        )
        self.assertEqual(
            resolve_media_url("pieces/item.png", request),
            "https://api.example/media/pieces/item.png",
        )
        self.assertEqual(
            resolve_media_url("https://legacy.example/item.png", request),
            "https://legacy.example/item.png",
        )
        self.assertIsNone(resolve_media_url(""))
        self.assertIsNone(resolve_media_url(None))
        self.assertIsNone(resolve_media_url("javascript:alert(1)", request))

    @override_settings(
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
        USE_X_FORWARDED_HOST=True,
        ALLOWED_HOSTS=["public.example"],
    )
    def test_respeta_proxy_https_configurado(self):
        request = RequestFactory().get(
            "/",
            HTTP_HOST="internal",
            HTTP_X_FORWARDED_HOST="public.example",
            HTTP_X_FORWARDED_PROTO="https",
        )

        self.assertEqual(
            resolve_media_url("pieces/item.png", request),
            "https://public.example/media/pieces/item.png",
        )


@override_settings(ALLOWED_HOSTS=["api.example", "testserver"])
class MultimediaApiContractTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="media-contract",
            password="password",
        )
        self.profile = Profile.objects.update_or_create(
            user=self.user,
            defaults={"avatar": "profiles/avatars/avatar.png"},
        )[0]
        self.master = ColeccionMaestra.objects.create(
            nombre="Colección multimedia",
            categoria="Pruebas",
            propietario=self.user,
            imagen="collections/collection.png",
        )
        participation = ColeccionUsuario.objects.create(
            user=self.user,
            coleccion=self.master,
        )
        catalog_piece = PiezaCatalogo.objects.create(
            coleccion=self.master,
            numero_item="1",
            nombre="Pieza multimedia",
            sku_base="MEDIA-CONTRACT-BASE",
        )
        inventory_piece = PiezaInventario.objects.create(
            user=self.user,
            coleccion_usuario=participation,
            pieza_catalogo=catalog_piece,
            sku="MEDIA-CONTRACT",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PUBLICA",
            condicion="NUEVA",
        )
        self.photo = PiezaFoto.objects.create(
            pieza_inventario=inventory_piece,
            archivo="pieces/item.png",
            url="https://legacy.example/item.png",
        )
        post = Post.objects.create(user=self.user, contenido="Multimedia")
        self.post_media = PostMedia.objects.create(
            post=post,
            tipo="image/png",
            archivo="community/posts/post.png",
            url="https://legacy.example/post.png",
        )
        self.comment = Comentario.objects.create(
            post=post,
            user=self.user,
            contenido="Comentario",
            imagen="community/comments/comment.png",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_rest_devuelve_urls_multimedia_absolutas_y_fuentes_historicas(self):
        cases = [
            ("/api/v1/accounts/profiles/", self.profile.id, "avatar", "profiles/avatars/avatar.png"),
            ("/api/v1/catalog/colecciones/", self.master.id, "imagen", "collections/collection.png"),
            ("/api/v1/catalog/fotos/", self.photo.id, "archivo", "pieces/item.png"),
            ("/api/v1/community/media/", self.post_media.id, "archivo", "community/posts/post.png"),
            ("/api/v1/community/comentarios/", self.comment.id, "imagen", "community/comments/comment.png"),
        ]

        for endpoint, object_id, field, path in cases:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint, secure=True, HTTP_HOST="api.example")
                self.assertEqual(response.status_code, 200)
                item = next(row for row in response.data if row["id"] == object_id)
                self.assertEqual(item[field], f"https://api.example/media/{path}")

        photos = self.client.get(
            "/api/v1/catalog/fotos/", secure=True, HTTP_HOST="api.example"
        ).data
        photo = next(row for row in photos if row["id"] == self.photo.id)
        self.assertEqual(photo["url"], "https://legacy.example/item.png")

    def test_graphql_representa_multimedia_igual_que_rest(self):
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(
            "/graphql/",
            {
                "query": """
                    {
                      perfiles { id avatar }
                      coleccionesMaestras { id imagen }
                      piezasFoto { id archivo url }
                      postMedia { id archivo url }
                      comentarios { id imagen }
                    }
                """
            },
            format="json",
            secure=True,
            HTTP_HOST="api.example",
        )

        payload = response.json()
        self.assertNotIn("errors", payload)
        data = payload["data"]
        expected = [
            ("perfiles", self.profile.id, "avatar", "profiles/avatars/avatar.png"),
            ("coleccionesMaestras", self.master.id, "imagen", "collections/collection.png"),
            ("piezasFoto", self.photo.id, "archivo", "pieces/item.png"),
            ("postMedia", self.post_media.id, "archivo", "community/posts/post.png"),
            ("comentarios", self.comment.id, "imagen", "community/comments/comment.png"),
        ]
        for collection, object_id, field, path in expected:
            with self.subTest(collection=collection):
                item = next(row for row in data[collection] if row["id"] == str(object_id))
                self.assertEqual(item[field], f"https://api.example/media/{path}")

        photo = next(row for row in data["piezasFoto"] if row["id"] == str(self.photo.id))
        self.assertEqual(photo["url"], "https://legacy.example/item.png")
