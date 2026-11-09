from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_alter_resena_puntuacion_and_more")]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="biografia",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
    ]
