import graphene
from graphene import ObjectType, String, Field, List, Mutation, Int, Float, InputObjectType
from graphene_django import DjangoObjectType
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order

# --- Types ---
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")

class ProductType(graphene.ObjectType):
    id = Int()
    name = String()
    price = Float()
    stock = Int()

class OrderType(graphene.ObjectType):
    id = Int()
    customer = Field(CustomerType)
    products = List(ProductType)
    total_amount = Float()
    order_date = String()

# --- Inputs ---
class CustomerInput(InputObjectType):
    name = String(required=True)
    email = String(required=True)
    phone = String()

class ProductInput(InputObjectType):
    name = String(required=True)
    price = Float(required=True)
    stock = Int()

class OrderInput(InputObjectType):
    customer_id = Int(required=True)
    product_ids = List(Int, required=True)
    order_date = String()

# --- Mutations ---
class CreateCustomer(Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = Field(CustomerType)
    message = String()

    def mutate(self, info, input):
        # Email validation
        try:
            validate_email(input.email)
        except ValidationError:
            return CreateCustomer(message="Invalid email format.")
        if Customer.objects.filter(email=input.email).exists():
            return CreateCustomer(message="Email already exists.")
        # Phone validation (simple example)
        if input.phone and not (input.phone.startswith('+') or '-' in input.phone):
            return CreateCustomer(message="Invalid phone format.")
        customer = Customer.objects.create(
            name=input.name,
            email=input.email,
            phone=input.phone or ""
        )
        return CreateCustomer(customer=customer, message="Customer created successfully.")

class BulkCreateCustomers(Mutation):
    class Arguments:
        input = List(CustomerInput, required=True)

    customers = List(CustomerType)
    errors = List(String)

    @classmethod
    def mutate(cls, root, info, input):
        created = []
        errors = []
        with transaction.atomic():
            for idx, data in enumerate(input):
                try:
                    validate_email(data.email)
                    if Customer.objects.filter(email=data.email).exists():
                        errors.append(f"Row {idx+1}: Email already exists.")
                        continue
                    if data.phone and not (data.phone.startswith('+') or '-' in data.phone):
                        errors.append(f"Row {idx+1}: Invalid phone format.")
                        continue
                    customer = Customer.objects.create(
                        name=data.name,
                        email=data.email,
                        phone=data.phone or ""
                    )
                    created.append(customer)
                except Exception as e:
                    errors.append(f"Row {idx+1}: {str(e)}")
        return BulkCreateCustomers(customers=created, errors=errors)

class CreateProduct(Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = Field(ProductType)

    def mutate(self, info, input):
        if input.price <= 0:
            raise Exception("Price must be positive.")
        if input.stock is not None and input.stock < 0:
            raise Exception("Stock cannot be negative.")
        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock or 0
        )
        return CreateProduct(product=product)

class CreateOrder(Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = Field(OrderType)

    def mutate(self, info, input):
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID.")
        if not input.product_ids:
            raise Exception("At least one product must be selected.")
        products = Product.objects.filter(id__in=input.product_ids)
        if products.count() != len(input.product_ids):
            raise Exception("One or more product IDs are invalid.")
        order = Order.objects.create(
            customer=customer,
            order_date=input.order_date or None
        )
        order.products.set(products)
        total = sum([p.price for p in products])
        order.total_amount = total
        order.save()
        return CreateOrder(order=order)

# --- Mutation Root ---
class Mutation(ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

# --- Query Root ---
class Query(ObjectType):
    hello = String(default_value="Hello, GraphQL!")
    all_customers = graphene.List(CustomerType)
    
    def resolve_all_customers(self, info):
        return Customer.objects.all()