# conftest.py — configuration pytest partagée
# Placé à la racine du dossier tests/

import pytest


def pytest_configure(config):
    """Marqueurs personnalisés pour filtrer les tests."""
    config.addinivalue_line("markers", "unit: tests unitaires (rapides, sans I/O)")
    config.addinivalue_line("markers", "e2e:  tests end-to-end (pipeline complet)")
    config.addinivalue_line("markers", "slow: tests lents (embeddings réels, GPU)")