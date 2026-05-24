from __future__ import annotations

import pytest

from bot import polar_client


def test_build_downloadable_payloads_is_network_free(tmp_path):
    path = tmp_path / "starter.zip"
    path.write_bytes(b"starter-kit")

    payload = polar_client.build_downloadable_payloads(str(path), "AI NOWA OS Starter Kit v0.1")

    assert payload["computed"]["size_bytes"] == len(b"starter-kit")
    assert payload["computed"]["part_count"] == 1
    assert payload["file_payload"]["service"] == "downloadable"
    assert payload["benefit_payload"]["type"] == "downloadables"
    assert payload["benefit_payload"]["properties"]["files"] == ["<FILE_ID_AFTER_UPLOAD>"]


def test_production_attach_requires_explicit_confirmation(tmp_path):
    path = tmp_path / "starter.zip"
    path.write_bytes(b"starter-kit")

    with pytest.raises(SystemExit, match="Production attach requires"):
        polar_client.main([
            "attach-downloadable",
            "--product-id",
            "prod_123",
            "--file",
            str(path),
            "--live",
        ])
