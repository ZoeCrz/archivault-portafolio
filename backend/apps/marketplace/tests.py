from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import (
    ColeccionMaestra,
    ColeccionUsuario,
    PiezaCatalogo,
    PiezaInventario,
)
from .models import Oferta, PublicacionMarket
from apps.webhooks.models import Notificacion


class PublicacionMarketApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="vendedor",
            password="test-password",
        )
        self.client.force_authenticate(user=self.user)
        self.maestra = ColeccionMaestra.objects.create(
            nombre="Colección personal",
            categoria="General",
            tipo="personal",
            propietario=self.user,
        )
        self.coleccion_usuario = ColeccionUsuario.objects.create(
            user=self.user,
            coleccion=self.maestra,
        )
        catalogo = PiezaCatalogo.objects.create(
            coleccion=self.maestra,
            numero_item="1",
            nombre="Pieza de prueba",
            sku_base="BASE-TEST",
        )
        self.pieza = PiezaInventario.objects.create(
            user=self.user,
            coleccion_usuario=self.coleccion_usuario,
            pieza_catalogo=catalogo,
            sku="SKU-TEST",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PUBLICA",
            condicion="NUEVA",
        )

    def test_lista_ofertas_del_usuario_autenticado(self):
        response = self.client.get("/api/v1/marketplace/ofertas/")

        self.assertEqual(response.status_code, 200)

    def test_permite_publicar_una_pieza(self):
        response = self.client.post(
            "/api/v1/marketplace/publicaciones/",
            {
                "pieza_inventario": self.pieza.id,
                "precio": "100.00",
                "descripcion": "  Conservada en funda protectora.  ",
                "condicion": "USADA",
                "estado": "ACTIVA",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["pieza_inventario"], self.pieza.id)
        self.assertIsNone(response.data["coleccion_usuario"])
        self.assertEqual(response.data["descripcion"], "Conservada en funda protectora.")
        self.assertEqual(response.data["condicion"], "USADA")

    def test_infiere_condicion_actual_de_la_pieza(self):
        self.pieza.condicion = "DAÑADA"
        self.pieza.save(update_fields=["condicion"])

        response = self.client.post(
            "/api/v1/marketplace/publicaciones/",
            {
                "pieza_inventario": self.pieza.id,
                "precio": "100.00",
                "descripcion": "Presenta detalles visibles.",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["condicion"], "DAÑADA")

    def test_permite_publicar_una_coleccion_completa(self):
        response = self.client.post(
            "/api/v1/marketplace/publicaciones/",
            {
                "coleccion_usuario": self.coleccion_usuario.id,
                "precio": "500.00",
                "descripcion": "Colección completa y bien conservada.",
                "condicion": "USADA",
                "estado": "ACTIVA",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["coleccion_usuario"], self.coleccion_usuario.id)
        self.assertIsNone(response.data["pieza_inventario"])

    def test_coleccion_exige_condicion(self):
        response = self.client.post(
            "/api/v1/marketplace/publicaciones/",
            {
                "coleccion_usuario": self.coleccion_usuario.id,
                "precio": "500.00",
                "descripcion": "Colección completa.",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("condicion", response.data["error"]["fields"])

    def test_descripcion_es_obligatoria_y_no_acepta_solo_espacios(self):
        for description in ["", "   "]:
            with self.subTest(description=repr(description)):
                response = self.client.post(
                    "/api/v1/marketplace/publicaciones/",
                    {
                        "pieza_inventario": self.pieza.id,
                        "precio": "100.00",
                        "descripcion": description,
                        "condicion": "NUEVA",
                    },
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("descripcion", response.data["error"]["fields"])

    def test_rechaza_descripcion_superior_a_500_caracteres(self):
        response = self.client.post(
            "/api/v1/marketplace/publicaciones/",
            {
                "pieza_inventario": self.pieza.id,
                "precio": "100.00",
                "descripcion": "x" * 501,
                "condicion": "NUEVA",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("descripcion", response.data["error"]["fields"])

    def test_rechaza_condicion_desconocida_o_reservada_para_historial(self):
        for condition in ["IMPECABLE", "NO_ESPECIFICADA"]:
            with self.subTest(condition=condition):
                response = self.client.post(
                    "/api/v1/marketplace/publicaciones/",
                    {
                        "pieza_inventario": self.pieza.id,
                        "precio": "100.00",
                        "descripcion": "Descripción válida.",
                        "condicion": condition,
                    },
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("condicion", response.data["error"]["fields"])

    def test_rechaza_publicacion_sin_objetivo(self):
        response = self.client.post(
            "/api/v1/marketplace/publicaciones/",
            {"precio": "100.00", "estado": "ACTIVA"},
        )

        self.assertEqual(response.status_code, 400)

    def test_rechaza_publicacion_con_pieza_y_coleccion(self):
        response = self.client.post(
            "/api/v1/marketplace/publicaciones/",
            {
                "pieza_inventario": self.pieza.id,
                "coleccion_usuario": self.coleccion_usuario.id,
                "precio": "100.00",
                "estado": "ACTIVA",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_rechaza_publicar_una_pieza_ajena(self):
        other = get_user_model().objects.create_user(username="otro", password="password")
        other_collection = ColeccionUsuario.objects.create(user=other, coleccion=self.maestra)
        other_piece = PiezaInventario.objects.create(
            user=other,
            coleccion_usuario=other_collection,
            pieza_catalogo=self.pieza.pieza_catalogo,
            sku="OTHER-SKU",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PUBLICA",
            condicion="NUEVA",
        )

        response = self.client.post(
            "/api/v1/marketplace/publicaciones/",
            {"pieza_inventario": other_piece.id, "precio": "100.00", "estado": "ACTIVA"},
        )

        self.assertEqual(response.status_code, 400)

    def test_graphql_publica_pieza_del_usuario(self):
        access = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.post(
            "/graphql/",
            {
                "query": f"""
                    mutation {{
                      createPublicacion(input: {{
                        piezaInventarioId: "{self.pieza.id}",
                        precio: "125.50",
                        descripcion: "Pieza lista para intercambio",
                        condicion: "NUEVA",
                        estado: "ACTIVA"
                      }}) {{ publicacion {{ id precio descripcion condicion }} }}
                    }}
                """
            },
            format="json",
        )

        self.assertNotIn("errors", response.json())
        self.assertEqual(response.json()["data"]["createPublicacion"]["publicacion"]["precio"], "125.50")
        self.assertEqual(response.json()["data"]["createPublicacion"]["publicacion"]["descripcion"], "Pieza lista para intercambio")
        self.assertEqual(response.json()["data"]["createPublicacion"]["publicacion"]["condicion"], "NUEVA")

    def test_graphql_actualiza_metadatos_con_el_serializer_compartido(self):
        publication = PublicacionMarket.objects.create(
            vendedor=self.user,
            pieza_inventario=self.pieza,
            precio="100.00",
        )
        access = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.post(
            "/graphql/",
            {
                "query": f'''mutation {{
                  updatePublicacion(
                    id: "{publication.id}",
                    descripcion: "  Estado actualizado  ",
                    condicion: "USADA"
                  ) {{ publicacion {{ id descripcion condicion }} }}
                }}'''
            },
            format="json",
        )

        self.assertNotIn("errors", response.json())
        data = response.json()["data"]["updatePublicacion"]["publicacion"]
        self.assertEqual(data["descripcion"], "Estado actualizado")
        self.assertEqual(data["condicion"], "USADA")

    def test_graphql_devuelve_error_estructurado_para_metadatos_invalidos(self):
        access = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.post(
            "/graphql/",
            {
                "query": f'''mutation {{
                  createPublicacion(input: {{
                    piezaInventarioId: "{self.pieza.id}",
                    precio: "100.00",
                    descripcion: "   ",
                    condicion: "NUEVA",
                    estado: "ACTIVA"
                  }}) {{ publicacion {{ id }} }}
                }}'''
            },
            format="json",
        )

        error = response.json()["errors"][0]
        self.assertEqual(error["extensions"]["code"], "VALIDATION_ERROR")
        self.assertIn("descripcion", error["extensions"]["fields"])

    def test_rest_y_graphql_exponen_los_mismos_metadatos(self):
        publication = PublicacionMarket.objects.create(
            vendedor=self.user,
            pieza_inventario=self.pieza,
            precio="100.00",
            descripcion="Metadatos compartidos",
            condicion="USADA",
        )
        rest_response = self.client.get(
            f"/api/v1/marketplace/publicaciones/{publication.id}/"
        )
        access = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        graphql_response = self.client.post(
            "/graphql/",
            {"query": "{ publicacionesMarket { id descripcion condicion } }"},
            format="json",
        )
        graphql_item = next(
            item
            for item in graphql_response.json()["data"]["publicacionesMarket"]
            if int(item["id"]) == publication.id
        )

        self.assertEqual(graphql_item["descripcion"], rest_response.data["descripcion"])
        self.assertEqual(graphql_item["condicion"], rest_response.data["condicion"])

    def test_publicacion_historica_admite_lectura_y_patch_no_relacionado(self):
        publication = PublicacionMarket.objects.create(
            vendedor=self.user,
            pieza_inventario=self.pieza,
            precio="100.00",
        )

        read_response = self.client.get(
            f"/api/v1/marketplace/publicaciones/{publication.id}/"
        )
        patch_response = self.client.patch(
            f"/api/v1/marketplace/publicaciones/{publication.id}/",
            {"precio": "120.00"},
        )

        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.data["descripcion"], "")
        self.assertEqual(read_response.data["condicion"], "NO_ESPECIFICADA")
        self.assertEqual(patch_response.status_code, 200)
        publication.refresh_from_db()
        self.assertEqual(publication.precio, 120)
        self.assertEqual(publication.descripcion, "")
        self.assertEqual(publication.condicion, "NO_ESPECIFICADA")

    def test_base_de_datos_rechaza_estado_de_publicacion_invalido(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            PublicacionMarket.objects.create(
                vendedor=self.user,
                pieza_inventario=self.pieza,
                precio="100.00",
                estado="INVENTADO",
            )

    def test_base_de_datos_rechaza_condicion_de_publicacion_invalida(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            PublicacionMarket.objects.create(
                vendedor=self.user,
                pieza_inventario=self.pieza,
                precio="100.00",
                condicion="INVENTADA",
            )

    def test_detalle_inactivo_solo_es_visible_para_personas_involucradas(self):
        publication = PublicacionMarket.objects.create(
            vendedor=self.user,
            pieza_inventario=self.pieza,
            precio="100.00",
            estado="VENDIDA",
        )
        buyer = get_user_model().objects.create_user(username="buyer-detail", password="password")
        outsider = get_user_model().objects.create_user(username="outsider-detail", password="password")
        Oferta.objects.create(publicacion=publication, comprador=buyer, monto="90.00")

        self.client.force_authenticate(user=outsider)
        self.assertEqual(self.client.get(f"/api/v1/marketplace/publicaciones/{publication.id}/").status_code, 404)
        self.client.force_authenticate(user=buyer)
        self.assertEqual(self.client.get(f"/api/v1/marketplace/publicaciones/{publication.id}/").status_code, 200)
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.get(f"/api/v1/marketplace/publicaciones/{publication.id}/").status_code, 200)

    def test_rest_y_graphql_aplican_la_misma_visibilidad(self):
        publication = PublicacionMarket.objects.create(
            vendedor=self.user,
            pieza_inventario=self.pieza,
            precio="100.00",
            estado="VENDIDA",
        )
        buyer = get_user_model().objects.create_user(username="buyer-visibility", password="password")
        outsider = get_user_model().objects.create_user(username="outsider-visibility", password="password")
        Oferta.objects.create(publicacion=publication, comprador=buyer, monto="90.00")

        for user, should_see in [(outsider, False), (buyer, True), (self.user, True)]:
            with self.subTest(user=user.username):
                self.client.credentials()
                self.client.force_authenticate(user=user)
                rest_response = self.client.get("/api/v1/marketplace/publicaciones/")
                rest_ids = {item["id"] for item in rest_response.data["results"]}

                self.client.force_authenticate(user=None)
                access = RefreshToken.for_user(user).access_token
                self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
                graphql_response = self.client.post(
                    "/graphql/",
                    {"query": "{ publicacionesMarket { id descripcion condicion } }"},
                    format="json",
                )
                graphql_ids = {
                    int(item["id"])
                    for item in graphql_response.json()["data"]["publicacionesMarket"]
                }
                self.assertEqual(publication.id in rest_ids, should_see)
                self.assertEqual(publication.id in graphql_ids, should_see)


class OfferWorkflowApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(username="seller", password="password")
        self.buyer = user_model.objects.create_user(username="buyer", password="password")
        self.other_buyer = user_model.objects.create_user(username="buyer2", password="password")
        self.master = ColeccionMaestra.objects.create(
            nombre="Venta", categoria="General", propietario=self.seller
        )
        self.seller_collection = ColeccionUsuario.objects.create(
            user=self.seller, coleccion=self.master
        )
        catalog_piece = PiezaCatalogo.objects.create(
            coleccion=self.master,
            numero_item="1",
            nombre="Pieza en venta",
            sku_base="SALE-BASE",
        )
        self.piece = PiezaInventario.objects.create(
            user=self.seller,
            coleccion_usuario=self.seller_collection,
            pieza_catalogo=catalog_piece,
            sku="SALE-SKU",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PUBLICA",
            condicion="NUEVA",
        )
        self.publication = PublicacionMarket.objects.create(
            vendedor=self.seller,
            pieza_inventario=self.piece,
            precio="100.00",
        )
        self.client = APIClient()

    def create_offer(self, buyer, amount="90.00"):
        self.client.force_authenticate(user=buyer)
        return self.client.post(
            "/api/v1/marketplace/ofertas/",
            {"publicacion": self.publication.id, "monto": amount, "estado": "COMPLETADA"},
        )

    def test_crea_oferta_pendiente_y_no_permite_autooferta(self):
        response = self.create_offer(self.buyer)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["estado"], "PENDIENTE")
        self.assertTrue(
            Notificacion.objects.filter(user=self.seller, tipo="oferta").exists()
        )

        self.client.force_authenticate(user=self.seller)
        own_response = self.client.post(
            "/api/v1/marketplace/ofertas/",
            {"publicacion": self.publication.id, "monto": "80.00"},
        )
        self.assertEqual(own_response.status_code, 400)

    def test_aceptar_rechaza_otras_ofertas_y_reserva_publicacion(self):
        first = self.create_offer(self.buyer).data
        second = self.create_offer(self.other_buyer, "95.00").data
        self.client.force_authenticate(user=self.seller)

        response = self.client.post(
            f"/api/v1/marketplace/ofertas/{first['id']}/aceptar/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "ACEPTADA")
        self.assertEqual(Oferta.objects.get(id=second["id"]).estado, "RECHAZADA")
        self.publication.refresh_from_db()
        self.assertEqual(self.publication.estado, "RESERVADA")
        self.assertTrue(
            Notificacion.objects.filter(user=self.buyer, tipo="oferta").exists()
        )

    def test_completar_venta_transfiere_pieza_al_comprador(self):
        self.master.total_piezas = 1
        self.master.save(update_fields=["total_piezas"])
        offer = self.create_offer(self.buyer).data
        self.client.force_authenticate(user=self.seller)
        self.client.post(f"/api/v1/marketplace/ofertas/{offer['id']}/aceptar/")

        response = self.client.post(
            f"/api/v1/marketplace/ofertas/{offer['id']}/completar/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "COMPLETADA")
        self.piece.refresh_from_db()
        self.publication.refresh_from_db()
        self.assertEqual(self.piece.user, self.buyer)
        self.assertEqual(self.piece.coleccion_usuario.user, self.buyer)
        self.assertEqual(self.publication.estado, "VENDIDA")
        self.assertEqual(self.publication.vendedor, self.seller)
        self.seller_collection.refresh_from_db()
        self.assertEqual(self.seller_collection.progreso, 0)
        self.assertEqual(self.piece.coleccion_usuario.progreso, 100)

    def test_solo_vendedor_puede_aceptar(self):
        offer = self.create_offer(self.buyer).data

        response = self.client.post(
            f"/api/v1/marketplace/ofertas/{offer['id']}/aceptar/"
        )

        self.assertEqual(response.status_code, 403)

    def test_oferta_inexistente_devuelve_404_seguro(self):
        self.client.force_authenticate(user=self.seller)

        response = self.client.post("/api/v1/marketplace/ofertas/999999/aceptar/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"]["code"], "not_found")

    def test_transicion_incompatible_devuelve_conflicto(self):
        offer = self.create_offer(self.buyer).data
        self.client.force_authenticate(user=self.seller)
        self.client.post(f"/api/v1/marketplace/ofertas/{offer['id']}/rechazar/")

        response = self.client.post(
            f"/api/v1/marketplace/ofertas/{offer['id']}/rechazar/"
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"]["code"], "conflict")

    def test_rechazar_oferta_conserva_publicacion_activa(self):
        offer = self.create_offer(self.buyer).data
        self.client.force_authenticate(user=self.seller)

        response = self.client.post(
            f"/api/v1/marketplace/ofertas/{offer['id']}/rechazar/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "RECHAZADA")
        self.publication.refresh_from_db()
        self.assertEqual(self.publication.estado, "ACTIVA")

    def test_completar_coleccion_fusiona_participacion_existente(self):
        self.publication.delete()
        self.master.total_piezas = 1
        self.master.save(update_fields=["total_piezas"])
        buyer_collection = ColeccionUsuario.objects.create(
            user=self.buyer,
            coleccion=self.master,
        )
        self.publication = PublicacionMarket.objects.create(
            vendedor=self.seller,
            coleccion_usuario=self.seller_collection,
            precio="500.00",
        )
        offer = self.create_offer(self.buyer, "450.00").data
        self.client.force_authenticate(user=self.seller)
        self.client.post(f"/api/v1/marketplace/ofertas/{offer['id']}/aceptar/")

        response = self.client.post(
            f"/api/v1/marketplace/ofertas/{offer['id']}/completar/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            ColeccionUsuario.objects.filter(id=self.seller_collection.id).exists()
        )
        self.publication.refresh_from_db()
        self.piece.refresh_from_db()
        self.master.refresh_from_db()
        self.assertEqual(self.publication.coleccion_usuario, buyer_collection)
        self.assertEqual(self.piece.coleccion_usuario, buyer_collection)
        self.assertEqual(self.piece.user, self.buyer)
        self.assertEqual(self.master.propietario, self.buyer)
        buyer_collection.refresh_from_db()
        self.assertEqual(buyer_collection.progreso, 100)
