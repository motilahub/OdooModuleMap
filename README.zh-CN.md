# OdooModuleMap

[English](README.md) | [中文](README.zh-CN.md)

[![Python](https://img.shields.io/badge/Odoo-10--19%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Mermaid](https://img.shields.io/badge/Graph-Mermaid-ff3670)](results/graph.mmd)
[![Manifest Depends](https://img.shields.io/badge/Scope-manifest%20depends-6f42c1)](#notes)



OdooModuleMap 是一个用于生成 Odoo 模块依赖图谱的小工具。

![1](./static/img/layout.png)

扫描 Odoo addon 目录中的 `__manifest__.py` / `__openerp__.py`，解析 manifest 里的 `depends`，并生成可交互的 Cytoscape HTML 图谱、Mermaid 图谱和统计摘要。

当前分析范围只包含 manifest `depends` 依赖，不包含 Python 模型继承、代理继承和 XML 视图继承。

## Features

- 扫描多个 Odoo addon 根目录。
- 自动处理同名 module：节点 ID 使用相对路径，页面显示仍使用 module 名。
- 输出交互式 HTML 依赖图谱。
- 支持搜索、模糊匹配、入边 / 出边筛选、来源筛选和布局切换。
- 生成 `graph.json`、`graph.mmd`、`summary.md`，便于二次处理或审查。
- 默认不依赖第三方 Python 包。

## Requirements

- Python 3.8+
- 浏览器

Python 脚本当前只使用标准库，`requirements.txt` 仅用于说明暂无 pip 依赖。

## Project Structure

```text
OdooModuleMap/
├── code/
│   ├── find_module_depends.py
│   └── render_graph_html.py
├── config/
│   └── source_roots.example.json
├── results/
│   ├── graph.json
│   ├── graph.mmd
│   ├── graph_cytoscape.html
│   └── summary.md
├── static/
│   └── js/
│       └── cytoscape.min.js
├── main.py
├── README.md
├── README.zh-CN.md
└── requirements.txt
```

## Quick Start

将 `OdooModuleMap` 放在 Odoo 项目的根目录中，并在 `OdooModuleMap` 所在项目根目录执行：

```bash
python3 OdooModuleMap/main.py
```

也可以进入工具目录执行：

```bash
cd OdooModuleMap
python3 main.py
```

生成完成后，直接用浏览器打开：

```text
OdooModuleMap/results/graph_cytoscape.html
```

## Source Roots

默认情况下，如果不存在 `config/source_roots.json`，工具会扫描 `OdooModuleMap` 父级目录下除 `OdooModuleMap` 外的所有文件夹。

如需手动维护扫描范围，复制示例配置：

```bash
cp OdooModuleMap/config/source_roots.example.json OdooModuleMap/config/source_roots.json
```

然后编辑 `source_roots`：

```json
{
  "source_roots": {
    "code": "code",
    "data": "data",
    "third_component": "third_component"
  }
}
```

配置说明：

- `source_roots` 的 key 会作为页面中的来源分类名称。
- 路径支持绝对路径。
- 相对路径基于 `OdooModuleMap` 的父级目录解析。
- 配置文件存在时，只扫描配置中声明的目录。

## Output

生成目录：

```text
OdooModuleMap/results
```

输出文件：

- `graph_cytoscape.html`：交互式依赖图谱页面。
- `graph.json`：结构化图谱数据。
- `graph.mmd`：Mermaid 图谱。
- `summary.md`：模块数量、边数量、目标来源等统计摘要。

页面会从 `OdooModuleMap/static/js/cytoscape.min.js` 加载本地 Cytoscape.js。

## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=yangtiancheng/OdooModuleMap&type=timeline&logscale&legend=top-left)](https://www.star-history.com/?repos=yangtiancheng%2FOdooModuleMap&type=timeline&logscale=&legend=top-left)

## Contributors

<a href="https://github.com/yangtiancheng/OdooModuleMap/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=yangtiancheng/OdooModuleMap" alt="Contributors" />
</a>

## Graph Page Usage

- 页面默认搜索 `base`，避免初次打开时渲染完整大图导致加载慢。
- 默认布局为 `Breadthfirst`。
- `Search` 候选格式为 `dir/moduleName`，例如 `base/base`。
- `Fuzzy` 默认开启；关闭后为精确搜索，支持匹配 module 名、相对路径或 `dir/moduleName`。
- `Direction` 中的 `In` / `Out` 只在 Search 匹配到 module 后可编辑。
- `Node Scope` 根据扫描来源筛选节点。
- `Run` 使用当前 layout 重新排版。
- `Fit` 将当前可见图谱缩放到视野内。
- 双击节点会把该 module 写入 Search 并重新排版。
- 点击节点后，出边显示绿色，入边显示红色。

## Scripts

- `main.py`：执行完整生成流程。
- `code/find_module_depends.py`：扫描 Odoo modules，解析 manifest `depends`，生成图谱数据。
- `code/render_graph_html.py`：读取 `graph.json`，渲染 `graph_cytoscape.html`。

## Notes

- 当前不会解析 Python `_inherit`、`_inherits` 或 XML `inherit_id`。
- 如果 module 新增、删除或 manifest 依赖发生变化，需要重新执行生成命令。
- 未在扫描范围内找到的依赖会标记为 `unknown/external`。
