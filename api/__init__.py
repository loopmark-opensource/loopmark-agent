"""Optional REST API for the marketing agent (install with `pip install loopmark-agent[api]`)."""

from api.app import create_app

__all__ = ["create_app"]
