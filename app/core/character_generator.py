from __future__ import annotations

import trimesh


def _ellipsoid(center, radii, color, subdivisions=2):
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions, radius=1.0)
    mesh.apply_scale(radii)
    mesh.apply_translation(center)
    mesh.visual.vertex_colors = color
    return mesh


def _limb_between(start, end, radius_x, radius_y, color):
    import numpy as np
    a, b = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    direction = b - a
    length = float(np.linalg.norm(direction))
    if length <= 1e-6:
        return _ellipsoid((a + b) / 2, (radius_x, radius_y, 0.05), color)
    cylinder = trimesh.creation.cylinder(
        radius=(radius_x + radius_y) / 2, height=length, sections=12
    )
    cylinder.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], direction))
    cylinder.apply_translation((a + b) / 2)
    cylinder.visual.vertex_colors = color
    return trimesh.util.concatenate([
        cylinder,
        _ellipsoid(a, (radius_x, radius_y, radius_x), color),
        _ellipsoid(b, (radius_x, radius_y, radius_x), color),
    ])


def _merge(meshes, name):
    meshes = [m for m in meshes if m is not None]
    if not meshes:
        raise ValueError(f"部件 {name} 没有有效几何体")
    mesh = trimesh.util.concatenate(meshes)
    mesh.metadata["part_name"] = name
    return mesh


def generate_humanoid_parts(parameters: dict | None = None) -> dict[str, trimesh.Trimesh]:
    """Return a named, independently exportable stylized humanoid blockout."""
    p = parameters or {}
    height = min(max(float(p.get("height", 1.8)), 1.2), 2.4)
    head_scale = min(max(float(p.get("head_scale", 1.0)), 0.75), 1.35)
    shoulder_width = min(max(float(p.get("shoulder_width", 0.44)), 0.28), 0.72)
    waist_width = min(max(float(p.get("waist_width", 0.27)), 0.18), 0.48)
    arm_length = min(max(float(p.get("arm_length", 0.58)), 0.38), 0.82)
    leg_length = min(max(float(p.get("leg_length", 0.88)), 0.58), 1.12)
    scale = height / 1.8
    skin, suit, joint = [214,171,143,255], [70,112,166,255], [48,72,105,255]
    eye_white, iris, mouth = [245,245,238,255], [50,115,175,255], [105,48,54,255]
    head_r = 0.105 * head_scale * scale
    head_z = height - head_r * 1.15
    face_y = -head_r * 0.69
    parts: dict[str, trimesh.Trimesh] = {}

    parts["头部"] = _merge([
        _ellipsoid((0,0,head_z),(head_r*.82,head_r*.72,head_r*1.18),skin),
        _ellipsoid((-.078*head_r, face_y-.004, head_z+.015*head_r),
                   (head_r*.20,head_r*.12,head_r*.24),skin),
        _ellipsoid(( .078*head_r, face_y-.004, head_z+.015*head_r),
                   (head_r*.20,head_r*.12,head_r*.24),skin),
    ], "头部")
    parts["耳朵"] = _merge([
        _ellipsoid((s*head_r*.79,0,head_z),(head_r*.20,head_r*.17,head_r*.34),skin)
        for s in (-1,1)
    ], "耳朵")
    parts["眼睛"] = _merge([
        _ellipsoid((s*head_r*.31,face_y-head_r*.055,head_z+head_r*.13),
                   (head_r*.17,head_r*.075,head_r*.105),eye_white)
        for s in (-1,1)
    ], "眼睛")
    parts["虹膜"] = _merge([
        _ellipsoid((s*head_r*.31,face_y-head_r*.125,head_z+head_r*.13),
                   (head_r*.075,head_r*.035,head_r*.078),iris)
        for s in (-1,1)
    ], "虹膜")
    parts["鼻子"] = _ellipsoid((0,face_y-head_r*.13,head_z-head_r*.02),
                               (head_r*.105,head_r*.13,head_r*.19),skin)
    parts["嘴部"] = _ellipsoid((0,face_y-head_r*.095,head_z-head_r*.36),
                               (head_r*.22,head_r*.055,head_r*.055),mouth)
    neck_z = head_z-head_r*1.15
    parts["颈部"] = _ellipsoid((0,0,neck_z),(.055*scale,.055*scale,.075*scale),skin)
    parts["躯干"] = _merge([
        _ellipsoid((0,0,1.16*scale),(shoulder_width*.55*scale,.19*scale,.27*scale),suit),
        _ellipsoid((0,0,.88*scale),(waist_width*.55*scale,.15*scale,.18*scale),suit),
    ], "躯干")

    shoulder_z = 1.34*scale
    hand_z = shoulder_z-arm_length*scale
    for side, label in [(-1,"左"),(1,"右")]:
        shoulder=(side*shoulder_width*.48*scale,0,shoulder_z)
        elbow=(side*(shoulder_width*.48+.08)*scale,0,shoulder_z-arm_length*scale*.52)
        wrist=(side*(shoulder_width*.48+.12)*scale,0,hand_z)
        parts[label+"手臂"]=_merge([
            _limb_between(shoulder,elbow,.075*scale,.075*scale,suit),
            _limb_between(elbow,wrist,.055*scale,.055*scale,suit),
        ],label+"手臂")
        palm=(wrist[0],-.012*scale,wrist[2]-.055*scale)
        fingers=[]
        for i in range(4):
            x=(i-1.5)*.022*scale
            start=(palm[0]+x,palm[1]-.025*scale,palm[2]-.025*scale)
            end=(start[0]+side*.008*scale,start[1]-.018*scale,start[2]-.075*scale)
            fingers.append(_limb_between(start,end,.009*scale,.009*scale,skin))
        thumb_start=(palm[0]-side*.045*scale,palm[1],palm[2])
        thumb_end=(thumb_start[0]-side*.035*scale,thumb_start[1]-.025*scale,thumb_start[2]-.04*scale)
        parts[label+"手掌"]=_merge([
            _ellipsoid(palm,(.052*scale,.035*scale,.065*scale),skin),
            *fingers,
            _limb_between(thumb_start,thumb_end,.014*scale,.014*scale,skin),
        ],label+"手掌")

    leg_top=.76*scale
    leg_bottom=max(.06*scale,(1.8-leg_length)*scale)
    for side,label in [(-1,"左"),(1,"右")]:
        hip=(side*waist_width*.42*scale,0,leg_top)
        knee=(side*waist_width*.52*scale,0,(leg_top+leg_bottom)/2)
        ankle=(side*waist_width*.52*scale,0,leg_bottom)
        parts[label+"腿部"]=_merge([
            _limb_between(hip,knee,.085*scale,.085*scale,suit),
            _limb_between(knee,ankle,.06*scale,.06*scale,joint),
        ],label+"腿部")
        parts[label+"脚部"]=_ellipsoid(
            (ankle[0],-.075*scale,ankle[2]-.035*scale),
            (.078*scale,.16*scale,.047*scale),joint
        )
        parts[label+"脚部"].metadata["part_name"]=label+"脚部"

    for name, mesh in parts.items():
        mesh.metadata["generator"]="3D Anime Character Studio humanoid blockout"
        mesh.metadata["part_name"]=name
    return parts


def generate_base_humanoid(parameters: dict | None = None):
    """Compatibility API: concatenate named parts into one unrigged blockout mesh."""
    parts = generate_humanoid_parts(parameters)
    result = trimesh.util.concatenate(list(parts.values()))
    result.metadata["generator"]="3D Anime Character Studio humanoid blockout"
    result.metadata["parameters"] = {
        key: float((parameters or {}).get(key, default))
        for key, default in {
            "height":1.8,"head_scale":1.0,"shoulder_width":.44,
            "waist_width":.27,"arm_length":.58,"leg_length":.88,
        }.items()
    }
    return result
