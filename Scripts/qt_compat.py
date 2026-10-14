"""Qt compatibility shim for Prism's Kitsu plugin.

Tries PySide6, then PySide2, then legacy PySide. Raises a clear
ModuleNotFoundError if none are available.

For headless debugging environments, set ``PRISM_QT_COMPAT=stub`` to load
minimal stub objects so the modules can be imported without real Qt
bindings. The stub should only be used for non-UI checks because it won't
render widgets.
"""
"""Qt compatibility shim for Prism 2 (PySide6 / qtpy) and legacy PySide2."""
from __future__ import annotations

try:
    from qtpy import QtCore, QtGui, QtWidgets
    from qtpy.QtCore import *
    from qtpy.QtGui import *
    from qtpy.QtWidgets import *
    qt_binding = "qtpy"
except ImportError:
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
        from PySide6.QtCore import *
        from PySide6.QtGui import *
        from PySide6.QtWidgets import *
        qt_binding = "PySide6"
    except ImportError:
        from PySide2 import QtCore, QtGui, QtWidgets
        from PySide2.QtCore import *
        from PySide2.QtGui import *
        from PySide2.QtWidgets import *
        qt_binding = "PySide2"

# Đảm bảo tương thích ngược cho các lệnh gọi .exec_() trên PySide6
for _cls in (QDialog, QMessageBox, QMenu):
    if not hasattr(_cls, "exec_") and hasattr(_cls, "exec"):
        setattr(_cls, "exec_", getattr(_cls, "exec"))

def _import_binding(binding: str) -> Tuple[ModuleType, ModuleType, ModuleType]:
    """Return QtCore, QtGui, QtWidgets modules for the given binding."""
    core = import_module(f"{binding}.QtCore")
    gui = import_module(f"{binding}.QtGui")
    try:
        widgets = import_module(f"{binding}.QtWidgets")
    except (ModuleNotFoundError, ImportError):
        if binding == "PySide":
            widgets = gui
        else:
            raise
    return core, gui, widgets


def _populate_globals(modules: Iterable[ModuleType]):
    for module in modules:
        for name in getattr(module, "__all__", dir(module)):
            if name.startswith("_"):
                continue
            globals()[name] = getattr(module, name)
            __all__.append(name)


def _load_qt_binding():
    if os.getenv("PRISM_QT_COMPAT", "").lower() == "stub":
        warnings.warn(
            "Using Qt stub bindings. UI functionality is disabled."
        )

        class _QtStub:
            def __init__(self, *_args, **_kwargs):
                pass

            def __call__(self, *_args, **_kwargs):
                return self

            def __getattr__(self, _name):
                return self

        stub_value = _QtStub()

        def _make_stub_module(name: str, exports: Iterable[str]) -> ModuleType:
            module = ModuleType(name)
            for attr in exports:
                setattr(module, attr, stub_value)

            def __getattr__(_self, _attr):
                return stub_value

            module.__getattr__ = __getattr__  # type: ignore[attr-defined]
            module.__all__ = list(exports)
            return module

        core = _make_stub_module("QtCore", ["Qt", "QCoreApplication", "QMetaObject"])
        gui = _make_stub_module("QtGui", ["QAction", "QIcon", "QPixmap", "QSizePolicy"])
        widgets = _make_stub_module(
            "QtWidgets",
            [
                "QAbstractItemView",
                "QAction",
                "QCheckBox",
                "QComboBox",
                "QDialog",
                "QDialogButtonBox",
                "QFormLayout",
                "QGroupBox",
                "QHBoxLayout",
                "QLabel",
                "QLineEdit",
                "QListWidget",
                "QListWidgetItem",
                "QMenu",
                "QMessageBox",
                "QPlainTextEdit",
                "QPushButton",
                "QTableWidget",
                "QTableWidgetItem",
                "QTreeWidget",
                "QTreeWidgetItem",
                "QVBoxLayout",
                "QWidget",
            ],
        )
        _populate_globals((core, gui, widgets))
        return "stub", core, gui, widgets

    last_exc: Exception | None = None
    for binding in ("PySide6", "PySide2", "PySide"):
        try:
            core, gui, widgets = _import_binding(binding)
            _populate_globals((core, gui, widgets))
            return binding, core, gui, widgets
        except (ModuleNotFoundError, ImportError) as exc:
            last_exc = exc
            continue
    raise ModuleNotFoundError(
        "No compatible Qt bindings found (PySide6/PySide2/PySide)"
    ) from last_exc


qt_binding, QtCore, QtGui, QtWidgets = _load_qt_binding()
