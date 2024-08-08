import numpy as np

from omnigibson.object_states.aabb import AABB
from omnigibson.object_states.adjacency import HorizontalAdjacency, flatten_planes
from omnigibson.object_states.kinematics_mixin import KinematicsMixin
from omnigibson.object_states.object_state_base import BooleanStateMixin, RelativeObjectState


class NextTo(KinematicsMixin, RelativeObjectState, BooleanStateMixin):

    @classmethod
    def get_dependencies(cls):
        deps = super().get_dependencies()
        deps.add(HorizontalAdjacency)
        return deps

    def _get_value(self, other):
        if other == self.obj:
            return False
        objA_states = self.obj.states
        objB_states = other.states

        assert AABB in objA_states
        assert AABB in objB_states

        objA_aabb = objA_states[AABB].get_value()
        objB_aabb = objB_states[AABB].get_value()

        self_pos = self.obj.get_position()
        other_pos = other.get_position()
        self_aabb_center = self.obj.aabb_center
        other_aabb_center = other.aabb_center
        objA_aabb = (objA_aabb[0] + self_pos - self_aabb_center, objA_aabb[1] + self_pos - self_aabb_center)
        objB_aabb = (objB_aabb[0] + other_pos - other_aabb_center, objB_aabb[1] + other_pos - other_aabb_center)

        objA_lower, objA_upper = objA_aabb
        objB_lower, objB_upper = objB_aabb
        distance_vec = []
        for dim in range(3):
            glb = max(objA_lower[dim], objB_lower[dim])
            lub = min(objA_upper[dim], objB_upper[dim])
            distance_vec.append(max(0, glb - lub))
        distance = np.linalg.norm(np.array(distance_vec))
        objA_dims = objA_upper - objA_lower
        objB_dims = objB_upper - objB_lower
        avg_aabb_length = np.mean(objA_dims + objB_dims)
        
        if distance > 2.4 * avg_aabb_length:
            return False

        return True
