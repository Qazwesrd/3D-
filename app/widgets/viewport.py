from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

try:
    import pyqtgraph.opengl as gl
    from pyqtgraph.opengl import MeshData
    OPENGL_AVAILABLE = True
    OPENGL_IMPORT_ERROR = ""
except Exception as exc:  # Keep the rest of the app usable on unsupported graphics setups.
    gl = None
    MeshData = None
    OPENGL_AVAILABLE = False
    OPENGL_IMPORT_ERROR = str(exc)


class CharacterPreview(QWidget):
    """Interactive OpenGL viewport for imported local 3D meshes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mesh_item = None
        self._model_path: Path | None = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        if not OPENGL_AVAILABLE:
            self._fallback = QLabel(
                "当前环境无法初始化3D视口。\n"
                "请确认已安装 requirements.txt 中的 pyqtgraph 与 PyOpenGL，"
                "并更新显卡驱动。\n\n详细信息：" + OPENGL_IMPORT_ERROR
            )
            self._fallback.setAlignment(Qt.AlignCenter)
            self._fallback.setWordWrap(True)
            self._fallback.setStyleSheet(
                "background:#111720;color:#dbe8f8;border:1px solid #35465e;"
                "border-radius:8px;padding:24px;"
            )
            self._layout.addWidget(self._fallback)
            self.view = None
            return

        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor("#111720")
        self.view.setCameraPosition(distance=5, elevation=15, azimuth=35)
        self._layout.addWidget(self.view, 1)

        grid = gl.GLGridItem()
        grid.setSize(4, 4)
        grid.setSpacing(0.25, 0.25)
        self.view.addItem(grid)
        axis = gl.GLAxisItem()
        axis.setSize(1.2, 1.2, 1.2)
        self.view.addItem(axis)

        self._hint = QLabel("尚未加载模型。点击上方“导入3D模型”选择 GLB、GLTF、OBJ、STL 或 PLY 文件。")
        self._hint.setStyleSheet("color:#aab3c2;padding:6px;")
        self._layout.addWidget(self._hint)

    @property
    def model_path(self) -> Path | None:
        return self._model_path

    def load_mesh(self, mesh, source_path: str | Path) -> None:
        if self.view is None:
            raise RuntimeError("当前设备未能初始化OpenGL视口。")
        import numpy as np

        vertices = np.asarray(mesh.vertices, dtype=np.float32)
        faces = np.asarray(mesh.faces, dtype=np.uint32)
        if vertices.size == 0 or faces.size == 0:
            raise ValueError("模型没有可显示的顶点或三角面。")

        colors = None
        try:
            candidate = np.asarray(mesh.visual.vertex_colors)
            if candidate.ndim == 2 and len(candidate) == len(vertices):
                colors = candidate.astype(np.float32) / 255.0
        except Exception:
            colors = None

        mesh_data = MeshData(vertexes=vertices, faces=faces, vertexColors=colors)
        item = gl.GLMeshItem(
            meshdata=mesh_data,
            smooth=True,
            shader="shaded",
            drawFaces=True,
            drawEdges=False,
        )
        if self._mesh_item is not None:
            self.view.removeItem(self._mesh_item)
        self._mesh_item = item
        self.view.addItem(item)
        self.view.setCameraPosition(distance=3.5, elevation=15, azimuth=35)
        self._model_path = Path(source_path)
        self._hint.setText(
            f"已加载：{self._model_path.name}  |  顶点：{len(vertices):,}  |  三角面：{len(faces):,}\n"
            "鼠标左键拖动：旋转；鼠标滚轮：缩放；鼠标右键拖动：平移。"
        )
