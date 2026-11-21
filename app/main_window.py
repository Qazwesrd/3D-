from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QComboBox, QMessageBox,
    QSplitter, QFrame, QLineEdit, QFormLayout, QFileDialog, QDoubleSpinBox,
    QGroupBox
)

from app.core.project_store import ProjectStore
from app.core.hardware import collect_hardware_summary
from app.core.model_loader import load_model_mesh
from app.core.character_generator import generate_base_humanoid, generate_humanoid_parts
from app.widgets.viewport import CharacterPreview
from app.services.engine_registry import EngineRegistry


APP_ROOT = Path(__file__).resolve().parents[1]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D动漫角色创作大师")
        self.resize(1450, 900)
        self.store = ProjectStore(APP_ROOT / "data" / "projects")
        self.engines = EngineRegistry()
        self.current_project = None
        self.current_mesh = None
        self.current_parts = {}
        self._build_ui()
        self._refresh_projects()
        self._show_hardware()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(12, 12, 12, 12)

        header = QHBoxLayout()
        title = QLabel("3D动漫角色创作大师")
        title.setObjectName("appTitle")
        subtitle = QLabel("独立桌面版 · 基础人物比例建模")
        subtitle.setObjectName("muted")
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch()
        self.hardware_label = QLabel("正在检测硬件…")
        self.hardware_label.setObjectName("muted")
        header.addWidget(self.hardware_label)
        outer.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        outer.addWidget(splitter, 1)

        left = QFrame()
        left.setObjectName("panel")
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("角色项目"))
        self.project_list = QListWidget()
        self.project_list.currentItemChanged.connect(self._on_project_selected)
        left_layout.addWidget(self.project_list, 1)
        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("输入新角色名称")
        left_layout.addWidget(self.project_name)
        create_btn = QPushButton("＋ 新建角色项目")
        create_btn.clicked.connect(self._create_project)
        left_layout.addWidget(create_btn)
        delete_btn = QPushButton("删除选中项目")
        delete_btn.setObjectName("secondaryButton")
        delete_btn.clicked.connect(self._delete_project)
        left_layout.addWidget(delete_btn)
        splitter.addWidget(left)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(8, 0, 8, 0)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("3D模型视口"))
        toolbar.addStretch()
        import_btn = QPushButton("导入3D模型")
        import_btn.clicked.connect(self._import_model)
        toolbar.addWidget(import_btn)
        generate_btn = QPushButton("生成基础人物")
        generate_btn.clicked.connect(self._generate_character)
        toolbar.addWidget(generate_btn)
        export_btn = QPushButton("导出GLB")
        export_btn.clicked.connect(self._export_glb)
        toolbar.addWidget(export_btn)
        center_layout.addLayout(toolbar)
        self.preview = CharacterPreview()
        center_layout.addWidget(self.preview, 1)
        splitter.addWidget(center)

        right = QFrame()
        right.setObjectName("panel")
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("角色外观设置"))
        form = QFormLayout()
        self.style_combo = QComboBox()
        self.style_combo.addItems(["3D国漫", "3D仿真人", "日漫3D", "奇幻盔甲3D"])
        form.addRow("角色风格", self.style_combo)
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["暂不指定", "男性", "女性", "自定义"])
        form.addRow("角色类型", self.gender_combo)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["自定义", "成年男性", "成年女性", "少年", "少女", "儿童"])
        form.addRow("体型预设", self.preset_combo)
        preset_btn = QPushButton("应用体型预设")
        preset_btn.clicked.connect(self._apply_preset)
        right_layout.addWidget(preset_btn)
        self.role_desc = QLineEdit()
        self.role_desc.setPlaceholderText("例如：银白长发、蓝色眼睛、精致战甲")
        form.addRow("外观描述", self.role_desc)
        right_layout.addLayout(form)

        proportions = QGroupBox("基础人体比例（米/比例系数）")
        pform = QFormLayout(proportions)
        self.controls = {}
        self._add_spin(pform, "height", "身高", 1.2, 2.4, 1.8, 0.01, " m")
        self._add_spin(pform, "head_scale", "头部大小", 0.75, 1.35, 1.0, 0.01, " x")
        self._add_spin(pform, "shoulder_width", "肩宽", 0.28, 0.72, 0.44, 0.01, " m")
        self._add_spin(pform, "waist_width", "腰胯宽度", 0.18, 0.48, 0.27, 0.01, " m")
        self._add_spin(pform, "arm_length", "手臂长度", 0.38, 0.82, 0.58, 0.01, " m")
        self._add_spin(pform, "leg_length", "腿部长度", 0.58, 1.12, 0.88, 0.01, " m")
        right_layout.addWidget(proportions)
        right_layout.addWidget(QLabel("可独立导出的身体部件"))
        self.part_list = QListWidget()
        self.part_list.setMaximumHeight(150)
        right_layout.addWidget(self.part_list)
        export_part_btn = QPushButton("导出选中部件")
        export_part_btn.setObjectName("secondaryButton")
        export_part_btn.clicked.connect(self._export_selected_part)
        right_layout.addWidget(export_part_btn)

        save_btn = QPushButton("保存角色设置")
        save_btn.clicked.connect(self._save_project)
        right_layout.addWidget(save_btn)
        right_layout.addStretch()
        self.status_label = QLabel("新建项目后，点击“生成基础人物”创建可调整比例的初始网格。")
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("muted")
        right_layout.addWidget(self.status_label)
        splitter.addWidget(right)
        splitter.setSizes([220, 850, 340])

        self.setStyleSheet("""
            QMainWindow, QWidget { background: #171a21; color: #edf0f6; font-size: 14px; }
            #appTitle { font-size: 23px; font-weight: 700; }
            #muted { color: #aab3c2; }
            #panel, QGroupBox { background: #222733; border: 1px solid #343c4b; border-radius: 10px; }
            QGroupBox { margin-top: 12px; padding-top: 12px; font-weight: 600; }
            QListWidget, QLineEdit, QComboBox, QDoubleSpinBox {
                background: #171d27; border: 1px solid #3b4658; border-radius: 6px;
                padding: 7px; color: #f4f6fa;
            }
            QPushButton {
                background: #3478db; border: 0; border-radius: 6px;
                padding: 9px; color: white; font-weight: 600;
            }
            QPushButton:hover { background: #4389ed; }
            #secondaryButton { background: #3a4352; }
        """)

    def _add_spin(self, form, key, label, minimum, maximum, value, step, suffix):
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.setSingleStep(step)
        spin.setDecimals(2)
        spin.setSuffix(suffix)
        self.controls[key] = spin
        form.addRow(label, spin)

    def _parameters(self):
        return {key: control.value() for key, control in self.controls.items()}

    def _set_parameters(self, parameters):
        for key, control in self.controls.items():
            if key in parameters:
                control.setValue(float(parameters[key]))

    def _show_hardware(self):
        info = collect_hardware_summary()
        self.hardware_label.setText(
            f"CPU：{info['cpu']}  |  内存：{info['ram_gb']} GB"
        )

    def _refresh_projects(self, select_id: str | None = None):
        self.project_list.blockSignals(True)
        self.project_list.clear()
        selected = None
        for project in self.store.list_projects():
            item = QListWidgetItem(project["name"])
            item.setData(Qt.UserRole, project["id"])
            self.project_list.addItem(item)
            if project["id"] == select_id:
                selected = item
        self.project_list.blockSignals(False)
        if selected:
            self.project_list.setCurrentItem(selected)
        elif self.project_list.count():
            self.project_list.setCurrentRow(0)

    def _on_project_selected(self, current, _previous):
        if not current:
            self.current_project = None
            return
        project_id = current.data(Qt.UserRole)
        self.current_project = self.store.get_project(project_id)
        if not self.current_project:
            return
        self.style_combo.setCurrentText(self.current_project.get("style", "3D国漫"))
        self.gender_combo.setCurrentText(self.current_project.get("character_type", "暂不指定"))
        self.role_desc.setText(self.current_project.get("description", ""))
        self._set_parameters(self.current_project.get("proportions", {}))
        self.preset_combo.setCurrentText(self.current_project.get("body_preset", "自定义"))
        self.status_label.setText(f"当前项目：{self.current_project['name']}")

    def _create_project(self):
        name = self.project_name.text().strip()
        if not name:
            QMessageBox.information(self, "提示", "请先输入角色名称。")
            return
        project = self.store.create_project(name)
        self.project_name.clear()
        self._refresh_projects(project["id"])
        self.status_label.setText(f"已创建项目：{name}")

    def _save_project(self):
        if not self.current_project:
            QMessageBox.information(self, "提示", "请先新建或选择一个角色项目。")
            return
        updated = dict(self.current_project)
        updated.update({
            "style": self.style_combo.currentText(),
            "character_type": self.gender_combo.currentText(),
            "description": self.role_desc.text().strip(),
            "proportions": self._parameters(),
        })
        self.current_project = self.store.update_project(updated["id"], updated)
        self.status_label.setText("角色外观与人体比例已保存到本地项目。")

    def _apply_preset(self):
        presets = {
            "成年男性": {"height":1.82,"head_scale":1.0,"shoulder_width":0.48,"waist_width":0.29,"arm_length":0.60,"leg_length":0.90},
            "成年女性": {"height":1.68,"head_scale":1.03,"shoulder_width":0.39,"waist_width":0.30,"arm_length":0.55,"leg_length":0.84},
            "少年": {"height":1.55,"head_scale":1.12,"shoulder_width":0.36,"waist_width":0.25,"arm_length":0.49,"leg_length":0.74},
            "少女": {"height":1.50,"head_scale":1.16,"shoulder_width":0.33,"waist_width":0.26,"arm_length":0.47,"leg_length":0.72},
            "儿童": {"height":1.25,"head_scale":1.28,"shoulder_width":0.30,"waist_width":0.23,"arm_length":0.40,"leg_length":0.62},
        }
        name = self.preset_combo.currentText()
        if name not in presets:
            return
        self._set_parameters(presets[name])
        self.status_label.setText(f"已应用{name}比例预设，可继续手动调整。")

    def _generate_character(self):
        try:
            self.current_parts = generate_humanoid_parts(self._parameters())
            mesh = generate_base_humanoid(self._parameters())
            self.preview.load_mesh(mesh, "内置基础人物模型")
            self.current_mesh = mesh
            self.part_list.clear()
            for part_name in self.current_parts:
                self.part_list.addItem(part_name)
            self.status_label.setText(
                f"基础人物已生成：顶点 {len(mesh.vertices):,}，三角面 {len(mesh.faces):,}。"
                "已包含基础五官、耳朵、手指和脚部；仍属于程序化灰盒，未包含精细拓扑、服装、盔甲和骨骼。"
            )
            if self.current_project:
                updated = dict(self.current_project)
                updated["proportions"] = self._parameters()
                updated["body_preset"] = self.preset_combo.currentText()
                updated.setdefault("assets", {})["model"] = "generated://base-humanoid"
                self.current_project = self.store.update_project(updated["id"], updated)
        except Exception as exc:
            QMessageBox.critical(self, "生成失败", f"基础人物生成失败：{exc}")

    def _import_model(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择3D模型", "",
            "3D模型 (*.glb *.gltf *.obj *.stl *.ply);;所有文件 (*.*)",
        )
        if not file_path:
            return
        try:
            mesh = load_model_mesh(file_path)
            self.preview.load_mesh(mesh, file_path)
            self.current_mesh = mesh
            self.current_parts = {}
            self.part_list.clear()
            if self.current_project:
                updated = dict(self.current_project)
                updated.setdefault("assets", {})["model"] = str(Path(file_path).resolve())
                self.current_project = self.store.update_project(updated["id"], updated)
            self.status_label.setText(f"模型加载成功：{Path(file_path).name}")
        except Exception as exc:
            QMessageBox.critical(
                self, "模型导入失败",
                f"无法加载该模型。请确认文件完整且格式受支持。\n\n错误信息：{exc}"
            )

    def _export_glb(self):
        if self.current_mesh is None:
            QMessageBox.information(self, "提示", "请先生成基础人物或导入一个3D模型。")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出GLB模型", "character.glb", "GLB模型 (*.glb)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".glb"):
            file_path += ".glb"
        try:
            self.current_mesh.export(file_path, file_type="glb")
            self.status_label.setText(f"GLB模型已导出：{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", f"GLB导出失败：{exc}")

    def _export_selected_part(self):
        item = self.part_list.currentItem()
        if item is None or item.text() not in self.current_parts:
            QMessageBox.information(self, "提示", "请先生成角色并选择一个身体部件。")
            return
        part_name = item.text()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出身体部件", f"{part_name}.glb",
            "GLB模型 (*.glb);;OBJ模型 (*.obj);;STL模型 (*.stl)"
        )
        if not file_path:
            return
        suffix = Path(file_path).suffix.lower()
        if suffix not in {".glb", ".obj", ".stl"}:
            suffix = ".glb"
            file_path += suffix
        try:
            self.current_parts[part_name].export(file_path, file_type=suffix[1:])
            self.status_label.setText(f"部件“{part_name}”已导出：{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", f"部件导出失败：{exc}")

    def _delete_project(self):
        if not self.current_project:
            QMessageBox.information(self, "提示", "请先选择一个角色项目。")
            return
        answer = QMessageBox.question(
            self, "确认删除",
            f"确定删除角色项目“{self.current_project['name']}”吗？此操作不可撤销。"
        )
        if answer == QMessageBox.Yes:
            self.store.delete_project(self.current_project["id"])
            self.current_project = None
            self._refresh_projects()
            self.status_label.setText("项目已删除。")


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("3D动漫角色创作大师")
    window = MainWindow()
    window.show()
    return app.exec()
