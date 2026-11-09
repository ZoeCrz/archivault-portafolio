import graphene
import apps.accounts.schema
import apps.catalog.schema
import apps.marketplace.schema
import apps.community.schema

class Query(
    apps.accounts.schema.Query,
    apps.catalog.schema.Query,
    apps.marketplace.schema.Query,
    apps.community.schema.Query,
    graphene.ObjectType
):
    pass

class Mutation(
    apps.accounts.schema.Mutation,
    apps.catalog.schema.Mutation,
    apps.marketplace.schema.Mutation,
    apps.community.schema.Mutation,
    graphene.ObjectType,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
