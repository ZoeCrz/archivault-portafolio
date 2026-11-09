from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Profile, Resena


class JwtAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="coleccionista",
            password="test-password",
            email="test@example.com",
        )

    def test_login_emite_access_y_refresh(self):
        response = self.client.post(
            "/api/v1/accounts/login/",
            {"username": "coleccionista", "password": "test-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user_id"], self.user.id)

    def test_endpoint_privado_rechaza_peticion_anonima(self):
        response = self.client.get("/api/v1/catalog/colecciones/")

        self.assertEqual(response.status_code, 401)

    def test_access_permite_consumir_endpoint_privado(self):
        login = self.client.post(
            "/api/v1/accounts/login/",
            {"username": "coleccionista", "password": "test-password"},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = self.client.get("/api/v1/catalog/colecciones/")

        self.assertEqual(response.status_code, 200)

    def test_refresh_emite_un_nuevo_access(self):
        login = self.client.post(
            "/api/v1/accounts/login/",
            {"username": "coleccionista", "password": "test-password"},
        )

        response = self.client.post(
            "/api/v1/accounts/token/refresh/",
            {"refresh": login.data["refresh"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_registro_permanece_publico(self):
        response = self.client.post(
            "/api/v1/accounts/users/",
            {
                "username": "nuevo_usuario",
                "email": "nuevo@example.com",
                "password": "secure-password",
            },
        )

        self.assertEqual(response.status_code, 201)

    def test_graphql_rechaza_consulta_anonima(self):
        response = self.client.post(
            "/graphql/",
            {"query": "{ usuarios { id } }"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_graphql_guarda_perfil_del_usuario_autenticado(self):
        login = self.client.post(
            "/api/v1/accounts/login/",
            {"username": "coleccionista", "password": "test-password"},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = self.client.post(
            "/graphql/",
            {
                "query": """
                    mutation {
                      saveProfile(input: {ubicacion: "CDMX"}) {
                        profile { id ubicacion }
                      }
                    }
                """
            },
            format="json",
        )

        self.assertNotIn("errors", response.json())
        self.assertEqual(response.json()["data"]["saveProfile"]["profile"]["ubicacion"], "CDMX")


class ReviewValidationApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.author = user_model.objects.create_user(username="author", password="password")
        self.recipient = user_model.objects.create_user(username="recipient", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.author)

    def test_rechaza_puntuacion_fuera_del_rango(self):
        response = self.client.post(
            "/api/v1/accounts/resenas/",
            {"receptor": self.recipient.id, "puntuacion": 6},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("puntuacion", response.data["error"]["fields"])

    def test_rechaza_autoresena_y_resena_duplicada(self):
        self_response = self.client.post(
            "/api/v1/accounts/resenas/",
            {"receptor": self.author.id, "puntuacion": 5},
        )
        Resena.objects.create(emisor=self.author, receptor=self.recipient, puntuacion=4)
        duplicate_response = self.client.post(
            "/api/v1/accounts/resenas/",
            {"receptor": self.recipient.id, "puntuacion": 5},
        )

        self.assertEqual(self_response.status_code, 400)
        self.assertEqual(duplicate_response.status_code, 400)


class ProfileDeepLinkApiTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.user = users.objects.create_user(username="profile-viewer", password="password")
        self.other = users.objects.create_user(username="profile-other", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.own_profile = Profile.objects.update_or_create(user=self.user, defaults={"perfil_publico": False})[0]
        self.other_profile = Profile.objects.update_or_create(user=self.other, defaults={"perfil_publico": True})[0]

    def test_perfil_propio_y_publico_tienen_detalle_estable(self):
        self.assertEqual(self.client.get(f"/api/v1/accounts/profiles/{self.own_profile.id}/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/accounts/profiles/{self.other_profile.id}/").status_code, 200)

    def test_perfil_privado_ajeno_es_indistinguible_de_inexistente(self):
        self.other_profile.perfil_publico = False
        self.other_profile.save(update_fields=["perfil_publico"])

        private_response = self.client.get(f"/api/v1/accounts/profiles/{self.other_profile.id}/")
        missing_response = self.client.get("/api/v1/accounts/profiles/999999/")

        self.assertEqual(private_response.status_code, 404)
        self.assertEqual(missing_response.status_code, 404)


class ProfileCreationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_registro_crea_el_perfil_del_usuario(self):
        response = self.client.post(
            "/api/v1/accounts/users/",
            {"username": "nueva-coleccionista", "email": "nueva@example.com", "password": "test-password"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Profile.objects.filter(user_id=response.data["id"]).exists())

    def test_el_perfil_propio_aparece_en_el_listado(self):
        user = get_user_model().objects.create_user(username="con-perfil", password="password")
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/v1/accounts/profiles/")

        self.assertEqual(response.status_code, 200)
        results = response.data if isinstance(response.data, list) else response.data["results"]
        self.assertIn(user.id, [item["user"] for item in results])
