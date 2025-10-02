# Entity Relationship Visualizer

Interactive web app that extracts entities and relationships from free-form text using Wikidata and presents the results as an explorable knowledge graph. The right panel renders the graph with Cytoscape.js, allowing you to drag nodes to refine layout.

- Live demo: <https://entity-relationship-visualizer.onrender.com>

## Requirements

- Python 3.10+
- Pip and virtual environment tooling

Install Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

(Optional) install any system libraries required by spaCy models listed in `requirements.txt`.

## Running the app

```bash
source .venv/bin/activate
flask --app src.app run --debug
```

By default the server starts on <http://127.0.0.1:5000>. Open that URL in a browser to use the UI.

### Command line helper

You can also generate triplets from a text file via the CLI:

```bash
python -m src.cli --input input.txt --output output.txt
```

## Using the visualizer

1. Paste or type descriptive text about people, places, organizations, works of art, etc. (multi-sentence paragraphs work best).
2. Click **Analyze**. The backend extracts named entities, finds related Wikidata entries, and fetches relationships.
3. The knowledge graph panel renders each entity as a draggable node. Hover to read labels, drag to rearrange, and inspect edge tooltips for predicate names.

### Input guidance

- Works with natural language prose describing people, locations, organizations, or creative works. Example: award announcements, biographies, company descriptions.
- Avoid long lists with no grammatical context; include sentences that describe relationships (e.g., "Louise Glück wrote The Wild Iris" rather than just bullet points).
- Provide enough context for Wikidata lookup (full names, city + country, etc.) to improve match accuracy.

## Project structure

- `src/` – Flask app, graph rendering assets, Wikidata integration
- `tests/` – Pytest suite covering pipeline and CLI
- `install.sh`, `generate.sh` – helper scripts for setup and ingestion

Feel free to open issues or pull requests if you expand the entity extraction pipeline or visualization capabilities.
