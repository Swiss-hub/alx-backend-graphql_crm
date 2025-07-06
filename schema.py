from graphene import ObjectType, String

class Query(ObjectType):
    hello = String(default_value="Hello, GraphQL!")