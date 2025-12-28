# app/video/skeletons.py
from typing import NamedTuple


class SkeletonEdge(NamedTuple):
    start: str
    end: str
    color: tuple[int, int, int]


COCO_SKELETON = [
    # Face
    SkeletonEdge("nose", "left_eye", (51, 153, 255)),
    SkeletonEdge("nose", "right_eye", (51, 153, 255)),
    SkeletonEdge("left_eye", "right_eye", (51, 153, 255)),
    SkeletonEdge("left_eye", "left_ear", (51, 153, 255)),
    SkeletonEdge("right_eye", "right_ear", (51, 153, 255)),

    # Left arm
    SkeletonEdge("left_shoulder", "left_elbow", (0, 255, 0)),
    SkeletonEdge("left_elbow", "left_wrist", (0, 255, 0)),

    # Right arm
    SkeletonEdge("right_shoulder", "right_elbow", (255, 128, 0)),
    SkeletonEdge("right_elbow", "right_wrist", (255, 128, 0)),

    # Torso
    SkeletonEdge("left_shoulder", "right_shoulder", (255, 255, 255)),
    SkeletonEdge("left_shoulder", "left_hip", (0, 255, 0)),
    SkeletonEdge("right_shoulder", "right_hip", (255, 128, 0)),
    SkeletonEdge("left_hip", "right_hip", (255, 255, 255)),

    # Left leg
    SkeletonEdge("left_hip", "left_knee", (0, 255, 0)),
    SkeletonEdge("left_knee", "left_ankle", (0, 255, 0)),

    # Right leg
    SkeletonEdge("right_hip", "right_knee", (255, 128, 0)),
    SkeletonEdge("right_knee", "right_ankle", (255, 128, 0)),
]


COCO_WHOLEBODY_SKELETON = COCO_SKELETON + [
    SkeletonEdge("left_ankle", "left_big_toe", (0, 255, 0)),
    SkeletonEdge("left_ankle", "left_small_toe", (0, 255, 0)),
    SkeletonEdge("left_ankle", "left_heel", (0, 255, 0)),
    SkeletonEdge("right_ankle", "right_big_toe", (255, 128, 0)),
    SkeletonEdge("right_ankle", "right_small_toe", (255, 128, 0)),
    SkeletonEdge("right_ankle", "right_heel", (255, 128, 0)),
]


GOLIATH_SKELETON = [
    SkeletonEdge(start='left_ankle', end='left_knee', color=(0, 255, 0)),
    SkeletonEdge(start='left_knee', end='left_hip', color=(0, 255, 0)),
    SkeletonEdge(start='right_ankle', end='right_knee', color=(255, 128, 0)),
    SkeletonEdge(start='right_knee', end='right_hip', color=(255, 128, 0)),
    SkeletonEdge(start='left_hip', end='right_hip', color=(51, 153, 255)),
    SkeletonEdge(start='left_shoulder', end='left_hip', color=(51, 153, 255)),
    SkeletonEdge(start='right_shoulder', end='right_hip', color=(51, 153, 255)),
    SkeletonEdge(start='left_shoulder', end='right_shoulder', color=(51, 153, 255)),
    SkeletonEdge(start='left_shoulder', end='left_elbow', color=(0, 255, 0)),
    SkeletonEdge(start='right_shoulder', end='right_elbow', color=(255, 128, 0)),
    SkeletonEdge(start='left_elbow', end='left_wrist', color=(0, 255, 0)),
    SkeletonEdge(start='right_elbow', end='right_wrist', color=(255, 128, 0)),
    SkeletonEdge(start='left_eye', end='right_eye', color=(51, 153, 255)),
    SkeletonEdge(start='nose', end='left_eye', color=(51, 153, 255)),
    SkeletonEdge(start='nose', end='right_eye', color=(51, 153, 255)),
    SkeletonEdge(start='left_eye', end='left_ear', color=(51, 153, 255)),
    SkeletonEdge(start='right_eye', end='right_ear', color=(51, 153, 255)),
    SkeletonEdge(start='left_ear', end='left_shoulder', color=(51, 153, 255)),
    SkeletonEdge(start='right_ear', end='right_shoulder', color=(51, 153, 255)),
    SkeletonEdge(start='left_ankle', end='left_big_toe', color=(0, 255, 0)),
    SkeletonEdge(start='left_ankle', end='left_small_toe', color=(0, 255, 0)),
    SkeletonEdge(start='left_ankle', end='left_heel', color=(0, 255, 0)),
    SkeletonEdge(start='right_ankle', end='right_big_toe', color=(255, 128, 0)),
    SkeletonEdge(start='right_ankle', end='right_small_toe', color=(255, 128, 0)),
    SkeletonEdge(start='right_ankle', end='right_heel', color=(255, 128, 0)),
    SkeletonEdge(start='left_wrist', end='left_thumb_third_joint', color=(255, 128, 0)),
    SkeletonEdge(start='left_thumb_third_joint', end='left_thumb2', color=(255, 128, 0)),
    SkeletonEdge(start='left_thumb2', end='left_thumb3', color=(255, 128, 0)),
    SkeletonEdge(start='left_thumb3', end='left_thumb4', color=(255, 128, 0)),
    SkeletonEdge(start='left_wrist', end='left_forefinger_third_joint', color=(255, 153, 255)),
    SkeletonEdge(start='left_forefinger_third_joint', end='left_forefinger2', color=(255, 153, 255)),
    SkeletonEdge(start='left_forefinger2', end='left_forefinger3', color=(255, 153, 255)),
    SkeletonEdge(start='left_forefinger3', end='left_forefinger4', color=(255, 153, 255)),
    SkeletonEdge(start='left_wrist', end='left_middle_finger_third_joint', color=(102, 178, 255)),
    SkeletonEdge(start='left_middle_finger_third_joint', end='left_middle_finger2', color=(102, 178, 255)),
    SkeletonEdge(start='left_middle_finger2', end='left_middle_finger3', color=(102, 178, 255)),
    SkeletonEdge(start='left_middle_finger3', end='left_middle_finger4', color=(102, 178, 255)),
    SkeletonEdge(start='left_wrist', end='left_ring_finger_third_joint', color=(255, 51, 51)),
    SkeletonEdge(start='left_ring_finger_third_joint', end='left_ring_finger2', color=(255, 51, 51)),
    SkeletonEdge(start='left_ring_finger2', end='left_ring_finger3', color=(255, 51, 51)),
    SkeletonEdge(start='left_ring_finger3', end='left_ring_finger4', color=(255, 51, 51)),
    SkeletonEdge(start='left_wrist', end='left_pinky_finger_third_joint', color=(0, 255, 0)),
    SkeletonEdge(start='left_pinky_finger_third_joint', end='left_pinky_finger2', color=(0, 255, 0)),
    SkeletonEdge(start='left_pinky_finger2', end='left_pinky_finger3', color=(0, 255, 0)),
    SkeletonEdge(start='left_pinky_finger3', end='left_pinky_finger4', color=(0, 255, 0)),
    SkeletonEdge(start='right_wrist', end='right_thumb_third_joint', color=(255, 128, 0)),
    SkeletonEdge(start='right_thumb_third_joint', end='right_thumb2', color=(255, 128, 0)),
    SkeletonEdge(start='right_thumb2', end='right_thumb3', color=(255, 128, 0)),
    SkeletonEdge(start='right_thumb3', end='right_thumb4', color=(255, 128, 0)),
    SkeletonEdge(start='right_wrist', end='right_forefinger_third_joint', color=(255, 153, 255)),
    SkeletonEdge(start='right_forefinger_third_joint', end='right_forefinger2', color=(255, 153, 255)),
    SkeletonEdge(start='right_forefinger2', end='right_forefinger3', color=(255, 153, 255)),
    SkeletonEdge(start='right_forefinger3', end='right_forefinger4', color=(255, 153, 255)),
    SkeletonEdge(start='right_wrist', end='right_middle_finger_third_joint', color=(102, 178, 255)),
    SkeletonEdge(start='right_middle_finger_third_joint', end='right_middle_finger2', color=(102, 178, 255)),
    SkeletonEdge(start='right_middle_finger2', end='right_middle_finger3', color=(102, 178, 255)),
    SkeletonEdge(start='right_middle_finger3', end='right_middle_finger4', color=(102, 178, 255)),
    SkeletonEdge(start='right_wrist', end='right_ring_finger_third_joint', color=(255, 51, 51)),
    SkeletonEdge(start='right_ring_finger_third_joint', end='right_ring_finger2', color=(255, 51, 51)),
    SkeletonEdge(start='right_ring_finger2', end='right_ring_finger3', color=(255, 51, 51)),
    SkeletonEdge(start='right_ring_finger3', end='right_ring_finger4', color=(255, 51, 51)),
    SkeletonEdge(start='right_wrist', end='right_pinky_finger_third_joint', color=(0, 255, 0)),
    SkeletonEdge(start='right_pinky_finger_third_joint', end='right_pinky_finger2', color=(0, 255, 0)),
    SkeletonEdge(start='right_pinky_finger2', end='right_pinky_finger3', color=(0, 255, 0)),
    SkeletonEdge(start='right_pinky_finger3', end='right_pinky_finger4', color=(0, 255, 0)),
]


SKELETON_DEFINITIONS = {
    "coco": COCO_SKELETON,
    "coco_wholebody": COCO_WHOLEBODY_SKELETON,
    "goliath": GOLIATH_SKELETON,
}
"""
Maps pose format names to their corresponding skeleton connectivity definitions.

Each value is a list of `SkeletonEdge` instances, where each edge defines:
- `start`: name of the starting keypoint,
- `end`: name of the ending keypoint,
- `color`: RGB color tuple for rendering the connection.

This dictionary enables pose-format-aware visualization by providing correct joint
pairings and rendering colors for supported formats such as COCO, COCO-WholeBody,
and Goliath.
"""