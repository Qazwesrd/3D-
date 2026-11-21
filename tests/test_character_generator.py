from app.core.character_generator import generate_base_humanoid


def test_generate_base_humanoid_has_geometry():
    mesh = generate_base_humanoid()
    assert len(mesh.vertices) > 0
    assert len(mesh.faces) > 0
    assert mesh.extents[2] > 1.0


def test_generate_base_humanoid_respects_proportion_ranges():
    mesh = generate_base_humanoid({
        "height": 2.2,
        "head_scale": 1.2,
        "shoulder_width": 0.6,
        "waist_width": 0.35,
        "arm_length": 0.7,
        "leg_length": 1.0,
    })
    assert len(mesh.vertices) > 0
    assert mesh.metadata["parameters"]["height"] == 2.2
    assert mesh.metadata["parameters"]["shoulder_width"] == 0.6
