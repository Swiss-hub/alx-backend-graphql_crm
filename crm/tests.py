from django.test import TestCase
from graphene.test import Client
from .schema import schema

class HelloWorldTestCase(TestCase):
    def setUp(self):
        self.client = Client(schema)

    def test_hello_query(self):
        query = '{ hello }'
        response = self.client.execute(query)
        self.assertEqual(response['data']['hello'], 'Hello, GraphQL!')