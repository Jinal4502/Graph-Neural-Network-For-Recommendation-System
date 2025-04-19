import json
from gpt_util import ask_gpt

# with open("./knowledge/process_cap_flat.json", "r") as file:
with open("./knowledge/process_capabilities.json", "r") as file:
    process_caps = json.load(file)

# for pc in process_caps:
#     # remove capability suffix from pc['concept']
#     pc["concept"] = pc["concept"].replace(" capability", "")

# save the modified process_caps to a new file
# with open("./knowledge/process_cap_flat2.json", "w") as file:
#     json.dump(process_caps, file, indent=4)


def fix_concept_name(node):
    node["concept"] = node["concept"].replace(" capability", "")
    for child in node.get("children", []):
        fix_concept_name(child)


for pc in process_caps:
    fix_concept_name(pc)

# save the modified process_caps to a new file
with open("./knowledge/process_capabilities2.json", "w") as file:
    json.dump(process_caps, file, indent=4)


# with open("./prompts/extract_process_cap_flat.txt", "r") as file:
with open("./prompts/extract_processing_capabilities.txt", "r") as file:
    extract_processing_cap_prompt = file.read()
    # print(extract_processing_capabilities_prompt)


def count_tree(node) -> int:
    subtree_count = 1
    for child in node.get("children", []):
        subtree_count += count_tree(child)
    return subtree_count


def depth_tree(node, curr_depth, leaf_depths):
    if not node["children"]:
        leaf_depths.append(curr_depth)

    for child in node["children"]:
        depth_tree(child, curr_depth + 1, leaf_depths)


def group_process_caps(process_caps):
    for process in process_caps:
        subtree_count = count_tree(process)
        process["count"] = subtree_count
        leaf_depths = []
        depth_tree(process, 1, leaf_depths)
        process["max_depth"] = max(leaf_depths)

    process_caps = sorted(
        process_caps, key=lambda x: (x["count"], x["max_depth"]), reverse=False
    )

    groups = []

    MAX_GROUP_COUNT = 100
    curr_group_count = 0
    curr_group = []

    for process in process_caps:
        if process["count"] + curr_group_count > MAX_GROUP_COUNT:
            print(f"curr_group count:{curr_group_count}")
            groups.append(curr_group)
            curr_group = []
            curr_group_count = 0

        curr_group.append(
            {
                "concept": process["concept"],
                "altLabels": process["altLabels"],
                "children": process["children"],
            }
        )
        curr_group_count += process["count"]

    print(f"curr_group count:{curr_group_count}")
    groups.append(curr_group)

    for group in groups:
        print(group)

    return groups


def extract_processing_capabilities(mfg_txt: str, debug: bool = False):
    global extract_processing_cap_prompt

    # matched_pc = []
    # unmatched_pc = []
    # for pc in process_caps_flat:
    #     keywords = pc['variants'].append(pc['concept'])
    #     # keywords = [keyword.lower() for keyword in keywords]
    #     if keywords and any(keyword in mfg_txt.lower() for keyword in keywords):
    #         matched_pc.append(pc['concept'])
    #     else:
    #         unmatched_pc.append(pc['concept'])

    groups = group_process_caps(process_caps)
    for idx, group in enumerate(groups):
        prompt = extract_processing_cap_prompt.replace(
            "{{process_caps}}", json.dumps(group)
        )
        print(f"prompt{idx}:{prompt}")

        # gpt_response = ask_gpt(
        #     mfg_txt,
        #     prompt,
        # )

        # if debug:
        #     print(f"gpt_response:{gpt_response}")

        # if not gpt_response:
        #     raise ValueError("Empty response from GPT")
