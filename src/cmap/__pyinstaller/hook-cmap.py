from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all(
    "cmap",
    # include_datas=["data/"],
    exclude_datas=["**/__pycache__/"],
    # filter_submodules=lambda x: x.startswith("cmap.data"),
)
excludedimports = [
    "bokeh",
    "colorspacious",
    "matplotlib",
    "napari",
    "numpy.typing",
    "pydantic_core",
    "pydantic",
    "numba",
    "pygfx",
    "pyqtgraph",
    "tkinter",
    "typing_extensions",
    "viscm",
    "vispy",
]
