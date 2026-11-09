from django.conf import settings
from django.db import models
from config.validators import validate_image_file


class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenido = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post de {self.user.username}"


class PostMedia(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    url = models.URLField(blank=True)
    archivo = models.FileField(
        upload_to="community/posts/",
        validators=[validate_image_file],
        blank=True,
    )
    tipo = models.CharField(max_length=50)

    def __str__(self):
        return self.url or self.archivo.name


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"],
                name="unique_user_post_like",
            )
        ]

    def __str__(self):
        return f"{self.user.username} like post {self.post.id}"


class Comentario(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenido = models.TextField()
    imagen = models.FileField(
        upload_to="community/comments/",
        validators=[validate_image_file],
        blank=True,
    )
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.user.username}"


class Chat(models.Model):
    usuarios = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="chats")

    def __str__(self):
        return f"Chat {self.id}"


class Mensaje(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenido = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["chat", "id"], name="message_chat_id_idx"),
        ]

    def __str__(self):
        return f"Mensaje de {self.user.username}"
