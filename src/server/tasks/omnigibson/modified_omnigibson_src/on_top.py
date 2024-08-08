import omnigibson as og
from omnigibson.object_states.kinematics_mixin import KinematicsMixin
from omnigibson.object_states.adjacency import VerticalAdjacency
from omnigibson.object_states.object_state_base import BooleanStateMixin, RelativeObjectState
from omnigibson.object_states.touching import Touching
from omnigibson.utils.object_state_utils import sample_kinematics
from omnigibson.utils.object_state_utils import m as os_m


class OnTop(KinematicsMixin, RelativeObjectState, BooleanStateMixin):

    @classmethod
    def get_dependencies(cls):
        deps = super().get_dependencies()
        deps.update({Touching, VerticalAdjacency})
        return deps

    def _set_value(self, other, new_value):
        if not new_value:
            raise NotImplementedError("OnTop does not support set_value(False)")

        state = og.sim.dump_state(serialized=False)

        for _ in range(os_m.DEFAULT_HIGH_LEVEL_SAMPLING_ATTEMPTS):
            if sample_kinematics("onTop", self.obj, other) and self.get_value(other):
                return True
            else:
                og.sim.load_state(state, serialized=False)

        return False

    def _get_value(self, other):

        touching = self.obj.states[Touching].get_value(other)
        # if not touching:
        #     return False

        adjacency = self.obj.states[VerticalAdjacency].get_value()
        other_adjacency = other.states[VerticalAdjacency].get_value()
        
        # return other in adjacency.negative_neighbors and other not in adjacency.positive_neighbors and self.obj not in other_adjacency.negative_neighbors

        if other in adjacency.negative_neighbors and other not in adjacency.positive_neighbors and self.obj not in other_adjacency.negative_neighbors:
            return True
        
        self_half_box = ( self.obj.aabb[1] - self.obj.aabb[0] ) / 2
        other_half_box = ( other.aabb[1] - other.aabb[0] ) / 2
        self_pos = self.obj.get_position()
        other_pos = other.get_position()

        if self_pos[0] >= other_pos[0] - other_half_box[0] - 1e-2 and self_pos[0] <= other_pos[0] + other_half_box[0] + 1e-2 \
            and self_pos[1] >= other_pos[1] - other_half_box[1] - 1e-2 and self_pos[1] <= other_pos[1] + other_half_box[1] + 1e-2 \
            and self_pos[2] - self_half_box[2] >= other_pos[2] + other_half_box[2] - 1e-2 \
            and self_pos[2] <= other_pos[2] + other_half_box[2] + 2 * self_half_box[2] + 1e-2:
            return True
        return False
