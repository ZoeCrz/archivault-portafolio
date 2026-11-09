from config.test_images import PNG_BYTES
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from django.test import TestCase
from django.test.utils import override_settings
import tempfile

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ColeccionMaestra, ColeccionUsuario, PiezaCatalogo, PiezaInventario
from apps.marketplace.models import PublicacionMarket


class ColeccionModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="coleccionista",
            password="test-password",
        )
        self.coleccion = ColeccionMaestra.objects.create(
            nombre="Colección personal",
            categoria="General",
            tipo="personal",
            propietario=self.user,
        )

    def test_coleccion_persiste_tipo_y_propietario(self):
        self.assertEqual(self.coleccion.tipo, "personal")
        self.assertEqual(self.coleccion.propietario, self.user)

    def test_usuario_no_puede_participar_dos_veces_en_la_misma_coleccion(self):
        ColeccionUsuario.objects.create(user=self.user, coleccion=self.coleccion)

        with self.assertRaises(IntegrityError), transaction.atomic():
            ColeccionUsuario.objects.create(user=self.user, coleccion=self.coleccion)


class CollectionProgressTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="progress", password="password"
        )
        self.master = ColeccionMaestra.objects.create(
            nombre="Progreso", categoria="General", total_piezas=4, propietario=self.user
        )
        self.participation = ColeccionUsuario.objects.create(
            user=self.user, coleccion=self.master
        )
        self.catalog_pieces = [
            PiezaCatalogo.objects.create(
                coleccion=self.master,
                numero_item=str(index),
                nombre=f"Pieza {index}",
                sku_base=f"PROGRESS-{index}",
            )
            for index in range(1, 3)
        ]

    def create_inventory_piece(self, catalog_piece, sku):
        return PiezaInventario.objects.create(
            user=self.user,
            coleccion_usuario=self.participation,
            pieza_catalogo=catalog_piece,
            sku=sku,
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PRIVADA",
            condicion="NUEVA",
        )

    def test_recalcula_progreso_al_agregar_y_eliminar_piezas(self):
        first = self.create_inventory_piece(self.catalog_pieces[0], "OWNED-1")
        self.participation.refresh_from_db()
        self.assertEqual(self.participation.progreso, 25)

        self.create_inventory_piece(self.catalog_pieces[1], "OWNED-2")
        self.participation.refresh_from_db()
        self.assertEqual(self.participation.progreso, 50)

        first.delete()
        self.participation.refresh_from_db()
        self.assertEqual(self.participation.progreso, 25)

    def test_cuenta_piezas_catalogo_unicas_y_limita_el_porcentaje(self):
        self.create_inventory_piece(self.catalog_pieces[0], "COPY-1")
        self.create_inventory_piece(self.catalog_pieces[0], "COPY-2")
        self.participation.refresh_from_db()
        self.assertEqual(self.participation.progreso, 25)

        self.master.total_piezas = 1
        self.master.save(update_fields=["total_piezas"])
        self.participation.refresh_from_db()
        self.assertEqual(self.participation.progreso, 100)

    def test_api_no_permite_asignar_progreso_manualmente(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.patch(
            f"/api/v1/catalog/colecciones-usuario/{self.participation.id}/",
            {"progreso": "99.00"},
        )

        self.assertEqual(response.status_code, 200)
        self.participation.refresh_from_db()
        self.assertEqual(self.participation.progreso, 0)

    def test_rechaza_estados_de_inventario_desconocidos(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post(
            "/api/v1/catalog/inventario/",
            {
                "coleccion_usuario": self.participation.id,
                "pieza_catalogo": self.catalog_pieces[0].id,
                "sku": "INVALID-STATE",
                "estado_adquisicion": "INVENTADO",
                "visibilidad": "OCULTA",
                "condicion": "PERFECTA",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("estado_adquisicion", response.data["error"]["fields"])
        self.assertIn("visibilidad", response.data["error"]["fields"])
        self.assertIn("condicion", response.data["error"]["fields"])

    def test_no_permite_favorito_duplicado(self):
        piece = self.create_inventory_piece(self.catalog_pieces[0], "FAVORITE")
        client = APIClient()
        client.force_authenticate(user=self.user)

        first = client.post("/api/v1/catalog/favoritos/", {"pieza_inventario": piece.id})
        duplicate = client.post("/api/v1/catalog/favoritos/", {"pieza_inventario": piece.id})

        self.assertEqual(first.status_code, 201)
        self.assertEqual(duplicate.status_code, 409)


class CatalogOwnershipApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="owner", password="password")
        self.other = user_model.objects.create_user(username="other", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.owner_master = ColeccionMaestra.objects.create(
            nombre="Privada owner", categoria="General", propietario=self.owner
        )
        self.other_master = ColeccionMaestra.objects.create(
            nombre="Privada other", categoria="General", propietario=self.other
        )
        self.owner_collection = ColeccionUsuario.objects.create(
            user=self.owner, coleccion=self.owner_master
        )
        self.other_collection = ColeccionUsuario.objects.create(
            user=self.other, coleccion=self.other_master
        )
        self.other_catalog_piece = PiezaCatalogo.objects.create(
            coleccion=self.other_master,
            numero_item="1",
            nombre="Pieza ajena",
            sku_base="OTHER-BASE",
        )
        self.other_piece = PiezaInventario.objects.create(
            user=self.other,
            coleccion_usuario=self.other_collection,
            pieza_catalogo=self.other_catalog_piece,
            sku="OTHER-SKU",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PRIVADA",
            condicion="NUEVA",
        )

    def test_listados_privados_solo_incluyen_datos_propios(self):
        response = self.client.get("/api/v1/catalog/colecciones-usuario/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [self.owner_collection.id])

    def test_detalle_de_coleccion_usuario_ajena_no_revela_el_recurso(self):
        own_response = self.client.get(
            f"/api/v1/catalog/colecciones-usuario/{self.owner_collection.id}/"
        )
        foreign_response = self.client.get(
            f"/api/v1/catalog/colecciones-usuario/{self.other_collection.id}/"
        )

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(foreign_response.status_code, 404)

    def test_colecciones_personales_ajenas_no_son_visibles(self):
        response = self.client.get("/api/v1/catalog/colecciones/")

        ids = [item["id"] for item in response.data]
        self.assertIn(self.owner_master.id, ids)
        self.assertNotIn(self.other_master.id, ids)


    def test_no_permite_acceder_a_pieza_ajena(self):
        response = self.client.delete(f"/api/v1/catalog/inventario/{self.other_piece.id}/")

        self.assertEqual(response.status_code, 404)

    def test_no_permite_asignar_inventario_a_coleccion_ajena(self):
        response = self.client.post(
            "/api/v1/catalog/inventario/",
            {
                "user": self.other.id,
                "coleccion_usuario": self.other_collection.id,
                "pieza_catalogo": self.other_catalog_piece.id,
                "sku": "SPOOFED-SKU",
                "estado_adquisicion": "ADQUIRIDA",
                "visibilidad": "PRIVADA",
                "condicion": "NUEVA",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_identidad_de_participacion_proviene_del_token(self):
        global_master = ColeccionMaestra.objects.create(
            nombre="Global", categoria="General", tipo="global"
        )
        response = self.client.post(
            "/api/v1/catalog/colecciones-usuario/",
            {"user": self.other.id, "coleccion": global_master.id},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"], self.owner.id)

    def test_recurso_publicado_es_visible_pero_no_modificable(self):
        PublicacionMarket.objects.create(
            vendedor=self.other,
            pieza_inventario=self.other_piece,
            precio="100.00",
            estado="ACTIVA",
        )

        list_response = self.client.get("/api/v1/catalog/inventario/")
        delete_response = self.client.delete(
            f"/api/v1/catalog/inventario/{self.other_piece.id}/"
        )

        self.assertIn(self.other_piece.id, [item["id"] for item in list_response.data])
        self.assertEqual(delete_response.status_code, 403)

    def test_no_permite_participar_en_coleccion_personal_ajena(self):
        response = self.client.post(
            "/api/v1/catalog/colecciones-usuario/",
            {"coleccion": self.other_master.id},
        )

        self.assertEqual(response.status_code, 400)

    def test_graphql_oculta_coleccion_personal_ajena(self):
        access = RefreshToken.for_user(self.owner).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.post(
            "/graphql/",
            {"query": "{ coleccionesMaestras { id } }"},
            format="json",
        )

        ids = [int(item["id"]) for item in response.json()["data"]["coleccionesMaestras"]]
        self.assertIn(self.owner_master.id, ids)
        self.assertNotIn(self.other_master.id, ids)

    def test_graphql_crea_coleccion_con_propietario_autenticado(self):
        access = RefreshToken.for_user(self.owner).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.post(
            "/graphql/",
            {
                "query": """
                    mutation {
                      createColeccionMaestra(input: {
                        nombre: "GraphQL", categoria: "Arte", tipo: "personal"
                      }) { coleccion { id nombre } }
                    }
                """
            },
            format="json",
        )

        self.assertNotIn("errors", response.json())
        created_id = response.json()["data"]["createColeccionMaestra"]["coleccion"]["id"]
        self.assertTrue(
            ColeccionMaestra.objects.filter(id=created_id, propietario=self.owner).exists()
        )

    def test_graphql_rechaza_actualizar_coleccion_ajena(self):
        access = RefreshToken.for_user(self.owner).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.post(
            "/graphql/",
            {
                "query": f"""
                    mutation {{
                      updateColeccionMaestra(
                        id: "{self.other_master.id}",
                        input: {{nombre: "Alterada", categoria: "General"}}
                      ) {{ coleccion {{ id }} }}
                    }}
                """
            },
            format="json",
        )

        self.assertIn("errors", response.json())
        self.other_master.refresh_from_db()
        self.assertEqual(self.other_master.nombre, "Privada other")


class PersistentMediaApiTests(TestCase):
    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        self.user = get_user_model().objects.create_user(username="media", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        master = ColeccionMaestra.objects.create(
            nombre="Multimedia", categoria="General", propietario=self.user
        )
        collection = ColeccionUsuario.objects.create(user=self.user, coleccion=master)
        catalog_piece = PiezaCatalogo.objects.create(
            coleccion=master,
            numero_item="1",
            nombre="Pieza multimedia",
            sku_base="MEDIA-BASE",
        )
        self.piece = PiezaInventario.objects.create(
            user=self.user,
            coleccion_usuario=collection,
            pieza_catalogo=catalog_piece,
            sku="MEDIA-SKU",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PRIVADA",
            condicion="NUEVA",
        )

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_guarda_y_sirve_foto_de_pieza(self):
        image = SimpleUploadedFile("pieza.png", PNG_BYTES, content_type="image/png")

        response = self.client.post(
            "/api/v1/catalog/fotos/",
            {"pieza_inventario": self.piece.id, "archivo": image},
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("/media/pieces/", response.data["archivo"])
        stored_name = response.data["archivo"].split("/media/", 1)[1]
        self.assertTrue(default_storage.exists(stored_name))

    def test_rechaza_archivo_que_no_es_imagen(self):
        invalid_file = SimpleUploadedFile("archivo.txt", b"text", content_type="text/plain")

        response = self.client.post(
            "/api/v1/catalog/fotos/",
            {"pieza_inventario": self.piece.id, "archivo": invalid_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("archivo", response.data["error"]["fields"])
