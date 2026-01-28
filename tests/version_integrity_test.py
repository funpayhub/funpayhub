from __future__ import annotations

import tomllib

from pytest import fixture
from packaging.version import Version

from funpayhub.app.properties import FunPayHubProperties


@fixture
def pyproject_version() -> Version:
    with open('pyproject.toml', 'rb') as f:
        data = tomllib.load(f)

    return Version(data['project']['version'])


def test_version_integrity(pyproject_version: Version) -> None:
    properties = FunPayHubProperties()
    assert pyproject_version == Version(properties.version.value)
