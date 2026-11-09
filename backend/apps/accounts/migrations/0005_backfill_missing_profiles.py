from django.conf import settings
from django.db import migrations


def create_missing_profiles(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Profile = apps.get_model("accounts", "Profile")
    existing = set(Profile.objects.values_list("user_id", flat=True))
    Profile.objects.bulk_create(
        [
            Profile(user_id=user_id)
            for user_id in User.objects.exclude(id__in=existing).values_list("id", flat=True)
        ]
    )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0004_profile_biografia"),
    ]

    operations = [
        migrations.RunPython(create_missing_profiles, migrations.RunPython.noop),
    ]
