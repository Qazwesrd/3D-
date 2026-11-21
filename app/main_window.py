from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QComboBox, QMessageBox,
    QSplitter, QFrame, QLineEdit, QFormLayout
)

from app.core.project_store import ProjectStore
from app.core.hardware import collect_hardware_summary
from app.widgets.viewport import CharacterPreview
from app.services.engine_registry import EngineRegistry


APP_ROOT = Path(__file__).resolve().parents[1]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D动漫角色创作大师")
        self.resize(1280, 800)
        self.store = ProjectStore(APP_ROOT / "data" / "projects")
        self.engines = EngineRegistry()
        self.current_project = None
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
        subtitle = QLabel("独立桌面版 · 本地项目管理")
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
        self.preview = CharacterPreview()
        center_layout.addWidget(self.preview, 1)
        hint = QLabel("当前为预览界面起始占位。下一阶段接入真正的3D视口和GLB模型加载。")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        center_layout.addWidget(hint)
        splitter.addWidget(center)

        right = QFrame()
        right.setObjectName("panel")
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("角色基础设置"))
        form = QFormLayout()
        self.style_combo = QComboBox()
        self.style_combo.addItems(["3D国漫", "3D仿真人", "日漫3D", "奇幻盔甲3D"])
        form.addRow("角色风格", self.style_combo)
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["暂不指定", "男性", "女性", "自定义"])
        form.addRow("角色类型", self.gender_combo)
        self.role_desc = QLineEdit()
        self.role_desc.setPlaceholderText("例如：银白长发、蓝色眼睛、精致战甲")
        form.addRow("外观描述", self.role_desc)
        right_layout.addLayout(form)
        save_btn = QPushButton("保存角色设置")
        save_btn.clicked.connect(self._save_project)
        right_layout.addWidget(save_btn)
        right_layout.addStretch()
        self.status_label = QLabel("请选择或新建一个角色项目。")
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("muted")
        right_layout.addWidget(self.status_label)
        splitter.addWidget(right)
        splitter.setSizes([230, 780, 270])

        self.setStyleSheet("""
            QMainWindow, QWidget { background: #171a21; color: #edf0f6; font-size: 14px; }
            #appTitle { font-size: 23px; font-weight: 700; }
            #muted { color: #aab3c2; }
            #panel { background: #222733; border: 1px solid #343c4b; border-radius: 10px; }
            QListWidget, QLineEdit, QComboBox {
                background: #171d27; border: 1px solid #3b4658; border-radius: 6px;
                padding: 8px; color: #f4f6fa;
            }
            QPushButton {
                background: #3478db; border: 0; border-radius: 6px;
                padding: 10px; color: white; font-weight: 600;
            }
            QPushButton:hover { background: #4389ed; }
            #secondaryButton { background: #3a4352; }
        """)

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
        })
        self.current_project = self.store.update_project(updated["id"], updated)
        self.status_label.setText("角色设置已保存到本地项目目录。")

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
