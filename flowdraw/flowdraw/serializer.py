from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsScene

from .items import NodeItem, EdgeItem, PortItem


@dataclass
class NodeData:
    id: int
    title: str
    x: float
    y: float
    fill: tuple[int, int, int, int]


@dataclass
class EdgeData:
    start_node_id: int
    start_side: str
    end_node_id: int
    end_side: str


def serialize_scene_to_dict(scene: QGraphicsScene) -> dict[str, Any]:
    nodes: list[NodeItem] = [i for i in scene.items() if isinstance(i, NodeItem)]
    node_to_id: dict[NodeItem, int] = {n: idx for idx, n in enumerate(nodes)}
    nodes_data: list[NodeData] = []
    edges_data: list[EdgeData] = []
    for node in nodes:
        pos: QPointF = node.pos()
        nodes_data.append(
            NodeData(
                id=node_to_id[node],
                title=node.get_title(),
                x=pos.x(),
                y=pos.y(),
                fill=(node.fill_color().red(), node.fill_color().green(), node.fill_color().blue(), node.fill_color().alpha()),
            )
        )
    # edges
    for item in scene.items():
        if isinstance(item, EdgeItem) and item.start_port is not None and item.end_port is not None:
            start_node = item.start_port.parentItem()
            end_node = item.end_port.parentItem()
            if isinstance(start_node, NodeItem) and isinstance(end_node, NodeItem):
                edges_data.append(
                    EdgeData(
                        start_node_id=node_to_id[start_node],
                        start_side=item.start_port.side,
                        end_node_id=node_to_id[end_node],
                        end_side=item.end_port.side,
                    )
                )
    return {
        "nodes": [asdict(n) for n in nodes_data],
        "edges": [asdict(e) for e in edges_data],
        "format": 1,
    }


def load_scene_from_dict(scene: QGraphicsScene, data: dict[str, Any]) -> None:
    scene.clear()
    nodes_map: dict[int, NodeItem] = {}
    for nd in data.get("nodes", []):
        node = NodeItem(nd.get("title", "Node"))
        node.setPos(nd.get("x", 0.0), nd.get("y", 0.0))
        fill = nd.get("fill", [255, 255, 255, 255])
        from PySide6.QtGui import QColor
        node.set_fill_color(QColor(*fill))
        scene.addItem(node)
        nodes_map[int(nd.get("id", len(nodes_map)))] = node
    # edges
    for ed in data.get("edges", []):
        start_node = nodes_map.get(int(ed.get("start_node_id")))
        end_node = nodes_map.get(int(ed.get("end_node_id")))
        if not start_node or not end_node:
            continue
        start_port = start_node.input_port if ed.get("start_side") == "left" else start_node.output_port
        end_port = end_node.input_port if ed.get("end_side") == "left" else end_node.output_port
        edge = EdgeItem(start_port, end_port)
        scene.addItem(edge)
