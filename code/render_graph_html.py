#!/usr/bin/env python3
import json
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parents[1]
GRAPH_JSON = TOOL_DIR / "results" / "graph.json"
OUT_HTML = TOOL_DIR / "results" / "graph_cytoscape.html"


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Odoo Module Graph</title>
  <script src="../static/js/cytoscape.min.js"></script>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f6f8;
      --panel: #ffffff;
      --line: #d9dee5;
      --text: #17202a;
      --muted: #64707d;
      --green: #2e7d32;
      --blue: #1565c0;
      --orange: #ef6c00;
      --red: #b3261e;
      --shadow: 0 8px 24px rgba(16, 24, 40, .07);
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}

    .app {{
      display: grid;
      grid-template-columns: 340px minmax(0, 1fr);
      min-height: 100vh;
    }}

    aside {{
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 14px;
      border-right: 1px solid var(--line);
      background: var(--panel);
      overflow-y: auto;
    }}

    main {{
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      min-width: 0;
    }}

    .graph-wrap {{
      position: relative;
      min-width: 0;
      min-height: 0;
    }}

    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 14px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, .92);
      backdrop-filter: blur(8px);
    }}

    h1 {{
      margin: 0;
      font-size: 18px;
      line-height: 1.25;
      font-weight: 700;
    }}

    h2 {{
      margin: 0 0 8px;
      font-size: 13px;
      font-weight: 700;
      color: #2b3440;
    }}

    .section {{
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, .96);
      box-shadow: var(--shadow);
    }}

    .stats {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}

    .stat {{
      padding: 8px;
      border: 1px solid #e4e7eb;
      border-radius: 6px;
      background: #fafbfc;
    }}

    .stat span {{
      display: block;
      color: var(--muted);
      font-size: 11px;
    }}

    .stat strong {{
      display: block;
      margin-top: 3px;
      font-size: 18px;
      line-height: 1;
    }}

    label {{
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 28px;
      font-size: 13px;
      color: #1f2933;
      cursor: pointer;
    }}

    input[type="checkbox"] {{
      width: 16px;
      height: 16px;
      margin: 0;
    }}

    input[type="search"], select {{
      width: 100%;
      min-height: 34px;
      border: 1px solid #c9d1d9;
      border-radius: 6px;
      padding: 7px 9px;
      background: #fff;
      color: var(--text);
      font-size: 13px;
    }}

    .row {{
      display: flex;
      gap: 8px;
      align-items: center;
    }}

    .row > * {{
      min-width: 0;
    }}

    button {{
      min-height: 34px;
      border: 1px solid #b9c2ce;
      border-radius: 6px;
      padding: 7px 10px;
      background: #fff;
      color: #1f2933;
      font-size: 13px;
      cursor: pointer;
    }}

    button:hover {{
      background: #f1f4f7;
    }}

    .legend {{
      display: grid;
      gap: 7px;
      font-size: 13px;
    }}

    .legend-item {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .swatch {{
      width: 18px;
      height: 12px;
      border-radius: 3px;
      border: 1px solid rgba(0, 0, 0, .2);
      flex: 0 0 auto;
    }}

    .source {{ background: #42a5f5; }}
    .external {{ background: #ff9800; }}

    #cy {{
      width: 100%;
      height: 100%;
      background:
        radial-gradient(circle at 20% 20%, rgba(46, 125, 50, .035), transparent 28%),
        radial-gradient(circle at 80% 10%, rgba(21, 101, 192, .035), transparent 26%),
        #fbfcfd;
    }}

    .zoom-control {{
      position: fixed;
      right: 22px;
      top: 50%;
      transform: translateY(-50%);
      z-index: 10;
      display: grid;
      grid-template-rows: 32px 148px 32px;
      align-items: center;
      justify-items: center;
      gap: 8px;
      padding: 8px 7px;
      border: 1px solid rgba(185, 194, 206, .9);
      border-radius: 8px;
      background: rgba(255, 255, 255, .94);
      box-shadow: 0 10px 28px rgba(16, 24, 40, .13);
      backdrop-filter: blur(8px);
    }}

    .zoom-button {{
      width: 32px;
      min-height: 32px;
      padding: 0;
      border-radius: 6px;
      font-size: 18px;
      font-weight: 650;
      line-height: 1;
    }}

    .zoom-slider {{
      writing-mode: vertical-lr;
      direction: rtl;
      width: 24px;
      height: 148px;
      accent-color: #344054;
      cursor: pointer;
    }}

    .details {{
      min-height: 96px;
      max-height: 230px;
      overflow: auto;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      color: #25313d;
      font-size: 12px;
      line-height: 1.45;
    }}

    .muted {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
    }}

    @media (max-width: 900px) {{
      .app {{
        grid-template-columns: 1fr;
        grid-template-rows: auto minmax(70vh, 1fr);
      }}

      aside {{
        max-height: 45vh;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <section class="section">
        <h1>Odoo Module Graph</h1>
        <p class="muted" id="scopeSummary">Manifest dependency graph.</p>
      </section>

      <section class="section">
        <h2>Stats</h2>
        <div class="stats">
          <div class="stat"><span>Visible nodes</span><strong id="visibleNodes">0</strong></div>
          <div class="stat"><span>Visible edges</span><strong id="visibleEdges">0</strong></div>
          <div class="stat"><span>All nodes</span><strong id="allNodes">0</strong></div>
          <div class="stat"><span>All edges</span><strong id="allEdges">0</strong></div>
        </div>
      </section>

      <section class="section">
        <h2>Search</h2>
        <div class="row">
          <input id="search" type="search" placeholder="Module name" value="base" list="moduleSuggestions">
          <datalist id="moduleSuggestions"></datalist>
          <button id="clearSearch" type="button">Clear</button>
        </div>
        <label><input id="fuzzySearch" type="checkbox" checked>Fuzzy</label>
      </section>

      <section class="section">
        <h2>Direction</h2>
        <label><input id="dirIn" type="checkbox" class="direction" value="in" checked disabled>In</label>
        <label><input id="dirOut" type="checkbox" class="direction" value="out" checked disabled>Out</label>
      </section>

      <section class="section">
        <h2>Node Scope</h2>
        <div id="kindFilters"></div>
      </section>

      <section class="section">
        <h2>Edge Types</h2>
        <label><input type="checkbox" class="etype" value="depends" checked>depends</label>
      </section>

      <section class="section">
        <h2>Layout</h2>
        <div class="row">
          <select id="layout">
            <option value="breadthfirst">Breadthfirst</option>
            <option value="cose">Cose</option>
            <option value="circle">Circle</option>
            <option value="grid">Grid</option>
            <option value="concentric">Concentric</option>
            <option value="random">Random</option>
            <option value="preset">Preset</option>
          </select>
          <button id="runLayout" type="button">Run</button>
          <button id="fit" type="button">Fit</button>
        </div>
      </section>

      <section class="section">
        <h2>Legend</h2>
        <div id="legend" class="legend"></div>
      </section>

      <section class="section">
        <h2>Selection</h2>
        <div id="details" class="details muted">Select a node or edge.</div>
      </section>
    </aside>

    <main>
      <div class="topbar">
        <div class="muted" id="status">Loading graph...</div>
        <div class="row">
          <button id="showExternalRefs" type="button">Only external targets</button>
          <button id="reset" type="button">Reset</button>
        </div>
      </div>
      <div class="graph-wrap">
        <div id="cy"></div>
        <div class="zoom-control" aria-label="Zoom controls">
          <button id="zoomIn" class="zoom-button" type="button" title="Zoom in">+</button>
          <input id="zoomSlider" class="zoom-slider" type="range" min="5" max="300" value="100" title="Zoom">
          <button id="zoomOut" class="zoom-button" type="button" title="Zoom out">-</button>
        </div>
      </div>
    </main>
  </div>

  <script>
    const graphData = __GRAPH_DATA__;
    const kindNames = [...new Set([
      ...Object.values(graphData.node_kinds || {{}}),
      "unknown/external"
    ])].sort((a, b) => a.localeCompare(b));
    const kindPalette = [
      { bg: "#f6f9fd", border: "#7f9fc5" },
      { bg: "#f4fbf6", border: "#7aa683" },
      { bg: "#fbf5fd", border: "#b47ac1" },
      { bg: "#fff8ed", border: "#d59b4f" },
      { bg: "#f6f7fb", border: "#9aa4b2" }
    ];

    const kindStyles = Object.fromEntries(kindNames.map((kind, index) => [
      kind,
      kind === "unknown/external"
        ? { bg: "#fffaf2", border: "#d9a05b" }
        : kindPalette[index % kindPalette.length]
    ]));

    function cssEscape(value) {{
      if (window.CSS && CSS.escape) return CSS.escape(value);
      return String(value).replace(/["\\\\]/g, "\\\\$&");
    }}

    function moduleDir(id, kind) {{
      const moduleInfo = graphData.modules[id];
      if (moduleInfo && moduleInfo.path) {{
        const parts = moduleInfo.path.split("/");
        return parts.length >= 2 ? parts[parts.length - 2] : "";
      }}
      return "external";
    }}

    const nodes = Object.entries(graphData.node_kinds).map(([id, kind]) => {{
      const label = graphData.modules[id]?.name || id;
      const path = graphData.modules[id]?.path || id;
      const dir = moduleDir(id, kind);
      return {{
        data: {{
          id,
          label,
          display: `${{dir}}/${{label}}`,
          path,
          kind,
          dir
        }}
      }};
    }});

    const edges = graphData.edges.map((edge, index) => ({
      data: {{
        id: `e${{index}}`,
        source: edge.source,
        target: edge.target,
        source_name: edge.source_name || edge.source,
        target_name: edge.target_name || edge.target,
        dependency_name: edge.dependency_name || edge.target_name || edge.target,
        type: edge.type,
        target_kind: edge.target_kind,
        file: edge.file || edge.manifest || ""
      }}
    }));

    const cy = cytoscape({{
      container: document.getElementById("cy"),
      elements: [...nodes, ...edges],
      minZoom: 0.05,
      maxZoom: 3,
      wheelSensitivity: 0.18,
      style: [
        {{
          selector: "node",
          style: {{
            "shape": "round-rectangle",
            "background-color": "#fbfdfb",
            "border-color": "#7aa683",
            "border-width": 1.2,
            "label": "data(label)",
            "font-size": 13,
            "font-weight": 650,
            "text-wrap": "wrap",
            "text-max-width": 178,
            "text-valign": "center",
            "text-halign": "center",
            "color": "#1f2933",
            "width": "label",
            "height": "label",
            "padding": "12px",
            "shadow-blur": 10,
            "shadow-color": "#162033",
            "shadow-opacity": 0.10,
            "shadow-offset-x": 0,
            "shadow-offset-y": 2
          }}
        }},
        ...kindNames.map(kind => ({
          selector: `node[kind = "${{cssEscape(kind)}}"]`,
          style: {{ "background-color": kindStyles[kind].bg, "border-color": kindStyles[kind].border }}
        })),
        {{
          selector: "edge",
          style: {{
            "width": 1.1,
            "line-color": "#b8c0ca",
            "target-arrow-color": "#b8c0ca",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            "opacity": 0.38
          }}
        }},
        {{ selector: 'edge[type = "depends"]', style: {{ "line-color": "#75808d", "target-arrow-color": "#75808d", "width": 1.4 }} }},
        {{ selector: ".outgoing-edge", style: {{ "line-color": "#2e7d32", "target-arrow-color": "#2e7d32", "width": 2.2, "opacity": 1 }} }},
        {{ selector: ".incoming-edge", style: {{ "line-color": "#b42318", "target-arrow-color": "#b42318", "width": 2.2, "opacity": 1 }} }},
        {{ selector: ".hidden", style: {{ "display": "none" }} }},
        {{ selector: ".matched", style: {{ "background-color": "#fffaf2" }} }},
        {{ selector: ":selected", style: {{ "border-width": 1.6, "border-color": "#b42318", "line-color": "#28323d", "target-arrow-color": "#28323d", "opacity": 1 }} }}
      ],
      layout: {{ name: "preset" }}
    }});

    const visibleNodes = document.getElementById("visibleNodes");
    const visibleEdges = document.getElementById("visibleEdges");
    const allNodes = document.getElementById("allNodes");
    const allEdges = document.getElementById("allEdges");
    const status = document.getElementById("status");
    const details = document.getElementById("details");
    const search = document.getElementById("search");
    const zoomSlider = document.getElementById("zoomSlider");
    const scopeSummary = document.getElementById("scopeSummary");
    const kindFilters = document.getElementById("kindFilters");
    const legend = document.getElementById("legend");

    allNodes.textContent = nodes.length;
    allEdges.textContent = edges.length;

    function renderScopeControls() {{
      const roots = Object.entries(graphData.scope?.roots || {{}});
      scopeSummary.textContent = roots.length
        ? `Manifest dependency graph generated from ${{roots.length}} source root(s).`
        : "Manifest dependency graph.";

      kindFilters.innerHTML = "";
      legend.innerHTML = "";
      kindNames.forEach(kind => {{
        const label = document.createElement("label");
        const input = document.createElement("input");
        input.type = "checkbox";
        input.className = "kind";
        input.value = kind;
        input.checked = true;
        label.appendChild(input);
        label.append(kind);
        kindFilters.appendChild(label);

        const item = document.createElement("div");
        item.className = "legend-item";
        const swatch = document.createElement("span");
        swatch.className = "swatch";
        swatch.style.background = kindStyles[kind].bg;
        swatch.style.borderColor = kindStyles[kind].border;
        item.appendChild(swatch);
        item.append(kind === "unknown/external" ? "unknown/external target" : `${{kind}} module`);
        legend.appendChild(item);
      }});
    }}

    function checkedValues(selector) {{
      return new Set([...document.querySelectorAll(selector + ":checked")].map(input => input.value));
    }}

    function edgeSearchText(edge) {{
      const d = edge.data();
      return [d.source, d.target, d.source_name, d.target_name, d.dependency_name, d.type, d.file].join(" ").toLowerCase();
    }}

    function nodeSearchText(node) {{
      return [node.data("id"), node.data("label"), node.data("display"), node.data("path"), node.data("dir")].join(" ").toLowerCase();
    }}

    function nodeMatchesSearch(node, query, fuzzy) {{
      if (fuzzy) return nodeSearchText(node).includes(query);
      return [node.data("label"), node.data("display"), node.data("id"), node.data("path")]
        .some(value => String(value).toLowerCase() === query);
    }}

    function populateModuleSuggestions() {{
      const datalist = document.getElementById("moduleSuggestions");
      const seen = new Set();
      datalist.innerHTML = "";
      cy.nodes()
        .map(node => node.data("display"))
        .filter(value => {{
          if (seen.has(value)) return false;
          seen.add(value);
          return true;
        }})
        .sort((a, b) => a.localeCompare(b))
        .forEach(value => {{
          const item = document.createElement("option");
          item.value = value;
          datalist.appendChild(item);
        }});
    }}

    function updateDirectionControls(enabled) {{
      const controls = [document.getElementById("dirIn"), document.getElementById("dirOut")];
      controls.forEach(control => {{
        control.disabled = !enabled;
        if (!enabled) control.checked = true;
      }});
    }}

    function applyFilters() {{
      const kinds = checkedValues(".kind");
      const types = checkedValues(".etype");
      const query = search.value.trim().toLowerCase();
      const fuzzy = document.getElementById("fuzzySearch").checked;
      const showIn = document.getElementById("dirIn").checked;
      const showOut = document.getElementById("dirOut").checked;

      cy.elements().removeClass("hidden matched");

      cy.nodes().forEach(node => {{
        if (!kinds.has(node.data("kind"))) node.addClass("hidden");
      }});

      cy.edges().forEach(edge => {{
        if (!types.has(edge.data("type"))) edge.addClass("hidden");
        if (edge.source().hasClass("hidden") || edge.target().hasClass("hidden")) edge.addClass("hidden");
      }});

      if (query) {{
        const baseVisibleNodes = new Set(cy.nodes().not(".hidden").map(node => node.id()));
        const baseVisibleEdges = new Set(cy.edges().not(".hidden").map(edge => edge.id()));
        const searchModules = new Set();
        cy.nodes().forEach(node => {{
          if (!baseVisibleNodes.has(node.id()) || !nodeMatchesSearch(node, query, fuzzy)) node.addClass("hidden");
          else {{
            node.addClass("matched");
            searchModules.add(node.id());
          }}
        }});
        updateDirectionControls(searchModules.size > 0);
        cy.edges().forEach(edge => {{
          const directionMatch =
            searchModules.size === 0 ||
            (showIn && searchModules.has(edge.target().id())) ||
            (showOut && searchModules.has(edge.source().id()));
          const textMatch = fuzzy && edgeSearchText(edge).includes(query);
          const edgeVisible = searchModules.size > 0 ? directionMatch : textMatch;
          if (!baseVisibleEdges.has(edge.id()) || !edgeVisible) edge.addClass("hidden");
          else {{
            edge.removeClass("hidden");
            if (baseVisibleNodes.has(edge.source().id())) edge.source().removeClass("hidden").addClass("matched");
            if (baseVisibleNodes.has(edge.target().id())) edge.target().removeClass("hidden").addClass("matched");
          }}
        }});
      }} else {{
        updateDirectionControls(false);
      }}

      const shownNodes = cy.nodes().not(".hidden");
      const shownEdges = cy.edges().not(".hidden");
      visibleNodes.textContent = shownNodes.length;
      visibleEdges.textContent = shownEdges.length;
      status.textContent = `${{shownNodes.length}} nodes, ${{shownEdges.length}} edges visible`;
    }}

    function runLayout() {{
      const name = document.getElementById("layout").value;
      const baseLayout = {{ fit: true, padding: 40 }};
      const options = {{
        cose: {{ ...baseLayout, name: "cose", animate: false, nodeRepulsion: 9000, idealEdgeLength: 120 }},
        breadthfirst: {{ ...baseLayout, name: "breadthfirst", animate: false, directed: true, spacingFactor: 1.25 }},
        circle: {{ ...baseLayout, name: "circle", animate: false }},
        grid: {{ ...baseLayout, name: "grid", animate: false }},
        concentric: {{ ...baseLayout, name: "concentric", animate: false, minNodeSpacing: 18 }},
        random: {{ ...baseLayout, name: "random", animate: false }},
        preset: {{ ...baseLayout, name: "preset" }},
        dagre: {{ ...baseLayout, name: "dagre", rankDir: "LR", nodeSep: 32, rankSep: 90, edgeSep: 12, animate: false }},
        cola: {{ ...baseLayout, name: "cola", animate: false, nodeSpacing: 12, edgeLength: 130 }},
        klay: {{ ...baseLayout, name: "klay", animate: false, klay: {{ direction: "RIGHT", spacing: 28 }} }},
        fcose: {{ ...baseLayout, name: "fcose", animate: false, quality: "default", nodeSeparation: 45, idealEdgeLength: 120 }}
      }}[name];
      try {{
        cy.elements().not(".hidden").layout(options).run();
        requestAnimationFrame(() => normalizeAutoZoom());
      }} catch (error) {{
        status.textContent = `${{name}} layout is not available.`;
      }}
    }}

    function graphCenterRenderedPosition() {{
      const box = cy.container().getBoundingClientRect();
      return {{ x: box.width / 2, y: box.height / 2 }};
    }}

    function setZoomValue(value) {{
      const zoom = Math.max(cy.minZoom(), Math.min(cy.maxZoom(), value));
      cy.zoom({{ level: zoom, renderedPosition: graphCenterRenderedPosition() }});
      zoomSlider.value = String(Math.round(zoom * 100));
    }}

    function syncZoomSlider() {{
      zoomSlider.value = String(Math.round(cy.zoom() * 100));
    }}

    function visibleElements() {{
      return cy.elements().not(".hidden");
    }}

    function normalizeAutoZoom() {{
      const maxAutoZoom = 1.15;
      if (cy.zoom() > maxAutoZoom) {{
        cy.zoom({{ level: maxAutoZoom, renderedPosition: graphCenterRenderedPosition() }});
      }}
      cy.center(visibleElements());
      syncZoomSlider();
    }}

    function clearDirectionMarks() {{
      cy.edges().removeClass("incoming-edge outgoing-edge");
    }}

    let lastNodeTap = {{ id: "", at: 0 }};

    function focusNode(node) {{
      search.value = node.data("label");
      applyFilters();
      runLayout();
    }}

    cy.on("tap", "node", event => {{
      const node = event.target;
      const now = Date.now();
      const isDoubleTap = lastNodeTap.id === node.id() && now - lastNodeTap.at < 350;
      lastNodeTap = {{ id: node.id(), at: now }};
      const incoming = node.incomers("edge").not(".hidden").length;
      const outgoing = node.outgoers("edge").not(".hidden").length;
      clearDirectionMarks();
      node.outgoers("edge").not(".hidden").addClass("outgoing-edge");
      node.incomers("edge").not(".hidden").addClass("incoming-edge");
      details.classList.remove("muted");
      details.textContent = JSON.stringify({{
        module: node.data("label"),
        path: node.data("path"),
        dir: node.data("dir"),
        kind: node.data("kind"),
        visible_incoming_edges: incoming,
        visible_outgoing_edges: outgoing
      }}, null, 2);
      if (isDoubleTap) focusNode(node);
    }});

    cy.on("tap", "edge", event => {{
      clearDirectionMarks();
      details.classList.remove("muted");
      details.textContent = JSON.stringify(event.target.data(), null, 2);
    }});

    cy.on("tap", event => {{
      if (event.target === cy) {{
        clearDirectionMarks();
        details.classList.add("muted");
        details.textContent = "Select a node or edge.";
      }}
    }});

    renderScopeControls();
    document.querySelectorAll(".kind, .etype, .direction").forEach(input => input.addEventListener("change", applyFilters));
    document.getElementById("fuzzySearch").addEventListener("change", applyFilters);
    search.addEventListener("input", applyFilters);
    document.getElementById("clearSearch").addEventListener("click", () => {{ search.value = ""; applyFilters(); }});
    document.getElementById("runLayout").addEventListener("click", runLayout);
    document.getElementById("fit").addEventListener("click", () => {{
      cy.fit(cy.elements().not(".hidden"), 40);
      syncZoomSlider();
    }});
    document.getElementById("zoomIn").addEventListener("click", () => setZoomValue(cy.zoom() * 1.25));
    document.getElementById("zoomOut").addEventListener("click", () => setZoomValue(cy.zoom() / 1.25));
    zoomSlider.addEventListener("input", event => setZoomValue(Number(event.target.value) / 100));
    cy.on("zoom", syncZoomSlider);
    document.getElementById("reset").addEventListener("click", () => {{
      document.querySelectorAll(".kind, .etype").forEach(input => input.checked = true);
      search.value = "";
      applyFilters();
      runLayout();
    }});
    document.getElementById("showExternalRefs").addEventListener("click", () => {{
      document.querySelectorAll(".kind").forEach(input => input.checked = true);
      document.querySelectorAll(".etype").forEach(input => input.checked = true);
      search.value = "";
      applyFilters();
      cy.edges().forEach(edge => {{
        if (edge.data("target_kind") !== "unknown/external") edge.addClass("hidden");
      }});
      cy.nodes().forEach(node => {{
        const hasVisibleEdge = node.connectedEdges().some(edge => !edge.hasClass("hidden"));
        if (!hasVisibleEdge) node.addClass("hidden");
      }});
      visibleNodes.textContent = cy.nodes().not(".hidden").length;
      visibleEdges.textContent = cy.edges().not(".hidden").length;
      status.textContent = `${{visibleNodes.textContent}} nodes, ${{visibleEdges.textContent}} edges visible`;
      runLayout();
    }});

    cy.ready(() => {{
      populateModuleSuggestions();
      applyFilters();
      runLayout();
      status.textContent = `${{cy.nodes().not(".hidden").length}} nodes, ${{cy.edges().not(".hidden").length}} edges visible`;
    }});
  </script>
</body>
</html>
"""


def main():
    data = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    template = HTML_TEMPLATE.replace("{{", "{").replace("}}", "}")
    graph_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    rendered = template.replace("__GRAPH_DATA__", graph_json)
    OUT_HTML.write_text(rendered, encoding="utf-8")
    print(OUT_HTML)


if __name__ == "__main__":
    main()
