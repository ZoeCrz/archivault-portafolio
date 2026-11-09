from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class PublicationMetadataMigrationTests(TransactionTestCase):
    migrate_from = [("marketplace", "0004_oferta_valid_market_offer_status_and_more")]
    migrate_to = [("marketplace", "0005_publication_metadata")]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        User = old_apps.get_model("auth", "User")
        Master = old_apps.get_model("catalog", "ColeccionMaestra")
        UserCollection = old_apps.get_model("catalog", "ColeccionUsuario")
        CatalogPiece = old_apps.get_model("catalog", "PiezaCatalogo")
        InventoryPiece = old_apps.get_model("catalog", "PiezaInventario")
        Publication = old_apps.get_model("marketplace", "PublicacionMarket")

        user = User.objects.create(username="historical-seller")
        master = Master.objects.create(
            nombre="Colección histórica",
            categoria="General",
            tipo="personal",
            propietario_id=user.id,
        )
        piece_collection = UserCollection.objects.create(user_id=user.id, coleccion_id=master.id)
        collection_listing_target = UserCollection.objects.create(
            user_id=user.id,
            coleccion_id=Master.objects.create(
                nombre="Otra colección histórica",
                categoria="General",
                tipo="personal",
                propietario_id=user.id,
            ).id,
        )
        catalog_piece = CatalogPiece.objects.create(
            coleccion_id=master.id,
            numero_item="1",
            nombre="Pieza histórica",
            sku_base="HISTORICAL-BASE",
        )
        inventory_piece = InventoryPiece.objects.create(
            user_id=user.id,
            coleccion_usuario_id=piece_collection.id,
            pieza_catalogo_id=catalog_piece.id,
            sku="HISTORICAL-SKU",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PUBLICA",
            condicion="DAÑADA",
        )
        self.piece_publication_id = Publication.objects.create(
            vendedor_id=user.id,
            pieza_inventario_id=inventory_piece.id,
            precio="123.45",
            estado="RESERVADA",
        ).id
        self.collection_publication_id = Publication.objects.create(
            vendedor_id=user.id,
            coleccion_usuario_id=collection_listing_target.id,
            precio="987.65",
            estado="ACTIVA",
        ).id

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migra_metadatos_sin_alterar_los_datos_del_anuncio(self):
        Publication = self.apps.get_model("marketplace", "PublicacionMarket")
        piece_publication = Publication.objects.get(pk=self.piece_publication_id)
        collection_publication = Publication.objects.get(pk=self.collection_publication_id)

        self.assertEqual(piece_publication.descripcion, "")
        self.assertEqual(piece_publication.condicion, "DAÑADA")
        self.assertEqual(piece_publication.precio, Decimal("123.45"))
        self.assertEqual(piece_publication.estado, "RESERVADA")
        self.assertIsNotNone(piece_publication.pieza_inventario_id)
        self.assertIsNone(piece_publication.coleccion_usuario_id)

        self.assertEqual(collection_publication.descripcion, "")
        self.assertEqual(collection_publication.condicion, "NO_ESPECIFICADA")
        self.assertEqual(collection_publication.precio, Decimal("987.65"))
        self.assertEqual(collection_publication.estado, "ACTIVA")
        self.assertIsNone(collection_publication.pieza_inventario_id)
        self.assertIsNotNone(collection_publication.coleccion_usuario_id)
