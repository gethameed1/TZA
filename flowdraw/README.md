## FlowDraw

FlowDraw is a cross-platform flowchart editor built with Python and PySide6. It lets you create nodes, connect them with edges, edit properties, and save/load to a JSON-based flowfile format. You can also export to PNG and SVG.

### Features

- Nodes with titles and customizable colors
- Connectors (ports) and curved edges with live updates
- Toolbar modes: Select, Pan, Add Node, Connect
- Property editor dock for selected node
- Grid background with snapping, zoom, and fit
- Keyboard shortcuts and context menus
- Save/Load `.flow.json` files and export as PNG/SVG

### Running

1. Create a virtual environment (optional but recommended)
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m flowdraw
```

### Packaging for Windows

Install PyInstaller and build a single-file executable:

```bash
pip install pyinstaller
pyinstaller --noconfirm --name FlowDraw --windowed --onefile -p . -m flowdraw
```

The executable will be in `dist/FlowDraw.exe`.

### File Format

Flowfiles are JSON with `.flow.json` extension containing nodes, ports, and edges. See `serializer.py` for details.
