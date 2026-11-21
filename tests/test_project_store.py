from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.project_store import ProjectStore


def test_create_update_delete_project():
    with TemporaryDirectory() as temp:
        store = ProjectStore(Path(temp))
        project = store.create_project("测试角色")
        assert project["name"] == "测试角色"
        loaded = store.get_project(project["id"])
        assert loaded["style"] == "3D国漫"
        updated = store.update_project(project["id"], {**loaded, "style": "日漫3D"})
        assert updated["style"] == "日漫3D"
        assert len(store.list_projects()) == 1
        store.delete_project(project["id"])
        assert store.list_projects() == []
