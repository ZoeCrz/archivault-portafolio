from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class NotificationNavigationMigrationTests(TransactionTestCase):
    migrate_from = [("webhooks", "0003_alter_notificacion_tipo")]
    migrate_to = [("webhooks", "0004_notification_navigation")]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        User = old_apps.get_model("auth", "User")
        Notification = old_apps.get_model("webhooks", "Notificacion")
        user = User.objects.create(username="historical-notification-user")
        notification = Notification.objects.create(
            user_id=user.id,
            tipo="general",
            mensaje="Mensaje histórico",
            leido=True,
        )
        self.snapshot = {
            "id": notification.id,
            "user_id": notification.user_id,
            "mensaje": notification.mensaje,
            "leido": notification.leido,
            "fecha": notification.fecha,
        }

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_conserva_notificacion_historica_sin_inferir_destino(self):
        Notification = self.apps.get_model("webhooks", "Notificacion")
        notification = Notification.objects.get(pk=self.snapshot["id"])

        self.assertEqual(notification.user_id, self.snapshot["user_id"])
        self.assertEqual(notification.mensaje, self.snapshot["mensaje"])
        self.assertEqual(notification.leido, self.snapshot["leido"])
        self.assertEqual(notification.fecha, self.snapshot["fecha"])
        self.assertEqual(notification.evento, "GENERAL")
        self.assertIsNone(notification.destino_tipo)
        self.assertIsNone(notification.destino_id)
        self.assertEqual(notification.metadata, {})
