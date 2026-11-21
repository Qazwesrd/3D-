from __future__ import annotations

import trimesh


def _ellipsoid(center, radii, color):
    mesh = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
    mesh.apply_scale(radii)
    mesh.apply_translation(center)
    mesh.visual.vertex_colors = color
    return mesh


def _limb_between(start, end, radius_x, radius_y, color):
    """Create a tapered-looking limb from overlapping ellipsoids and a cylinder."""
    import numpy as np

    a = np.asarray(start, dtype=float)
    b = np.asarray(end, dtype=float)
    direction = b - a
    length = float(np.linalg.norm(direction))
    if length <= 1e-6:
        return _ellipsoid((a + b) / 2, (radius_x, radius_y, 0.05), color)

    middle = (a + b) / 2
    cylinder = trimesh.creation.cylinder(radius=(radius_x + radius_y) / 2, height=length, sections=12)
    rotation = trimesh.geometry.align_vectors([0, 0, 1], direction)
    cylinder.apply_transform(rotation)
    cylinder.apply_translation(middle)
    cylinder.visual.vertex_colors = color
    cap_a = _ellipsoid(a, (radius_x, radius_y, radius_x), color)
    cap_b = _ellipsoid(b, (radius_x, radius_y, radius_x), color)
    return trimesh.util.concatenate([cylinder, cap_a, cap_b])


def generate_base_humanoid(parameters: dict | None = None):
    """Generate a stylized, unrigged humanoid blockout mesh for proportion editing.

    This is a primitive blockout, not a finished anatomical or production character.
    """
    p = parameters or {}
    height = float(p.get("height", 1.8))
    head_scale = float(p.get("head_scale", 1.0))
    shoulder_width = float(p.get("shoulder_width", 0.44))
    waist_width = float(p.get("waist_width", 0.27))
    arm_length = float(p.get("arm_length", 0.58))
    leg_length = float(p.get("leg_length", 0.88))

    height = min(max(height, 1.2), 2.4)
    head_scale = min(max(head_scale, 0.75), 1.35)
    shoulder_width = min(max(shoulder_width, 0.28), 0.72)
    waist_width = min(max(waist_width, 0.18), 0.48)
    arm_length = min(max(arm_length, 0.38), 0.82)
    leg_length = min(max(leg_length, 0.58), 1.12)

    scale = height / 1.8
    skin = [214, 171, 143, 255]
    suit = [70, 112, 166, 255]
    joint = [48, 72, 105, 255]
    parts = []

    head_r = 0.105 * head_scale * scale
    head_z = 1.8 * scale - head_r * 1.15
    parts.append(_ellipsoid((0, 0, head_z), (head_r * 0.82, head_r * 0.72, head_r * 1.18), skin))

    neck_z = head_z - head_r * 1.15
    parts.append(_ellipsoid((0, 0, neck_z), (0.055 * scale, 0.055 * scale, 0.075 * scale), skin))

    shoulder_z = 1.34 * scale
    chest_z = 1.16 * scale
    hip_z = 0.88 * scale
    parts.append(_ellipsoid((0, 0, chest_z), (shoulder_width * 0.55 * scale, 0.19 * scale, 0.27 * scale), suit))
    parts.append(_ellipsoid((0, 0, hip_z), (waist_width * 0.55 * scale, 0.15 * scale, 0.18 * scale), suit))

    arm_drop = min(0.22 * scale, arm_length * 0.35)
    hand_z = shoulder_z - arm_length * scale
    for side in (-1, 1):
        shoulder = (side * shoulder_width * 0.48 * scale, 0, shoulder_z)
        elbow = (side * (shoulder_width * 0.48 + 0.08) * scale, 0, shoulder_z - arm_length * scale * 0.52)
        wrist = (side * (shoulder_width * 0.48 + 0.12) * scale, 0, hand_z)
        parts.append(_limb_between(shoulder, elbow, 0.075 * scale, 0.075 * scale, suit))
        parts.append(_limb_between(elbow, wrist, 0.055 * scale, 0.055 * scale, suit))
        parts.append(_ellipsoid((wrist[0], 0, wrist[2] - 0.045 * scale), (0.055 * scale, 0.045 * scale, 0.075 * scale), skin))

    leg_top = hip_z - 0.12 * scale
    leg_bottom = max(0.06 * scale, (1.8 - leg_length) * scale)
    for side in (-1, 1):
        hip = (side * waist_width * 0.42 * scale, 0, leg_top)
        knee = (side * waist_width * 0.52 * scale, 0, (leg_top + leg_bottom) / 2)
        ankle = (side * waist_width * 0.52 * scale, 0, leg_bottom)
        parts.append(_limb_between(hip, knee, 0.085 * scale, 0.085 * scale, suit))
        parts.append(_limb_between(knee, ankle, 0.06 * scale, 0.06 * scale, joint))
        parts.append(_ellipsoid((ankle[0], -0.045 * scale, ankle[2] - 0.035 * scale), (0.075 * scale, 0.13 * scale, 0.045 * scale), joint))

    result = trimesh.util.concatenate(parts)
    result.metadata["generator"] = "3D Anime Character Studio base humanoid blockout"
    result.metadata["parameters"] = {
        "height": height,
        "head_scale": head_scale,
        "shoulder_width": shoulder_width,
        "waist_width": waist_width,
        "arm_length": arm_length,
        "leg_length": leg_length,
    }
    return result
