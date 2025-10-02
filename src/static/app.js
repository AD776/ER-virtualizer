(function () {
  const form = document.getElementById("analysis-form");
  const textarea = document.getElementById("input-text");
  const statusEl = document.getElementById("status-message");
  const button = document.getElementById("analyze-button");
  const exportButton = document.getElementById("export-button");
  const graphEl = document.getElementById("graph");
  const emptyState = document.getElementById("graph-empty");

  let cy = null;
  let latestTriplets = [];

  function getCssColor(variableName, fallback) {
    const value = getComputedStyle(document.documentElement)
      .getPropertyValue(variableName)
      .trim();
    return value || fallback;
  }

  function colorFor(type) {
    if (!type) {
      return getCssColor("--node", "#38bdf8");
    }
    const palette = {
      human: "--human",
      person: "--human",
      country: "--country",
      gpe: "--country",
      organisation: "--org",
      organization: "--org",
      org: "--org",
    };
    const key = palette[type.toLowerCase()] || "--node";
    return getCssColor(key, "#38bdf8");
  }

  function formatLabel(label, type) {
    const name = label || "Unknown";
    const typeLabel = (type || "entity").replace(/_/g, " ").toUpperCase();
    return `${name}\n${typeLabel}`;
  }

  function destroyGraph() {
    if (cy) {
      cy.destroy();
      cy = null;
    }
    if (graphEl) {
      graphEl.innerHTML = "";
    }
    setExportAvailability(false);
  }

  function buildElements(triplets) {
    const nodesMap = new Map();
    const edges = [];

    triplets.forEach((triplet, index) => {
      const subjectId = triplet.subject_qid || `${triplet.subject}-${index}-s`;
      const objectId = triplet.object_qid || `${triplet.object}-${index}-o`;

      if (!nodesMap.has(subjectId)) {
        nodesMap.set(subjectId, {
          id: subjectId,
          label: triplet.subject,
          type: triplet.subject_type || "entity",
        });
      }

      if (!nodesMap.has(objectId)) {
        nodesMap.set(objectId, {
          id: objectId,
          label: triplet.object,
          type: triplet.object_type || "entity",
        });
      }

      edges.push({
        data: {
          id: `e-${index}`,
          source: subjectId,
          target: objectId,
          label: triplet.predicate || "",
        },
      });
    });

    const nodes = Array.from(nodesMap.values()).map((node) => ({
      data: {
        id: node.id,
        label: node.label || "Unknown",
        type: node.type || "entity",
        color: colorFor(node.type),
        displayLabel: formatLabel(node.label, node.type),
      },
    }));

    return { nodes, edges };
  }

  function layoutFor(nodesCount) {
    if (nodesCount <= 2) {
      return { name: "grid", fit: true, padding: 50 };
    }
    if (nodesCount <= 4) {
      return { name: "circle", fit: true, padding: 50 }; 
    }
    return {
      name: "cose",
      animate: false,
      fit: true,
      padding: 80,
      nodeRepulsion: 9000,
      idealEdgeLength: 160,
      nodeOverlap: 16,
      gravity: 0.8,
      numIter: 1200,
      initialTemp: 1000,
      coolingFactor: 0.99,
      minTemp: 1.0,
    };
  }

  function renderGraph(triplets) {
    latestTriplets = Array.isArray(triplets) ? triplets : [];

    destroyGraph();

    if (!latestTriplets.length) {
      emptyState.hidden = false;
      setExportAvailability(false);
      return;
    }

    emptyState.hidden = true;

    if (typeof cytoscape === "undefined") {
      console.error("Cytoscape.js failed to load.");
      return;
    }

    const { nodes, edges } = buildElements(latestTriplets);

    cy = cytoscape({
      container: graphEl,
      elements: [...nodes, ...edges],
      minZoom: 0.4,
      maxZoom: 1.8,
      wheelSensitivity: 0.2,
      autoungrabify: false,
      autounselectify: false,
      style: [
        {
          selector: "node",
          style: {
            width: 84,
            height: 84,
            "background-color": "data(color)",
            "border-width": 2,
            "border-color": "rgba(14, 116, 144, 0.55)",
            label: "data(displayLabel)",
            color: "#e2e8f0",
            "text-wrap": "wrap",
            "text-max-width": 90,
            "text-valign": "center",
            "text-halign": "center",
            "font-size": 12,
            "font-weight": 600,
            "text-outline-color": "rgba(15, 23, 42, 0.7)",
            "text-outline-width": 3,
            "line-height": 1.2,
          },
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "curve-style": "bezier",
            "line-color": getCssColor("--edge", "#facc15"),
            "target-arrow-color": getCssColor("--edge", "#facc15"),
            "target-arrow-shape": "triangle",
            "arrow-scale": 1.1,
            label: "data(label)",
            "font-size": 11,
            color: getCssColor("--edge", "#facc15"),
            "text-background-color": "rgba(15, 23, 42, 0.75)",
            "text-background-opacity": 0.9,
            "text-background-padding": 3,
            "text-background-shape": "roundrectangle",
            "text-rotation": "autorotate"
          },
        },
      ],
    });

    const layout = layoutFor(nodes.length);
    cy.layout(layout).run();
    cy.center();
    cy.fit(null, 40);
    setExportAvailability(true);
  }

  function setExportAvailability(enabled) {
    if (exportButton) {
      exportButton.disabled = !enabled;
    }
  }

  function exportGraph() {
    if (!cy) {
      return;
    }

    try {
      const background = getCssColor("--bg", "#0f172a");
      const dataUrl = cy.png({ full: true, scale: 2, bg: background || "#0f172a" });
      const link = document.createElement("a");
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      link.href = dataUrl;
      link.download = `knowledge-graph-${timestamp}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error("Failed to export graph", err);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const text = textarea.value.trim();
    if (!text) {
      statusEl.textContent = "Please provide some text to analyze.";
      renderGraph([]);
      return;
    }

    button.disabled = true;
    statusEl.textContent = "Analyzing...";

    try {
      const response = await fetch("/api/triplets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      const payload = await response.json();
      if (!response.ok) {
        const message = payload && payload.error ? payload.error : "Request failed.";
        statusEl.textContent = message;
        renderGraph([]);
        return;
      }

      const triplets = payload.triplets || [];
      renderGraph(triplets);
      statusEl.textContent = triplets.length
        ? `Found ${triplets.length} relationship${triplets.length === 1 ? "" : "s"}.`
        : "No relationships found for the provided text.";
    } catch (err) {
      console.error(err);
      statusEl.textContent = "Unable to contact the backend. Check your connection.";
      renderGraph([]);
    } finally {
      button.disabled = false;
    }
  }

  form.addEventListener("submit", handleSubmit);
  if (exportButton) {
    exportButton.addEventListener("click", exportGraph);
  }
  renderGraph([]);
})();
