from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ProfileBiographyMigrationTests(TransactionTestCase):
    migrate_from = [("accounts", "0003_alter_resena_puntuacion_and_more")]
    migrate_to = [("accounts", "0004_profile_biografia")]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        apps = executor.loader.project_state(self.migrate_from).apps
        User = apps.get_model("auth", "User")
        Profile = apps.get_model("accounts", "Profile")
        user = User.objects.create(username="historical-profile")
        profile = Profile.objects.create(user_id=user.id, ubicacion="Quito", perfil_publico=False, avatar="profiles/avatars/a.png")
        self.profile_id = profile.id
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_conserva_perfil_y_agrega_biografia_vacia(self):
        profile = self.apps.get_model("accounts", "Profile").objects.get(pk=self.profile_id)
        self.assertEqual(profile.biografia, "")
        self.assertEqual(profile.ubicacion, "Quito")
        self.assertFalse(profile.perfil_publico)
        self.assertEqual(profile.avatar, "profiles/avatars/a.png")


class MissingProfileBackfillMigrationTests(TransactionTestCase):
    migrate_from = [("accounts", "0004_profile_biografia")]
    migrate_to = [("accounts", "0005_backfill_missing_profiles")]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        apps = executor.loader.project_state(self.migrate_from).apps
        User = apps.get_model("auth", "User")
        Profile = apps.get_model("accounts", "Profile")
        without_profile = User.objects.create(username="sin-perfil")
        with_profile = User.objects.create(username="con-perfil")
        existing = Profile.objects.create(user_id=with_profile.id, ubicacion="Lima")
        self.without_profile_id = without_profile.id
        self.with_profile_id = with_profile.id
        self.existing_profile_id = existing.id
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_crea_los_perfiles_faltantes_sin_duplicar_los_existentes(self):
        Profile = self.apps.get_model("accounts", "Profile")
        self.assertTrue(Profile.objects.filter(user_id=self.without_profile_id).exists())
        self.assertEqual(Profile.objects.filter(user_id=self.with_profile_id).count(), 1)
        self.assertEqual(Profile.objects.get(user_id=self.with_profile_id).id, self.existing_profile_id)
