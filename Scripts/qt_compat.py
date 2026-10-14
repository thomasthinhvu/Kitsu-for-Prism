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
