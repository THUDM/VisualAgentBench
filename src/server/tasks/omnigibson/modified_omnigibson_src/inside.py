import omnigibson as og
from omnigibson.object_states.aabb import AABB
from omnigibson.object_states.adjacency import HorizontalAdjacency, VerticalAdjacency, flatten_planes
from omnigibson.object_states.kinematics_mixin import KinematicsMixin
from omnigibson.object_states.object_state_base import BooleanStateMixin, RelativeObjectState
from omnigibson.utils.object_state_utils import sample_kinematics
from omnigibson.utils.usd_utils import BoundingBoxAPI
from omnigibson.utils.object_state_utils import m as os_m


class Inside(RelativeObjectState, KinematicsMixin, BooleanStateMixin):
    @classmethod
    def get_dependencies(cls):
        deps = super().get_dependencies()
        deps.update({AABB, HorizontalAdjacency, VerticalAdjacency})
        return deps

    def _set_value(self, other, new_value):
        if not new_value:
            raise NotImplementedError("Inside does not support set_value(False)")

        state = og.sim.dump_state(serialized=False)

        for _ in range(os_m.DEFAULT_HIGH_LEVEL_SAMPLING_ATTEMPTS):
            if sample_kinematics("inside", self.obj, other) and self.get_value(other):
                return True
            else:
                og.sim.load_state(state, serialized=False)

        return False

    def _get_value(self, other):
        self_half_box = ( self.obj.aabb[1] - self.obj.aabb[0] ) / 2
        other_half_box = ( other.aabb[1] - other.aabb[0] ) / 2
        self_pos = self.obj.get_position()
        other_pos = other.get_position()
        self_bbox = self.obj.native_bbox
        other_bbox = other.native_bbox

        if self_pos[0] < other_pos[0] - other_half_box[0] - 1e-2 or self_pos[0] > other_pos[0] + other_half_box[0] + 1e-2 \
            or self_pos[1] < other_pos[1] - other_half_box[1] - 1e-2 or self_pos[1] > other_pos[1] + other_half_box[1] + 1e-2 \
            or self_pos[2] < other_pos[2] - other_half_box[2] - 1e-2 or self_pos[2] > other_pos[2] + other_half_box[2] + 1e-2:
            return False
        if self_bbox[0] * self_bbox[1] * self_bbox[2] > other_bbox[0] * other_bbox[1] * other_bbox[2]:
            return False
        return True
