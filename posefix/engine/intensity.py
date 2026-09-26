from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntensityPolicy:
    mode: str
    correction_signal_threshold: float
    secondary_weight: float
    mechanic_budget: int
    pose_adherence_threshold: float
    change_magnitude: tuple[float, float]
    maximum_pose_change: str
    limb_reconstruction_allowance: str
    reconstruction_tolerance: str
    status: str


INTENSITY_POLICIES = {
    "natural": IntensityPolicy(
        mode="natural",
        correction_signal_threshold=0.45,
        secondary_weight=0.35,
        mechanic_budget=2,
        pose_adherence_threshold=0.80,
        change_magnitude=(0.20, 0.40),
        maximum_pose_change="moderate",
        limb_reconstruction_allowance="low",
        reconstruction_tolerance="low",
        status="locked",
    ),
    "enhanced": IntensityPolicy(
        mode="enhanced",
        correction_signal_threshold=0.30,
        secondary_weight=0.50,
        mechanic_budget=4,
        pose_adherence_threshold=0.86,
        change_magnitude=(0.45, 0.70),
        maximum_pose_change="clear",
        limb_reconstruction_allowance="medium_low",
        reconstruction_tolerance="medium_low",
        status="active",
    ),
    "bold": IntensityPolicy(
        mode="bold",
        correction_signal_threshold=0.15,
        secondary_weight=0.65,
        mechanic_budget=6,
        pose_adherence_threshold=0.90,
        change_magnitude=(0.70, 1.00),
        maximum_pose_change="substantial",
        limb_reconstruction_allowance="medium",
        reconstruction_tolerance="medium",
        status="experimental",
    ),
}


MECHANIC_MULTIPLIERS = {
    "natural": {},
    "enhanced": {
        "weight_distribution": 1.35,
        "free_knee": 1.30,
        "hip_offset": 1.35,
        "hip_yaw": 1.30,
        "shoulder_angle": 1.30,
        "shoulder_counterbalance": 1.30,
        "torso_yaw": 1.30,
        "torso_lean": 1.25,
        "arm_to_torso_spacing": 1.25,
        "elbow_bend": 1.20,
        "neck_extension": 1.15,
        "chin_direction": 1.15,
        "gaze_direction": 1.15,
        "head_orientation": 1.10,
        "hand_purpose": 1.05,
    },
    "bold": {
        "weight_distribution": 1.60,
        "free_knee": 1.50,
        "hip_offset": 1.60,
        "hip_yaw": 1.55,
        "shoulder_angle": 1.50,
        "shoulder_counterbalance": 1.50,
        "torso_yaw": 1.55,
        "torso_lean": 1.45,
        "arm_to_torso_spacing": 1.40,
        "elbow_bend": 1.35,
        "neck_extension": 1.25,
        "chin_direction": 1.25,
        "gaze_direction": 1.25,
        "head_orientation": 1.20,
        "hand_purpose": 1.15,
    },
}


def get_intensity_policy(mode: str) -> IntensityPolicy:
    try:
        return INTENSITY_POLICIES[mode]
    except KeyError as exc:
        raise ValueError(f"Unsupported PoseFix intensity: {mode}") from exc


def scale_mechanic_strength(mode: str, mechanic: str, strength: float) -> float:
    multiplier = MECHANIC_MULTIPLIERS.get(mode, {}).get(mechanic, 1.0)
    return round(min(1.0, max(0.0, strength * multiplier)), 4)
