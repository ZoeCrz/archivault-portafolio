from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.community.models import Post
from config.exceptions import api_exception_handler


class ExplodingView(APIView):
    def get(self, request):
        raise RuntimeError("internal database hostname must never be public")


class PublicErrorContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="error-owner", password="password"
        )
        self.other = get_user_model().objects.create_user(
            username="error-other", password="password"
        )

    def assert_contract(self, response, status_code, code):
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.data["error"]["code"], code)
        self.assertTrue(response.data["error"]["message"])
        self.assertTrue(response.data["error"]["request_id"])
        self.assertEqual(
            response["X-Request-ID"], response.data["error"]["request_id"]
        )

    def test_validation_error_includes_fields(self):
        response = self.client.post(
            "/api/v1/accounts/users/", {"username": ""}, format="json"
        )

        self.assert_contract(response, 400, "validation_error")
        self.assertIn("username", response.data["error"]["fields"])
        self.assertIn("password", response.data["error"]["fields"])

    def test_invalid_login_and_missing_authentication_are_distinct(self):
        invalid = self.client.post(
            "/api/v1/accounts/login/",
            {"username": "error-owner", "password": "wrong"},
        )
        missing = self.client.get("/api/v1/catalog/colecciones/")

        self.assert_contract(invalid, 401, "invalid_credentials")
        self.assert_contract(missing, 401, "authentication_required")

    def test_permission_denied_uses_public_contract(self):
        post = Post.objects.create(user=self.other, contenido="Privado")
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(f"/api/v1/community/posts/{post.id}/")

        self.assert_contract(response, 403, "permission_denied")

    def test_unexpected_exception_is_safe_json(self):
        request = APIRequestFactory().get("/api/test/unexpected/")
        force_authenticate(request, user=self.user)

        response = ExplodingView.as_view()(request)
        response.render()

        self.assert_contract(response, 500, "internal_error")
        body = response.rendered_content.decode()
        self.assertNotIn("RuntimeError", body)
        self.assertNotIn("database hostname", body)

    def test_integrity_error_is_a_conflict(self):
        request = APIRequestFactory().post("/api/test/conflict/")
        force_authenticate(request, user=self.user)

        response = api_exception_handler(
            IntegrityError("duplicate sensitive constraint"),
            {"request": request, "view": None},
        )

        self.assert_contract(response, 409, "conflict")
        self.assertNotIn("constraint", str(response.data).lower())

    def test_graphql_validation_uses_extensions(self):
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.post(
            "/graphql/",
            {
                "query": f"""
                    mutation {{
                      createResena(input: {{
                        receptorId: "{self.user.id}", puntuacion: 5
                      }}) {{ resena {{ id }} }}
                    }}
                """
            },
            format="json",
        )

        error = response.json()["errors"][0]
        self.assertEqual(error["extensions"]["code"], "VALIDATION_ERROR")
        self.assertIn("non_field_errors", error["extensions"]["fields"])
        self.assertTrue(error["extensions"]["request_id"])
        self.assertFalse(error["message"].startswith("{"))
