from django.contrib import admin
from .models import Chat, Comentario, Mensaje, Post, PostLike, PostMedia

admin.site.register(Chat)
admin.site.register(Comentario)
admin.site.register(Mensaje)
admin.site.register(Post)
admin.site.register(PostLike)
admin.site.register(PostMedia)