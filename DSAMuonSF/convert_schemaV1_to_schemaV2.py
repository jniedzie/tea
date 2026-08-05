import json
import sys

def add_descriptions(corr):
    """
    Add empty descriptions for inputs/output if missing.
    """
    if "inputs" in corr:
        for inp in corr["inputs"]:
            if "description" not in inp:
                inp["description"] = ""
    if "output" in corr and "description" not in corr["output"]:
        corr["output"]["description"] = ""

def process_data(node, input_names, depth=0):
    nodetype = node.get("nodetype")

    # Assign input based on depth
    if depth < len(input_names):
        node["input"] = input_names[depth]
    else:
        if "input" not in node:
            node["input"] = f"input{depth+1}"

    if nodetype == "binning":
        if "flow" not in node:
            node["flow"] = "clamp"
        for c in node.get("content", []):
            process_data(c, input_names, depth+1)

    elif nodetype == "category":
        if "keys" in node and "content" in node:
            keys = node.pop("keys")
            values = node.pop("content")
            node["content"] = [{"key": k, "value": v} for k, v in zip(keys, values)]


def convert_v1_to_v2(v1_json):
    """
    Convert a full schema v1 JSON to schema v2.
    """
    v2_json = v1_json.copy()
    v2_json["schema_version"] = 2

    for corr in v2_json.get("corrections", []):
        add_descriptions(corr)
        if "data" in corr:
            # get the list of input names in order
            input_names = [inp["name"] for inp in corr.get("inputs", [])]
            process_data(corr["data"], input_names)

    return v2_json

def main():
    if len(sys.argv) != 3:
        print("Usage: python convert_v1_to_v2.py input_v1.json output_v2.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, "r") as f:
        v1_json = json.load(f)

    v2_json = convert_v1_to_v2(v1_json)

    with open(output_file, "w") as f:
        json.dump(v2_json, f, indent=2)

    print(f"Converted {input_file} (v1) → {output_file} (v2) successfully.")

if __name__ == "__main__":
    main()
