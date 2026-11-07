from odoo.exceptions import AccessDenied, ValidationError
from odoo.tests import TransactionCase, tagged

from ..models.res_users import normalize_email_login


@tagged("post_install", "-at_install")
class TestEmailLogin(TransactionCase):
    def test_normalization_preserves_local_part(self):
        self.assertEqual(
            normalize_email_login("  Mixed.Local@EXAMPLE.ORG  "),
            "Mixed.Local@example.org",
        )

    def test_invalid_values_are_rejected(self):
        for value in ("admin", "agent@", "@example.org", "", " "):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                normalize_email_login(value)

    def test_authentication_rejects_invalid_login_syntax_generically(self):
        with self.assertRaises(AccessDenied):
            self.env.registry["res.users"]._login(
                self.env.cr.dbname, "@example.org", "unused-test-value", {}
            )

    def test_create_requires_valid_login(self):
        with self.assertRaises(ValidationError):
            self.env["res.users"].with_context(no_reset_password=True).create({
                "name": "Synthetic invalid fixture",
                "login": "simple-user-name",
            })

    def test_create_trims_and_normalizes_domain(self):
        user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Synthetic email fixture",
            "login": "  fixture.user@example.TEST  ",
        })
        self.assertEqual(user.login, "fixture.user@example.test")

    def test_write_rejects_invalid_login(self):
        user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Synthetic write fixture",
            "login": "write.fixture@example.test",
        })
        with self.assertRaises(ValidationError):
            user.write({"login": "not-an-email"})

    def test_case_insensitive_duplicate_is_rejected(self):
        self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Synthetic duplicate fixture one",
            "login": "duplicate@example.test",
        })
        with self.assertRaises(ValidationError):
            self.env["res.users"].with_context(no_reset_password=True).create({
                "name": "Synthetic duplicate fixture two",
                "login": "DUPLICATE@EXAMPLE.TEST",
            })

