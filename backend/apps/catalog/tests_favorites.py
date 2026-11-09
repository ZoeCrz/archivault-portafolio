from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.marketplace.models import Oferta, PublicacionMarket
from apps.marketplace.services import complete_offer
from .models import (
    ColeccionMaestra,
    ColeccionUsuario,
    Favorito,
    PiezaCatalogo,
    PiezaInventario,
)


class FavoriteApiTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user(username="favorite-owner")
        self.other = users.objects.create_user(username="favorite-other")
        self.third = users.objects.create_user(username="favorite-third")
        self.master = ColeccionMaestra.objects.create(
            nombre="Colección privada",
            categoria="General",
            tipo="personal",
            propietario=self.owner,
        )
        self.participation = ColeccionUsuario.objects.create(
            user=self.owner, coleccion=self.master
        )
        catalog_piece = PiezaCatalogo.objects.create(
            coleccion=self.master,
            numero_item="1",
            nombre="Pieza favorita",
            sku_base="FAV-BASE",
        )
        self.piece = PiezaInventario.objects.create(
            user=self.owner,
            coleccion_usuario=self.participation,
            pieza_catalogo=catalog_piece,
            sku="FAV-SKU",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PRIVADA",
            condicion="NUEVA",
        )
        self.client = APIClient()

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def test_crea_lista_filtra_y_elimina_ambos_tipos(self):
        self.authenticate(self.owner)
        piece = self.client.post(
            "/api/v1/catalog/favoritos/", {"pieza_inventario": self.piece.id}
        )
        collection = self.client.post(
            "/api/v1/catalog/favoritos/", {"coleccion_maestra": self.master.id}
        )
        self.assertEqual(piece.status_code, 201)
        self.assertEqual(piece.data["tipo"], "PIEZA")
        self.assertEqual(piece.data["objetivo_id"], self.piece.id)
        self.assertTrue(piece.data["disponible"])
        self.assertEqual(collection.status_code, 201)
        self.assertEqual(collection.data["tipo"], "COLECCION")
        self.assertEqual(collection.data["objetivo_id"], self.master.id)

        pieces = self.client.get("/api/v1/catalog/favoritos/?tipo=PIEZA")
        collections = self.client.get("/api/v1/catalog/favoritos/?tipo=COLECCION")
        self.assertEqual([item["id"] for item in pieces.data], [piece.data["id"]])
        self.assertEqual(
            [item["id"] for item in collections.data], [collection.data["id"]]
        )
        self.assertEqual(
            self.client.patch(
                f"/api/v1/catalog/favoritos/{piece.data['id']}/", {}
            ).status_code,
            405,
        )
        self.assertEqual(
            self.client.delete(
                f"/api/v1/catalog/favoritos/{piece.data['id']}/"
            ).status_code,
            204,
        )
        self.assertTrue(PiezaInventario.objects.filter(pk=self.piece.id).exists())

    def test_rechaza_objetivos_invalidos_y_duplicados(self):
        self.authenticate(self.owner)
        no_target = self.client.post("/api/v1/catalog/favoritos/", {})
        both = self.client.post(
            "/api/v1/catalog/favoritos/",
            {
                "pieza_inventario": self.piece.id,
                "coleccion_maestra": self.master.id,
            },
        )
        self.assertEqual(no_target.status_code, 400)
        self.assertEqual(both.status_code, 400)
        self.client.post(
            "/api/v1/catalog/favoritos/", {"pieza_inventario": self.piece.id}
        )
        duplicate = self.client.post(
            "/api/v1/catalog/favoritos/", {"pieza_inventario": self.piece.id}
        )
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.data["error"]["code"], "conflict")

    def test_permisos_de_piezas(self):
        self.authenticate(self.other)
        private = self.client.post(
            "/api/v1/catalog/favoritos/", {"pieza_inventario": self.piece.id}
        )
        self.assertEqual(private.status_code, 404)

        self.piece.visibilidad = "PUBLICA"
        self.piece.save(update_fields=["visibilidad"])
        public = self.client.post(
            "/api/v1/catalog/favoritos/", {"pieza_inventario": self.piece.id}
        )
        self.assertEqual(public.status_code, 201)

    def test_publicacion_visible_habilita_pieza_pero_cerrada_ajena_no(self):
        publication = PublicacionMarket.objects.create(
            vendedor=self.owner,
            pieza_inventario=self.piece,
            precio="10",
            descripcion="Pieza visible",
            condicion="NUEVA",
        )
        self.authenticate(self.other)
        self.assertEqual(
            self.client.post(
                "/api/v1/catalog/favoritos/", {"pieza_inventario": self.piece.id}
            ).status_code,
            201,
        )
        Favorito.objects.all().delete()
        publication.estado = "VENDIDA"
        publication.save(update_fields=["estado"])
        self.authenticate(self.third)
        self.assertEqual(
            self.client.post(
                "/api/v1/catalog/favoritos/", {"pieza_inventario": self.piece.id}
            ).status_code,
            404,
        )

    def test_permisos_de_colecciones(self):
        global_collection = ColeccionMaestra.objects.create(
            nombre="Global", categoria="General", tipo="global"
        )
        participated = ColeccionMaestra.objects.create(
            nombre="Participada", categoria="General", tipo="personal", propietario=self.owner
        )
        ColeccionUsuario.objects.create(user=self.other, coleccion=participated)
        self.authenticate(self.other)
        for collection in [global_collection, participated]:
            with self.subTest(collection=collection.nombre):
                self.assertEqual(
                    self.client.post(
                        "/api/v1/catalog/favoritos/",
                        {"coleccion_maestra": collection.id},
                    ).status_code,
                    201,
                )
        self.assertEqual(
            self.client.post(
                "/api/v1/catalog/favoritos/",
                {"coleccion_maestra": self.master.id},
            ).status_code,
            404,
        )

    def test_publicacion_visible_habilita_coleccion(self):
        publication = PublicacionMarket.objects.create(
            vendedor=self.owner,
            coleccion_usuario=self.participation,
            precio="100",
            descripcion="Colección visible",
            condicion="USADA",
        )
        self.authenticate(self.other)
        self.assertEqual(
            self.client.post(
                "/api/v1/catalog/favoritos/",
                {"coleccion_maestra": self.master.id},
            ).status_code,
            201,
        )
        publication.estado = "CANCELADA"
        publication.save(update_fields=["estado"])
        self.assertFalse(
            self.client.get("/api/v1/catalog/favoritos/").data[0]["disponible"]
        )

    def test_aislamiento_entre_usuarios(self):
        favorite = Favorito.objects.create(user=self.owner, pieza_inventario=self.piece)
        self.authenticate(self.other)
        self.assertEqual(self.client.get("/api/v1/catalog/favoritos/").data, [])
        self.assertEqual(
            self.client.delete(f"/api/v1/catalog/favoritos/{favorite.id}/").status_code,
            404,
        )

    def test_restricciones_de_base_de_datos(self):
        Favorito.objects.create(user=self.owner, pieza_inventario=self.piece)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Favorito.objects.create(user=self.owner, pieza_inventario=self.piece)
        Favorito.objects.create(user=self.owner, coleccion_maestra=self.master)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Favorito.objects.create(user=self.owner, coleccion_maestra=self.master)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Favorito.objects.create(user=self.other)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Favorito.objects.create(
                user=self.other,
                pieza_inventario=self.piece,
                coleccion_maestra=self.master,
            )
        Favorito.objects.create(user=self.other, pieza_inventario=self.piece)

    def test_cascade_de_objetivos(self):
        piece_favorite = Favorito.objects.create(
            user=self.owner, pieza_inventario=self.piece
        )
        self.piece.delete()
        self.assertFalse(Favorito.objects.filter(pk=piece_favorite.id).exists())

        collection = ColeccionMaestra.objects.create(
            nombre="Temporal", categoria="General", propietario=self.owner
        )
        collection_favorite = Favorito.objects.create(
            user=self.owner, coleccion_maestra=collection
        )
        collection.delete()
        self.assertFalse(Favorito.objects.filter(pk=collection_favorite.id).exists())

    def test_transferir_pieza_conserva_favorito_y_respeta_privacidad(self):
        self.piece.visibilidad = "PUBLICA"
        self.piece.save(update_fields=["visibilidad"])
        favorite = Favorito.objects.create(user=self.third, pieza_inventario=self.piece)
        publication = PublicacionMarket.objects.create(
            vendedor=self.owner,
            pieza_inventario=self.piece,
            precio="100",
            estado="RESERVADA",
        )
        offer = Oferta.objects.create(
            publicacion=publication,
            comprador=self.other,
            monto="90",
            estado="ACEPTADA",
        )
        complete_offer(offer.id, self.owner)
        self.assertTrue(Favorito.objects.filter(pk=favorite.id).exists())
        self.authenticate(self.third)
        self.assertFalse(
            self.client.get("/api/v1/catalog/favoritos/").data[0]["disponible"]
        )
        token = RefreshToken.for_user(self.third).access_token
        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        graphql = self.client.post(
            "/graphql/",
            {"query": "{ favoritos { disponible piezaInventario { id sku } } }"},
            format="json",
        ).json()
        self.assertFalse(graphql["data"]["favoritos"][0]["disponible"])
        self.assertIsNone(graphql["data"]["favoritos"][0]["piezaInventario"])

    def test_transferir_y_fusionar_coleccion_conserva_favorito_maestro(self):
        favorite = Favorito.objects.create(
            user=self.third, coleccion_maestra=self.master
        )
        buyer_participation = ColeccionUsuario.objects.create(
            user=self.other, coleccion=self.master
        )
        publication = PublicacionMarket.objects.create(
            vendedor=self.owner,
            coleccion_usuario=self.participation,
            precio="200",
            estado="RESERVADA",
        )
        offer = Oferta.objects.create(
            publicacion=publication,
            comprador=self.other,
            monto="190",
            estado="ACEPTADA",
        )
        complete_offer(offer.id, self.owner)
        publication.refresh_from_db()
        self.assertEqual(publication.coleccion_usuario_id, buyer_participation.id)
        self.assertTrue(Favorito.objects.filter(pk=favorite.id).exists())
        self.assertEqual(favorite.coleccion_maestra_id, self.master.id)

    def test_graphql_crea_lista_filtra_elimina_y_reporta_conflicto(self):
        token = RefreshToken.for_user(self.owner).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        create = self.client.post(
            "/graphql/",
            {
                "query": f'''mutation {{ crearFavorito(input: {{
                  piezaInventarioId: "{self.piece.id}"
                }}) {{ favorito {{ id tipo objetivoId disponible }} }} }}'''
            },
            format="json",
        ).json()
        self.assertNotIn("errors", create)
        favorite_id = create["data"]["crearFavorito"]["favorito"]["id"]
        duplicate = self.client.post(
            "/graphql/",
            {
                "query": f'''mutation {{ crearFavorito(input: {{
                  piezaInventarioId: "{self.piece.id}"
                }}) {{ favorito {{ id }} }} }}'''
            },
            format="json",
        ).json()
        self.assertEqual(duplicate["errors"][0]["extensions"]["code"], "CONFLICT")
        invalid = self.client.post(
            "/graphql/",
            {"query": "mutation { crearFavorito(input: {}) { favorito { id } } }"},
            format="json",
        ).json()
        self.assertEqual(invalid["errors"][0]["extensions"]["code"], "VALIDATION_ERROR")
        self.assertTrue(invalid["errors"][0]["extensions"]["request_id"])
        query = self.client.post(
            "/graphql/",
            {"query": "{ favoritos(tipo: PIEZA) { id tipo objetivoId disponible } }"},
            format="json",
        ).json()
        self.assertEqual(query["data"]["favoritos"][0]["objetivoId"], str(self.piece.id))
        deleted = self.client.post(
            "/graphql/",
            {"query": f'mutation {{ eliminarFavorito(id: "{favorite_id}") {{ ok }} }}'},
            format="json",
        ).json()
        self.assertTrue(deleted["data"]["eliminarFavorito"]["ok"])
