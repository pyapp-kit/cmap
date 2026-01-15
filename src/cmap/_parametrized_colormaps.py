"""Registry of parametrized colormap functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from .data.cubehelix import cubehelix

if TYPE_CHECKING:
    from typing import Any

    import numpy as np

    LutCallable = Callable[[np.ndarray], np.ndarray]

# Registry of colormap functions that accept parameters
FUNCTION_REGISTRY: dict[str, Callable[..., Any]] = {
    "cubehelix": cubehelix,
}


def get_parametrized_colormap_function(name: str) -> Callable[..., Any]:
    """
    Get a parametrized colormap function by name.

    Args:
        name: Name of the colormap function

    Returns
    -------
        The colormap function

    Raises
    ------
        ValueError: If the function name is not in the registry
    """
    if name not in FUNCTION_REGISTRY:
        available = ", ".join(sorted(FUNCTION_REGISTRY.keys()))
        raise ValueError(
            f"Unknown colormap function: {name!r}. Available functions: {available}"
        )
    return FUNCTION_REGISTRY[name]
