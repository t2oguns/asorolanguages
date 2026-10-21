
import copy
import json
import os
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

DRF_SCHEMA = BUILD / "openapi-drf.json"
OUTPUT_SCHEMA = BUILD / "openapi.json"

# Override this for a deployed or differently configured Django server.
ALLAUTH_SCHEMA_URL = os.environ.get(
    "ALLAUTH_SCHEMA_URL",
    "http://127.0.0.1:8000/_allauth/openapi.json",
)

COMPONENT_GROUPS = (
    "schemas",
    "responses",
    "parameters",
    "examples",
    "requestBodies",
    "headers",
    "securitySchemes",
    "links",
    "callbacks",
)



def rename_allauth_refs(value):
    """Namespace Allauth component references recursively."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key == "$ref" and isinstance(item, str):
                match = re.fullmatch(
                    r"#/components/([^/]+)/(.+)", item
                )
                if match and match.group(1) in COMPONENT_GROUPS:
                    group, name = match.groups()
                    item = f"#/components/{group}/Allauth_{name}"
            result[key] = rename_allauth_refs(item)
        return result

    if isinstance(value, list):
        return [rename_allauth_refs(item) for item in value]

    return value

def expand_allauth_client_paths(spec):
    """Expand Allauth's {client} paths into app and browser paths."""
    expanded = {}

    for path, path_item in spec.get("paths", {}).items():
        if "{client}" not in path:
            expanded[path] = path_item
            continue

        for client in ("app", "browser"):
            concrete_path = path.replace("{client}", client)
            expanded[concrete_path] = copy.deepcopy(path_item)

            # Remove the client path parameter from path-level parameters.
            # It is no longer part of the concrete URL.
            parameters = expanded[concrete_path].get("parameters", [])
            expanded[concrete_path]["parameters"] = [
                parameter
                for parameter in parameters
                if not (
                    parameter.get("in") == "path"
                    and parameter.get("name") == "client"
                )
            ]

            # Also remove it from operation-level parameters.
            for method, operation in expanded[concrete_path].items():
                if method.lower() not in {
                    "get", "put", "post", "delete",
                    "options", "head", "patch", "trace",
                }:
                    continue

                if "parameters" in operation:
                    operation["parameters"] = [
                        parameter
                        for parameter in operation["parameters"]
                        if not (
                            parameter.get("in") == "path"
                            and parameter.get("name") == "client"
                        )
                    ]

    spec["paths"] = expanded
    return spec

def main():
    with DRF_SCHEMA.open(encoding="utf-8") as f:
        drf = json.load(f)

    response = requests.get(ALLAUTH_SCHEMA_URL, timeout=30)
    response.raise_for_status()
    allauth = response.json()
    allauth = expand_allauth_client_paths(allauth)


    # Start with the DRF document as the base.
    merged = copy.deepcopy(drf)

    # Merge endpoint paths. Fail rather than silently overwrite
    # an endpoint if both specifications define the same path.
    for path, path_item in allauth.get("paths", {}).items():
        if path in merged.get("paths", {}):
            raise ValueError(
                f"Path collision: {path}. Resolve it explicitly."
            )
        merged.setdefault("paths", {})[path] = (
            rename_allauth_refs(path_item)
        )

    # Namespace and merge Allauth components.
    merged.setdefault("components", {})
    allauth_components = allauth.get("components", {})

    for group in COMPONENT_GROUPS:
        source = allauth_components.get(group, {})
        target = merged["components"].setdefault(group, {})

        for name, component in source.items():
            new_name = f"Allauth_{name}"
            if new_name in target:
                raise ValueError(
                    f"Component collision: {group}/{new_name}"
                )
            target[new_name] = rename_allauth_refs(component)

    # Preserve tags from both documents without duplicate names.
    tags = merged.setdefault("tags", [])
    existing_tags = {tag["name"] for tag in tags}

    for tag in allauth.get("tags", []):
        if tag["name"] not in existing_tags:
            tags.append(tag)
            existing_tags.add(tag["name"])

    # Keep the DRF document's OpenAPI version and metadata.
    OUTPUT_SCHEMA.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_SCHEMA.open("w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
        f.write("\n")

    print(f"Merged schema written to {OUTPUT_SCHEMA}")


if __name__ == "__main__":
    main()
