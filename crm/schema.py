import graphene
from graphene import ObjectType, String, Field, List, Mutation, Int, Float, InputObjectType
from graphene_django import DjangoObjectType, DjangoFilterConnectionField
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
import re
from django.utils import timezone

# --- Types ---
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")
        filterset_class = CustomerFilter

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        filterset_class = ProductFilter

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")
        filterset_class = OrderFilter

# --- Inputs ---
class CustomerInput(InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int()

class OrderInput(InputObjectType):
    customer_id = graphene.Int(required=True)
    product_ids = graphene.List(graphene.Int, required=True)
    order_date = graphene.String()

# --- Mutations ---
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        # Email validation
        try:
            validate_email(input.email)
        except ValidationError:
            return CreateCustomer(message="Invalid email format.")
        if Customer.objects.filter(email=input.email).exists():
            return CreateCustomer(message="Email already exists.")
        # Phone validation (simple example: +1234567890 or 123-456-7890)
        if input.phone:
            if not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', input.phone):
                return CreateCustomer(message="Invalid phone format.")
        customer = Customer.objects.create(
            name=input.name,
            email=input.email,
            phone=input.phone or ""
        )
        return CreateCustomer(customer=customer, message="Customer created successfully.")

class BulkCreateCustomers(graphene.Mutation):
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
                    if data.phone and not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', data.phone):
                        errors.append(f"Row {idx+1}: Invalid phone format.")
                        continue
                    customer = Customer.objects.create(
                        name=data.name,
                        email=data.email,
                        phone=data.phone or ""
                    )
                    created.append(customer)
                except ValidationError:
                    errors.append(f"Row {idx+1}: Invalid email format.")
                except Exception as e:
                    errors.append(f"Row {idx+1}: {str(e)}")
        return BulkCreateCustomers(customers=created, errors=errors)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = Field(ProductType)
    message = String()

    def mutate(self, info, input):
        if input.price is None or input.price <= 0:
            return CreateProduct(message="Price must be positive.")
        if input.stock is not None and input.stock < 0:
            return CreateProduct(message="Stock cannot be negative.")
        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock or 0
        )
        return CreateProduct(product=product, message="Product created successfully.")

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = Field(OrderType)
    message = String()

    def mutate(self, info, input):
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(message="Invalid customer ID.")
        if not input.product_ids:
            return CreateOrder(message="At least one product must be selected.")
        products = Product.objects.filter(id__in=input.product_ids)
        if products.count() != len(input.product_ids):
            return CreateOrder(message="One or more product IDs are invalid.")
        order = Order.objects.create(
            customer=customer,
            order_date=input.order_date or timezone.now()
        )
        order.products.set(products)
        total = sum([p.price for p in products])
        order.total_amount = total
        order.save()
        return CreateOrder(order=order, message="Order created successfully.")

# --- Mutation Root ---
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

# --- Query Root ---
class Query(graphene.ObjectType):
    hello = String(default_value="Hello, GraphQL!")
    
    # Filtered queries using DjangoFilterConnectionField
    all_customers = DjangoFilterConnectionField(CustomerType)
    all_products = DjangoFilterConnectionField(ProductType)
    all_orders = DjangoFilterConnectionField(OrderType)
    
    # Legacy simple query for backward compatibility
    customers = graphene.List(CustomerType)
    
    def resolve_customers(self, info):
        return Customer.objects.all()