# Semiotic Graph Structures

## Overview

CDSCE generates five types of semantic graphs to visualize and analyze relationships between legal terms, doctrines, etymologies, and concepts. These graphs enable network analysis, cluster detection, and relationship mining across the legal semantic space.

## Graph Types

### 1. Synonym Graph

**Purpose:** Map terms with similar or equivalent meanings.

**Structure:** Undirected graph (adjacency list)
```json
{
  "node_count": 42,
  "edges": {
    "liberty": ["freedom", "autonomy", "independence"],
    "freedom": ["liberty", "independence"],
    "search": ["examination", "inspection"],
    "seizure": ["taking", "confiscation"]
  }
}
```

**Edge Criteria:**
- Explicit synonyms in dictionary definitions
- High semantic similarity (>0.8)
- Overlapping doctrinal usage

**Applications:**
- Query expansion in case law search
- Alternative term suggestions
- Semantic equivalence chains

---

### 2. Antonym Graph

**Purpose:** Map terms with opposite or contrasting meanings.

**Structure:** Undirected graph (adjacency list)
```json
{
  "node_count": 28,
  "edges": {
    "liberty": ["restraint", "confinement", "tyranny"],
    "freedom": ["bondage", "servitude"],
    "reasonable": ["arbitrary", "capricious"],
    "public": ["private"]
  }
}
```

**Edge Criteria:**
- Explicit antonyms in definitions
- Semantic opposition markers ("not", "opposite of")
- Doctrinal opposition (e.g., strict scrutiny vs. rational basis)

**Applications:**
- Contradiction detection
- Doctrinal conflict identification
- Interpretive tension analysis

---

### 3. Etymology Lineage Graph

**Purpose:** Map etymological relationships and derivations across languages.

**Structure:** Directed acyclic graph (DAG) - roots → derivatives
```json
{
  "node_count": 156,
  "nodes": {
    "latin:libertas": {
      "language": "latin",
      "root": "libertas",
      "meaning": "freedom, state of being free",
      "era": "classical",
      "derivatives": [
        "liberty",
        "liberal",
        "liberation",
        "libertarian"
      ]
    },
    "greek:demokratia": {
      "language": "greek",
      "root": "dēmokratía",
      "meaning": "rule by the people",
      "era": "classical",
      "derivatives": [
        "democracy",
        "democratic"
      ]
    }
  }
}
```

**Node Types:**
- **Root nodes:** Etymology sources (Latin, Greek, Canon Law)
- **Derivative nodes:** Modern legal terms

**Edge Direction:** Root → Derivative

**Applications:**
- Semantic drift analysis (compare modern vs. classical)
- Authority weighting (Latin roots = highest)
- Original meaning interpretation (OPM)

---

### 4. Doctrine-Meaning Graph

**Purpose:** Map legal doctrines to the terms they define or interpret.

**Structure:** Bipartite graph (doctrines ↔ terms)
```json
{
  "node_count": 89,
  "edges": {
    "due_process": [
      "liberty",
      "property",
      "life",
      "deprivation",
      "notice",
      "hearing"
    ],
    "fourth_amendment": [
      "search",
      "seizure",
      "probable_cause",
      "warrant",
      "reasonableness"
    ],
    "strict_scrutiny": [
      "compelling_interest",
      "narrowly_tailored",
      "fundamental_right"
    ]
  }
}
```

**Applications:**
- Doctrine-based term lookup
- Identify key terms for doctrines
- Case law annotation and tagging

---

### 5. Concept Clusters

**Purpose:** Group semantically related terms into coherent concept clusters.

**Structure:** Clustered graph with similarity metrics
```json
{
  "cluster_count": 12,
  "clusters": [
    {
      "cluster_id": 1,
      "terms": [
        "search",
        "seizure",
        "arrest",
        "warrant",
        "probable_cause"
      ],
      "size": 5,
      "common_doctrines": [
        "fourth_amendment",
        "search_and_seizure"
      ],
      "common_etymology": ["latin"],
      "centroid_term": "search"
    },
    {
      "cluster_id": 2,
      "terms": [
        "liberty",
        "freedom",
        "autonomy",
        "independence"
      ],
      "size": 4,
      "common_doctrines": [
        "due_process",
        "substantive_due_process"
      ],
      "common_etymology": ["latin"],
      "centroid_term": "liberty"
    }
  ]
}
```

**Clustering Algorithm:**
1. Calculate term-term similarity matrix
2. Threshold: similarity ≥ 0.6 (default)
3. Group connected components
4. Identify common features (doctrines, etymology)

**Similarity Factors:**
- Shared doctrines: 40% weight
- Shared etymology language: 30% weight
- Shared eras: 30% weight

**Applications:**
- Conceptual organization of legal terminology
- Related term suggestions
- Taxonomy construction

## Graph Analysis

### Centrality Measures

#### Degree Centrality
Identifies most connected terms:
```python
degree_centrality = len(edges[node]) / (total_nodes - 1)
```

**High degree centrality** indicates:
- Foundational legal concepts (e.g., "liberty", "due process")
- Terms with many synonyms/related concepts
- Hub terms in legal reasoning

#### Betweenness Centrality
Identifies bridge terms connecting clusters:
```python
betweenness = Σ(shortest_paths_through_node / total_shortest_paths)
```

**High betweenness** indicates:
- Terms connecting multiple doctrines
- Cross-cutting concepts
- Integration points between legal areas

### Cycle Detection

**Etymology Graph:** Should be acyclic (DAG)
- Cycles indicate circular etymology (error condition)
- Validation check during graph construction

**Synonym/Antonym Graphs:** Cycles are acceptable
- Synonym cycle: A↔B↔C↔A (valid equivalence chain)
- Antonym cycle: Logical contradiction (flag for review)

### Path Analysis

#### Shortest Path
Find semantic distance between terms:
```python
path = shortest_path(graph, "liberty", "tyranny")
# => ["liberty", "restraint", "tyranny"]
```

**Applications:**
- Measure semantic relatedness
- Find definitional chains
- Identify conceptual bridges

#### All Paths
Enumerate all semantic connections:
```python
paths = all_simple_paths(graph, "search", "privacy", max_length=4)
```

**Applications:**
- Discover indirect relationships
- Map doctrinal connections
- Generate explanation chains

## Graph Generation Process

### Step 1: Corpus Ingestion
```python
corpus = cdsce_engine.generate_corpus(terms)
```

### Step 2: Graph Building
```python
builder = CDSCEGraphBuilder()
graphs = builder.build_all_graphs(corpus)
```

### Step 3: Validation
- Check etymology graph is acyclic
- Verify node count matches term count
- Validate edge consistency

### Step 4: Analysis
- Calculate centrality measures
- Detect clusters
- Identify outliers

### Step 5: Export
```python
builder.save_graph_index(graphs)
# => legal/semiotics/SEMIOTIC_GRAPH_INDEX.json
```

## Graph Metrics

### Density
```python
density = 2 × edge_count / (node_count × (node_count - 1))
```

**Interpretation:**
- Low density (< 0.1): Sparse, specialized terminology
- Medium density (0.1-0.3): Moderate interconnection
- High density (> 0.3): Highly interconnected concepts

### Diameter
```python
diameter = max(shortest_path_length(u, v) for all u, v)
```

**Interpretation:**
- Small diameter (≤ 3): Tightly connected semantic space
- Large diameter (> 5): Disparate concept clusters

### Connected Components
```python
components = strongly_connected_components(graph)
```

**Interpretation:**
- Single component: Unified semantic field
- Multiple components: Distinct conceptual domains

## Visualization

### Graph Layouts

**Force-Directed Layout** (Synonym/Antonym):
- Nodes repel each other
- Edges act as springs
- Reveals natural clusters

**Hierarchical Layout** (Etymology):
- Roots at top
- Derivatives below
- Clear lineage visualization

**Bipartite Layout** (Doctrine-Meaning):
- Doctrines on left
- Terms on right
- Edges connect domains

### Color Coding

**By Etymology:**
- Latin: Blue
- Greek: Green
- Canon Law: Purple
- Common Law: Orange

**By Era:**
- Founding (1789-1791): Dark blue
- Reconstruction (1868): Gray
- Modern (2000+): Light blue

**By Drift:**
- Minimal (< 0.2): Green
- Moderate (0.2-0.6): Yellow
- Severe (> 0.6): Red

## Integration with Other Systems

### JIM (Judicial Interpretive Matrix)
- Doctrine graph feeds JIM doctrine mappings
- Centrality measures inform term importance
- Path analysis reveals doctrinal connections

### MSH (Meaning Stabilization & Harmonization)
- Synonym graph informs harmonization
- Etymology graph provides authority weighting
- Cluster analysis guides divergence detection

### ACE (Anomaly Correlation Engine)
- Antonym graph helps detect contradictions
- Outlier terms flagged as anomalies
- Disconnected components indicate gaps

## Use Cases

### Legal Research
- Find all terms related to Fourth Amendment
- Discover connections between doctrines
- Generate comprehensive term lists

### Judicial Analysis
- Identify key terms in legal arguments
- Map semantic relationships in opinions
- Detect conceptual shifts over time

### Education
- Visualize legal concept relationships
- Build interactive terminology maps
- Create semantic navigation tools

## Performance

| Operation | Complexity | Time (167 terms) |
|-----------|-----------|------------------|
| Build etymology graph | O(n) | ~50ms |
| Build doctrine graph | O(n) | ~30ms |
| Build synonym/antonym | O(n²) | ~200ms |
| Cluster detection | O(n²) | ~500ms |
| Full graph generation | O(n²) | ~1-2s |

## Future Enhancements

1. **Interactive Visualization**
   - Web-based graph explorer
   - Zoom, pan, filter capabilities
   - Real-time updates

2. **Machine Learning**
   - Automated synonym detection
   - Cluster prediction
   - Link prediction for missing relationships

3. **Temporal Graphs**
   - Track graph evolution over time
   - Visualize semantic drift
   - Animate meaning changes

4. **3D Visualization**
   - Multi-dimensional semantic space
   - VR/AR exploration
   - Immersive legal concept navigation

## References

- **CDSCE Overview:** `docs/cdsce_overview.md`
- **Source Code:** `scripts/jim/cdsce_graph_builder.py`
- **Test Suite:** `tests/cdsce/test_graph_builder.py`
- **Graph Index:** `legal/semiotics/SEMIOTIC_GRAPH_INDEX.json`
