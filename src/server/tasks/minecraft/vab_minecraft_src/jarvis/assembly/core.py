def translate_inventory(info):
    inventory = {}
    for i in range(36):
        if info['inventory'][i]['type'] == 'none':
            continue
        
        if info['inventory'][i]['type'] in inventory.keys():
            inventory[info['inventory'][i]['type']] += info['inventory'][i]['quantity']
        else:
            inventory[info['inventory'][i]['type']] = info['inventory'][i]['quantity']
    if not len(inventory.keys()):
        return "Now your inventory has nothing."
    else:
        content = []
        for k, v in inventory.items():
            content.append(f"{v} {k}")
        return f"Now your inventory has {', '.join(content)}."

def translate_equipment(info):
    # return info['equipped_items']['mainhand']['type']
    return f"Now you hold the {info['equipped_items']['mainhand']['type']} in your hand."

def translate_height(info):
    # return int(info['location_stats']['ypos'])
    return f"Now you locate in height of {int(info['player_pos']['y'])}."

def translate_location(info):
    # return int(info['location_stats']['ypos'])
    x = info['player_pos']['x']
    y = info['player_pos']['y']
    z = info['player_pos']['z']
    pitch = info['player_pos']['pitch']
    yaw = info['player_pos']['yaw']
    return f"Now you locate in X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}, Pitch: {pitch:.2f}, Yaw: {yaw:.2f}."

