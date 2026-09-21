import unittest
from unittest.mock import AsyncMock, patch

from app.security.url_validator import (
    MonitorUrlRejectedError,
    validate_monitor_url,
    validate_monitor_url_syntax,
)


class MonitorUrlSyntaxTests(unittest.TestCase):
    def test_accepts_credential_free_http_and_https_urls(self):
        http_target = validate_monitor_url_syntax(
            "http://example.com/health"
        )
        https_target = validate_monitor_url_syntax(
            "https://example.com:8443/health"
        )

        self.assertEqual(http_target.hostname, "example.com")
        self.assertEqual(http_target.port, 80)
        self.assertEqual(https_target.port, 8443)

    def test_rejects_non_web_schemes_and_embedded_credentials(self):
        invalid_urls = (
            "file:///etc/passwd",
            "ftp://example.com/file",
            "gopher://example.com/resource",
            "data:text/plain,hello",
            "http://admin:password@example.com",
            "http://admin@example.com",
        )

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(MonitorUrlRejectedError):
                    validate_monitor_url_syntax(url)

    def test_rejects_parser_ambiguity_and_invalid_ports(self):
        invalid_urls = (
            "http://example.com\\@127.0.0.1",
            "http://example.com:70000",
            "http://example.com:0",
        )

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(MonitorUrlRejectedError):
                    validate_monitor_url_syntax(url)


class MonitorUrlNetworkTests(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_public_literal_addresses(self):
        await validate_monitor_url("https://8.8.8.8/health")
        await validate_monitor_url("https://[2001:4860:4860::8888]/health")

    async def test_rejects_non_public_literal_addresses(self):
        invalid_urls = (
            "http://127.0.0.1",
            "http://10.0.0.1",
            "http://192.168.1.1",
            "http://169.254.169.254",
            "http://0.0.0.0",
            "http://224.0.0.1",
            "http://[::1]",
            "http://[fc00::1]",
            "http://[fe80::1]",
            "http://[ff02::1]",
        )

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(MonitorUrlRejectedError):
                    await validate_monitor_url(url)

    async def test_accepts_hostname_when_every_address_is_public(self):
        with patch(
            "app.security.url_validator._resolve_hostname",
            AsyncMock(return_value=("8.8.8.8", "1.1.1.1")),
        ):
            await validate_monitor_url("https://example.com/health")

    async def test_rejects_hostname_when_any_address_is_non_public(self):
        with patch(
            "app.security.url_validator._resolve_hostname",
            AsyncMock(return_value=("8.8.8.8", "127.0.0.1")),
        ):
            with self.assertRaises(MonitorUrlRejectedError):
                await validate_monitor_url("https://example.com/health")


if __name__ == "__main__":
    unittest.main()
