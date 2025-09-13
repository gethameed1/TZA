from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QDockWidget,
    QWidget,
    QFormLayout,
    QLineEdit,
    QColorDialog,
    QPushButton,
    QToolBar,
)

from .canvas_view import CanvasView
from .serializer import serialize_scene_to_dict, load_scene_from_dict


class PropertyEditor(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._title_edit = QLineEdit(self)
        self._color_button = QPushButton("Pick Color", self)
        layout = QFormLayout(self)
        layout.addRow("Title", self._title_edit)
        layout.addRow("Fill", self._color_button)
        self._current_item = None
        self._title_edit.editingFinished.connect(self._apply_title)
        self._color_button.clicked.connect(self._pick_color)

    def bind_item(self, item) -> None:
        self._current_item = item
        if item is None:
            self._title_edit.setText("")
            self._color_button.setEnabled(False)
            self._title_edit.setEnabled(False)
        else:
            self._title_edit.setText(item.get_title())
            self._color_button.setEnabled(True)
            self._title_edit.setEnabled(True)

    def _apply_title(self) -> None:
        if self._current_item is not None:
            self._current_item.set_title(self._title_edit.text())

    def _pick_color(self) -> None:
        if self._current_item is None:
            return
        color = QColorDialog.getColor(self._current_item.fill_color(), self, "Choose Fill Color")
        if color.isValid():
            self._current_item.set_fill_color(color)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FlowDraw")
        self.resize(QSize(1200, 800))

        self.view = CanvasView(self)
        self.setCentralWidget(self.view)

        # Property dock
        self.property_editor = PropertyEditor(self)
        dock = QDockWidget("Properties", self)
        dock.setWidget(self.property_editor)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        self._build_actions()
        self._build_menus_and_toolbars()

        self.view.scene().selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self) -> None:
        item = self.view.get_single_selected_node()
        self.property_editor.bind_item(item)

    def _build_actions(self) -> None:
        self.action_new = QAction("New", self)
        self.action_open = QAction("Open...", self)
        self.action_save = QAction("Save", self)
        self.action_save_as = QAction("Save As...", self)
        self.action_export_png = QAction("Export PNG...", self)
        self.action_export_svg = QAction("Export SVG...", self)
        self.action_quit = QAction("Quit", self)

        self.action_mode_select = QAction(QIcon.fromTheme("select"), "Select", self)
        self.action_mode_pan = QAction(QIcon.fromTheme("pan"), "Pan", self)
        self.action_mode_add = QAction(QIcon.fromTheme("list-add"), "Add Node", self)
        self.action_mode_connect = QAction(QIcon.fromTheme("connect"), "Connect", self)

        self.action_fit = QAction("Fit", self)
        self.action_delete = QAction("Delete", self)

        # Shortcuts
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_quit.setShortcut(QKeySequence.StandardKey.Quit)
        self.action_delete.setShortcut(QKeySequence(Qt.Key_Delete))

        # Triggers
        self.action_new.triggered.connect(self.new_file)
        self.action_open.triggered.connect(self.open_dialog)
        self.action_save.triggered.connect(self.save)
        self.action_save_as.triggered.connect(self.save_as)
        self.action_export_png.triggered.connect(self.export_png)
        self.action_export_svg.triggered.connect(self.export_svg)
        self.action_quit.triggered.connect(self.close)

        self.action_mode_select.triggered.connect(lambda: self.view.set_mode("select"))
        self.action_mode_pan.triggered.connect(lambda: self.view.set_mode("pan"))
        self.action_mode_add.triggered.connect(lambda: self.view.set_mode("add"))
        self.action_mode_connect.triggered.connect(lambda: self.view.set_mode("connect"))

        self.action_fit.triggered.connect(self.view.fit_to_scene)
        self.action_delete.triggered.connect(self.view.delete_selected)

        self._filename: Optional[Path] = None

    def _build_menus_and_toolbars(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
        file_menu.addSeparator()
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.action_export_png)
        file_menu.addAction(self.action_export_svg)
        file_menu.addSeparator()
        file_menu.addAction(self.action_quit)

        edit_menu = self.menuBar().addMenu("Edit")
        edit_menu.addAction(self.action_delete)

        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self.action_fit)

        toolbar = QToolBar("Tools", self)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)
        toolbar.addAction(self.action_mode_select)
        toolbar.addAction(self.action_mode_pan)
        toolbar.addAction(self.action_mode_add)
        toolbar.addAction(self.action_mode_connect)

    def new_file(self) -> None:
        self.view.clear_scene()
        self._filename = None

    def open_dialog(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Open Flowfile", str(Path.home()), "FlowDraw (*.flow.json)")
        if filename:
            self.open_file(filename)

    def open_file(self, filename: str | Path) -> None:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            load_scene_from_dict(self.view.scene(), data)
            self._filename = Path(filename)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Open Error", f"Failed to open file:\n{exc}")

    def save(self) -> None:
        if self._filename is None:
            self.save_as()
            return
        self._save_to(self._filename)

    def save_as(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Save Flowfile", str(Path.home() / "diagram.flow.json"), "FlowDraw (*.flow.json)")
        if filename:
            self._filename = Path(filename)
            self._save_to(self._filename)

    def _save_to(self, path: Path) -> None:
        try:
            data = serialize_scene_to_dict(self.view.scene())
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{exc}")

    def export_png(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Export PNG", str(Path.home() / "diagram.png"), "PNG (*.png)")
        if not filename:
            return
        rect = self.view.scene().itemsBoundingRect().adjusted(-50, -50, 50, 50)
        self.view.export_png(Path(filename), rect)

    def export_svg(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Export SVG", str(Path.home() / "diagram.svg"), "SVG (*.svg)")
        if not filename:
            return
        rect = self.view.scene().itemsBoundingRect().adjusted(-50, -50, 50, 50)
        self.view.export_svg(Path(filename), rect)
