"""
Locust load testing script for Marketplace API.
Simulates realistic user behavior with product browsing, searching, and transactions.
"""
import random
import json
from locust import HttpUser, task, between, events
from faker import Faker

fake = Faker()


class MarketplaceUser(HttpUser):
    """
    Simulates a marketplace user with realistic behavior patterns.
    """

    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Called when a simulated user starts."""
        self.user_id = None
        self.auth_token = None
        self.products = []
        self.categories = []

        # 70% of users register/login, 30% browse anonymously
        if random.random() < 0.7:
            self.register_and_login()

    def register_and_login(self):
        """Register a new user and login."""
        # Generate fake user data
        email = fake.email()
        username = fake.user_name() + str(random.randint(1000, 9999))
        password = "Test123456!"

        # Register
        register_data = {
            "email": email,
            "username": username,
            "password": password,
            "full_name": fake.name(),
            "phone": fake.phone_number(),
            "location": fake.city(),
        }

        with self.client.post(
            "/api/v1/auth/register",
            json=register_data,
            catch_response=True,
            name="/api/v1/auth/register"
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 400:
                # User already exists, that's ok
                response.success()

        # Login
        login_data = {
            "email": email,
            "password": password,
        }

        with self.client.post(
            "/api/v1/auth/login",
            json=login_data,
            catch_response=True,
            name="/api/v1/auth/login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                response.success()

    @property
    def auth_headers(self):
        """Return authorization headers."""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    @task(10)
    def browse_products(self):
        """Browse products - most common action."""
        params = {
            "page": random.randint(1, 5),
            "page_size": random.choice([10, 20, 50]),
        }

        with self.client.get(
            "/api/v1/products/",
            params=params,
            catch_response=True,
            name="/api/v1/products/ [browse]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    self.products = data["items"]
                response.success()

    @task(5)
    def search_products(self):
        """Search for products."""
        search_terms = [
            "laptop", "phone", "camera", "bike", "furniture",
            "book", "clothes", "shoes", "watch", "headphones"
        ]

        params = {
            "search": random.choice(search_terms),
            "page": 1,
            "page_size": 20,
        }

        with self.client.get(
            "/api/v1/products/",
            params=params,
            catch_response=True,
            name="/api/v1/products/ [search]"
        ) as response:
            if response.status_code == 200:
                response.success()

    @task(8)
    def view_product_detail(self):
        """View a specific product."""
        if self.products:
            product = random.choice(self.products)
            product_id = product["id"]
        else:
            product_id = random.randint(1, 100)

        with self.client.get(
            f"/api/v1/products/{product_id}",
            catch_response=True,
            name="/api/v1/products/{id}"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()

    @task(3)
    def create_product(self):
        """Create a new product listing (authenticated users only)."""
        if not self.auth_token:
            return

        product_data = {
            "title": f"{fake.word().capitalize()} {fake.word().capitalize()}",
            "description": fake.text(max_nb_chars=200),
            "price": round(random.uniform(10, 1000), 2),
            "condition": random.choice(["new", "like_new", "good", "fair"]),
            "category_id": random.randint(1, 10),
            "location": fake.city(),
            "is_negotiable": random.choice([True, False]),
        }

        with self.client.post(
            "/api/v1/products/",
            json=product_data,
            headers=self.auth_headers,
            catch_response=True,
            name="/api/v1/products/ [create]"
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code in [401, 422]:
                response.success()

    @task(2)
    def initiate_transaction(self):
        """Initiate a transaction (purchase)."""
        if not self.auth_token or not self.products:
            return

        product = random.choice(self.products)

        transaction_data = {
            "product_id": product["id"],
            "amount": product["price"],
            "payment_method": random.choice(["cash", "card", "bank_transfer"]),
            "buyer_notes": "Interested in buying this item.",
        }

        with self.client.post(
            "/api/v1/transactions/",
            json=transaction_data,
            headers=self.auth_headers,
            catch_response=True,
            name="/api/v1/transactions/ [create]"
        ) as response:
            if response.status_code in [201, 400, 401, 404]:
                response.success()

    @task(2)
    def send_message(self):
        """Send a message to another user."""
        if not self.auth_token:
            return

        message_data = {
            "receiver_id": random.randint(1, 100),
            "content": fake.sentence(nb_words=10),
            "product_id": random.randint(1, 50),
        }

        with self.client.post(
            "/api/v1/messages/",
            json=message_data,
            headers=self.auth_headers,
            catch_response=True,
            name="/api/v1/messages/ [send]"
        ) as response:
            if response.status_code in [201, 400, 401]:
                response.success()

    @task(1)
    def check_messages(self):
        """Check received messages."""
        if not self.auth_token:
            return

        with self.client.get(
            "/api/v1/messages/",
            headers=self.auth_headers,
            catch_response=True,
            name="/api/v1/messages/ [list]"
        ) as response:
            if response.status_code in [200, 401]:
                response.success()

    @task(1)
    def health_check(self):
        """Health check endpoint."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                response.success()


class HeavyUser(HttpUser):
    """
    Simulates heavy users who create lots of traffic.
    Used for stress testing.
    """

    wait_time = between(0.1, 0.5)  # Very short wait time
    weight = 1  # Lower weight compared to normal users

    @task
    def rapid_fire_requests(self):
        """Make rapid requests to stress test the system."""
        endpoints = [
            "/health",
            "/api/v1/products/?page=1",
            "/api/v1/products/1",
        ]

        endpoint = random.choice(endpoints)
        self.client.get(endpoint, name="[stress test]")


# Event listeners for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts."""
    print("Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    print("Load test completed.")
    print(f"Total users: {environment.runner.user_count}")
