import json
import os
from collections import Counter
from typing import Tuple

FUELS = []
ALTERNATIVE_FUELS = []
cur_path = os.path.abspath(os.path.dirname(__file__))
root_path = cur_path[:cur_path.find('jarvis')]
relative_path = os.path.join("jarvis/assets/tag_items.json")
tag_json_path = os.path.join(root_path, relative_path)
with open(tag_json_path) as file:
    tag_info = json.load(file)
FUELS += [ _[10:] for _ in tag_info['minecraft:coals']]
ALTERNATIVE_FUELS += [ _[10:] for _ in tag_info['minecraft:planks']]
ALTERNATIVE_FUELS += [ _[10:] for _ in tag_info['minecraft:logs']]
fuel_str = ', '.join(FUELS)
alternative_fuel_str = ', '.join(ALTERNATIVE_FUELS)


def recipe_description(recipe_info: dict) -> str:

    if recipe_info['type'] == "minecraft:crafting_shaped" or recipe_info['type'] == "minecraft:crafting_shapeless":
        items = dict()
        items_type = dict()
        item_name = recipe_info['result']['item'][10:]
        if "pattern" in recipe_info:
            ingredients_str = "".join(recipe_info["pattern"])
            ingredients_symbols = Counter(ingredients_str)
            for k, v in recipe_info["key"].items():
                if k not in ingredients_symbols:
                    return "Cannot obtain the object."
                count = ingredients_symbols[k]
                if "item" in v:
                    item = v["item"][10:]
                    item_type = 'item'
                else:
                    item = v["tag"][10:]
                    item_type = 'tag'
                items_type[item] = item_type
                items[item] = count
        
        else:
            ingredients = recipe_info.get('ingredients')

            # calculate the amount needed and store <item, quantity> in items
            for i in range(len(ingredients)):
                if ingredients[i].get('item'):
                    item = ingredients[i].get('item')[10:]
                    item_type = 'item'
                else:
                    item = ingredients[i].get('tag')[10:]
                    item_type = 'tag'
                items_type[item] = item_type
                if items.get(item):
                    items[item] += 1
                else:
                    items[item] = 1

        count = recipe_info["result"].get("count")
        count = count if count else 1

        result = f"Crafting {recipe_info['result']['item'][10:]} needs "
        for item, quantity in items.items():
            if item == list(items.keys())[-1]:
                result += f"{quantity} {item}"
                if items_type[item] == 'tag':
                    result += " (tag)"
                result += ". "
            else:
                result += f"{quantity} {item}"
                if items_type[item] == 'tag':
                    result += " (tag)"
                result += ", "
        result += f"Every time you craft {item_name} with the ingredients above, you will get {count} {item_name}."
        return result

    elif recipe_info['type'] == "minecraft:smelting":
        item_name = recipe_info['result'][10:]
        result = f"Smelting 1 {item_name} needs 1 unit of fuel and 1 ingredient. Fuel can be one of the following: {fuel_str}. " + \
            f"Or you can use 2 pieces of the following as a unit of fuel: {alternative_fuel_str}. Ingredient: "
        if "tag" in recipe_info["ingredient"]:
            ingredient = recipe_info["ingredient"]["tag"][10:]
            result += f"1 {ingredient} (tag)."
        else:
            ingredient = recipe_info["ingredient"]["item"][10:]
            result += f"1 {ingredient}."
        return result

    else:
        return "Cannot obtain the object."


def look_up(target: str) -> str:
    
    # is item/tag
    is_tag = False
    for key in tag_info:
        if key[10:] == target:
            is_tag = True
    
    if is_tag:
        
        result = f"{target} is a tag. Following items belong to this tag: "
        item_list = tag_info['minecraft:'+target]
        for item in item_list:
            if item == item_list[-1]:
                result += item[10:] + '.'
            else:
                result += item[10:] + ', '
        
        for item in item_list:
            subtarget = item[10:]
            cur_path = os.path.abspath(os.path.dirname(__file__))
            root_path = cur_path[:cur_path.find('jarvis')]
            relative_path = os.path.join("jarvis/assets/recipes", subtarget + '.json')
            recipe_json_path = os.path.join(root_path, relative_path)
            if os.path.exists(recipe_json_path):
                with open(recipe_json_path) as file:
                    recipe_info = json.load(file)
                result += f"\n{subtarget}: " + recipe_description(recipe_info)
            else:
                result += f"\n{subtarget}: It is a raw item you can mine from the environment."
    
    else:
        cur_path = os.path.abspath(os.path.dirname(__file__))
        root_path = cur_path[:cur_path.find('jarvis')]
        relative_path = os.path.join("jarvis/assets/recipes", target + '.json')
        recipe_json_path = os.path.join(root_path, relative_path)
        
        if not os.path.exists(recipe_json_path):
            return "No recipe for this item. Maybe it is a raw item or you take the wrong name as an argument."

        with open(recipe_json_path) as file:
            recipe_info = json.load(file)

        result = f"{target}: {recipe_description(recipe_info)}"

    return result


def teleport(x: float, y: float, z: float, env, mark) -> Tuple[bool, str]:
    if x < -30000000 or x > 30000000 or z < -30000000 or z > 30000000 or y < 0 or y > 255:
        return False, "Coordinates out of range. x and z should be in [-30000000, 30000000]; y should be in [0, 255]."
    noop_action = env.env._env.env.action_space.noop()
    env.env._env.env.step(noop_action)
    command = f"/tp @p {x:.2f} {y:.2f} {z:.2f} 0 0"
    env.env._env.env.execute_cmd(command)
    for i in range(10):
        env.env._env.env.step(noop_action)
    equipment = mark.record_infos[-1]['equipped_items']['mainhand']['type']
    equipment = "none" if equipment == "air" else equipment
    success, message = mark.do("equip", target_item=equipment)
    return success, "Successfully teleported."


if __name__ == "__main__":

    print(look_up("iron_pickaxe"))
    print()

    print(look_up("glass"))
    print()

    print(look_up("logs"))
    print()

    print(look_up("planks"))
    print()

    print(look_up("furnace"))
    print()

    print(look_up("stone_pickaxe"))
    print()

    print(look_up("oak_logs"))
    print()

    print(look_up("stone_crafting_materials"))
    print()

    print(look_up("stone_tool_materials"))
    print()
