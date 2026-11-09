import unittest

from app.api.health import get_health
from app.main import app


class HealthEndpointTests(unittest.TestCase):
    def test_health_returns_service_status(self) -> None:
        self.assertEqual(
            get_health(),
            {
                "status": "UP",
                "service": "n42-api",
                "version": "0.1.0",
            },
        )

    def test_health_route_is_registered(self) -> None:
        paths = set(app.openapi()["paths"])
        self.assertIn("/api/health", paths)


if __name__ == "__main__":
    unittest.main()
