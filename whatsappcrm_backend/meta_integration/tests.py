from django.test import SimpleTestCase, TestCase

# Create your tests here.


class WebhookSignatureTests(SimpleTestCase):
    """X-Hub-Signature-256 is HMAC-SHA256 of the raw body with the Meta App Secret."""

    def _sign(self, secret, body):
        import hashlib
        import hmac
        return 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    def test_valid_signature_passes_even_with_pasted_whitespace(self):
        from meta_integration.views import MetaWebhookAPIView
        body = b'{"object":"whatsapp_business_account"}'
        sig = self._sign('abc123secret', body)
        view = MetaWebhookAPIView()
        self.assertTrue(view._verify_signature(body, sig, 'abc123secret'))
        self.assertTrue(view._verify_signature(body, sig, '  abc123secret\n'))

    def test_wrong_secret_fails(self):
        from meta_integration.views import MetaWebhookAPIView
        body = b'{"object":"whatsapp_business_account"}'
        self.assertFalse(MetaWebhookAPIView()._verify_signature(body, self._sign('other', body), 'abc123secret'))
