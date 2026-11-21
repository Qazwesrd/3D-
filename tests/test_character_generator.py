from app.core.character_generator import generate_base_humanoid, generate_humanoid_parts


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


def test_generator_returns_independent_face_and_limb_parts():
    parts = generate_humanoid_parts()
    required = {"头部", "耳朵", "眼睛", "虹膜", "鼻子", "嘴部",
                "左手掌", "右手掌", "左腿部", "右腿部", "左脚部", "右脚部"}
    assert required.issubset(parts)
    for name in required:
        assert len(parts[name].vertices) > 0
        assert len(parts[name].faces) > 0
        assert parts[name].metadata["part_name"] == name


def test_parts_follow_requested_height_scale():
    parts = generate_humanoid_parts({"height": 2.0})
    assert parts["头部"].vertices[:, 2].max() > 1.9
    assert parts["左脚部"].vertices[:, 2].min() < 0.2
