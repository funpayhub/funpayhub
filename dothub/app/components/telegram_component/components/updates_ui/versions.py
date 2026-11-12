from __future__ import annotations


__all__ = ['release_url', 'releases_url']

from packaging.version import Version


def releases_url(repo_url: str) -> str:
    return f'{repo_url.rstrip("/")}/releases'


def release_url(repo_url: str, version: Version | str) -> str:
    """GitHub release page of a version (tags are ``vX.Y.Z``)."""
    version = Version(str(version))
    return f'{releases_url(repo_url)}/tag/v{version.major}.{version.minor}.{version.micro}'
