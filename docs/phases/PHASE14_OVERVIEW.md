# Phase 14: Meta-Causal Inference & Recursive Predictive Governance Engine (RPG-14)

## Executive Summary

**Phase 14** introduces the **Recursive Predictive Governance Engine (RPG-14)** — a meta-causal inference layer that sits above Phases 1-13 as the "governing intelligence" of the entire Oraculus-DI-Auditor system.

**Version**: 1.0.0  
**Status**: ✅ Complete  
**Test Coverage**: 63 tests (100% passing)  
**Total System Tests**: 581 passing (up from 518)  
**Code Volume**: 2,689 lines (core) + 826 lines (tests) = 3,515 total lines  
**Architecture Type**: Meta-causal predictive governance with retrocausal inference

---

## 🎯 Phase 14 Objectives

### Primary Goals

Phase 14 creates a comprehensive governing intelligence layer that:

1. **Retrocausal Inference**
   - Traces causal chains backward to identify root causes
   - Maps causal responsibility across all system components
   - Identifies causal breaks and discontinuities
   - Computes causal influence and pathway strength

2. **Causal Responsibility Quantification**
   - Deterministic Causal Responsibility Index (CRI) on 0-1 scale
   - Harmonic weighted factors from Phase 12
   - QDCL probability integration from Phase 13
   - Deviation-slope adjustments
   - Anomaly-penalty multipliers

3. **Governance Anomaly Detection**
   - 7 required outputs per detection cycle
   - Identifies breaks, contradictions, non-convergent trajectories
   - Detects undefined, impossible, and unexplainable states
   - Discovers systemic inconsistencies
   - Generates prioritized recommended actions

4. **Predictive Governance Prognosis**
   - Best-case governance trajectory
   - Worst-case governance trajectory
   - Scalar-harmonic weighted median trajectory
   - Risk advisory generation
   - Governance stability index calculation

5. **Integration with Phases 1-13**
   - Scalar harmonic weighting (Phase 12)
   - QDCL probability flows (Phase 13)
   - Predictive auditing hooks (Phase 11)
   - Synthetic coherence alignment (Phase 10)

6. **Traceability & Reproducibility**
   - Deterministic outputs
   - Complete reasoning chain documentation
   - Version-locked components
   - Full explainability

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│          Phase 14: Recursive Predictive Governance Engine (RPG-14)          │
│                      (Meta-Causal Intelligence Layer)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Causal Graph Constructor                         │   │
│  │  • Directed acyclic graph (DAG) with retrocausal nodes             │   │
│  │  • State vectors with confidence weights                            │   │
│  │  • Deviation slopes and QDCL probabilities                         │   │
│  │  • Scalar harmonic weighting                                        │   │
│  │  • Cycle detection and validation                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓ ↑                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              Retrocausal Inference Engine                           │   │
│  │  • Root cause identification                                        │   │
│  │  • Backward causal chain tracing                                    │   │
│  │  • Causal influence computation                                     │   │
│  │  • Path strength calculation                                        │   │
│  │  • Causal break detection                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓ ↑                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │         Causal Responsibility Index (CRI) Calculator                │   │
│  │  • 0-1 scale deterministic metric                                   │   │
│  │  • Harmonic factor (30%)                                            │   │
│  │  • Probability factor (30%)                                         │   │
│  │  • Deviation factor (20%)                                           │   │
│  │  • Connectivity factor (20%)                                        │   │
│  │  • Anomaly penalty application                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓ ↑                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              Causal Anomaly Detector                                │   │
│  │  7 Required Outputs:                                                │   │
│  │  1. Anomaly summary                                                 │   │
│  │  2. Break locations                                                 │   │
│  │  3. Contradiction map                                               │   │
│  │  4. Non-convergent trajectories                                     │   │
│  │  5. Undefined states                                                │   │
│  │  6. Systemic inconsistencies                                        │   │
│  │  7. Recommended actions                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓ ↑                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │           Governance Prognosis Generator                            │   │
│  │  • Best-case trajectory (optimistic projection)                     │   │
│  │  • Worst-case trajectory (pessimistic projection)                   │   │
│  │  • Median trajectory (scalar-harmonic weighted)                     │   │
│  │  • Governance stability index                                       │   │
│  │  • Risk advisories with recommendations                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓ ↑                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              Phase 14 Service Orchestrator                          │   │
│  │  • Complete RPG-14 cycle execution                                  │   │
│  │  • Integration with Phases 1-13                                     │   │
│  │  • Governance health auditing                                       │   │
│  │  • Traceability report generation                                   │   │
│  │  • Execution history tracking                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                         Integration Points                                  │
│  Phase 12 (Scalar Convergence)     →  Scalar harmonic weights             │
│  Phase 13 (QDCL)                   →  Probability flows                   │
│  Phase 11 (Predictive Auditing)    →  Detection hooks                     │
│  Phase 10 (Synthetic Coherence)    →  Coherence alignment                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Core Components

### 1. Causal Graph (`causal_graph.py`)

**Purpose**: Foundational data structure for causal relationships

**Key Classes**:
- `CausalGraph`: Main graph container with DAG operations
- `CausalNode`: Individual node with state vectors and metadata
- `StateVector`: Multi-dimensional state representation
- `NodeType`: Enum for forward, retrocausal, predictive nodes

**Features**:
- Directed acyclic graph with cycle detection
- Support for retrocausal nodes (backward inference)
- State vectors with confidence weights
- Deviation slopes and QDCL probabilities
- Scalar harmonic weighting
- Graph validation and traversal algorithms
- Ancestor/descendant queries
- Causal path finding

**Example**:
```python
from oraculus_di_auditor.rpg14 import CausalGraph, NodeType

graph = CausalGraph()
node1 = graph.add_node(
    node_type=NodeType.FORWARD,
    qdcl_probability=0.9,
    scalar_harmonic=1.2,
    deviation_slope=0.3
)
node2 = graph.add_node(qdcl_probability=0.8)
graph.add_edge(node1.node_id, node2.node_id)

validation = graph.validate_graph()
print(f"Graph valid: {validation['is_valid']}")
```

---

### 2. Retrocausal Inference Engine (`retrocausal_inference.py`)

**Purpose**: Backward causal chain tracing and root cause analysis

**Key Methods**:
- `infer_root_causes()`: Identify root causes for target node
- `identify_causal_breaks()`: Detect breaks in causal flow
- `compute_causal_influence()`: Calculate influence strength
- `analyze_causal_chain()`: Analyze node sequence

**Algorithm**:
1. Backward depth-first search from target node
2. Traverse parent relationships up to max_depth
3. Calculate path strength using:
   - QDCL probability multiplication
   - Scalar harmonic averaging
   - Deviation slope penalty
4. Normalize causal strengths across paths
5. Rank root causes by normalized strength

**Path Strength Formula**:
```
strength = prob_product × harmonic_avg × deviation_penalty
where:
  prob_product = ∏ node.qdcl_probability
  harmonic_avg = Σ node.scalar_harmonic / path_length
  deviation_penalty = ∏ (1 / (1 + |node.deviation_slope|))
```

**Example**:
```python
from oraculus_di_auditor.rpg14 import RetrocausalInferenceEngine

engine = RetrocausalInferenceEngine(max_depth=12)
result = engine.infer_root_causes(graph, target_node_id)

for root_cause in result["root_causes"]:
    print(f"Root: {root_cause['root_node_id']}")
    print(f"Strength: {root_cause['normalized_strength']:.3f}")
```

---

### 3. Causal Responsibility Index (`causal_responsibility_index.py`)

**Purpose**: Quantify causal responsibility on deterministic 0-1 scale

**CRI Formula**:
```
CRI = w_h × f_h + w_p × f_p + w_d × f_d + w_c × f_c

where:
  w_h = harmonic_weight (default: 0.3)
  w_p = probability_weight (default: 0.3)
  w_d = deviation_weight (default: 0.2)
  w_c = connectivity_weight (default: 0.2)

  f_h = harmonic_factor = 1 / (1 + |harmonic - 1.0|)
  f_p = probability_factor = qdcl_probability
  f_d = deviation_factor = exp(-|deviation_slope|)
  f_c = connectivity_factor = √(connections / max_connections)

final_CRI = raw_CRI × (1 - anomaly_penalty)
```

**Key Methods**:
- `compute_cri()`: Calculate CRI for single node
- `compute_aggregate_cri()`: Aggregate statistics for multiple nodes
- `rank_by_responsibility()`: Sort all nodes by CRI
- `explain_cri()`: Generate human-readable explanation

**Properties**:
- Deterministic: Same inputs always produce same output
- Bounded: Always in [0, 1] range
- Explainable: Full factor breakdown provided
- Configurable: Weights can be adjusted (must sum to 1.0)

**Example**:
```python
from oraculus_di_auditor.rpg14 import CausalResponsibilityIndex

cri_calc = CausalResponsibilityIndex()
result = cri_calc.compute_cri(graph, node_id, anomaly_penalty=0.2)

print(f"CRI: {result['cri']:.3f}")
print(f"Harmonic factor: {result['factors']['harmonic']:.3f}")
print(cri_calc.explain_cri(result))
```

---

### 4. Causal Anomaly Detector (`causal_anomaly_detector.py`)

**Purpose**: Detect governance anomalies with 7 required outputs

**7 Required Outputs**:

1. **Anomaly Summary**
   - Total anomaly count
   - Breakdown by category
   - Severity distribution

2. **Break Locations**
   - Probability breaks (< threshold)
   - Deviation discontinuities (> threshold)
   - Causal terminations

3. **Contradiction Map**
   - State vector contradictions
   - Invalid probabilities
   - Impossible configurations

4. **Non-Convergent Trajectories**
   - Paths that don't align
   - Divergent outcomes
   - Convergence score < threshold

5. **Undefined States**
   - Missing state vectors
   - Zero-confidence states
   - Incomplete node data

6. **Systemic Inconsistencies**
   - Disconnected subgraphs
   - Harmonic mismatches
   - Global inconsistencies

7. **Recommended Actions**
   - Prioritized by severity
   - Specific action for each anomaly type
   - Actionable guidance

**Detection Algorithms**:
- Probability threshold checking (default: 0.3)
- Deviation slope monitoring (default: 3.0)
- Convergence alignment calculation
- Connected component analysis
- Harmonic consistency validation

**Example**:
```python
from oraculus_di_auditor.rpg14 import CausalAnomalyDetector

detector = CausalAnomalyDetector(
    probability_threshold=0.3,
    deviation_threshold=3.0
)
report = detector.detect_all_anomalies(graph)

summary = report["output_1_anomaly_summary"]
print(f"Total anomalies: {summary['total_anomalies']}")

actions = report["output_7_recommended_actions"]
for action in actions[:5]:
    print(f"[{action['severity']}] {action['action']}")
```

---

### 5. Governance Prognosis Generator (`governance_prognosis.py`)

**Purpose**: Generate predictive governance trajectories

**Trajectory Types**:

1. **Best-Case Trajectory**
   - Optimistic projection
   - Selects highest probability paths
   - Favors high scalar harmonics
   - Minimizes deviation slopes

2. **Worst-Case Trajectory**
   - Pessimistic projection
   - Selects lowest probability paths
   - Accounts for maximum deviations
   - Identifies failure modes

3. **Median Trajectory**
   - Balanced projection
   - Scalar-harmonic weighted selection
   - Closest to harmonic = 1.0
   - Realistic middle ground

**Stability Index Calculation**:
```
stability_score = 0.5 × outcome_stability
                + 0.3 × structural_stability
                + 0.2 × avg_probability

where:
  outcome_stability = 1 - |best_score - worst_score|
  structural_stability = 1 / (1 + 0.1 × (roots + leaves))
  avg_probability = Σ node.qdcl_probability / node_count
```

**Risk Advisory Generation**:
- Unstable governance (stability < threshold)
- Catastrophic trajectory (worst-case < 0.3)
- High uncertainty (spread > 0.5)
- Weak causal chains (avg_prob < 0.5)
- Fragmented causality (too many roots)

**Example**:
```python
from oraculus_di_auditor.rpg14 import GovernancePrognosisGenerator

generator = GovernancePrognosisGenerator(
    time_depth=12,
    branching_factor=5
)
prognosis = generator.generate_prognosis(graph)

print(f"Best-case score: {prognosis['best_case_trajectory']['outcome_score']:.3f}")
print(f"Worst-case score: {prognosis['worst_case_trajectory']['outcome_score']:.3f}")
print(f"Stability: {prognosis['governance_stability_index']['stability_score']:.3f}")
```

---

### 6. Phase 14 Service (`phase14_service.py`)

**Purpose**: Complete RPG-14 orchestration and integration

**Main Methods**:

- `run_cycle()`: Execute complete RPG-14 cycle
- `compute_cri()`: Calculate CRI for nodes
- `detect_causal_breaks()`: Run anomaly detection
- `generate_prognosis()`: Create governance prognosis
- `audit_governance()`: Assess overall governance health
- `integrate_with_phase13()`: Extract Phase 13 probabilities
- `produce_traceability_report()`: Document reasoning chain

**Cycle Execution Flow**:
1. Build causal graph from system state
2. Apply Phase 12 harmonics and Phase 13 probabilities
3. Run anomaly detection (7 outputs)
4. Compute CRI for all nodes
5. Generate governance prognosis
6. Audit governance health
7. Produce traceability report
8. Store in execution history

**Governance Health Assessment**:
```python
if anomalies == 0 and avg_cri >= 0.7 and stability >= 0.8:
    health = "excellent" (score: 0.95)
elif anomalies <= 5 and avg_cri >= 0.5 and stability >= 0.6:
    health = "good" (score: 0.75)
elif anomalies <= 15 and avg_cri >= 0.3 and stability >= 0.4:
    health = "fair" (score: 0.55)
else:
    health = "poor" (score: 0.30)
```

**Example**:
```python
from oraculus_di_auditor.rpg14 import Phase14Service

service = Phase14Service(
    time_depth=12,
    branching_factor=5,
    max_retrocausal_depth=12
)

system_state = {
    "components": [...],
    "dependencies": [...]
}

result = service.run_cycle(
    system_state,
    phase12_harmonics=harmonics,
    phase13_probabilities=probabilities
)

audit = result["governance_audit"]
print(f"Health: {audit['health_status']}")
print(f"Score: {audit['health_score']:.3f}")
```

---

## 🔬 Algorithm Details

### Retrocausal Inference Algorithm

**Input**: Causal graph G, target node n_t, max depth d

**Output**: Set of root causes with normalized strengths

**Pseudocode**:
```
function infer_root_causes(G, n_t, d):
    paths = []
    
    function dfs(node, path, depth):
        if depth > d:
            return
        path = [node] + path
        if node has no parents:
            paths.append(path)
            return
        for parent in node.parents:
            dfs(parent, path, depth + 1)
    
    dfs(n_t, [], 0)
    
    root_causes = []
    for path in paths:
        if path[0] is root:
            strength = calculate_path_strength(path)
            root_causes.append((path[0], strength))
    
    normalize(root_causes)
    return sorted(root_causes, by=strength, reverse=True)
```

**Time Complexity**: O(V + E) where V = vertices, E = edges  
**Space Complexity**: O(V × d) for path storage

---

### CRI Computation Algorithm

**Input**: Graph G, node n, anomaly penalty a

**Output**: CRI value in [0, 1]

**Steps**:

1. **Compute Harmonic Factor**:
   ```
   f_h = 1 / (1 + |n.scalar_harmonic - 1.0|)
   ```

2. **Compute Probability Factor**:
   ```
   f_p = n.qdcl_probability
   ```

3. **Compute Deviation Factor**:
   ```
   f_d = exp(-|n.deviation_slope|)
   ```

4. **Compute Connectivity Factor**:
   ```
   connections = |n.parents| + |n.children|
   max_connections = |G.nodes| - 1
   f_c = √(connections / max_connections)
   ```

5. **Weighted Sum**:
   ```
   raw_CRI = w_h × f_h + w_p × f_p + w_d × f_d + w_c × f_c
   ```

6. **Apply Anomaly Penalty**:
   ```
   final_CRI = raw_CRI × (1 - a)
   ```

7. **Clamp to [0, 1]**:
   ```
   final_CRI = max(0, min(final_CRI, 1))
   ```

**Time Complexity**: O(1) per node  
**Determinism**: Fully deterministic, no random elements

---

### Anomaly Detection Algorithm

**Input**: Causal graph G, thresholds T

**Output**: 7 anomaly reports

**Detection Methods**:

1. **Break Detection**:
   - Check n.qdcl_probability < T.probability
   - Check |n.deviation_slope| > T.deviation

2. **Contradiction Detection**:
   - Compare state vectors within node
   - Check for value_diff > 1.0 with high confidence
   - Validate probability ∈ [0, 1]

3. **Non-Convergence Detection**:
   - Calculate alignment scores between ancestors
   - Compare leaf states to root states
   - Convergence = Σ alignment / ancestor_count

4. **Undefined State Detection**:
   - Check for missing state vectors
   - Identify zero-confidence states

5. **Impossible Node Detection**:
   - Retrocausal with children but no parents
   - Negative scalar harmonics
   - Extreme deviation slopes (|slope| > 100)

6. **Systemic Inconsistency Detection**:
   - Find disconnected components using DFS
   - Compare expected vs actual harmonics

7. **Unexplainable State Detection**:
   - Non-root nodes with no parents
   - Orphan nodes with causal influence

**Time Complexity**: O(V + E) for full graph scan

---

### Trajectory Generation Algorithm

**Input**: Graph G, starting nodes S, optimization mode M

**Output**: Trajectory with nodes and outcome score

**Path Selection**:

- **Best-case**: Select max(probability × harmonic / (1 + |deviation|))
- **Worst-case**: Select min(probability × harmonic / (1 + |deviation|))
- **Median**: Select node closest to harmonic = 1.0

**Outcome Score Calculation**:
```
score = 0.4 × cumulative_probability
      + 0.3 × harmonic_score
      + 0.3 × deviation_score

where:
  cumulative_probability = ∏ node.qdcl_probability
  harmonic_score = 1 / (1 + |avg_harmonic - 1.0|)
  deviation_score = exp(-|avg_deviation|)
```

**Time Complexity**: O(V × time_depth × branching_factor)

---

## 📊 Test Coverage

### Test Statistics

- **Total Tests**: 63
- **Pass Rate**: 100%
- **Coverage Areas**:
  - Causal Graph: 16 tests
  - State Vectors & Nodes: 7 tests
  - Retrocausal Inference: 5 tests
  - CRI Calculation: 7 tests
  - Anomaly Detection: 7 tests
  - Governance Prognosis: 6 tests
  - Phase 14 Service: 15 tests

### Test Categories

**Unit Tests**:
- Component initialization
- Individual method functionality
- Edge case handling
- Input validation
- Error handling

**Integration Tests**:
- Cross-component interaction
- Phase 12/13 integration
- End-to-end cycle execution
- Data flow validation

**Determinism Tests**:
- Output consistency
- Reproducibility verification
- Version locking validation

**Example Test**:
```python
def test_deterministic_output(self):
    """Test that outputs are deterministic."""
    service1 = Phase14Service()
    service2 = Phase14Service()
    
    system_state = {
        "components": [{"id": "comp1", "deviation_slope": 0.5}],
        "dependencies": []
    }
    
    result1 = service1.run_cycle(system_state)
    result2 = service2.run_cycle(system_state)
    
    cri1 = result1["cri_rankings"]["aggregate"]["avg_cri"]
    cri2 = result2["cri_rankings"]["aggregate"]["avg_cri"]
    
    assert cri1 == cri2  # Must be identical
```

---

## 🔌 Integration Guide

### Phase 12 Integration (Scalar Harmonics)

```python
from oraculus_di_auditor.scalar_convergence import Phase12Service
from oraculus_di_auditor.rpg14 import Phase14Service

# Get Phase 12 scalar harmonics
phase12 = Phase12Service()
phase12_report = phase12.execute_phase12_analysis()
harmonics = phase12_report["outputs"]["scalar_recursive_map"]["layers"]

# Extract harmonic values per layer
harmonic_dict = {i: layer["health_score"] for i, layer in enumerate(harmonics)}

# Use in Phase 14
phase14 = Phase14Service()
result = phase14.run_cycle(
    system_state,
    phase12_harmonics=harmonic_dict
)
```

### Phase 13 Integration (QDCL Probabilities)

```python
from oraculus_di_auditor.qdcl import QDCLService
from oraculus_di_auditor.rpg14 import Phase14Service

# Get Phase 13 probabilities
phase13 = QDCLService()
qdcl_output = phase13.execute_qdcl_cycle(system_state)

# Extract probabilities
trajectory_cube = qdcl_output["output_4_trajectory_probability_cube"]
probabilities = {
    t["trajectory_id"]: t["probability"]
    for t in trajectory_cube["trajectories"]
}

# Use in Phase 14
phase14 = Phase14Service()
phase14_integration = phase14.integrate_with_phase13(qdcl_output)

result = phase14.run_cycle(
    system_state,
    phase13_probabilities=probabilities
)
```

### Complete Integration Example

```python
from oraculus_di_auditor.scalar_convergence import Phase12Service
from oraculus_di_auditor.qdcl import QDCLService
from oraculus_di_auditor.rpg14 import Phase14Service

# Initialize services
phase12 = Phase12Service()
phase13 = QDCLService()
phase14 = Phase14Service()

# Define system state
system_state = {
    "components": [
        {"id": "comp1", "deviation_slope": 0.3},
        {"id": "comp2", "deviation_slope": 0.5},
    ],
    "dependencies": [
        {"source": "comp1", "target": "comp2"}
    ]
}

# Get Phase 12 harmonics
phase12_report = phase12.execute_phase12_analysis()
harmonics = {i: 1.0 for i in range(len(system_state["components"]))}

# Get Phase 13 probabilities
qdcl_output = phase13.execute_qdcl_cycle(system_state)
probabilities = {"comp1": 0.9, "comp2": 0.8}

# Run Phase 14 with full integration
result = phase14.run_cycle(
    system_state,
    phase12_harmonics=harmonics,
    phase13_probabilities=probabilities
)

# Access results
print(f"Governance health: {result['governance_audit']['health_status']}")
print(f"Stability: {result['governance_prognosis']['governance_stability_index']['stability_score']:.3f}")
```

---

## 🎓 Usage Examples

See `scripts/phase14_example.py` for comprehensive examples including:

1. **Building Causal Graphs**
   - Node creation with state vectors
   - Edge addition with cycle detection
   - Graph validation

2. **Retrocausal Inference**
   - Root cause identification
   - Causal path tracing
   - Influence computation

3. **CRI Computation**
   - Individual node CRI
   - Aggregate statistics
   - Ranking and explanation

4. **Anomaly Detection**
   - Complete detection cycle
   - 7 required outputs
   - Recommended actions

5. **Governance Prognosis**
   - Best/worst/median trajectories
   - Stability assessment
   - Risk advisories

6. **Complete Service Integration**
   - Full RPG-14 cycle
   - Phase 12/13 integration
   - Governance auditing
   - Traceability reporting

Run the examples:
```bash
export PYTHONPATH=$(pwd)/src
python scripts/phase14_example.py
```

---

## ⚠️ Edge Cases & Limitations

### Edge Cases Handled

1. **Empty Graphs**: Returns valid empty results
2. **Single-Node Graphs**: Handles root/leaf identification
3. **Disconnected Subgraphs**: Detected as systemic inconsistency
4. **Circular Dependencies**: Prevented in forward nodes, allowed for retrocausal
5. **Invalid Probabilities**: Caught by validation
6. **Missing State Vectors**: Flagged as undefined states
7. **Zero Confidence**: Identified as undefined states
8. **Extreme Deviations**: Detected as impossible nodes

### Known Limitations

1. **Graph Size**: Performance degrades with >10,000 nodes (O(V+E) complexity)
2. **Time Depth**: Limited to configurable max (default: 12)
3. **Branching Factor**: Limited to configurable max (default: 5)
4. **Retrocausal Depth**: Limited to prevent infinite loops (default: 12)

### Performance Considerations

- **Memory**: O(V × d) for path storage during retrocausal inference
- **Computation**: O(V + E) for graph traversal operations
- **Scalability**: Tested up to 1,000 nodes with good performance

---

## 🚀 Future Enhancements

Potential Phase 14 extensions:

1. **Parallel Processing**: Multi-threaded anomaly detection
2. **Incremental Updates**: Delta-based graph updates
3. **Machine Learning**: Train CRI weights from historical data
4. **Visualization**: Interactive causal graph visualization
5. **Real-time Monitoring**: Streaming anomaly detection
6. **Advanced Prognosis**: Monte Carlo trajectory simulation
7. **Distributed Graphs**: Federated causal graphs across systems

---

## 📚 API Reference

### Core Classes

**CausalGraph**
- `add_node(node_type, deviation_slope, qdcl_probability, scalar_harmonic, metadata)` → CausalNode
- `add_edge(parent_id, child_id)` → bool
- `get_node(node_id)` → CausalNode | None
- `get_ancestors(node_id, max_depth)` → list[CausalNode]
- `get_descendants(node_id, max_depth)` → list[CausalNode]
- `get_causal_path(start_id, end_id)` → list[CausalNode] | None
- `validate_graph()` → dict
- `get_root_nodes()` → list[CausalNode]
- `get_leaf_nodes()` → list[CausalNode]
- `to_dict()` → dict

**RetrocausalInferenceEngine**
- `infer_root_causes(graph, target_node_id)` → dict
- `identify_causal_breaks(graph, threshold)` → list[dict]
- `compute_causal_influence(graph, source_id, target_id)` → dict
- `analyze_causal_chain(graph, node_ids)` → dict

**CausalResponsibilityIndex**
- `compute_cri(graph, node_id, anomaly_penalty)` → dict
- `compute_aggregate_cri(graph, node_ids, anomaly_penalties)` → dict
- `rank_by_responsibility(graph, anomaly_penalties)` → list[dict]
- `explain_cri(cri_result)` → str

**CausalAnomalyDetector**
- `detect_all_anomalies(graph, scalar_harmonics)` → dict

**GovernancePrognosisGenerator**
- `generate_prognosis(graph, starting_nodes)` → dict

**Phase14Service**
- `run_cycle(system_state, phase12_harmonics, phase13_probabilities)` → dict
- `compute_cri(node_ids, anomaly_penalties)` → dict
- `detect_causal_breaks(scalar_harmonics)` → dict
- `generate_prognosis(starting_nodes)` → dict
- `audit_governance(anomaly_report, cri_rankings, prognosis)` → dict
- `integrate_with_phase13(phase13_output)` → dict
- `produce_traceability_report(anomaly_report, cri_rankings, prognosis)` → dict
- `get_service_info()` → dict

---

## 🛡️ Security & Compliance

**Security Measures**:
- No external dependencies beyond Python stdlib
- No network access
- No file system writes (except explicit saves)
- Input validation on all public methods
- Bounded recursion to prevent stack overflow

**Compliance**:
- ✅ Passes ruff linting (0 errors)
- ✅ Passes black formatting
- ✅ CodeQL security scan (0 vulnerabilities)
- ✅ 100% test passing rate
- ✅ Zero regression in existing tests

---

## 📝 Version History

**Version 1.0.0** (Current)
- Initial release
- 6 core modules (2,689 lines)
- 63 comprehensive tests
- Full integration with Phases 12 & 13
- Complete documentation
- Example scripts

---

## 🎯 Conclusion

Phase 14 successfully delivers a comprehensive meta-causal governance intelligence layer that:

✅ **Traces causality backward and forward**  
✅ **Quantifies responsibility deterministically**  
✅ **Detects anomalies with 7 required outputs**  
✅ **Generates predictive governance prognoses**  
✅ **Integrates seamlessly with Phases 1-13**  
✅ **Provides full traceability and explainability**  
✅ **Passes all quality gates with zero regressions**

**Phase 14 Status**: ✅ **OPERATIONAL**

For questions or issues, see the test suite in `tests/test_phase14.py` or run `scripts/phase14_example.py` for hands-on demonstrations.

---

*Oraculus-DI-Auditor Phase 14: Meta-Causal Inference & Recursive Predictive Governance Engine*  
*Version 1.0.0 | 581 Passing Tests | 0 Security Vulnerabilities*
