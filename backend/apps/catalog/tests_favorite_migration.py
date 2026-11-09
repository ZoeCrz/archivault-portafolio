from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class FavoriteCollectionMigrationTests(TransactionTestCase):
    migrate_from = [("catalog", "0005_alter_piezainventario_condicion_and_more")]
    migrate_to = [("catalog", "0006_favorite_collections")]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        User = old_apps.get_model("auth", "User")
        Master = old_apps.get_model("catalog", "ColeccionMaestra")
        Participation = old_apps.get_model("catalog", "ColeccionUsuario")
        CatalogPiece = old_apps.get_model("catalog", "PiezaCatalogo")
        Piece = old_apps.get_model("catalog", "PiezaInventario")
        Favorite = old_apps.get_model("catalog", "Favorito")

        user = User.objects.create(username="historical-favorite")
        master = Master.objects.create(
            nombre="Histórica", categoria="General", propietario_id=user.id
        )
        participation = Participation.objects.create(
            user_id=user.id, coleccion_id=master.id
        )
        catalog_piece = CatalogPiece.objects.create(
            coleccion_id=master.id,
            numero_item="1",
            nombre="Histórica",
            sku_base="HIST-FAV-BASE",
        )
        piece = Piece.objects.create(
            user_id=user.id,
            coleccion_usuario_id=participation.id,
            pieza_catalogo_id=catalog_piece.id,
            sku="HIST-FAV",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PUBLICA",
            condicion="NUEVA",
        )
        favorite = Favorite.objects.create(user_id=user.id, pieza_inventario_id=piece.id)
        self.expected = (favorite.id, user.id, piece.id)

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_conserva_favorito_de_pieza_sin_transformarlo(self):
        Favorite = self.apps.get_model("catalog", "Favorito")
        favorite = Favorite.objects.get(pk=self.expected[0])
        self.assertEqual(favorite.user_id, self.expected[1])
        self.assertEqual(favorite.pieza_inventario_id, self.expected[2])
        self.assertIsNone(favorite.coleccion_maestra_id)


class FavoriteMySQLUniquenessMigrationTests(TransactionTestCase):
    migrate_from = [("catalog", "0006_favorite_collections")]
    migrate_to = [("catalog", "0007_mysql_compatible_favorite_uniqueness")]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        User = old_apps.get_model("auth", "User")
        Master = old_apps.get_model("catalog", "ColeccionMaestra")
        Participation = old_apps.get_model("catalog", "ColeccionUsuario")
        CatalogPiece = old_apps.get_model("catalog", "PiezaCatalogo")
        Piece = old_apps.get_model("catalog", "PiezaInventario")
        Favorite = old_apps.get_model("catalog", "Favorito")

        user = User.objects.create(username="mysql-favorite")
        master = Master.objects.create(
            nombre="Compatible", categoria="General", propietario_id=user.id
        )
        participation = Participation.objects.create(
            user_id=user.id, coleccion_id=master.id
        )
        catalog_piece = CatalogPiece.objects.create(
            coleccion_id=master.id,
            numero_item="1",
            nombre="Compatible",
            sku_base="MYSQL-FAV-BASE",
        )
        piece = Piece.objects.create(
            user_id=user.id,
            coleccion_usuario_id=participation.id,
            pieza_catalogo_id=catalog_piece.id,
            sku="MYSQL-FAV",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PUBLICA",
            condicion="NUEVA",
        )
        piece_favorite = Favorite.objects.create(
            user_id=user.id, pieza_inventario_id=piece.id
        )
        collection_favorite = Favorite.objects.create(
            user_id=user.id, coleccion_maestra_id=master.id
        )
        self.expected = {
            "user_id": user.id,
            "piece_id": piece.id,
            "master_id": master.id,
            "favorite_ids": {piece_favorite.id, collection_favorite.id},
        }

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_conserva_datos_validos_y_aplica_ambas_restricciones(self):
        Favorite = self.apps.get_model("catalog", "Favorito")
        favorites = Favorite.objects.filter(user_id=self.expected["user_id"])
        self.assertEqual(
            set(favorites.values_list("id", flat=True)),
            self.expected["favorite_ids"],
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Favorite.objects.create(
                user_id=self.expected["user_id"],
                pieza_inventario_id=self.expected["piece_id"],
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Favorite.objects.create(
                user_id=self.expected["user_id"],
                coleccion_maestra_id=self.expected["master_id"],
            )
