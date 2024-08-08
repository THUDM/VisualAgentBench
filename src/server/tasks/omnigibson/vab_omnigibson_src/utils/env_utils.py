import numpy as np
import cv2
from scipy.spatial.transform import Rotation as R
import omnigibson as og

def cal_dis(pos1, pos2):
    return np.linalg.norm(pos1 - pos2)

def distance_to_cuboid(point, cuboid):
    min_corner, max_corner = cuboid
    closest_point = np.clip(point, min_corner, max_corner)
    return np.linalg.norm(point - closest_point)

def quaternion_multiply(q1, q2):
    # calculate the multiply of two quaternion
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    return np.array([x, y, z, w])

def trans_camera(q):
    random_yaw = np.pi / 2
    yaw_orn = R.from_euler("Z", random_yaw)
    new_camera_orn = quaternion_multiply(yaw_orn.as_quat(), q)
    return new_camera_orn

def update_obj(robot, obj, all_objs):
    # update objects position according to robot position
    obj_pos = obj.get_position()
    inside_obj_pos = []
    on_top_obj_pos = []

    for o in all_objs:
        if o == obj:
            continue
        if o.states[og.object_states.Inside].get_value(obj):
            inside_obj_pos.append((o, o.get_position() - obj_pos))
        if o.states[og.object_states.OnTop].get_value(obj):
            on_top_obj_pos.append((o, o.get_position() - obj_pos))

    robot_pos = robot.get_position()
    robot_pos[2] += robot.aabb_center[2] - 0.2
    obj.set_position(robot_pos)

    for o, pos in inside_obj_pos:
        o.set_position(robot_pos + pos)
        if not o.states[og.object_states.Inside].get_value(obj):
            o.states[og.object_states.Inside].set_value(obj, True)
            
    for o, pos in on_top_obj_pos:
        o.set_position(robot_pos + pos)
        if not o.states[og.object_states.OnTop].get_value(obj):
            o.states[og.object_states.OnTop].set_value(obj, True)

def get_text_color(background_color):
    if 0.213*background_color[0] + 0.715*background_color[1] + 0.072*background_color[2] > 255 / 2:
        return (0, 0, 0)
    else:
        return (255, 255, 255)
    
def overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))

def place_text_boxes(image, rects, texts, colors):
    text_boxes = []
    for rect, text in zip(rects, texts):
        x1, y1, x2, y2 = rect
        w = x2 - x1
        h = y2 - y1
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.64, 2)
        positions = []
        if y1 - text_height - 1 >= 0 and x1 + text_width < image.shape[1]:
            positions.append((x1, y1 - text_height - 1))
        if y2 + text_height + 1 < image.shape[0] and x1 + text_width < image.shape[1]:
            positions.append((x1, y2 + 1))
        if x1 - text_width - 1 >= 0:
            positions.append((x1 - text_width, y1))
        if x2 + text_width + 1 < image.shape[1]:
            positions.append((x2 + 1, y1))
        if len(positions) == 0:
            positions = [(x1, y1 - text_height - 1), (x1, y2 + 1), (x1 - text_width - 1, y1), (x2 + 1, y1)]

        best_position = None
        best_overlap = float('inf')
        for position in positions:
            text_box = [position[0], position[1], text_width + 1, text_height + 1]
            total_overlap = 0
            for existing_text_box in text_boxes:
                total_overlap += overlap((text_box[0], text_box[0] + text_box[2]), (existing_text_box[0], existing_text_box[0] + existing_text_box[2])) * overlap((text_box[1], text_box[1] + text_box[3]), (existing_text_box[1], existing_text_box[1] + existing_text_box[3]))
            if total_overlap < best_overlap:
                best_overlap = total_overlap
                best_position = position
        text_boxes.append([best_position[0], best_position[1], text_width + 1, text_height + 1])
    for rect, text_box, text, color in zip(rects, text_boxes, texts, colors):
        x1, y1, x2, y2 = rect
        cv2.rectangle(image, (int(text_box[0]), int(text_box[1])), (int(text_box[0] + text_box[2]), int(text_box[1] + text_box[3])), color, -1)
        cv2.putText(image, text, (int(text_box[0] + 1), int(text_box[1] + text_box[3] - 1)), cv2.FONT_HERSHEY_SIMPLEX, 0.64, get_text_color(color), 2)
    return image

def is_digit(n):
    try:
        int(n)
        return True, int(n)
    except ValueError:
        return  False, None

def get_seg_instance(camera):
    mod_kwargs = dict()
    mod_kwargs["viewport"] = camera._viewport.viewport_api
    mod_kwargs.update({"parsed": True, "return_mapping": True})
    return camera._SENSOR_HELPERS["seg_instance"](**mod_kwargs)
