from pathlib import Path

import trimesh

from app.core.model_loader import load_model_mesh


def test_load_obj_and_normalize(tmp_path: Path):
    source = tmp_path / "sample.obj"
    trimesh.creation.box(extents=(2, 4, 6)).export(source)

    mesh = load_model_mesh(source)

    assert len(mesh.vertices) > 0
    assert len(mesh.faces) > 0
    assert abs(float(mesh.extents.max()) - 2.0) < 1e-5
    assert max(abs(float(value)) for value in mesh.bounding_box.centroid) < 1e-5
