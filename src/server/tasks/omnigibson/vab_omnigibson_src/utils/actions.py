import numpy as np
import omnigibson as og
from utils.env_utils import *
delta=1.2

def grasp(robot, grasped_obj, obj, all_objs):
    
    if len(grasped_obj):
        return False, f"Cannot grasp! Robot already holds something!"
    
    if obj.mass > 128:
        return False, f"Cannot grasp! Object is too heavy!"
    
    robot_pos = robot.get_position()
    obj_pos = obj.get_position()
    dis = distance_to_cuboid(robot_pos[:2], (obj.aabb[0][:2], obj.aabb[1][:2]))
    
    if dis > delta:
        return False, f"Cannot grasp! The object is not within reach of the robot!"
    
    else:
        robot_pos[2] += robot.aabb_center[2] - 0.2

        inside_obj_pos = []
        on_top_obj_pos = []

        for o in all_objs:
            if o == obj or o.mass > 128:
                continue
            if o.states[og.object_states.Inside].get_value(obj):
                inside_obj_pos.append((o, o.get_position() - obj_pos))
            if o.states[og.object_states.OnTop].get_value(obj):
                on_top_obj_pos.append((o, o.get_position() - obj_pos))

        obj.set_position(robot_pos)

        flag_inside = True
        for o, pos in inside_obj_pos:
            o.set_position(robot_pos + pos)
            if not o.states[og.object_states.Inside].get_value(obj):
                o.states[og.object_states.Inside]._set_value(obj, True)
                if not o.states[og.object_states.Inside].get_value(obj):
                    flag_inside = False

        flag_ontop = True
        for o, pos in on_top_obj_pos:
            o.set_position(robot_pos + pos)
            if not o.states[og.object_states.OnTop].get_value(obj):
                o.states[og.object_states.OnTop]._set_value(obj, True)
                if not o.states[og.object_states.OnTop].get_value(obj):
                    flag_ontop = False

        grasped_obj.append(obj)
        msg = "Grasped successfully!"
        if not flag_ontop:
            msg += " But something on top of the object is left there!"
        if not flag_inside:
            msg += " But something inside the object is left there!"
        
        return True, msg


def move(robot, obj, pos, grasped_obj, all_objs):
    robot.set_position(pos)
    if len(grasped_obj):
        update_obj(robot, grasped_obj[0], all_objs)
    return True, "Moved successfully!"


def put_inside(robot, obj, grasped_obj, container, all_objs):
    
    if len(grasped_obj) == 0 or grasped_obj[0] != obj:
        return False, "Cannot put inside! Robot does not hold the object!"
    
    if obj.mass > 128:
        return False, f"Cannot put inside! Object is too heavy!"

    if og.object_states.Open in container.states and not container.states[og.object_states.Open].get_value():
        return False, "Cannot put inside! The container is closed!"

    robot_pos = robot.get_position()
    container_pos = container.get_position()
    
    aabb = container.aabb[1] - container.aabb[0]
    
    possible_pos = [np.copy(container_pos) for _ in range(9)]
    possible_pos[7][2] += aabb[2] / 10
    possible_pos[2][2] -= aabb[2] / 10
    possible_pos[8][2] += aabb[2] / 8
    possible_pos[1][2] -= aabb[2] / 8
    possible_pos[3][0] += aabb[0] / 10
    possible_pos[4][0] -= aabb[0] / 10
    possible_pos[5][1] += aabb[1] / 10
    possible_pos[6][1] -= aabb[1] / 10
    
    dis = distance_to_cuboid(robot_pos, container.aabb)
    
    if dis > delta:
        return False, f"Cannot put inside! The container is not within reach of the robot!"
    
    else:

        inside_obj_pos = []
        on_top_obj_pos = []

        for o in all_objs:
            if o == obj or o.mass > 128:
                continue
            if o.states[og.object_states.Inside].get_value(obj):
                inside_obj_pos.append((o, o.get_position() - obj.get_position()))
            if o.states[og.object_states.OnTop].get_value(obj):
                on_top_obj_pos.append((o, o.get_position() - obj.get_position()))
        
        okay = False
        for p in possible_pos:
            obj.set_position(p)
            if not obj.states[og.object_states.Inside].get_value(container):
                obj.states[og.object_states.Inside]._set_value(container, True)
                if obj.states[og.object_states.Inside].get_value(container):
                    okay = True
                    break
            else:
                okay = True
                break
        if not okay:
            robot_pos = robot.get_position()
            robot_pos[2] += robot.aabb_center[2] - 0.2
            obj.set_position(robot_pos)
            return False, "Cannot put inside! The container is full!"

        for o, pos in inside_obj_pos:
            o.set_position(p + pos)
            if not o.states[og.object_states.Inside].get_value(obj):
                o.states[og.object_states.Inside]._set_value(obj, True)
        for o, pos in on_top_obj_pos:
            o.set_position(p + pos)
            if not o.states[og.object_states.OnTop].get_value(obj):
                o.states[og.object_states.OnTop]._set_value(obj, True)

        grasped_obj.remove(obj)    
        return True, "Put inside successfully!"


def put_on_top(robot, obj, grasped_obj, surface, all_objs):
    
    if len(grasped_obj) == 0 or grasped_obj[0] != obj:
        return False, "Cannot put on top! Robot does not hold the object!"
    
    if obj.mass > 128:
        return False, f"Cannot put on top! Object is too heavy!"

    robot_pos = robot.get_position()
    surface_pos = surface.get_position()
    surface_pos[2] = surface_pos[2] + (surface.aabb[1][2] - surface.aabb[0][2] + obj.aabb[1][2] - obj.aabb[0][2]) / 2 + 5e-3
    
    aabb = surface.aabb[1] - surface.aabb[0]
    
    possible_pos = [np.copy(surface_pos) for _ in range(5)]
    possible_pos[1][0] -= aabb[0] / 6
    possible_pos[2][1] -= aabb[1] / 6
    possible_pos[3][0] += aabb[0] / 6
    possible_pos[4][1] += aabb[1] / 6
    
    dis = distance_to_cuboid(robot_pos, surface.aabb)
    
    if dis > delta:
        return False, f"Cannot put on top! The surface is not within reach of the robot!"
    
    else:

        inside_obj_pos = []
        on_top_obj_pos = []

        for o in all_objs:
            if o == obj or o.mass > 128:
                continue
            if o.states[og.object_states.Inside].get_value(obj):
                inside_obj_pos.append((o, o.get_position() - obj.get_position()))
            if o.states[og.object_states.OnTop].get_value(obj):
                on_top_obj_pos.append((o, o.get_position() - obj.get_position()))
        
        okay = False
        for p in possible_pos:
            obj.set_position(p)
            if not obj.states[og.object_states.OnTop].get_value(surface):
                obj.states[og.object_states.OnTop]._set_value(surface, True)
                if obj.states[og.object_states.OnTop].get_value(surface):
                    okay = True
                    break
            else:
                okay = True
                break
        if not okay:
            robot_pos = robot.get_position()
            robot_pos[2] += robot.aabb_center[2] - 0.2
            obj.set_position(robot_pos)
            return False, "Cannot put on top! The surface is full!"

        for o, pos in inside_obj_pos:
            o.set_position(p + pos)
            if not o.states[og.object_states.Inside].get_value(obj):
                o.states[og.object_states.Inside]._set_value(obj, True)
        for o, pos in on_top_obj_pos:
            o.set_position(p + pos)
            if not o.states[og.object_states.OnTop].get_value(obj):
                o.states[og.object_states.OnTop]._set_value(obj, True)

        grasped_obj.remove(obj)    
        return True, "Put on top successfully!"


def put_under(robot, obj, grasped_obj, surface, all_objs):
    
    if len(grasped_obj) == 0 or grasped_obj[0] != obj:
        return False, "Cannot put under! Robot does not hold the object!"
    
    if obj.mass > 128:
        return False, f"Cannot put under! Object is too heavy!"

    robot_pos = robot.get_position()
    surface_pos = surface.get_position()
    surface_pos[2] = surface_pos[2] - (surface.aabb[1][2] - surface.aabb[0][2])/2 - (obj.aabb[1][2] - obj.aabb[0][2])
    
    aabb = surface.aabb[1] - surface.aabb[0]
    
    possible_pos = [np.copy(surface_pos) for _ in range(5)]
    possible_pos[1][0] -= aabb[0] / 6
    possible_pos[2][1] -= aabb[1] / 6
    possible_pos[3][0] += aabb[0] / 6
    possible_pos[4][1] += aabb[1] / 6
    
    dis = distance_to_cuboid(robot_pos, surface.aabb)
    
    if dis > delta:
        return False, f"Cannot put under! The surface is not within reach of the robot!"
    
    else:

        inside_obj_pos = []
        on_top_obj_pos = []

        for o in all_objs:
            if o == obj or o.mass > 128:
                continue
            if o.states[og.object_states.Inside].get_value(obj):
                inside_obj_pos.append((o, o.get_position() - obj.get_position()))
            if o.states[og.object_states.OnTop].get_value(obj):
                on_top_obj_pos.append((o, o.get_position() - obj.get_position()))
        
        okay = False
        for p in possible_pos:
            obj.set_position(p)
            if not obj.states[og.object_states.Under].get_value(surface):
                obj.states[og.object_states.Under]._set_value(surface, True)
                if obj.states[og.object_states.Under].get_value(surface):
                    okay = True
                    break
            else:
                okay = True
                break
        if not okay:
            robot_pos = robot.get_position()
            robot_pos[2] += robot.aabb_center[2] - 0.2
            obj.set_position(robot_pos)
            return False, "Cannot put under! The surface is full!"

        for o, pos in inside_obj_pos:
            o.set_position(p + pos)
            if not o.states[og.object_states.Inside].get_value(obj):
                o.states[og.object_states.Inside]._set_value(obj, True)
        for o, pos in on_top_obj_pos:
            o.set_position(p + pos)
            if not o.states[og.object_states.OnTop].get_value(obj):
                o.states[og.object_states.OnTop]._set_value(obj, True)

        grasped_obj.remove(obj)    
        return True, "Put under successfully!"


def put_next_to(robot, obj, grasped_obj, surface, all_objs):

    if len(grasped_obj) == 0 or grasped_obj[0] != obj:
        return False, "Cannot put next to! Robot doesn't hold the object!"
    
    if obj.mass > 128:
        return False, f"Cannot put next to! Object is too heavy!"
    
    robot_pos = robot.get_position()
    surface_pos = surface.get_position()
    possible_pos = [np.copy(surface_pos) for _ in range(4)]
    possible_pos[0][0] -= (surface.aabb[1][0] - surface.aabb[0][0]) / 2
    possible_pos[1][0] += (surface.aabb[1][0] - surface.aabb[0][0]) / 2
    possible_pos[2][1] -= (surface.aabb[1][1] - surface.aabb[0][1]) / 2
    possible_pos[3][1] += (surface.aabb[1][1] - surface.aabb[0][1]) / 2
    dis = distance_to_cuboid(robot_pos, surface.aabb)
    
    if dis > delta:
        return False, f"Cannot put next to! The object is not within reach of the robot!"
    
    else:

        inside_obj_pos = []
        on_top_obj_pos = []

        for o in all_objs:
            if o == obj or o.mass > 128:
                continue
            if o.states[og.object_states.Inside].get_value(obj):
                inside_obj_pos.append((o, o.get_position() - obj.get_position()))
            if o.states[og.object_states.OnTop].get_value(obj):
                on_top_obj_pos.append((o, o.get_position() - obj.get_position()))

        flag = False
        for p in possible_pos:
            obj.set_position(p)
            if obj.states[og.object_states.NextTo].get_value(surface):
                flag = True
                break

        if not flag:
            robot_pos = robot.get_position()
            robot_pos[2] += robot.aabb_center[2] - 0.2
            obj.set_position(robot_pos)
            return False, "Cannot put next to! The space around the object is occupied!"

        for o, pos in inside_obj_pos:
            o.set_position(pos + p)
            if not o.states[og.object_states.Inside].get_value(obj):
                o.states[og.object_states.Inside]._set_value(obj, True)

        for o, pos in on_top_obj_pos:
            o.set_position(pos + p)
            if not o.states[og.object_states.OnTop].get_value(obj):
                o.states[og.object_states.OnTop]._set_value(obj, True)

        grasped_obj.remove(obj)
        return True, "Put next to successfully!"


def cook(robot, obj):

    if og.object_states.Cooked not in obj.states:
        return False, "Cannot cook! Object is not cookable!"
    
    robot_pos = robot.get_position()
    dis = distance_to_cuboid(robot_pos, obj.aabb)
    if dis > delta:
        return False, f"Cannot cook! The object is not within reach of the robot!"
    
    else:
        obj.states[og.object_states.Cooked].set_value(True)
        if not obj.states[og.object_states.Cooked].get_value():
            return False, "Cannot cook! Something went wrong!"
        return True, "Cooked successfully!"


def burn(robot, obj):

    if og.object_states.Burnt not in obj.states:
        return False, "Cannot burn! Object is not burnable!"
    
    robot_pos = robot.get_position()
    dis = distance_to_cuboid(robot_pos, obj.aabb)
    if dis > delta:
        return False, f"Cannot burn! The object is not within reach of the robot!"
    
    else:
        obj.states[og.object_states.Burnt].set_value(True)
        if not obj.states[og.object_states.Burnt].get_value():
            return False, "Cannot burn! Something went wrong!"
        return True, "Burnt successfully!"


def freeze(robot, obj):

    if og.object_states.Frozen not in obj.states:
        return False, "Cannot freeze! Object is not freezable!"
    
    robot_pos = robot.get_position()
    dis = distance_to_cuboid(robot_pos, obj.aabb)
    if dis > delta:
        return False, f"Cannot freeze! The object is not within reach of the robot!"
    
    else:
        obj.states[og.object_states.Frozen].set_value(True)
        if not obj.states[og.object_states.Frozen].get_value():
            return False, "Cannot freeze! Something went wrong!"
        return True, "Frozen successfully!"


def heat(robot, obj):
    
    if og.object_states.Heated not in obj.states:
        return False, "Cannot heat! Object is not heatable!"
    
    robot_pos = robot.get_position()
    dis = distance_to_cuboid(robot_pos, obj.aabb)
    if dis > delta:
        return False, f"Cannot heat! The object is not within reach of the robot!"
    
    else:
        obj.states[og.object_states.Heated].set_value(True)
        if not obj.states[og.object_states.Heated].get_value():
            return False, "Cannot heat! Something went wrong!"
        return True, "Heated successfully!"


def open(robot, obj):
        
    if og.object_states.Open not in obj.states:
        return False, "Cannot open! Object is not openable!"
    
    robot_pos = robot.get_position()
    dis = distance_to_cuboid(robot_pos, obj.aabb)
    if dis > delta:
        return False, f"Cannot open! The object is not within reach of the robot!"
    
    else:
        for _ in range(4):
            obj.states[og.object_states.Open].set_value(True)
        if not obj.states[og.object_states.Open].get_value():
            return False, "Cannot open! Something went wrong!"
        return True, "Opened successfully!"
    

def close(robot, obj):

    if og.object_states.Open not in obj.states:
        return False, "Cannot close! Object is not openable!"
    
    robot_pos = robot.get_position()
    dis = distance_to_cuboid(robot_pos, obj.aabb)
    if dis > delta:
        return False, f"Cannot close! The object is not within reach of the robot!"
    
    else:
        obj.states[og.object_states.Open].set_value(False)
        if obj.states[og.object_states.Open].get_value():
            return False, "Cannot close! Something went wrong!"
        return True, "Closed successfully!"


def toggle_on(robot, obj):

    if og.object_states.ToggledOn not in obj.states:
        return False, "Cannot toggle on! Object is not toggleable!"
    
    robot_pos = robot.get_position()
    dis = distance_to_cuboid(robot_pos, obj.aabb)
    if dis > delta:
        return False, f"Cannot toggle on! The object is not within reach of the robot!"
    
    else:
        obj.states[og.object_states.ToggledOn].set_value(True)
        if not obj.states[og.object_states.ToggledOn].get_value():
            return False, "Cannot toggle on! Something went wrong!"
        return True, "Toggled on successfully!"
    

def toggle_off(robot, obj):

    if og.object_states.ToggledOn not in obj.states:
        return False, "Cannot toggle off! Object is not toggleable!"
    
    robot_pos = robot.get_position()
    dis = distance_to_cuboid(robot_pos, obj.aabb)
    if dis > delta:
        return False, f"Cannot toggle off! The object is not within reach of the robot!"
    
    else:
        obj.states[og.object_states.ToggledOn].set_value(False)
        if obj.states[og.object_states.ToggledOn].get_value():
            return False, "Cannot toggle off! Something went wrong!"
        return True, "Toggled off successfully!"
