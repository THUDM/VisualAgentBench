import numpy as np
import re
import cv2
import omnigibson as og
from omnigibson.macros import gm
import yaml
from os import path
import os
from utils.env_utils import *
from utils.actions import *
import builtins
from gensim.models import KeyedVectors

# Make sure object states are enabled
gm.ENABLE_OBJECT_STATES = True
gm.USE_GPU_DYNAMICS = True

class Env(object):

    def __init__(self, args):

        self.args = args
        
        cfg = yaml.load(builtins.open("configs/og.yaml", "r"), Loader=yaml.FullLoader)
        cfg["scene"]["scene_model"] = args.scene
        cfg["task"]["activity_name"] = args.task

        self.env = og.Environment(configs=cfg)
        self.env.reset()
        
        self.robot = self.env.robots[0]
        self.grasped_obj = []
        self.camera = self.robot.sensors['robot0:eyes_Camera_sensor']
        self.camera.focal_length = 4.8

        self.prim_path_to_obj = {}                  # obj.prim_path -> obj

        self.seen_objs = set()                      # once seen objects
        self.visible_objs = set()                   # set of currently visible objects
        self.moveable_objs = set()                  # set of moveable objects
        self.rooms = []
        self.current_room = None

        for i, room_name in self.env.scene._seg_map.room_ins_id_to_ins_name.items():
            self.rooms.append(room_name)
        
        for i in self.env.scene.objects:
            self.prim_path_to_obj[i.prim_path] = i

        self.num_step = 0
        self.reward = - self.env.task._reward_functions['potential']._potential
        self.done = False
        self.task_objs = []
        self.task_obj_to_name = {}                  # task_obj -> "id.obj_name"

        fixed_objs = list(self.env.scene.fixed_objects.values())
        
        for key, value in self.env.task.object_scope.items():
            f = False
            if "agent" not in key and "floor" not in key:
                f = True
            if "floor" in key:
                for goal_condition in self.env.task.activity_natural_language_goal_conditions:
                    if "floor" in goal_condition:
                        f = True
                        break
            if f:
                self.task_objs.append(value.unwrapped)
                category = key.split('.')[0].split('_')[-1]
                self.task_obj_to_name[value.unwrapped] = f"{len(self.task_objs)}.{category}"
                if value.unwrapped not in fixed_objs:
                    self.moveable_objs.add(value.unwrapped)

        self.colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255), (255, 0, 255),
            (255, 255, 0), (255, 165, 0), (128, 0, 128), (255, 250, 205), (255, 102, 204),
            (0, 255, 127), (135, 206, 250), (255, 105, 180), (173, 255, 47), (255, 20, 147),
            (255, 215, 0), (255, 228, 181), (230, 230, 250), (57, 255, 20), (255, 69, 0),
            (0, 0, 128), (152, 251, 152), (238, 130, 238), (139, 69, 19), (255, 127, 80),
            (165, 42, 42), (0, 191, 255), (255, 20, 147), (165, 42, 42), (128, 128, 0)
        ]

        while len(self.colors) < len(self.task_objs):
            self.colors.append((np.random.randint(16, 255), np.random.randint(16, 255), np.random.randint(16, 255)))

        self.fridge_camera, self.fridge = None, None
        self.use_fridge_view = False
        fridge_in_task = False
        for obj in self.task_objs:
            if "fridge" in obj.name:
                fridge_in_task = True
                fridge_pos = obj.get_position()
                self.fridge = obj
                break
        if fridge_in_task:
            self.fridge_camera = og.sim.viewer_camera
            self.fridge_camera.focal_length = 4.8
            fridge_pos[2] = self.fridge.aabb[1][2] - 0.16
            self.fridge_camera.set_position(fridge_pos)
            fridge_camera_ori = np.array([0, 0, 1, 0])
            self.fridge_camera.set_orientation(fridge_camera_ori)
            self.fridge_camera.add_modality('seg_instance')
            self.fridge_camera._post_load()

        self.no_op = {'robot0': np.zeros(11)}
        for _ in range(16):
            state, reward, done, info = self.env.step(self.no_op)
            self.reward += reward
            self.done = info['done']['success']

        self.camera_orientation_id = 0
        self.camera_orientations = [np.array([-0.30927377, 0.54179592, 0.6829376, -0.38000415])]
        for _ in range(3):
            self.camera_orientations.append(trans_camera(self.camera_orientations[-1]))

        self.robot_camera_height = 1.05
        robot_camera_pos = self.camera.get_position()
        robot_camera_pos[2] = self.robot_camera_height
        self.camera.set_position(robot_camera_pos)
        self.robot_orientation = np.array([-1.96598936e-04, 1.99141558e-02, 2.81910330e-01, -9.59234059e-01])

        self.log_dir = args.log_dir
        if not path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        self.word2vec = KeyedVectors.load_word2vec_format('/GoogleNews-vectors-negative300.bin', binary=True)

        self.func_list = ['turn_left', 'turn_right', 'get_fridge_view', 'raise_camera', 'lower_camera', "grasp", "move", "put_inside", \
                     "put_on_top", "put_under", "put_next_to", "cook", "burn", "freeze", "heat", "open", \
                     "close", "toggle_on", "toggle_off", "move_to_room", 'done']

        self.func_vectors = {}
        for func_name in self.func_list:
            words = func_name.split('_')
            vectors = [self.word2vec[word] for word in words if word in self.word2vec]
            if len(vectors):
                self.func_vectors[func_name] = np.mean(vectors, axis=0)

    def get_obs(self):
        
        objs = set()
        
        if self.use_fridge_view:
            fridge_rgb = self.fridge_camera._get_obs()['rgb']
            fridge_rgb = cv2.cvtColor(fridge_rgb, cv2.COLOR_BGR2RGB)
            fridge_seg_instance = get_seg_instance(self.fridge_camera)
            fridge_img = self.label_som(fridge_rgb, fridge_seg_instance)
            img_path = path.join(self.log_dir, f"{self.num_step:03}.png")
            cv2.imwrite(img_path, fridge_img)
            
            objs = self.get_visible_objects(self.fridge_camera)
            self.use_fridge_view = False

        else:
            o = self.camera_orientations[self.camera_orientation_id]
            self.camera.set_orientation(o)
            for __ in range(6):
                state, reward, done, info = self.env.step(self.no_op)
                self.reward += reward
                self.done = info['done']['success']
            rgb = self.camera._get_obs()['rgb']
            rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
            seg_instance = get_seg_instance(self.camera)
            som_rgb = self.label_som(rgb, seg_instance)
            img_path = path.join(self.log_dir, f"{self.num_step:03}.png")
            cv2.imwrite(img_path, som_rgb)
            objs = self.get_visible_objects(self.camera)

        self.visible_objs = objs
        self.seen_objs.update(objs)

        grasped_obj = f"{self.task_obj_to_name[self.grasped_obj[0]]}" if self.grasped_obj != [] else None
        self.current_room = self.env.scene._seg_map.get_room_instance_by_point(self.robot.get_position()[:2])

        reward = - self.env.task._reward_functions['potential']._potential
        
        obs_dict = {
            "image": img_path.replace("\\", "/"),
            "grasped_obj": grasped_obj,
            "rooms": self.rooms,
            "current_room": self.current_room,
            "reward": reward,
            "done": self.done,
            "num_step": self.num_step
        }
        return obs_dict


    def step(self, action: str):

        self.num_step += 1
        
        if action == "None ACTION.":
            return False, "You should include \'ACTION: <the action code>\' in your response!"
        
        if "(" in action and ")" in action:
            func = action.split('(')[0]
            args = re.split(', |,', action.split('(')[-1].split(')')[0])
            args = [arg.split("=")[-1] for arg in args]
        
        else:
            return False, f"Invalid action! You should call the function using the format: function_name(arg)"
        
        for id, arg in enumerate(args):
            if (arg.startswith('"') or arg.startswith("'")) and (arg.endswith('"') or arg.endswith("'")):
                args[id] = arg[1:-1]
            if arg.startswith('_'):
                args[id] = arg[1:]
            if arg.endswith("_"):
                args[id] = arg[:-1]
        
        if func not in self.func_list:
            
            if func == "move_to_object" or func == "move_to_obj":
                return False, f"Invalid action! You should call the function in the Predefined Action List! Do you mean the function 'move'?"

            if func == "pick_up":
                return False, f"Invalid action! You should call the function in the Predefined Action List! Do you mean the function 'grasp'?"

            if func == "move_to":
                if len(args) > 0 and '.' in args[0] and args[0].split('.')[0].isdigit():
                    return False, f"Invalid action! You should call the function in the Predefined Action List! Do you mean the function 'move'?"
                else:
                    return False, f"Invalid action! You should call the function in the Predefined Action List! Do you mean the function 'move_to_room'?"
            
            if func == "place" or func == "put" or func == "place_at":
                return False, f"Invalid action! You should call the function in the Predefined Action List! Do you mean the function 'put_inside', 'put_on_top', 'put_under' or 'put_next_to'?"
            
            if func == "put_in" or func == "place_into":
                return False, f"Invalid action! You should call the function in the Predefined Action List! Do you mean the function 'put_inside'?"
            
            if func == "put_on" or func == "place_on":
                return False, f"Invalid action! You should call the function in the Predefined Action List! Do you mean the function 'put_on_top'?"
            
            else:
                words = func.split('_')
                vectors = [self.word2vec[word] for word in words if word in self.word2vec]
                if len(vectors):
                    new_function_call_vector = np.mean(vectors, axis=0)
                else:
                    return False, f"Invalid action! You should call the function in the Predefined Action List!"
                
                similarities = {fn: np.dot(new_function_call_vector, vec) / (np.linalg.norm(new_function_call_vector) * np.linalg.norm(vec)) for fn, vec in self.func_vectors.items()}

                if similarities != {}:
                    most_similar_function_name = max(similarities, key=similarities.get)
                else:
                    return False, f"Invalid action! You should call the function in the Predefined Action List!"
                
                return False, f"Invalid action! You should call the function in the Predefined Action List! Do you mean the function '{most_similar_function_name}'?"

        if func == "turn_left":
            if args == ['']:
                self.camera_orientation_id = (self.camera_orientation_id + 1) % 4
                self.camera.set_orientation(self.camera_orientations[self.camera_orientation_id])
                for __ in range(6):
                    state, reward, done, info = self.env.step(self.no_op)
                    self.reward += reward
                    self.done = info['done']['success']
                return True, "Turned left successfully!"
            else:
                return False, f"turn_left doesn't need any arguments!"
        
        if func == "turn_right":
            if args == ['']:
                self.camera_orientation_id = (self.camera_orientation_id + 3) % 4
                self.camera.set_orientation(self.camera_orientations[self.camera_orientation_id])
                for __ in range(6):
                    state, reward, done, info = self.env.step(self.no_op)
                    self.reward += reward
                    self.done = info['done']['success']
                return True, "Turned right successfully!"
            else:
                return False, f"turn_right doesn't need any arguments!"
        
        if func == "get_fridge_view":
            if args == ['']:
                if self.fridge_camera is None:
                    return False, f"No fridge in the scene!"
                elif distance_to_cuboid(self.robot.get_position(), self.fridge.aabb) > 2.7:
                    return False, f"Fridge is too far away!"
                elif not self.fridge.states[og.object_states.Open].get_value():
                    return False, f"Fridge is not open!"
                self.use_fridge_view = True
                return True, "Get fridge view successfully!"
            else:
                return False, f"get_fridge_view doesn't need any arguments!"
            
        if func == "raise_camera":
            if args == [''] and self.robot_camera_height <= 1.1:
                self.robot_camera_height += 0.5
                camera_pos = self.camera.get_position()
                camera_pos[2] = self.robot_camera_height
                self.camera.set_position(camera_pos)
                return True, "Raise camera successfully!"
            elif args != ['']:
                return False, f"raise_camera doesn't need any arguments!"
            else:
                return False, f"Camera height is already at the highest level!"
            
        if func == "lower_camera":
            if args == [''] and self.robot_camera_height >= 0.8:
                self.robot_camera_height -= 0.5
                camera_pos = self.camera.get_position()
                camera_pos[2] = self.robot_camera_height
                self.camera.set_position(camera_pos)
                return True, "Lower camera successfully!"
            elif args != ['']:
                return False, f"lower_camera doesn't need any arguments!"
            else:
                return False, f"Camera height is already at the lowest level!"

        if func == action or len(args) == 0 or args[0] == "":
            return False, f"Invalid action! You should call the function using the format: function_name(arg)"

        arg_objs = []

        if func != "move_to_room":
            for arg in args:
                
                if "." in arg:
                    arg_id = arg.split('.')[0]
                    arg_name = arg.split('.')[-1]
                    flag, id = is_digit(arg_id)
                elif "_" in arg:
                    arg_id = arg.split('_')[0]
                    arg_name = arg.split('_')[-1]
                    flag, id = is_digit(arg_id)
                else:
                    arg_id, arg_name = arg, arg
                    flag, id = is_digit(arg_id)                

                if flag:
                    if id < 1 or id > len(self.task_objs):
                        return False, f"Invalid object id {id}! The corresponding object does not exist."
                    obj = self.task_objs[id-1]
                    if arg_id != arg and self.task_obj_to_name[obj] != arg and self.task_obj_to_name[obj].split('.')[-1] != arg_name:
                        return False, f"ID {id} doesn't match object '{arg_name}'. Maybe you take the wrong object id."
                else:
                    return False, f"Object {arg} not found in the scene! You should use the digital object identifier shown in the image."
                
                if func != "move" and obj not in self.visible_objs and obj not in self.grasped_obj and \
                    distance_to_cuboid(self.robot.get_position()[:2], (obj.aabb[0][:2], obj.aabb[1][:2])) > 2.4:
                    return False, f"Can not execute the action! Object {arg} is not visible to the robot."
                if func == "move" and obj not in self.seen_objs and obj not in self.visible_objs and obj not in self.grasped_obj:
                    return False, f"Can not move to the object! Object {arg} hasn't seen by the robot."
                if func == "move" and obj not in self.visible_objs and obj not in self.grasped_obj and \
                    self.env.scene._seg_map.get_room_instance_by_point(obj.get_position()[:2]) != self.current_room and "None" not in self.current_room:
                    return False, f"Can not move to the object! Object {arg} isn't in the same room with the robot."
                
                arg_objs.append(obj)

        func_list = ["grasp", "move", "put_inside", "put_on_top", "put_under", "put_next_to", "cook", "burn", "freeze", "heat", "open", \
                     "close", "toggle_on", "toggle_off", "move_to_room"]

        if func not in func_list:
            return False, f"Invalid action function! You should call the function in the Predefined Action List!"

        if func in func_list[2:6]:
            if len(args) != 2:
                return False, f"Need 2 arguments for action {func}!"
        else:
            if len(args) != 1:
                return False, f"Need 1 argument for action {func}!"

        ret, msg = None, None    
        
        if func == "grasp":
            obj = arg_objs[0]
            if obj not in self.moveable_objs:
                ret, msg = False, f"Can not grasp! Object {self.task_obj_to_name[arg_objs[0]]} is not moveable!"
            else:
                ret, msg = grasp(self.robot, self.grasped_obj, obj, self.task_objs)
        
        elif func == "move":
            obj = arg_objs[0]
            pos = self.calc_move_to_pos(obj)
            ret, msg = move(self.robot, obj, pos, self.grasped_obj, self.task_objs)
            
            if ret:
                best_orientation = 0
                best_count = 0
                for _ in range(4):
                    o = self.camera_orientations[_]
                    self.camera.set_orientation(o)
                    for __ in range(6):
                        state, reward, done, info = self.env.step(self.no_op)
                        self.reward += reward
                        self.done = info['done']['success']
                    seg_instance = get_seg_instance(self.camera)
                    mapping = seg_instance[1]
                    seg_instance = seg_instance[0]
                    for row in mapping:
                        if obj.prim_path == row[1]:
                            obj_id = row[0]
                            break
                    count = np.count_nonzero(seg_instance == obj_id)
                    if count < 900 * 720 and count > best_count:
                        best_count = count
                        best_orientation = _
                if best_count > 0:
                    self.camera_orientation_id = best_orientation       
        
        elif func == "put_inside":
            obj = arg_objs[0]
            container = arg_objs[1]
            ret, msg = put_inside(self.robot, obj, self.grasped_obj, container, self.task_objs)
        
        elif func == "put_on_top":
            obj = arg_objs[0]
            surface = arg_objs[1]
            ret, msg = put_on_top(self.robot, obj, self.grasped_obj, surface, self.task_objs)
        
        elif func == "put_under":
            obj = arg_objs[0]
            surface = arg_objs[1]
            ret, msg = put_under(self.robot, obj, self.grasped_obj, surface, self.task_objs)
        
        elif func == "put_next_to":
            obj = arg_objs[0]
            surface = arg_objs[1]
            ret, msg = put_next_to(self.robot, obj, self.grasped_obj, surface, self.task_objs)
        
        elif func == "cook":
            obj = arg_objs[0]
            ret, msg = cook(self.robot, obj)
        
        elif func == "burn":
            obj = arg_objs[0]
            ret, msg = burn(self.robot, obj)
        
        elif func == "freeze":
            obj = arg_objs[0]
            ret, msg = freeze(self.robot, obj)
        
        elif func == "heat":
            obj = arg_objs[0]
            ret, msg = heat(self.robot, obj)
        
        elif func == "open":
            obj = arg_objs[0]
            ret, msg = open(self.robot, obj)
        
        elif func == "close":
            obj = arg_objs[0]
            ret, msg = close(self.robot, obj)

        elif func == "toggle_on":
            obj = arg_objs[0]
            ret, msg = toggle_on(self.robot, obj)
        
        elif func == "toggle_off":
            obj = arg_objs[0]
            ret, msg = toggle_off(self.robot, obj)

        elif func == "move_to_room":
            room_name = args[0]
            if room_name not in self.env.scene._seg_map.room_ins_id_to_ins_name.values():
                return False, f"Invalid room name!"
            _, robot_pos = self.env.scene._seg_map.get_random_point_by_room_instance(room_name)
            robot_pos[2] = 0.004
            ret, msg = move(self.robot, None, robot_pos, self.grasped_obj, self.task_objs)
        
        else:
            return False, f"Invalid action! You should call the function in the Predefined Action List!"
        
        if ret:
            robot_pos = self.robot.get_position()
            robot_pos[2] = 0.004
            self.robot.set_position(robot_pos)
            self.robot.set_orientation(self.robot_orientation)
            for _ in range(16):
                state, reward, done, info = self.env.step(self.no_op)
                self.reward += reward
                self.done = info['done']['success']
            return True, msg
        
        else:
            return False, msg

    def get_visible_objects(self, camera):
        visible_objs = set()
        seg_instance = get_seg_instance(camera)
        mapping = seg_instance[1]
        seg_instance = seg_instance[0]
        count = np.unique(seg_instance, return_counts = True)
        for i in range(len(count[0])):
            id, cnt = count[0][i].item(), count[1][i].item()
            if id == 0:
                continue
            obj = self.prim_path_to_obj[mapping[id-1][1]]
            if obj in self.task_objs:
                visible_objs.add(obj)
        return visible_objs

    def calc_move_to_pos(self, obj):
        if obj.category == "floors":
            pos = obj.get_position()
            pos[2] = 0.004
            return pos
        best_orientation = 0
        best_count = 0
        for _ in range(4):
            o = self.camera_orientations[_]
            self.camera.set_orientation(o)
            for __ in range(6):
                state, reward, done, info = self.env.step(self.no_op)
                self.reward += reward
                self.done = info['done']['success']
            
            seg_instance = get_seg_instance(self.camera)
            mapping = seg_instance[1]
            seg_instance = seg_instance[0]
            for row in mapping:
                if obj.prim_path == row[1]:
                    obj_id = row[0]
                    break
            count = np.count_nonzero(seg_instance == obj_id)
            if count < 900 * 720 and count > best_count:
                best_count = count
                best_orientation = _
            
        if best_count > 0:
            self.camera_orientation_id = best_orientation
            self.camera.set_orientation(self.camera_orientations[self.camera_orientation_id])
            pos = self.robot.get_position()
            obj_pos = obj.get_position()
            while distance_to_cuboid(pos[:2], (obj.aabb[0][:2], obj.aabb[1][:2])) > 1.1:
                pos = 0.7 * pos + 0.3 * obj_pos
                pos[2] = 0.004
            while cal_dis(pos[:2], obj_pos[:2]) < 0.7 or (pos[0] >= obj.aabb[0][0] and pos[0] <= obj.aabb[1][0] and pos[1] >= obj.aabb[0][1] and pos[1] <= obj.aabb[1][1]):
                pos = obj_pos + np.random.uniform(1.2, 1.5) * (pos - obj_pos)
                pos[2] = 0.004
            return pos
        
        walls = list(self.env.scene.object_registry._objects_by_category['walls'])
        obj_pos = obj.get_position()
        closest_walls = sorted(walls, key=lambda x: distance_to_cuboid(obj_pos, x.aabb))[:2]
        pos = (np.clip(obj_pos, *closest_walls[0].aabb) + np.clip(obj_pos, *closest_walls[1].aabb)) / 2
        pos[2] = 0.004
        if distance_to_cuboid(pos[:2], (obj.aabb[0][:2], obj.aabb[1][:2])) < 1:
            pos = obj_pos - np.random.uniform(1.4, 1.7) * (pos - obj_pos)
            pos[2] = 0.004
        while distance_to_cuboid(pos[:2], (obj.aabb[0][:2], obj.aabb[1][:2])) < 1:
            pos = obj_pos + np.random.uniform(1.4, 1.6) * (pos - obj_pos)
            pos[2] = 0.004
        while distance_to_cuboid(pos[:2], (obj.aabb[0][:2], obj.aabb[1][:2])) > 1.2:
            pos = obj_pos + np.random.uniform(0.85, 0.9) * (pos - obj_pos)
            pos[2] = 0.004
        while distance_to_cuboid(pos[:2], (obj.aabb[0][:2], obj.aabb[1][:2])) < 0.7:
            pos = obj_pos + np.random.uniform(1.2, 1.5) * (pos - obj_pos)
            pos[2] = 0.004
        return pos

    def label_som(self, rgb, seg_instance):
        mapping = seg_instance[1]
        seg_instance = seg_instance[0]
        count = np.unique(seg_instance, return_counts = True)
        id_to_count = {}
        for _ in range(len(count[0])):
            id, cnt = count[0][_].item(), count[1][_].item()
            id_to_count[id] = cnt
        id_to_range = {}
        for id, count in id_to_count.items():
            if id == 0 or count < 2 or self.prim_path_to_obj[mapping[id-1][1]] not in self.task_objs:
                continue
            coords = np.where(seg_instance == id)
            x1, y1, x2, y2 = min(coords[1]), min(coords[0]), max(coords[1]), max(coords[0])
            id_to_range[id] = [x1, y1, x2, y2]

        rects, texts, colors = [], [], []

        for id, _range in id_to_range.items():    
            color = self.colors[self.task_objs.index(self.prim_path_to_obj[mapping[id-1][1]])]
            cv2.rectangle(rgb, (_range[0], _range[1]), (_range[2], _range[3]), color, 2)
            text = f"{self.task_obj_to_name[self.prim_path_to_obj[mapping[id-1][1]]]}"
            rects.append(_range)
            texts.append(text)
            colors.append(color)

        rgb = place_text_boxes(rgb, rects, texts, colors)

        return rgb

    def close(self):
        self.env.close()
