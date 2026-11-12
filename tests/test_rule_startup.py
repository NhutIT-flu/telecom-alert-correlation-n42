import asyncio
import importlib

import pytest
from pydantic import ValidationError

main = importlib.import_module("app.main")


def test_startup_loads_disabled_catalog() -> None:
    async def startup() -> None:
        async with main.app.router.lifespan_context(main.app):
            config = main.app.state.rule_configuration
            assert config.version == "0.1.1"
            assert len(config.rules) == 3
            assert all(not rule.enabled for rule in config.rules)

    asyncio.run(startup())


def test_startup_rejects_invalid_catalog(tmp_path, monkeypatch) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text('version: "0.1.1"\nrules: []\n', encoding="utf-8")
    monkeypatch.setattr(main, "RULES_PATH", path)

    async def startup() -> None:
        async with main.app.router.lifespan_context(main.app):
            pytest.fail("startup must not serve with invalid configuration")

    with pytest.raises(ValidationError):
        asyncio.run(startup())
