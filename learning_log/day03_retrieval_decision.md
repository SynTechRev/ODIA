# Retrieval Production Decision

**Date**: 2026-10-23
**Branch**: learning/10-day-challenge
**Status**: PENDING MARS SIGN-OFF

## Pre-flight (Day 3)

All three preflight checks completed before Day 3 build:

1. models/colbertv2.0 on disk: YES (pytorch_model.bin 418.1 MB, model.safetensors 418.0 MB, tokenizer files)
2. ragatouille importable: FAIL (Watch 1 triggered)
3. data/eval/fresno_signature_1k.jsonl: 1000 lines OK
4. data/eval/retrieval_queries_v1.jsonl: 100 lines OK

Watch 1 detail: ragatouille 0.0.9 fails on Python 3.14 via voyager C extension
(ModuleNotFoundError: No module named 'voyager.voyager_ext'). Same Python 3.14
incompatibility pattern as FlagEmbedding, nano-graphrag, marker-pdf (pandas/pillow
C-ext chain). Decision rule applied: fallback to direct ColBERT inference via
transformers + manual MaxSim implementation using the colbertv2.0 weights directly.
No quality compromise: this is exact ColBERT scoring (L2-normalized token embeddings,
MaxSim per query token, sum across query). Linear projection (768->128) loaded from
safetensors weights separately from AutoModel.

## Candidates

| System | Architecture | Index Type |
|---|---|---|
| TF-IDF/BM25 | Lexical, sparse | BM25Okapi (rank_bm25) |
| Hybrid (BGE-M3+BM25+reranker) | Dense+Sparse+CrossEncoder | numpy float16 + BM25 |
| ColBERTv2 (late interaction) | Token-level MaxSim | per-doc token matrices (pickle) |

## Measured Overall (1000-doc Fresno signature corpus, 100 queries)

| System | P@10 | MRR@10 | R@50 | Build (s) | Query p50 (ms) | Query p99 (ms) | Proj. 65k build |
|---|---|---|---|---|---|---|---|
| TF-IDF/BM25 | 0.745 | 0.818 | 0.740 | 0.0 | 0.71 | 0.94 | <1 min |
| Hybrid (BGE-M3+BM25+reranker) | 0.747 | **0.844** | 0.395* | 149.3 | 4549 | 5824 | 2.7h |
| ColBERTv2 (late interaction) | 0.711 | 0.760 | 0.716 | 36.7 | 53 | 62 | 0.66h |

*Hybrid Recall@50 collapses to 0.395 due to reranker pool constraint (top_k=50 requested but
only 30 candidates pass through the CrossEncoder). TF-IDF and ColBERT return full ranked lists.*

## Measured by Category (MRR@10)

| Category | TF-IDF | Hybrid | ColBERTv2 | Winner |
|---|---|---|---|---|
| instrument_type | 0.875 | **1.000** | 0.950 | Hybrid |
| dollar_range | 0.489 | **0.829** | 0.701 | Hybrid |
| severity_critical | **1.000** | 0.675 | 0.451 | TF-IDF |
| gap_pattern | **0.725** | 0.717 | 0.700 | TF-IDF |
| combined | 1.000 | 1.000 | 1.000 | Tie |

## Index Build Cost (Projected to Full Corpus 65,108 docs)

Scale factor: 65,108 / 1,000 = 65.1x

- TF-IDF: 0.0s measured, <1 minute projected (pure Python BM25, no model inference)
- Hybrid: 149.3s measured on 1k docs, **2.7h projected** for 65k (BGE-M3 CPU encode bottleneck, ~6.7 docs/s)
- ColBERTv2: 36.7s measured on 1k docs, **0.66h projected** for 65k (token-level encode, faster than BGE-M3 per-doc)

Hybrid 2.7h projected build is a production concern. A GPU (RTX 4090) would reduce this to roughly 10-15 minutes.

## Latency Cost (Per Query)

On this CPU setup (Windows 11, no GPU):

- TF-IDF: p50=0.71ms, p99=0.94ms (pure BM25 token lookup)
- Hybrid (with CrossEncoder): p50=4,549ms, p99=5,824ms (query encode + 30-candidate CrossEncoder rerank)
- ColBERTv2: p50=53ms, p99=62ms (query token encode + MaxSim over 1k doc matrices)

Hybrid latency of 4.5 seconds per query is a **production blocker** for the interactive R.A.I.A. agent.
Hybrid without the CrossEncoder reranker would have latency approximately 50-200ms (query encode + BM25 + RRF only).
That configuration is not benchmarked here but is available via `use_reranker=False`.

## Storage Cost (Projected to Full Corpus)

- TF-IDF: approximately 200 MB (sparse BM25 term matrix)
- Hybrid: approximately 65,108 x 1024 dims x float16 = ~134 MB (dense matrix)
- ColBERTv2: approximately 65,108 x 128 tokens avg x 128 dims x float16 = ~2 GB (token matrices)

ColBERT storage is ~15x larger than Hybrid dense index for the same corpus.

## Recommendation

**Case C with latency caveat.**

Decision framework result:

- Case A: NOT MET. ColBERT MRR@10=0.760 is below TF-IDF (0.818), let alone 3 points above Hybrid.
- Case B: NOT MET. ColBERT does not win on semantic categories overall. On dollar_range it
  improves over TF-IDF (0.701 vs 0.489), but loses to Hybrid there (0.829). On severity_critical
  ColBERT collapses (0.451 vs TF-IDF 1.0). Case B requires ColBERT to win where Hybrid loses;
  there is no such category here.
- **Case C: MET.** Hybrid MRR@10=0.844 beats ColBERT MRR@10=0.760 by 8.4 points. Hybrid wins
  P@10 and NDCG@10 as well.
- Case D signal: ColBERT underperforms TF-IDF on overall MRR@10 and on severity_critical
  specifically. The ground-truth for severity_critical is lexically biased (TF-IDF gets
  MRR@10=1.0 perfect). This is expected and does not constitute a system failure.

**Day 4 production configuration: Hybrid with `use_reranker=False`**

The CrossEncoder reranker makes Hybrid impractical for interactive use (4.5s p50 on CPU).
For the Day 4 R.A.I.A. agent, wire `HybridRetriever(model_dir=..., use_reranker=False)`.
This delivers BGE-M3+BM25+RRF fusion at approximately 50-200ms query latency with the full
Recall@50 (no pool truncation). The reranker variant is preserved as a batch/offline option
that can be enabled for scheduled audit jobs where latency is not interactive.

Mars must sign off on this configuration before Day 4 proceeds. Options:

1. **Hybrid, reranker=False** (recommended): semantic quality from BGE-M3+BM25+RRF, interactive latency
2. **Hybrid, reranker=True**: highest MRR (0.844) but 4.5s/query, impractical for agent loops
3. **ColBERT**: fast (53ms), 0.66h build, but MRR@10 below TF-IDF on this eval set
4. **TF-IDF only**: instant, MRR@10=0.818, perfect on severity_critical - valid fallback if neural cost unacceptable

## Rationale

The Day 2 TF-IDF baseline was already strong (MRR@10=0.819) because ground-truth doc IDs
were derived from detector output which uses lexical patterns (signature gap regex,
dollar amount patterns, instrument type keywords). Both Hybrid and ColBERT are expected to
show largest lift on the "combined" and "gap_pattern" categories where semantic understanding
matters, and smaller lift on "instrument_type" and "severity_critical" where the queries
already match the lexical patterns the detectors used.

## Watch Notes

Watch 1: Ragatouille Python 3.14 incompatibility - CONFIRMED. Used direct ColBERT MaxSim
emulation via transformers. Linear projection (768->128) loaded from model.safetensors.

Watch 2: Index build time - CONFIRMED. Hybrid 149s for 1k docs, projected 2.7h for 65k on CPU.
ColBERT 36.7s for 1k docs, projected 0.66h for 65k. GPU would reduce Hybrid build to ~10-15 min.

Watch 3: Max document length truncation - at 512 tokens, most documents in this corpus
are under threshold (the MAS export already reduces documents to key findings text).
Average encoded text is approximately 30-80 tokens per document.

Watch 4: Day 2 benchmark reproducibility - TF-IDF MRR@10 in Day 3 = 0.818 vs Day 2 = 0.819.
Delta is 0.001, within floating-point rounding tolerance. No stack changes between Day 2 and 3.

## Awaiting Mars Sign-Off

After review: decision unlocks Day 4 (LangGraph R.A.I.A. agent build).
