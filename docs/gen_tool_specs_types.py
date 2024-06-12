"""
Automatically generate JSON schema for the tool specification types.
"""

import importlib
import json
from io import TextIOWrapper
from typing import List

import mkdocs_gen_files
import yaml
from pydantic import BaseModel, RootModel

from ethereum_test_tools.common.json import to_json

t8n_types_file = "tool_specs/t8n/types.md"

# Parse the file to get the types to be populated
file_lines: List[str] = []
with mkdocs_gen_files.open(t8n_types_file, "r") as f:
    file_lines = f.readlines()


module_cache = {}


def print_type(module: str | None, type_name: str | None, f: TextIOWrapper):
    """
    Print the JSON schema for the given type.
    """
    if module is None or type_name is None:
        return
    if module not in module_cache:
        module_cache[module] = importlib.import_module(module)
    imported_module = module_cache[module]
    type = getattr(imported_module, type_name)
    assert issubclass(type, BaseModel) or issubclass(type, RootModel)
    type_json_schema = type.model_json_schema()
    f.write("#### JSON schema\n\n")
    f.write("```yaml\n")
    f.write(yaml.dump(type_json_schema, indent=2, default_flow_style=False, sort_keys=False))
    f.write("```\n\n")

    if hasattr(type, "model_json_examples"):
        type_json_examples = type.model_json_examples()
        f.write("#### JSON example\n\n")
        for type_json_example in type_json_examples:
            f.write("```json\n")
            f.write(json.dumps(to_json(type_json_example), indent=2, sort_keys=False))
            f.write("\n```\n\n")


with mkdocs_gen_files.open(t8n_types_file, "w") as f:
    current_module: str | None = None
    current_type: str | None = None
    for line in file_lines:
        if line.startswith("## "):
            if current_module is not None or current_type is not None:
                print_type(current_module, current_type, f)
            current_module = line[3:].strip()
            current_type = None
        elif line.startswith("### "):
            if current_module is not None or current_type is not None:
                print_type(current_module, current_type, f)
            current_type = line[4:].strip()
        f.write(line)
    if current_module is not None or current_type is not None:
        print_type(current_module, current_type, f)
