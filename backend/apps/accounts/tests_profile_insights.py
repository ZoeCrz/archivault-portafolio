from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import ColeccionMaestra, ColeccionUsuario, PiezaCatalogo, PiezaInventario
from apps.community.models import Post, PostLike
from apps.marketplace.models import Oferta, PublicacionMarket
from .models import Profile, Resena


class ExtendedProfileTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner", email="private@example.com", password="password")
        self.viewer = User.objects.create_user(username="viewer", password="password")
        self.private_user = User.objects.create_user(username="private", password="password")
        self.profile = Profile.objects.update_or_create(user=self.owner, defaults={"perfil_publico": True, "ubicacion": "Madrid"})[0]
        self.private_profile = Profile.objects.update_or_create(user=self.private_user, defaults={"perfil_publico": False})[0]
        self.viewer_profile = Profile.objects.get(user=self.viewer)
        self.master = ColeccionMaestra.objects.create(nombre="Visible", categoria="General", propietario=self.owner)
        self.collection = ColeccionUsuario.objects.create(user=self.owner, coleccion=self.master, progreso=50)
        catalog = PiezaCatalogo.objects.create(coleccion=self.master, numero_item="1", nombre="Pieza", sku_base="PROFILE")
        self.public_piece = self.piece(catalog, "PUBLICA", "PROFILE-PUB")
        self.private_piece = self.piece(catalog, "PRIVADA", "PROFILE-PRIVATE")
        self.post = Post.objects.create(user=self.owner, contenido="Post del perfil")
        PostLike.objects.create(post=self.post, user=self.viewer)
        PostLike.objects.create(post=self.post, user=self.owner)
        other_post = Post.objects.create(user=self.viewer, contenido="Post externo")
        PostLike.objects.create(post=other_post, user=self.owner)
        Resena.objects.create(emisor=self.viewer, receptor=self.owner, puntuacion=5, comentario="Excelente")
        self.publication = PublicacionMarket.objects.create(vendedor=self.owner, pieza_inventario=self.public_piece, precio=100, descripcion="Venta", condicion="NUEVA", estado="VENDIDA")
        Oferta.objects.create(publicacion=self.publication, comprador=self.viewer, monto=90, estado="COMPLETADA")
        self.client = APIClient()

    def piece(self, catalog, visibility, sku):
        return PiezaInventario.objects.create(user=self.owner, coleccion_usuario=self.collection, pieza_catalogo=catalog, sku=sku, estado_adquisicion="ADQUIRIDA", visibilidad=visibility, condicion="NUEVA")

    def get_summary(self, user, profile=None):
        self.client.force_authenticate(user)
        return self.client.get(f"/api/v1/accounts/profiles/{(profile or self.profile).id}/resumen/")

    def test_propietario_ve_metricas_separadas_y_datos_privados_permitidos(self):
        response = self.get_summary(self.owner)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_owner"])
        self.assertEqual(response.data["estadisticas"]["piezas_registradas"], 2)
        self.assertEqual(response.data["estadisticas"]["likes_realizados"], 2)
        self.assertEqual(response.data["estadisticas"]["likes_recibidos"], 1)
        self.assertEqual(response.data["estadisticas"]["ventas_completadas"], 1)
        self.assertEqual(response.data["estadisticas"]["promedio_resenas"], 5)

    def test_publico_ajeno_no_recibe_inventario_privado_ni_metricas_privadas(self):
        response = self.get_summary(self.viewer)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["is_owner"])
        self.assertEqual(response.data["estadisticas"]["piezas_publicas"], 1)
        self.assertNotIn("likes_realizados", response.data["estadisticas"])
        self.assertNotIn("realizados", response.data["likes"])
        self.assertNotIn("hechas", response.data["resenas"])
        self.assertNotIn("email", str(response.data).lower())
        self.assertNotIn("comprador", str(response.data).lower())

    def test_privado_ajeno_e_inexistente_son_indistinguibles(self):
        private = self.get_summary(self.viewer, self.private_profile)
        missing = self.client.get("/api/v1/accounts/profiles/999999/resumen/")
        self.assertEqual(private.status_code, 404)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(private.data["error"]["code"], missing.data["error"]["code"])

    def test_edita_biografia_con_trim_y_limite(self):
        self.client.force_authenticate(self.owner)
        ok = self.client.patch(f"/api/v1/accounts/profiles/{self.profile.id}/", {"biografia": "  Coleccionista  "})
        invalid = self.client.patch(f"/api/v1/accounts/profiles/{self.profile.id}/", {"biografia": "x" * 501})
        self.assertEqual(ok.data["biografia"], "Coleccionista")
        self.assertEqual(invalid.status_code, 400)

    def test_actividad_aplica_permisos_lista_blanca_y_paginacion(self):
        self.client.force_authenticate(self.owner)
        own = self.client.get(f"/api/v1/accounts/profiles/{self.profile.id}/actividad/?tipo=likes_realizados&page_size=1")
        invalid = self.client.get(f"/api/v1/accounts/profiles/{self.profile.id}/actividad/?tipo=desconocido")
        self.assertEqual(own.status_code, 200)
        self.assertEqual(len(own.data["results"]), 1)
        self.assertIsNotNone(own.data["next"])
        self.assertEqual(invalid.status_code, 400)
        self.client.force_authenticate(self.viewer)
        denied = self.client.get(f"/api/v1/accounts/profiles/{self.profile.id}/actividad/?tipo=likes_realizados")
        received = self.client.get(f"/api/v1/accounts/profiles/{self.profile.id}/actividad/?tipo=likes_recibidos")
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(received.status_code, 200)
        self.assertEqual(received.data["count"], 1)

    def test_resenas_rest_no_expone_resenas_privadas_ajenas(self):
        hidden_target = get_user_model().objects.create_user(username="hidden-target")
        Profile.objects.update_or_create(user=hidden_target, defaults={"perfil_publico": False})
        Resena.objects.create(emisor=self.private_user, receptor=hidden_target, puntuacion=2)
        self.client.force_authenticate(self.viewer)
        response = self.client.get("/api/v1/accounts/resenas/")
        self.assertEqual([item["receptor"] for item in response.data], [self.owner.id])

    def test_graphql_reutiliza_contrato_y_no_expone_email(self):
        token = RefreshToken.for_user(self.viewer).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post("/graphql/", {"query": f'{{ perfilResumen(profileId: "{self.profile.id}") }}'}, format="json")
        self.assertNotIn("errors", response.json())
        summary = response.json()["data"]["perfilResumen"]
        self.assertEqual(summary["estadisticas"]["likes_recibidos"], 1)
        self.assertNotIn("email", str(summary).lower())

    def test_actividad_graphql_es_equivalente_a_rest(self):
        self.client.force_authenticate(self.viewer)
        rest = self.client.get(
            f"/api/v1/accounts/profiles/{self.profile.id}/actividad/?tipo=likes_recibidos"
        )
        self.client.force_authenticate(user=None)
        token = RefreshToken.for_user(self.viewer).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        graphql = self.client.post(
            "/graphql/",
            {
                "query": (
                    "{ perfilActividad("
                    f'profileId: "{self.profile.id}", tipo: "likes_recibidos"'
                    ") }"
                )
            },
            format="json",
        ).json()["data"]["perfilActividad"]
        self.assertEqual(graphql["count"], rest.data["count"])
        self.assertEqual(graphql["results"], rest.data["results"])

    def test_queries_no_crecen_con_cinco_colecciones(self):
        self.client.force_authenticate(self.owner)
        with CaptureQueriesContext(connection) as first:
            self.client.get(f"/api/v1/accounts/profiles/{self.profile.id}/resumen/")
        for index in range(4):
            master = ColeccionMaestra.objects.create(nombre=f"C{index}", categoria="G", propietario=self.owner)
            ColeccionUsuario.objects.create(user=self.owner, coleccion=master)
        with CaptureQueriesContext(connection) as five:
            self.client.get(f"/api/v1/accounts/profiles/{self.profile.id}/resumen/")
        self.assertLessEqual(len(five), 13)
        self.assertLessEqual(len(five), len(first) + 1)

    def test_conteo_y_queries_publicas_no_dependen_del_preview(self):
        self.client.force_authenticate(self.viewer)
        with CaptureQueriesContext(connection) as one:
            self.client.get(f"/api/v1/accounts/profiles/{self.profile.id}/resumen/")
        for index in range(5):
            master = ColeccionMaestra.objects.create(nombre=f"Pública {index}", categoria="G", propietario=self.owner)
            collection = ColeccionUsuario.objects.create(user=self.owner, coleccion=master)
            catalog = PiezaCatalogo.objects.create(coleccion=master, numero_item=str(index), nombre=f"P{index}", sku_base=f"PUB-{index}")
            PiezaInventario.objects.create(
                user=self.owner,
                coleccion_usuario=collection,
                pieza_catalogo=catalog,
                sku=f"PUBLIC-{index}",
                visibilidad="PUBLICA",
                estado_adquisicion="ADQUIRIDA",
                condicion="NUEVA",
            )
        with CaptureQueriesContext(connection) as six:
            response = self.client.get(f"/api/v1/accounts/profiles/{self.profile.id}/resumen/")
        self.assertEqual(response.data["estadisticas"]["colecciones"], 6)
        self.assertEqual(len(response.data["colecciones"]["results"]), 5)
        self.assertLessEqual(len(six), 10)
        self.assertLessEqual(len(six), len(one) + 1)
