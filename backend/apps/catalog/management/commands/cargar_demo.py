from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import ColeccionMaestra, PiezaCatalogo


class Command(BaseCommand):
    help = "Carga una colección pública ficticia sin crear cuentas."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("La carga de demo requiere DEBUG=True.")
        collection, _ = ColeccionMaestra.objects.get_or_create(
            nombre="Demo · Exploración espacial",
            categoria="Figuras",
            tipo="global",
            propietario=None,
            defaults={"total_piezas": 3},
        )
        for index, name in enumerate(("Sonda Aurora", "Estación Alba", "Módulo Cometa"), start=1):
            item, _ = PiezaCatalogo.objects.get_or_create(
                sku_base=f"DEMO-ESPACIO-{index:02}",
                defaults={"coleccion": collection, "nombre": name, "numero_item": str(index)},
            )
            if item.coleccion_id != collection.pk:
                raise CommandError("Un SKU de demo ya pertenece a otra colección.")
        self.stdout.write(self.style.SUCCESS("Colección de demo disponible en el catálogo."))
