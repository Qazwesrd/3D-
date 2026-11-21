from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS = {".glb", ".gltf", ".obj", ".stl", ".ply"}


def load_model_mesh(file_path: str | Path):
    """Load a local 3D file and combine its scene geometry into one trimesh mesh."""
    import trimesh

    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"找不到模型文件：{path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"暂不支持该模型格式：{path.suffix}")

    loaded = trimesh.load(path, force="scene", process=False)
    if isinstance(loaded, trimesh.Trimesh):
        mesh = loaded
    elif isinstance(loaded, trimesh.Scene):
        mesh = loaded.dump(concatenate=True)
    else:
        raise ValueError("文件中没有可识别的3D网格。")

    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        raise ValueError("模型不包含有效的网格数据。")

    # Center and scale for a predictable first view; source file is not modified.
    mesh = mesh.copy()
    mesh.apply_translation(-mesh.bounding_box.centroid)
    largest_extent = float(mesh.extents.max())
    if largest_extent > 0:
        mesh.apply_scale(2.0 / largest_extent)
    return mesh
