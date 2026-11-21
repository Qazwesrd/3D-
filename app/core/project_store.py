from __future__ import annotations

import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path


class ProjectStore:
    """Simple local JSON project store; one directory per character project."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_name(name: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
        return cleaned[:64] or "未命名角色"

    def _project_file(self, project_id: str) -> Path:
        return self.root / project_id / "project.json"

    def list_projects(self) -> list[dict]:
        projects = []
        for file in self.root.glob("*/project.json"):
            try:
                projects.append(json.loads(file.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return sorted(projects, key=lambda p: p.get("updated_at", ""), reverse=True)

    def get_project(self, project_id: str) -> dict | None:
        file = self._project_file(project_id)
        if not file.is_file():
            return None
        try:
            return json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def create_project(self, name: str) -> dict:
        project_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "id": project_id,
            "name": self._safe_name(name),
            "style": "3D国漫",
            "character_type": "暂不指定",
            "description": "",
            "schema_version": 1,
            "created_at": now,
            "updated_at": now,
            "assets": {"model": None, "textures": [], "animations": []},
        }
        folder = self.root / project_id
        folder.mkdir(parents=True, exist_ok=False)
        self._write_atomic(folder / "project.json", data)
        return data

    def update_project(self, project_id: str, data: dict) -> dict:
        current = self.get_project(project_id)
        if not current:
            raise FileNotFoundError(f"Project not found: {project_id}")
        merged = {**current, **data}
        merged["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._write_atomic(self._project_file(project_id), merged)
        return merged

    def delete_project(self, project_id: str) -> None:
        folder = self.root / project_id
        if folder.exists():
            shutil.rmtree(folder)

    @staticmethod
    def _write_atomic(path: Path, data: dict) -> None:
        temp = path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)
