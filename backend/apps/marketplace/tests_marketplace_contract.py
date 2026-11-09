from config.test_images import PNG_BYTES
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from apps.catalog.models import (
    ColeccionMaestra,
    ColeccionUsuario,
    Favorito,
    PiezaCatalogo,
    PiezaFoto,
    PiezaInventario,
)
from config.schema import schema
from .models import Oferta, PublicacionMarket


class MarketplaceContractTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(username="seller-contract")
        self.buyer = user_model.objects.create_user(username="buyer-contract")
        self.outsider = user_model.objects.create_user(username="outsider-contract")
        self.master = ColeccionMaestra.objects.create(
            nombre="Colección Espacial",
            categoria="Figuras",
            tipo="personal",
            propietario=self.seller,
        )
        self.participation = ColeccionUsuario.objects.create(
            user=self.seller, coleccion=self.master
        )
        self.catalog_piece = PiezaCatalogo.objects.create(
            coleccion=self.master,
            numero_item="1",
            nombre="Astronauta de catálogo",
            sku_base="SPACE-BASE",
        )
        self.piece = PiezaInventario.objects.create(
            user=self.seller,
            coleccion_usuario=self.participation,
            pieza_catalogo=self.catalog_piece,
            nombre_personalizado="Astronauta personalizado",
            sku="SPACE-001",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PUBLICA",
            condicion="NUEVA",
        )
        self.photo = PiezaFoto.objects.create(
            pieza_inventario=self.piece,
            archivo=SimpleUploadedFile("actual.png", PNG_BYTES, content_type="image/png"),
            url="https://legacy.example/space.png",
        )
        self.piece_publication = PublicacionMarket.objects.create(
            vendedor=self.seller,
            pieza_inventario=self.piece,
            precio="100.00",
            descripcion="Anuncio espacial",
            condicion="USADA",
        )
        collection_master = ColeccionMaestra.objects.create(
            nombre="Colección Retro",
            categoria="Tarjetas",
            tipo="personal",
            propietario=self.seller,
        )
        self.collection_participation = ColeccionUsuario.objects.create(
            user=self.seller, coleccion=collection_master
        )
        self.collection_publication = PublicacionMarket.objects.create(
            vendedor=self.seller,
            coleccion_usuario=self.collection_participation,
            precio="250.00",
            descripcion="Colección histórica",
            condicion="NUEVA",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.buyer)

    def results(self, **params):
        response = self.client.get("/api/v1/marketplace/publicaciones/", params)
        self.assertEqual(response.status_code, 200, response.data)
        return response.data["results"]

    def test_contrato_enriquecido_de_pieza_e_imagen_historica(self):
        response = self.client.get(
            f"/api/v1/marketplace/publicaciones/{self.piece_publication.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tipo"], "PIEZA")
        self.assertEqual(response.data["objetivo_id"], self.piece.id)
        self.assertEqual(response.data["nombre"], "Astronauta personalizado")
        self.assertEqual(response.data["sku"], "SPACE-001")
        self.assertEqual(response.data["coleccion"]["id"], self.master.id)
        self.assertEqual(
            response.data["coleccion"]["coleccion_usuario_id"], self.participation.id
        )
        self.assertEqual(response.data["descripcion"], "Anuncio espacial")
        self.assertEqual(response.data["condicion"], "USADA")
        self.assertTrue(response.data["imagen"][0].endswith(self.photo.archivo.url))
        self.assertEqual(response.data["imagen"][1], self.photo.url)
        self.assertEqual(
            response.data["vendedor"], {"id": self.seller.id, "nombre": self.seller.username}
        )
        self.assertEqual(response.data["categoria"], "Figuras")
        self.assertEqual(response.data["estado_objetivo"], "ADQUIRIDA")
        self.assertNotIn("email", response.data["vendedor"])

    def test_nombre_de_pieza_usa_fallback_de_catalogo(self):
        self.piece.nombre_personalizado = "  "
        self.piece.save(update_fields=["nombre_personalizado"])
        item = self.client.get(
            f"/api/v1/marketplace/publicaciones/{self.piece_publication.id}/"
        ).data
        self.assertEqual(item["nombre"], "Astronauta de catálogo")

    def test_contrato_enriquecido_de_coleccion(self):
        item = self.client.get(
            f"/api/v1/marketplace/publicaciones/{self.collection_publication.id}/"
        ).data
        self.assertEqual(item["tipo"], "COLECCION")
        self.assertEqual(item["nombre"], "Colección Retro")
        self.assertIsNone(item["sku"])
        self.assertEqual(item["coleccion"]["id"], self.collection_participation.coleccion_id)
        self.assertEqual(item["categoria"], "Tarjetas")
        self.assertIsNone(item["estado_objetivo"])

    def test_publicacion_historica_sigue_siendo_legible(self):
        self.piece_publication.descripcion = ""
        self.piece_publication.condicion = "NO_ESPECIFICADA"
        self.piece_publication.save(update_fields=["descripcion", "condicion"])
        item = self.client.get(
            f"/api/v1/marketplace/publicaciones/{self.piece_publication.id}/"
        ).data
        self.assertEqual(item["descripcion"], "")
        self.assertEqual(item["condicion"], "NO_ESPECIFICADA")

    def test_filtros_individuales_y_combinados(self):
        cases = [
            ({"q": "SPACE-001"}, {self.piece_publication.id}),
            ({"q": "histórica"}, {self.collection_publication.id}),
            ({"tipo": "PIEZA"}, {self.piece_publication.id}),
            ({"tipo": "COLECCION"}, {self.collection_publication.id}),
            ({"estado": "ACTIVA"}, {self.piece_publication.id, self.collection_publication.id}),
            ({"condicion": "USADA"}, {self.piece_publication.id}),
            ({"categoria": "tarjetas"}, {self.collection_publication.id}),
            ({"coleccion": self.master.id}, {self.piece_publication.id}),
            ({"precio_min": "100", "precio_max": "100"}, {self.piece_publication.id}),
            (
                {"tipo": "PIEZA", "condicion": "USADA", "categoria": "Figuras"},
                {self.piece_publication.id},
            ),
        ]
        for params, expected in cases:
            with self.subTest(params=params):
                self.assertEqual({item["id"] for item in self.results(**params)}, expected)

    def test_filtros_invalidos_devuelven_campos_normalizados(self):
        cases = [
            ({"tipo": "OTRO"}, "tipo"),
            ({"estado": "OTRO"}, "estado"),
            ({"condicion": "OTRA"}, "condicion"),
            ({"coleccion": "abc"}, "coleccion"),
            ({"precio_min": "abc"}, "precio_min"),
            ({"precio_min": "20", "precio_max": "10"}, "precio_min"),
            ({"orden": "precio"}, "orden"),
            ({"page_size": "101"}, "page_size"),
        ]
        for params, field in cases:
            with self.subTest(params=params):
                response = self.client.get("/api/v1/marketplace/publicaciones/", params)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data["error"]["code"], "validation_error")
                self.assertIn(field, response.data["error"]["fields"])

    def test_ordenes_son_deterministas(self):
        cases = {
            "recientes": [self.collection_publication.id, self.piece_publication.id],
            "antiguos": [self.piece_publication.id, self.collection_publication.id],
            "precio_asc": [self.piece_publication.id, self.collection_publication.id],
            "precio_desc": [self.collection_publication.id, self.piece_publication.id],
            "nombre_asc": [self.piece_publication.id, self.collection_publication.id],
        }
        for ordering, expected in cases.items():
            with self.subTest(ordering=ordering):
                self.assertEqual(
                    [item["id"] for item in self.results(orden=ordering)], expected
                )

    def test_paginacion_es_especifica_y_navegable(self):
        first = self.client.get(
            "/api/v1/marketplace/publicaciones/", {"page_size": 1}
        )
        self.assertEqual(first.data["count"], 2)
        self.assertEqual(len(first.data["results"]), 1)
        self.assertIsNotNone(first.data["next"])
        second = self.client.get(
            "/api/v1/marketplace/publicaciones/", {"page_size": 1, "page": 2}
        )
        self.assertEqual(len(second.data["results"]), 1)
        self.assertIsNotNone(second.data["previous"])

    def test_visibilidad_se_aplica_antes_de_los_filtros(self):
        self.piece_publication.estado = "VENDIDA"
        self.piece_publication.save(update_fields=["estado"])
        Oferta.objects.create(
            publicacion=self.piece_publication, comprador=self.buyer, monto="90"
        )
        self.assertIn(
            self.piece_publication.id,
            {item["id"] for item in self.results(estado="VENDIDA")},
        )
        self.client.force_authenticate(self.outsider)
        self.assertNotIn(
            self.piece_publication.id,
            {item["id"] for item in self.results(estado="VENDIDA")},
        )
        self.client.force_authenticate(self.seller)
        self.assertIn(
            self.piece_publication.id,
            {item["id"] for item in self.results(estado="VENDIDA")},
        )

    def test_es_favorito_y_filtro_incluyen_piezas_y_colecciones(self):
        Favorito.objects.create(user=self.buyer, pieza_inventario=self.piece)
        Favorito.objects.create(
            user=self.buyer,
            coleccion_maestra=self.collection_participation.coleccion,
        )
        results = self.results(favoritos="true")
        self.assertEqual(
            {item["id"] for item in results},
            {self.piece_publication.id, self.collection_publication.id},
        )
        self.assertTrue(all(item["es_favorito"] for item in results))
        piece_only = self.results(favoritos="true", tipo="PIEZA", precio_max="100")
        self.assertEqual([item["id"] for item in piece_only], [self.piece_publication.id])
        self.assertEqual(
            [item["id"] for item in self.results(favoritos="false")], []
        )

    def test_favoritos_no_amplian_visibilidad(self):
        self.piece_publication.estado = "VENDIDA"
        self.piece_publication.save(update_fields=["estado"])
        Favorito.objects.create(user=self.outsider, pieza_inventario=self.piece)
        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.results(favoritos="true"), [])

    def test_numero_de_queries_rest_es_constante(self):
        with self.assertNumQueries(3):
            response = self.client.get(
                "/api/v1/marketplace/publicaciones/",
                {"page_size": 1, "orden": "antiguos"},
            )
            self.assertEqual(response.status_code, 200)
        with self.assertNumQueries(3):
            response = self.client.get(
                "/api/v1/marketplace/publicaciones/",
                {"page_size": 24, "orden": "antiguos"},
            )
            self.assertEqual(response.status_code, 200)

    def graphql(self, query):
        request = RequestFactory().post("/graphql/")
        request.user = self.buyer
        return schema.execute(query, context_value=request)

    def test_graphql_equivale_a_rest_y_filtra(self):
        Favorito.objects.create(user=self.buyer, pieza_inventario=self.piece)
        rest = self.results(tipo="PIEZA", favoritos="true")[0]
        result = self.graphql(
            '''{ publicacionesMarketplace(
              filtros: {tipo: "PIEZA", favoritos: true, orden: "precio_asc"}, pageSize: 1
            ) { total page pageSize results {
              id tipo objetivoId nombre sku descripcion condicion imagen precio
              categoria estado estadoObjetivo
              esFavorito
              coleccion { id coleccionUsuarioId nombre }
              vendedor { id nombre }
            } } }'''
        )
        self.assertIsNone(result.errors)
        graphql_item = result.data["publicacionesMarketplace"]["results"][0]
        for field in ["tipo", "nombre", "sku", "descripcion", "condicion", "categoria", "estado"]:
            self.assertEqual(graphql_item[field], rest[field])
        self.assertEqual(result.data["publicacionesMarketplace"]["total"], 1)

    def test_graphql_error_de_filtro_es_estructurado(self):
        result = self.graphql(
            '{ publicacionesMarketplace(filtros: {tipo: "OTRO"}) { total } }'
        )
        self.assertEqual(result.errors[0].extensions["code"], "VALIDATION_ERROR")
        self.assertIn("tipo", result.errors[0].extensions["fields"])

    def test_numero_de_queries_graphql_es_constante(self):
        query = '{ publicacionesMarketplace(pageSize: 24) { total results { id nombre imagen } } }'
        with self.assertNumQueries(3):
            result = self.graphql(query)
            self.assertIsNone(result.errors)
