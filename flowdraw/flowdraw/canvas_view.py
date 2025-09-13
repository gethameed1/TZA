from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene

from .items import NodeItem, EdgeItem, PortItem


class CanvasView(QGraphicsView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        scene = QGraphicsScene(self)
        scene.setSceneRect(QRectF(-5000, -5000, 10000, 10000))
        self.setScene(scene)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self._mode: str = "select"
        self._pan_active = False
        self._last_mouse_pos: Optional[QPointF] = None
        self._temp_edge: Optional[EdgeItem] = None
        self._connect_from: Optional[PortItem] = None
        self.setBackgroundBrush(self._grid_brush())
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self._snap = True
        self._snap_size = 20

    def _grid_brush(self):
        fine = 20
        color = QColor(230, 230, 230)
        return color

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:  # noqa: N802
        super().drawBackground(painter, rect)
        # Grid
        fine = 20
        bold = 100
        left = int(rect.left()) - (int(rect.left()) % fine)
        top = int(rect.top()) - (int(rect.top()) % fine)
        lines_fine = []
        lines_bold = []
        pen_fine = QPen(QColor(235, 235, 235))
        pen_bold = QPen(QColor(210, 210, 210))
        for x in range(left, int(rect.right()), fine):
            line = (QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            if x % bold == 0:
                lines_bold.append(line)
            else:
                lines_fine.append(line)
        for y in range(top, int(rect.bottom()), fine):
            line = (QPointF(rect.left(), y), QPointF(rect.right(), y))
            if y % bold == 0:
                lines_bold.append(line)
            else:
                lines_fine.append(line)
        painter.setPen(pen_fine)
        for a, b in lines_fine:
            painter.drawLine(a, b)
        painter.setPen(pen_bold)
        for a, b in lines_bold:
            painter.drawLine(a, b)

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        if mode == "pan":
            self.setDragMode(QGraphicsView.NoDrag)
        elif mode == "select":
            self.setDragMode(QGraphicsView.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.NoDrag)

    def fit_to_scene(self) -> None:
        rect = self.scene().itemsBoundingRect()
        if rect.isEmpty():
            rect = QRectF(-200, -150, 400, 300)
        self.fitInView(rect, Qt.KeepAspectRatio)

    def wheelEvent(self, event):  # noqa: N802
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):  # noqa: N802
        pos = self.mapToScene(event.pos())
        if self._mode == "pan" and event.button() == Qt.LeftButton:
            self._pan_active = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        if self._mode == "add" and event.button() == Qt.LeftButton:
            node = NodeItem.new_default()
            if self._snap:
                pos = QPointF(round(pos.x() / self._snap_size) * self._snap_size, round(pos.y() / self._snap_size) * self._snap_size)
            node.setPos(pos)
            self.scene().addItem(node)
            event.accept()
            return
        if self._mode == "connect" and event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            scene_item = self.itemAt(event.pos())
            item = self.scene().itemAt(pos, self.transform())
            if isinstance(item, PortItem):
                self._connect_from = item
                self._temp_edge = EdgeItem(item, None)
                self.scene().addItem(self._temp_edge)
                self._temp_edge.set_end_pos(pos)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # noqa: N802
        if self._pan_active and self._last_mouse_pos is not None:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        if self._temp_edge is not None:
            pos = self.mapToScene(event.pos())
            self._temp_edge.set_end_pos(pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802
        if self._pan_active and event.button() == Qt.LeftButton:
            self._pan_active = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        if self._temp_edge is not None and self._connect_from is not None:
            pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(pos, self.transform())
            if isinstance(item, PortItem) and item is not self._connect_from:
                self._temp_edge.set_end_port(item)
                self._temp_edge = None
                self._connect_from = None
                event.accept()
                return
            # cancel temp edge
            self.scene().removeItem(self._temp_edge)
            self._temp_edge = None
            self._connect_from = None
        super().mouseReleaseEvent(event)

    def get_single_selected_node(self) -> Optional[NodeItem]:
        items = [i for i in self.scene().selectedItems() if isinstance(i, NodeItem)]
        return items[0] if len(items) == 1 else None

    def delete_selected(self) -> None:
        for item in list(self.scene().selectedItems()):
            if isinstance(item, NodeItem):
                # remove connected edges first
                for edge in list(item.input_port.edges):
                    edge.remove()
                for edge in list(item.output_port.edges):
                    edge.remove()
            self.scene().removeItem(item)

    def clear_scene(self) -> None:
        self.scene().clear()

    def export_png(self, path: Path, rect: QRectF) -> None:
        from PySide6.QtGui import QImage
        image = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32_Premultiplied)
        image.fill(QColor(255, 255, 255, 0))
        painter = QPainter(image)
        self.scene().render(painter, target=QRectF(0, 0, rect.width(), rect.height()), source=rect)
        painter.end()
        image.save(str(path))

    def export_svg(self, path: Path, rect: QRectF) -> None:
        from PySide6.QtSvg import QSvgGenerator
        generator = QSvgGenerator()
        generator.setFileName(str(path))
        generator.setSize(self.viewport().size())
        painter = QPainter()
        painter.begin(generator)
        self.scene().render(painter, target=QRectF(0, 0, rect.width(), rect.height()), source=rect)
        painter.end()
