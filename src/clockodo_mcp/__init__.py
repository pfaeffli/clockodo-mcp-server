try:
    from ._version import version as __version__  # type: ignore
except ImportError:
    try:
        from importlib.metadata import version as _version

        __version__ = _version("clockodo-mcp")
    except Exception:  # pylint: disable=broad-exception-caught
        __version__ = "unknown"

__all__ = ["__version__"]
