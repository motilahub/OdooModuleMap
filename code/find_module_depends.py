#!/usr/bin/env python3
import ast
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree


TOOL_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = TOOL_DIR.parent
CONFIG_PATH = TOOL_DIR / "config" / "source_roots.json"
OUT_DIR = TOOL_DIR / "results"


def path_display(path):
    try:
        return str(path.relative_to(WORKSPACE_ROOT))
    except ValueError:
        return str(path)


def resolve_source_path(value):
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (WORKSPACE_ROOT / path).resolve()


def load_configured_source_roots():
    if not CONFIG_PATH.exists():
        return None

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    roots = data.get("source_roots") if isinstance(data, dict) else data
    if not isinstance(roots, dict):
        raise ValueError(f"{path_display(CONFIG_PATH)} must contain a source_roots object")

    source_roots = {}
    for kind, value in roots.items():
        if not isinstance(kind, str) or not isinstance(value, str):
            raise ValueError(f"{path_display(CONFIG_PATH)} source root names and paths must be strings")
        source_roots[kind] = resolve_source_path(value)
    return source_roots


def default_source_roots():
    source_roots = {}
    for path in sorted(WORKSPACE_ROOT.iterdir()):
        if not path.is_dir() or path.name == TOOL_DIR.name:
            continue
        source_roots[path.name] = path.resolve()
    return source_roots


def get_source_roots():
    configured_roots = load_configured_source_roots()
    if configured_roots is not None:
        return configured_roots, "config"
    return default_source_roots(), "default_workspace_dirs"


def module_name_from_manifest(path):
    return path.parent.name


def module_id_from_manifest(path):
    return path_display(path.parent)


def find_manifests(root):
    files = []
    for name in ("__manifest__.py", "__openerp__.py"):
        files.extend(root.rglob(name))
    return sorted(files)


def literal_value(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def read_manifest(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        data = ast.literal_eval(text)
        if isinstance(data, dict):
            return data, None
    except Exception as exc:
        return {}, str(exc)
    return {}, "manifest is not a dict literal"


def normalize_depends(value):
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, str)]
    return []


def classify_module_name(name, module_kinds):
    if name in module_kinds:
        return module_kinds[name]
    return "unknown/external"


def iter_module_files(module_path, suffixes):
    for suffix in suffixes:
        yield from module_path.rglob(f"*{suffix}")


def parse_model_assignments(py_path):
    text = py_path.read_text(encoding="utf-8", errors="replace")
    result = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return result

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        values = {}
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id in {"_name", "_inherit", "_inherits"}:
                        values[target.id] = literal_value(stmt.value)
        if values:
            result.append(values)
    return result


def as_string_list(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, str)]
    return []


def as_dict_keys(value):
    if isinstance(value, dict):
        return [key for key in value.keys() if isinstance(key, str)]
    return []


def build_model_index(modules):
    model_owners = defaultdict(set)
    model_inherits = defaultdict(list)
    delegation_inherits = defaultdict(list)

    for module, info in modules.items():
        for py_path in iter_module_files(info["path"], (".py",)):
            for values in parse_model_assignments(py_path):
                names = as_string_list(values.get("_name"))
                inherits = as_string_list(values.get("_inherit"))
                delegations = as_dict_keys(values.get("_inherits"))

                for model_name in names:
                    model_owners[model_name].add(module)

                for inherited in inherits:
                    model_inherits[module].append(
                        {
                            "model": inherited,
                            "file": path_display(py_path),
                        }
                    )

                for inherited in delegations:
                    delegation_inherits[module].append(
                        {
                            "model": inherited,
                            "file": path_display(py_path),
                        }
                    )

    return model_owners, model_inherits, delegation_inherits


def xml_ref_module(ref):
    if not ref or "." not in ref:
        return None
    return ref.split(".", 1)[0]


def parse_xml_inherit_refs(xml_path):
    refs = []
    try:
        root = ElementTree.parse(xml_path).getroot()
    except (ElementTree.ParseError, ValueError):
        text = xml_path.read_text(encoding="utf-8", errors="replace")
        refs.extend(re.findall(r'<field[^>]+name=["\']inherit_id["\'][^>]+ref=["\']([^"\']+)["\']', text))
        refs.extend(re.findall(r'ref=["\']([^"\']+)["\'][^>]+name=["\']inherit_id["\']', text))
        return refs

    for field in root.iter("field"):
        if field.attrib.get("name") == "inherit_id" and "ref" in field.attrib:
            refs.append(field.attrib["ref"])
    return refs


def collect_xml_inherits(modules, module_kinds):
    edges = []
    for module, info in modules.items():
        for xml_path in iter_module_files(info["path"], (".xml",)):
            for ref in parse_xml_inherit_refs(xml_path):
                target_module = xml_ref_module(ref)
                if not target_module:
                    target_module = module
                target_kind = classify_module_name(target_module, module_kinds)
                edges.append(
                    {
                        "source": module,
                        "target": target_module,
                        "target_kind": target_kind,
                        "type": "xml_inherit",
                        "ref": ref,
                        "file": path_display(xml_path),
                    }
                )
    return edges


def owner_kinds(model_name, model_owners, module_kinds):
    owners = sorted(model_owners.get(model_name, []))
    if not owners:
        return [("unknown_model:" + model_name, "unknown/external")]
    return [(owner, classify_module_name(owner, module_kinds)) for owner in owners]


def collect_python_inherit_edges(model_inherits, delegation_inherits, model_owners, module_kinds):
    edges = []
    for source, refs in model_inherits.items():
        for item in refs:
            for owner, kind in owner_kinds(item["model"], model_owners, module_kinds):
                if owner == source:
                    continue
                edges.append(
                    {
                        "source": source,
                        "target": owner,
                        "target_kind": kind,
                        "type": "python_inherit",
                        "model": item["model"],
                        "file": item["file"],
                    }
                )
    for source, refs in delegation_inherits.items():
        for item in refs:
            for owner, kind in owner_kinds(item["model"], model_owners, module_kinds):
                if owner == source:
                    continue
                edges.append(
                    {
                        "source": source,
                        "target": owner,
                        "target_kind": kind,
                        "type": "delegation_inherit",
                        "model": item["model"],
                        "file": item["file"],
                    }
                )
    return edges


def unique_edges(edges):
    seen = set()
    output = []
    for edge in edges:
        key = (
            edge.get("source"),
            edge.get("target"),
            edge.get("type"),
            edge.get("model"),
            edge.get("ref"),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(edge)
    return output


def mermaid_id(name):
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def write_mermaid(edges, node_kinds, path):
    lines = ["flowchart LR"]
    for node, kind in sorted(node_kinds.items()):
        label = f"{node}\\n[{kind}]"
        lines.append(f'    {mermaid_id(node)}["{label}"]')

    labels = {
        "depends": "depends",
        "python_inherit": "py inherit",
        "delegation_inherit": "delegation",
        "xml_inherit": "xml inherit",
    }
    for edge in edges:
        lines.append(
            f'    {mermaid_id(edge["source"])} -- "{labels.get(edge["type"], edge["type"])}" --> {mermaid_id(edge["target"])}'
        )

    lines.extend(
        [
            "    classDef source fill:#e3f2fd,stroke:#1565c0,color:#111;",
            "    classDef external fill:#fff3e0,stroke:#ef6c00,color:#111;",
        ]
    )
    for node, kind in sorted(node_kinds.items()):
        cls = "external" if kind == "unknown/external" else "source"
        lines.append(f"    class {mermaid_id(node)} {cls};")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(modules, edges, manifest_errors, out_path):
    edge_counts = Counter(edge["type"] for edge in edges)
    module_counts = Counter(info["kind"] for info in modules.values())
    source_kind_counts = Counter(edge.get("source_kind", "unknown/external") for edge in edges)
    target_kind_counts = Counter(edge["target_kind"] for edge in edges)
    depends_targets = Counter(edge["target_kind"] for edge in edges if edge["type"] == "depends")
    inherit_targets = Counter(edge["target_kind"] for edge in edges if edge["type"] != "depends")
    unknown_targets = sorted(
        {(edge["target"], edge["type"]) for edge in edges if edge["target_kind"] == "unknown/external"}
    )

    lines = [
        "# Odoo Module Graph Summary",
        "",
        f"- modules: {len(modules)}",
        f"- graph edges: {len(edges)}",
        f"- manifest parse errors: {len(manifest_errors)}",
        "",
        "## Module Counts",
    ]
    for key, value in sorted(module_counts.items()):
        lines.append(f"- {key}: {value}")

    lines.extend([
        "",
        "## Edge Type Counts",
    ])
    for key, value in sorted(edge_counts.items()):
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Source Kind Counts"])
    for key, value in sorted(source_kind_counts.items()):
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Target Kind Counts"])
    for key, value in sorted(target_kind_counts.items()):
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Depends Target Counts"])
    for key, value in sorted(depends_targets.items()):
        lines.append(f"- {key}: {value}")

    if inherit_targets:
        lines.extend(["", "## Inherit Target Counts"])
        for key, value in sorted(inherit_targets.items()):
            lines.append(f"- {key}: {value}")

    if unknown_targets:
        lines.extend(["", "## Unknown/External Targets"])
        for target, edge_type in unknown_targets:
            lines.append(f"- {target} ({edge_type})")

    if manifest_errors:
        lines.extend(["", "## Manifest Parse Errors"])
        for path, error in manifest_errors.items():
            lines.append(f"- {path}: {error}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    source_roots, source_mode = get_source_roots()
    modules = {}
    modules_by_name = defaultdict(list)
    manifest_errors = {}

    for kind, root in source_roots.items():
        if not root.exists():
            manifest_errors[path_display(root)] = "source root does not exist"
            continue
        for path in find_manifests(root):
            module = module_id_from_manifest(path)
            module_name = module_name_from_manifest(path)
            data, error = read_manifest(path)
            if error:
                manifest_errors[path_display(path)] = error
            modules[module] = {
                "name": module_name,
                "kind": kind,
                "path": path.parent,
                "manifest": path_display(path),
                "depends": normalize_depends(data.get("depends")),
            }
            modules_by_name[module_name].append(module)

    module_kinds = {module: info["kind"] for module, info in modules.items()}

    edges = []
    for module, info in modules.items():
        for dep in info["depends"]:
            targets = modules_by_name.get(dep, [dep])
            for target in targets:
                edges.append(
                    {
                        "source": module,
                        "source_name": info["name"],
                        "target": target,
                        "target_name": modules.get(target, {}).get("name", dep),
                        "dependency_name": dep,
                        "source_kind": info["kind"],
                        "target_kind": classify_module_name(target, module_kinds),
                        "type": "depends",
                        "manifest": info["manifest"],
                    }
                )

    edges = unique_edges(edges)

    node_kinds = dict(module_kinds)
    for edge in edges:
        node_kinds.setdefault(edge["source"], edge.get("source_kind", "unknown/external"))
        node_kinds[edge["target"]] = edge["target_kind"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    serializable_modules = {
        module: {
            "name": info["name"],
            "kind": info["kind"],
            "path": path_display(info["path"]),
            "manifest": info["manifest"],
            "depends": info["depends"],
        }
        for module, info in sorted(modules.items())
    }
    module_counts = Counter(info["kind"] for info in modules.values())
    data = {
        "scope": {
            "mode": source_mode,
            "config": path_display(CONFIG_PATH) if CONFIG_PATH.exists() else None,
            "roots": {kind: path_display(path) for kind, path in source_roots.items()},
            "edge_scope": "manifest depends only",
            "module_count": len(modules),
            "module_counts": dict(module_counts),
        },
        "modules": serializable_modules,
        "edges": edges,
        "node_kinds": node_kinds,
        "manifest_errors": manifest_errors,
    }
    (OUT_DIR / "graph.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_mermaid(edges, node_kinds, OUT_DIR / "graph.mmd")
    write_summary(modules, edges, manifest_errors, OUT_DIR / "summary.md")

    print(json.dumps({
        "modules": len(modules),
        "module_counts": module_counts,
        "edges": len(edges),
        "edge_counts": Counter(edge["type"] for edge in edges),
        "target_kind_counts": Counter(edge["target_kind"] for edge in edges),
        "output_dir": path_display(OUT_DIR),
        "source_mode": source_mode,
    }, ensure_ascii=False, default=dict, sort_keys=True))


if __name__ == "__main__":
    main()
