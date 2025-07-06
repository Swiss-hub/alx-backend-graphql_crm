# alx-backend-graphql_crm

This project is a Django application that sets up a GraphQL endpoint using `graphene-django`. It serves as a simple introduction to building GraphQL APIs with Django.

## Project Structure

```
alx-backend-graphql_crm
├── alx_backend_graphql_crm
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── schema.py
├── crm
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── manage.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd alx-backend-graphql_crm
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required libraries:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the migrations:**

   ```bash
   python manage.py migrate
   ```

5. **Start the development server:**

   ```bash
   python manage.py runserver
   ```

6. **Access the GraphQL endpoint:**

   Open your browser and visit: [http://localhost:8000/graphql](http://localhost:8000/graphql)

## Usage

You can test the GraphQL endpoint by running the following query:

```graphql
{
  hello
}
```

This should return:

```json
{
  "data": {
    "hello": "Hello, GraphQL!"
  }
}
```

## License

This project is licensed under the MIT License.