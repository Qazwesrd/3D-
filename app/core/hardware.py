from __future__ import annotations

import platform
import psutil


def collect_hardware_summary() -> dict:
    cpu = platform.processor() or platform.uname().processor or "未识别"
    ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    return {
        "cpu": cpu,
        "ram_gb": ram_gb,
        "system": platform.platform(),
        "architecture": platform.machine(),
        "gpu_detection": "待接入跨厂商GPU检测模块",
        "recommended_profile": "保守轻量模式（待GPU/显存实测后调整）",
    }
