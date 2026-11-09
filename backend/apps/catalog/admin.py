from django.contrib import admin
from .models import (
    ColeccionMaestra, 
    ColeccionUsuario, 
    Favorito, 
    PiezaCatalogo, 
    PiezaFoto, 
    PiezaInventario
)

admin.site.register(ColeccionMaestra)
admin.site.register(ColeccionUsuario)
admin.site.register(Favorito)
admin.site.register(PiezaCatalogo)
admin.site.register(PiezaFoto)
admin.site.register(PiezaInventario)