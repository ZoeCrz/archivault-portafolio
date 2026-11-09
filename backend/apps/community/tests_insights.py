from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import (
    ColeccionMaestra,
    ColeccionUsuario,
    PiezaCatalogo,
    PiezaInventario,
)
from apps.marketplace.models import PublicacionMarket
from config.schema import schema
from .insights import latest_marketplace_publications, top_collectors
from .models import Comentario, Post, PostLike


class TopCollectorsInsightTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.zero = users.objects.create_user(username="zero")
        self.likes_only = users.objects.create_user(username="likes-only")
        self.comments_only = users.objects.create_user(username="comments-only")
        self.combined = users.objects.create_user(username="combined")
        self.tied = users.objects.create_user(username="tied")
        self.multiple = users.objects.create_user(username="multiple")
        self.actors = [users.objects.create_user(username=f"actor-{index}") for index in range(5)]

        zero_post = Post.objects.create(user=self.zero, contenido="Sin interacción externa")
        PostLike.objects.create(post=zero_post, user=self.zero)
        Comentario.objects.create(post=zero_post, user=self.zero, contenido="Propio")

        likes_post = Post.objects.create(user=self.likes_only, contenido="Sólo likes")
        for actor in self.actors[:2]:
            PostLike.objects.create(post=likes_post, user=actor)

        comments_post = Post.objects.create(user=self.comments_only, contenido="Sólo comentarios")
        for actor in self.actors[:3]:
            Comentario.objects.create(post=comments_post, user=actor, contenido="Comentario")

        combined_post = Post.objects.create(user=self.combined, contenido="Combinado")
        for actor in self.actors[:2]:
            PostLike.objects.create(post=combined_post, user=actor)
        for actor in self.actors[:3]:
            Comentario.objects.create(post=combined_post, user=actor, contenido="Comentario")

        tied_post = Post.objects.create(user=self.tied, contenido="Empate")
        for actor in self.actors[:1]:
            PostLike.objects.create(post=tied_post, user=actor)
        for actor in self.actors[:4]:
            Comentario.objects.create(post=tied_post, user=actor, contenido="Comentario")

        first = Post.objects.create(user=self.multiple, contenido="Primero")
        second = Post.objects.create(user=self.multiple, contenido="Segundo")
        PostLike.objects.create(post=first, user=self.actors[0])
        PostLike.objects.create(post=second, user=self.actors[1])
        Comentario.objects.create(post=first, user=self.actors[2], contenido="Uno")
        Comentario.objects.create(post=second, user=self.actors[3], contenido="Dos")

    def test_ranking_cubre_ceros_likes_comentarios_combinacion_empate_y_posts(self):
        ranking = list(top_collectors())
        by_id = {user.id: user for user in ranking}
        self.assertNotIn(self.zero.id, by_id)
        self.assertEqual(by_id[self.likes_only.id].likes_recibidos, 2)
        self.assertEqual(by_id[self.likes_only.id].comentarios_recibidos, 0)
        self.assertEqual(by_id[self.likes_only.id].score, 2)
        self.assertEqual(by_id[self.comments_only.id].score, 3)
        self.assertEqual(by_id[self.combined.id].likes_recibidos, 2)
        self.assertEqual(by_id[self.combined.id].comentarios_recibidos, 3)
        self.assertEqual(by_id[self.combined.id].score, 5)
        self.assertEqual(by_id[self.multiple.id].score, 4)
        tied_ids = [user.id for user in ranking if user.score == 5]
        self.assertEqual(tied_ids, sorted([self.combined.id, self.tied.id]))

    def test_dos_likes_mas_tres_comentarios_no_se_multiplican(self):
        combined = next(user for user in top_collectors() if user.id == self.combined.id)
        self.assertEqual(
            (combined.likes_recibidos, combined.comentarios_recibidos, combined.score),
            (2, 3, 5),
        )

    def test_limita_a_cinco_y_no_rellena_con_score_cero(self):
        users = get_user_model()
        for index in range(6):
            author = users.objects.create_user(username=f"ranked-{index}")
            post = Post.objects.create(user=author, contenido="Ranking")
            for actor in self.actors[: index % 5 + 1]:
                Comentario.objects.create(post=post, user=actor, contenido="Interacción")
        ranking = list(top_collectors())
        self.assertEqual(len(ranking), 5)
        self.assertTrue(all(user.score > 0 for user in ranking))
        self.assertEqual(
            [(user.score, user.id) for user in ranking],
            sorted(
                [(user.score, user.id) for user in ranking],
                key=lambda item: (-item[0], item[1]),
            ),
        )

    def test_ranking_se_resuelve_en_una_consulta(self):
        with self.assertNumQueries(1):
            self.assertGreater(len(list(top_collectors())), 0)


class MarketplaceNewsInsightTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.seller = users.objects.create_user(username="news-seller")
        self.viewer = users.objects.create_user(username="news-viewer")
        self.publications = []
        base_time = timezone.now() - timedelta(days=1)
        names = [
            ("Personalizada", "Catálogo 0"),
            ("", "Catálogo fallback"),
            ("   ", ""),
            ("Cuarta", "Catálogo 3"),
            ("Quinta", "Catálogo 4"),
        ]
        for index, (custom, catalog_name) in enumerate(names):
            publication = self.create_piece_publication(
                index, custom, catalog_name, "RESERVADA" if index == 3 else "ACTIVA"
            )
            PublicacionMarket.objects.filter(pk=publication.id).update(
                fecha_publicacion=base_time + timedelta(minutes=index)
            )
            publication.refresh_from_db()
            self.publications.append(publication)

        collection = ColeccionMaestra.objects.create(
            nombre="Colección real", categoria="General", propietario=self.seller
        )
        participation = ColeccionUsuario.objects.create(user=self.seller, coleccion=collection)
        collection_publication = PublicacionMarket.objects.create(
            vendedor=self.seller,
            coleccion_usuario=participation,
            precio="600",
            descripcion="Colección",
            condicion="USADA",
        )
        PublicacionMarket.objects.filter(pk=collection_publication.id).update(
            fecha_publicacion=base_time + timedelta(minutes=5)
        )
        collection_publication.refresh_from_db()
        self.publications.append(collection_publication)

        hidden = self.create_piece_publication(20, "Vendida", "Vendida", "VENDIDA")
        PublicacionMarket.objects.filter(pk=hidden.id).update(
            fecha_publicacion=base_time + timedelta(hours=2)
        )

    def create_piece_publication(self, index, custom, catalog_name, state):
        master = ColeccionMaestra.objects.create(
            nombre=f"Colección {index}", categoria="General", propietario=self.seller
        )
        participation = ColeccionUsuario.objects.create(user=self.seller, coleccion=master)
        catalog = PiezaCatalogo.objects.create(
            coleccion=master,
            numero_item=str(index),
            nombre=catalog_name,
            sku_base=f"NEWS-BASE-{index}",
        )
        piece = PiezaInventario.objects.create(
            user=self.seller,
            coleccion_usuario=participation,
            pieza_catalogo=catalog,
            nombre_personalizado=custom,
            sku=f"NEWS-{index}",
            estado_adquisicion="ADQUIRIDA",
            visibilidad="PRIVADA",
            condicion="NUEVA",
        )
        return PublicacionMarket.objects.create(
            vendedor=self.seller,
            pieza_inventario=piece,
            precio=str(100 + index),
            descripcion="Novedad",
            condicion="NUEVA",
            estado=state,
        )

    def test_novedades_limite_orden_nombres_tipos_y_estados(self):
        news = list(latest_marketplace_publications(self.viewer))
        self.assertEqual(len(news), 5)
        self.assertEqual(
            [item.id for item in news],
            [item.id for item in reversed(self.publications[1:])],
        )
        self.assertEqual(news[0].insight_tipo, "COLECCION")
        self.assertEqual(news[0].insight_nombre, "Colección real")
        by_id = {item.id: item for item in news}
        self.assertEqual(by_id[self.publications[1].id].insight_nombre, "Catálogo fallback")
        self.assertEqual(by_id[self.publications[2].id].insight_nombre, "Pieza sin nombre")
        self.assertTrue(any(item.estado == "RESERVADA" for item in news))
        self.assertFalse(any(item.estado in {"VENDIDA", "CANCELADA"} for item in news))
        self.assertFalse(any("#" in item.insight_nombre for item in news))

    def test_misma_fecha_desempata_por_id_descendente(self):
        same_time = timezone.now()
        ids = [self.publications[-1].id, self.publications[-2].id]
        PublicacionMarket.objects.filter(id__in=ids).update(fecha_publicacion=same_time)
        returned = [item.id for item in latest_marketplace_publications(self.viewer)]
        self.assertEqual(returned[:2], sorted(ids, reverse=True))

    def test_nombre_personalizado_tiene_prioridad(self):
        PublicacionMarket.objects.filter(pk=self.publications[0].id).update(
            fecha_publicacion=timezone.now()
        )
        first = latest_marketplace_publications(self.viewer)[0]
        self.assertEqual(first.insight_nombre, "Personalizada")

    def test_coleccion_sin_nombre_usa_fallback_amigable(self):
        collection = ColeccionMaestra.objects.create(
            nombre="", categoria="General", propietario=self.seller
        )
        participation = ColeccionUsuario.objects.create(
            user=self.seller, coleccion=collection
        )
        PublicacionMarket.objects.create(
            vendedor=self.seller,
            coleccion_usuario=participation,
            precio="50",
            descripcion="Sin nombre",
            condicion="USADA",
        )
        first = latest_marketplace_publications(self.viewer)[0]
        self.assertEqual(first.insight_nombre, "Colección sin nombre")
        self.assertNotIn("#", first.insight_nombre)

    def test_cero_publicaciones(self):
        PublicacionMarket.objects.all().delete()
        self.assertEqual(list(latest_marketplace_publications(self.viewer)), [])

    def test_numero_de_consultas_no_crece_de_uno_a_cinco(self):
        with self.assertNumQueries(1):
            list(latest_marketplace_publications(self.viewer, limit=1))
        with self.assertNumQueries(1):
            list(latest_marketplace_publications(self.viewer, limit=5))


class CommunitySummaryContractTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.author = users.objects.create_user(username="summary-author", email="private@example.com")
        self.actor = users.objects.create_user(username="summary-actor")
        post = Post.objects.create(user=self.author, contenido="Resumen")
        PostLike.objects.create(post=post, user=self.actor)
        master = ColeccionMaestra.objects.create(
            nombre="Resumen colección", categoria="General", propietario=self.author
        )
        participation = ColeccionUsuario.objects.create(user=self.author, coleccion=master)
        PublicacionMarket.objects.create(
            vendedor=self.author,
            coleccion_usuario=participation,
            precio="75",
            descripcion="Resumen",
            condicion="NUEVA",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.actor)

    def test_rest_ejecuta_dos_consultas_y_no_expone_datos_privados(self):
        with self.assertNumQueries(2):
            response = self.client.get("/api/v1/community/resumen/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["novedades_marketplace"]), 1)
        self.assertEqual(len(response.data["coleccionistas_top"]), 1)
        collector = response.data["coleccionistas_top"][0]
        self.assertEqual(set(collector), {
            "id", "nombre", "likes_recibidos", "comentarios_recibidos", "score"
        })
        self.assertNotIn("email", collector)

    def test_graphql_es_equivalente_a_rest_y_usa_dos_consultas(self):
        rest = self.client.get("/api/v1/community/resumen/").data
        request = RequestFactory().post("/graphql/")
        request.user = self.actor
        with self.assertNumQueries(2):
            result = schema.execute(
                '''{ novedadesMarketplace { id tipo nombre precio fechaPublicacion }
                     coleccionistasTop { id nombre likesRecibidos comentariosRecibidos score } }''',
                context_value=request,
            )
        self.assertIsNone(result.errors)
        self.assertEqual(
            [item["id"] for item in result.data["novedadesMarketplace"]],
            [str(item["id"]) for item in rest["novedades_marketplace"]],
        )
        self.assertEqual(
            result.data["coleccionistasTop"],
            [
                {
                    "id": str(item["id"]),
                    "nombre": item["nombre"],
                    "likesRecibidos": item["likes_recibidos"],
                    "comentariosRecibidos": item["comentarios_recibidos"],
                    "score": item["score"],
                }
                for item in rest["coleccionistas_top"]
            ],
        )
