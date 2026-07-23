import builtins
import importlib
import os
import unittest
from unittest.mock import patch

from django.test import TestCase


class ManageTests(TestCase):
    def test_main_levanta_erro_se_django_nao_disponivel(self):
        import manage

        import_original = builtins.__import__

        def falha_import(*args, **kwargs):
            if args[0] == "django.core.management":
                raise ImportError("django nao instalado")
            return import_original(*args, **kwargs)

        with patch("builtins.__import__", side_effect=falha_import):
            with self.assertRaises(ImportError) as ctx:
                manage.main()
            self.assertIn("Django", str(ctx.exception))
            # Exercita o fallback do helper de mock
            self.assertIsInstance(falha_import("unittest"), type(unittest))


class SettingsTests(TestCase):
    def test_allowed_hosts_adiciona_localhosts_quando_env_tem_hosts(self):
        with patch.dict(os.environ, {"DJANGO_ALLOWED_HOSTS": "example.com"}):
            settings = importlib.import_module("financeiro.settings")
            importlib.reload(settings)
            self.assertIn("example.com", settings.ALLOWED_HOSTS)
            self.assertIn("localhost", settings.ALLOWED_HOSTS)
            self.assertIn("127.0.0.1", settings.ALLOWED_HOSTS)
        # Restaura com env vazio para os demais testes
        with patch.dict(os.environ, {"DJANGO_ALLOWED_HOSTS": ""}, clear=False):
            importlib.reload(importlib.import_module("financeiro.settings"))
