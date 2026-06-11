#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = TOOL_DIR.parent


def run(script_name):
    script_path = TOOL_DIR / script_name
    print(f"Running {script_path.relative_to(WORKSPACE_ROOT)}", flush=True)
    subprocess.run([sys.executable, str(script_path)], cwd=TOOL_DIR, check=True)


def main():
    run("code/find_module_depends.py")
    run("code/render_graph_html.py")
    print("Generated OdooModuleMap/results/graph_cytoscape.html", flush=True)


if __name__ == "__main__":
    main()
