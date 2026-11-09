from django.db.models import Q
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from config.permissions import IsResourceOwnerOrReadOnly
from .models import PublicacionMarket, Oferta
from .serializers import PublicacionMarketSerializer, OfertaSerializer
from .services import (
    accept_offer,
    complete_offer,
    filter_marketplace_publications,
    marketplace_publications_for,
    reject_offer,
)


class MarketplacePagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_page_size(self, request):
        raw_value = request.query_params.get(self.page_size_query_param)
        if raw_value is None:
            return self.page_size
        try:
            value = int(raw_value)
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError(
                {"page_size": ["Introduce un tamaño de página válido."]}
            ) from exc
        if value < 1 or value > self.max_page_size:
            raise serializers.ValidationError(
                {"page_size": [f"El tamaño de página debe estar entre 1 y {self.max_page_size}."]}
            )
        return value


class PublicacionMarketViewSet(viewsets.ModelViewSet):
    queryset = PublicacionMarket.objects.all()
    serializer_class = PublicacionMarketSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]
    pagination_class = MarketplacePagination

    def get_queryset(self):
        queryset = marketplace_publications_for(self.request.user)
        return filter_marketplace_publications(queryset, self.request.query_params)

    def perform_create(self, serializer):
        serializer.save(vendedor=self.request.user, estado="ACTIVA")

    def is_owner(self, obj, user):
        return obj.vendedor_id == user.id


class OfertaViewSet(viewsets.ModelViewSet):
    queryset = Oferta.objects.all()
    serializer_class = OfertaSerializer

    def get_queryset(self):
        return Oferta.objects.filter(
            Q(comprador=self.request.user)
            | Q(publicacion__vendedor=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(comprador=self.request.user, estado="PENDIENTE")

    def _transition_response(self, offer):
        return Response(self.get_serializer(offer).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def aceptar(self, request, pk=None):
        return self._transition_response(accept_offer(pk, request.user))

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        return self._transition_response(reject_offer(pk, request.user))

    @action(detail=True, methods=["post"])
    def completar(self, request, pk=None):
        return self._transition_response(complete_offer(pk, request.user))
