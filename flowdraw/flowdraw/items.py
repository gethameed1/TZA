from __future__ import annotations

from typing import Optional, Tuple

from PySide6.QtCore import QRectF, QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainterPath, QPen, QPainter
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem, QStyleOptionGraphicsItem, QWidget


class NodeItem(QGraphicsItem):
    WIDTH = 180
    HEIGHT = 100
    RADIUS = 10

    def __init__(self, title: str = "Node") -> None:
        super().__init__()
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self._title = title
        self._fill = QColor(255, 255, 255)
        self._stroke = QColor(60, 60, 60)
        self._title_item = QGraphicsTextItem(self._title, self)
        self._title_item.setDefaultTextColor(QColor(30, 30, 30))
        self._title_item.setPos(12, 8)
        # ports
        self.input_port = PortItem(self, side="left")
        self.output_port = PortItem(self, side="right")
        self._update_ports()

    def boundingRect(self) -> QRectF:  # noqa: N802
        return QRectF(0, 0, self.WIDTH, self.HEIGHT)

    def shape(self) -> QPainterPath:  # noqa: N802
        path = QPainterPath()
        path.addRoundedRect(self.boundingRect(), self.RADIUS, self.RADIUS)
        return path

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None) -> None:  # noqa: N802
        del option, widget
        rect = self.boundingRect()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QBrush(self._fill))
        painter.setPen(QPen(self._stroke, 1.2))
        painter.drawRoundedRect(rect, self.RADIUS, self.RADIUS)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):  # noqa: N802
        if change == QGraphicsItem.ItemPositionChange:
            self._update_ports()
        return super().itemChange(change, value)

    def _update_ports(self) -> None:
        self.input_port.setPos(0, self.HEIGHT / 2)
        self.output_port.setPos(self.WIDTH, self.HEIGHT / 2)
        for edge in list(self.input_port.edges) + list(self.output_port.edges):
            edge.update_path()

    # Property helpers
    def get_title(self) -> str:
        return self._title

    def set_title(self, title: str) -> None:
        self._title = title
        self._title_item.setPlainText(title)

    def fill_color(self) -> QColor:
        return self._fill

    def set_fill_color(self, color: QColor) -> None:
        self._fill = color
        self.update()

    @classmethod
    def new_default(cls) -> "NodeItem":
        return cls("Node")


class PortItem(QGraphicsItem):
    RADIUS = 6

    def __init__(self, parent: NodeItem, side: str) -> None:
        super().__init__(parent)
        self.setFlags(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.side = side
        self.edges: set[EdgeItem] = set()
        self._hover = False

    def boundingRect(self) -> QRectF:  # noqa: N802
        r = self.RADIUS
        return QRectF(-r, -r, r * 2, r * 2)

    def shape(self) -> QPainterPath:  # noqa: N802
        path = QPainterPath()
        path.addEllipse(self.boundingRect())
        return path

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None) -> None:  # noqa: N802
        del option, widget
        painter.setRenderHint(QPainter.Antialiasing, True)
        color = QColor(90, 90, 90) if not self._hover else QColor(50, 120, 220)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.boundingRect())

    def hoverEnterEvent(self, event):  # noqa: N802
        self._hover = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):  # noqa: N802
        self._hover = False
        self.update()
        super().hoverLeaveEvent(event)

    def scenePosCenter(self) -> QPointF:
        br = self.boundingRect()
        center = QPointF(br.x() + br.width() / 2, br.y() + br.height() / 2)
        return self.mapToScene(center)


class EdgeItem(QGraphicsPathItem):
    def __init__(self, start_port: PortItem, end_port: Optional[PortItem]) -> None:
        super().__init__()
        self.setZValue(-1)
        self.setPen(QPen(QColor(50, 50, 50), 2))
        self.start_port = start_port
        self.end_port = end_port
        self._end_pos: Optional[QPointF] = None
        start_port.edges.add(self)
        if end_port is not None:
            end_port.edges.add(self)
        self.update_path()

    def set_end_port(self, port: PortItem) -> None:
        if self.end_port is not None:
            self.end_port.edges.discard(self)
        self.end_port = port
        port.edges.add(self)
        self._end_pos = None
        self.update_path()

    def set_end_pos(self, pos: QPointF) -> None:
        self._end_pos = pos
        self.update_path()

    def update_path(self) -> None:
        start = self.start_port.scenePosCenter()
        end = self.end_port.scenePosCenter() if self.end_port is not None else (self._end_pos or start)
        dx = max(40, abs(end.x() - start.x()) * 0.5)
        c1 = QPointF(start.x() + dx, start.y())
        c2 = QPointF(end.x() - dx, end.y())
        path = QPainterPath(start)
        path.cubicTo(c1, c2, end)
        self.setPath(path)

    def remove(self) -> None:
        self.start_port.edges.discard(self)
        if self.end_port is not None:
            self.end_port.edges.discard(self)
        if self.scene() is not None:
            self.scene().removeItem(self)
