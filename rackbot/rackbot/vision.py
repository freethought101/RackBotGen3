"""Vision (03-software §6): tag detection, approach controller, bay fine alignment, caddy ID.

Conventions for TagPose (camera frame, x right, z forward):
  d      forward distance to the tag (mm)
  x      lateral tag offset, + = tag to the right (mm)
  theta  bearing to the tag, + = to the right (deg)
  psi    robot yaw relative to the tag normal, + = robot turned counter-clockwise (deg)
With these signs the §6.2 law w = −kθ·θ − kψ·ψ (w + = CCW) steers onto the tag's centre line.
"""

from __future__ import annotations

import asyncio
import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class TagPose:
    tag_id: int
    d: float
    x: float
    theta: float
    psi: float


@dataclass
class ApproachCmd:
    v: float  # mm/s
    w: float  # deg/s
    handoff: bool = False  # aligned: hand over to the blind DOCK
    too_close: bool = False  # inside abort_d without alignment: back off and retry


def approach_step(pose: TagPose, p) -> ApproachCmd:
    """One step of the station approach controller (03 §6.2). `p` is the `approach` config section."""
    if pose.d < p.handoff_d and abs(pose.x) < p.handoff_x and abs(pose.psi) < p.handoff_psi:
        return ApproachCmd(0.0, 0.0, handoff=True)
    if pose.d < p.abort_d:
        return ApproachCmd(0.0, 0.0, too_close=True)
    w = -p.k_theta * pose.theta - p.k_psi * pose.psi
    v = min(max(p.k_d * (pose.d - p.d_target), p.v_min), p.v_max)
    return ApproachCmd(v, w)


class VisionBase(ABC):
    def __init__(self):
        self.last_detections: list[TagPose] = []

    async def start(self) -> None:  # noqa: B027 - optional hook
        pass

    async def stop(self) -> None:  # noqa: B027 - optional hook
        pass

    @abstractmethod
    async def find_tag(self, tag_id: int) -> TagPose | None:
        """Wait for the next frame and return the pose of `tag_id` in it (None if not seen)."""

    @abstractmethod
    async def shelf_z_error(self, tag_id: int) -> float | None:
        """Z correction (mm, + = raise the lift) from a shelf/bay strip tag. None if the tag is not seen."""

    @abstractmethod
    async def read_caddy_tag(self, station: str, shelf_h: float) -> int | None:
        """Caddy ID (tag 101-106) visible at a shelf, read at standstill. None if no caddy tag is seen."""


class SimVision(VisionBase):
    """Answers from the simulated world, at the configured camera frame rate."""

    def __init__(self, world, clock, fps: float = 10.0):
        super().__init__()
        self.world = world
        self.clock = clock
        self.period = 1.0 / fps
        self.motion = None  # set by the system so the pose is integrated before observing

    async def find_tag(self, tag_id: int) -> TagPose | None:
        await self.clock.sleep(self.period)
        if self.motion is not None:
            self.motion.update_pose()
        pose = self.world.observe(tag_id)
        self.last_detections = [pose] if pose else []
        return pose

    async def shelf_z_error(self, tag_id: int) -> float | None:
        await self.clock.sleep(self.period)
        if self.world.docked_at is None:
            return None
        return self.world.shelf_z_error.get(tag_id, 0.0)

    async def read_caddy_tag(self, station: str, shelf_h: float) -> int | None:
        await self.clock.sleep(self.period)
        if self.world.docked_at != station:
            return None
        return self.world.caddy_on_shelf(station, shelf_h)


class AprilTagVision(VisionBase):
    """Picamera2 + pupil-apriltags on the Pi (03 §6.1). Untested until the camera is on the robot."""

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self._cam = None
        self._det = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        from picamera2 import Picamera2  # apt: python3-picamera2
        from pupil_apriltags import Detector

        v = self.cfg.vision
        self._det = Detector(families=self.cfg.tags.family, nthreads=v.threads, quad_decimate=v.quad_decimate)
        self._cam = Picamera2()
        self._cam.configure(self._cam.create_video_configuration(
            main={"size": (v.width, v.height), "format": "YUV420"}))
        self._cam.start()
        if v.camera_matrix is None:
            log.warning("camera not calibrated: tag poses use a nominal focal length")

    async def stop(self) -> None:
        if self._cam is not None:
            self._cam.stop()

    def _intrinsics(self) -> tuple[float, float, float, float]:
        v = self.cfg.vision
        if v.camera_matrix:
            m = v.camera_matrix
            return m[0][0], m[1][1], m[0][2], m[1][2]
        f = v.width / (2 * math.tan(math.radians(102 / 2)))  # Camera Module 3 Wide, nominal HFOV
        return f, f, v.width / 2, v.height / 2

    async def _detect(self) -> list:
        async with self._lock:
            frame = await asyncio.to_thread(self._cam.capture_array, "main")
            gray = frame[: self.cfg.vision.height, :]
            sizes = self.cfg.tags.sizes_mm
            dets = await asyncio.to_thread(self._det.detect, gray, True, self._intrinsics(), 1.0)
            for d in dets:  # pupil-apriltags scales pose_t by tag_size: rescale per tag
                d.pose_t = d.pose_t * float(sizes.get(d.tag_id, 1.0))
            return dets

    async def find_tag(self, tag_id: int) -> TagPose | None:
        dets = await self._detect()
        poses = [_to_pose(d) for d in dets]
        self.last_detections = poses
        return next((p for p in poses if p.tag_id == tag_id), None)

    async def shelf_z_error(self, tag_id: int) -> float | None:
        # The reference row and mm/px come from calibration (tools/); until then use the pose's y.
        dets = await self._detect()
        d = next((d for d in dets if d.tag_id == tag_id), None)
        return None if d is None else float(d.pose_t[1][0])

    async def read_caddy_tag(self, station: str, shelf_h: float) -> int | None:
        ids = set(self.cfg.tags.caddy_ids)
        dets = await self._detect()
        seen = [d.tag_id for d in dets if d.tag_id in ids]
        return seen[0] if len(seen) == 1 else None


def _to_pose(det) -> TagPose:
    tx, _, tz = (float(v[0]) for v in det.pose_t)
    r = det.pose_R
    # Tag z axis points into the tag; its yaw relative to the optical axis about the camera's vertical.
    yaw = math.degrees(math.atan2(r[0][2], r[2][2]))
    return TagPose(det.tag_id, d=tz, x=tx, theta=math.degrees(math.atan2(tx, tz)), psi=-yaw)
