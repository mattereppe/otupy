import json
import subprocess

# Your list of map names
maps_to_find = ["map_name_1", "map_name_2"]

def get_map_ids(map_names):
    # 1. Run the command once to get all maps in JSON format
    result = subprocess.run(
        ["sudo", "bpftool", "map", "show", "-j"],
        capture_output=True, text=True, check=True
    )
    all_maps = json.loads(result.stdout)
    
    found_ids = {}
    
    # 2. Match your names against the kernel data
    for target in map_names:
        for m in all_maps:
            if m.get('name') == target:
                found_ids[target] = m.get('id')
                break
    
    return found_ids

# Example usage:
map_results = get_map_ids(maps_to_find)
print(map_results) # Outputs: {'map_name_1': 123, 'map_name_2': 124}