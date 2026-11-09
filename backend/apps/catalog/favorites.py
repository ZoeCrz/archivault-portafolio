from apps.marketplace.services import visible_publications_for


def can_access_favorite_piece(user, piece):
    if piece.user_id == user.id or piece.visibilidad == "PUBLICA":
        return True
    return visible_publications_for(user).filter(pieza_inventario=piece).exists()


def can_access_favorite_collection(user, collection):
    if (
        collection.tipo == "global"
        or collection.propietario_id == user.id
        or collection.coleccionusuario_set.filter(user=user).exists()
    ):
        return True
    return visible_publications_for(user).filter(
        coleccion_usuario__coleccion=collection
    ).exists()


def favorite_is_available(favorite, user):
    if favorite.pieza_inventario_id:
        return can_access_favorite_piece(user, favorite.pieza_inventario)
    return can_access_favorite_collection(user, favorite.coleccion_maestra)
