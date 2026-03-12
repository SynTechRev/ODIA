# RAG Setup Guide

This guide explains how to set up and use the RAG (Retrieval-Augmented Generation) system for natural language querying of the Oraculus legislative document corpus.

## Overview

The RAG system allows you to ask natural language questions about the legislative corpus and receive AI-generated answers with source citations. It combines:

1. **Vector Retrieval**: Semantic search using TF-IDF embeddings
2. **Context Assembly**: Intelligent ranking and deduplication
3. **LLM Generation**: Answer generation with OpenAI, Anthropic, or Ollama

## Prerequisites

### 1. Vector Indices

Before using RAG, ensure you have generated vector indices from your corpus:

```bash
# Ingest and index corpus documents
python scripts/ingest_and_index.py
```

This creates:
- `data/vectors/collection_vectors.npy` - Vector embeddings
- `data/vectors/collection_metadata.npy` - Document metadata
- `data/vectors/collection_vocab.pkl` - Vocabulary for embedder

### 2. LLM Provider Setup

Choose one of the following LLM providers:

#### Option A: OpenAI (Recommended)

1. Sign up at https://platform.openai.com/
2. Generate an API key
3. Set environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

**Cost**: ~$0.15 per 1M tokens with `gpt-4o-mini` (default)

#### Option B: Anthropic Claude

1. Sign up at https://console.anthropic.com/
2. Generate an API key
3. Set environment variable:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export RAG_LLM_PROVIDER="anthropic"
```

#### Option C: Ollama (Local, Free)

1. Install Ollama: https://ollama.ai/
2. Pull a model:

```bash
ollama pull llama3.1
```

3. Configure environment:

```bash
export RAG_LLM_PROVIDER="ollama"
export RAG_LLM_MODEL="llama3.1"
export OLLAMA_BASE_URL="http://localhost:11434"  # default
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This includes:
- `openai>=1.12.0` - OpenAI API client
- `anthropic>=0.21.0` - Anthropic Claude API
- `tiktoken>=0.6.0` - Token counting

## Usage

### CLI Tool

The `rag_query.py` script provides command-line access:

#### Basic Query

```bash
python scripts/rag_query.py --query "What Axon contracts exist in the corpus?"
```

**Output:**
```
======================================================================
Query: What Axon contracts exist in the corpus?
======================================================================

Answer:
Based on the retrieved documents, there are multiple Axon contracts in the corpus,
including body-worn camera systems and related services...

Sources (Confidence: 0.87):
----------------------------------------------------------------------

[1] Axon Enterprise Contract
    ID:        #23-0148
    File:      Axon Quote (1).pdf
    Relevance: 0.920
    Snippet:   This contract establishes terms for body-worn cameras...
```

#### JSON Output

```bash
python scripts/rag_query.py \
  --query "Show surveillance vendors" \
  --json \
  --output results.json
```

#### Filter by Corpus

```bash
python scripts/rag_query.py \
  --query "Body-worn camera contracts" \
  --corpus-filter "#23-0148,#23-0214"
```

#### Dry Run (No LLM)

Test retrieval without consuming API credits:

```bash
python scripts/rag_query.py \
  --query "test query" \
  --dry-run
```

#### Custom Provider/Model

```bash
python scripts/rag_query.py \
  --query "Constitutional issues?" \
  --provider anthropic \
  --model claude-3-haiku-20240307
```

### Integrated Search CLI

The existing `search_cli.py` now supports RAG mode:

```bash
# Standard semantic search (no LLM)
python scripts/search_cli.py --query "vendor contracts"

# RAG mode (with LLM answer)
python scripts/search_cli.py --query "vendor contracts" --rag
```

### API Endpoint

The FastAPI server includes a `/api/v1/rag/query` endpoint:

#### Start Server

```bash
uvicorn oraculus_di_auditor.interface.api:app --reload
```

#### Query via API

```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What Axon contracts were approved in 2023?",
    "top_k": 5,
    "corpus_filter": ["#23-0148", "#23-0214"]
  }'
```

**Response:**
```json
{
  "answer": "Based on the legislative corpus...",
  "sources": [
    {
      "corpus_id": "#23-0148",
      "title": "Axon Contract Agreement",
      "file": "axon_contract.pdf",
      "relevance_score": 0.920,
      "snippet": "This contract was approved on..."
    }
  ],
  "confidence": 0.87
}
```

### Python API

Use RAG programmatically in Python:

```python
from oraculus_di_auditor.rag import OracRAG

# Initialize
rag = OracRAG(llm_provider="openai", llm_model="gpt-4o-mini")

# Load index
rag.load_index(
    index_name="collection",
    vocab_path="data/vectors/collection_vocab.pkl"
)

# Query
result = rag.query(
    question="What constitutional issues are present?",
    top_k=5,
    include_sources=True
)

print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
for source in result['sources']:
    print(f"  - [{source['corpus_id']}] {source['file']}")
```

## Configuration

### Environment Variables

All RAG settings can be configured via environment variables:

```bash
# LLM Configuration
export RAG_LLM_PROVIDER="openai"          # openai | anthropic | ollama
export RAG_LLM_MODEL="gpt-4o-mini"        # Model name
export RAG_TEMPERATURE="0.1"              # 0.0-2.0 (lower = more factual)
export RAG_MAX_RESPONSE_TOKENS="1000"    # Max tokens in response

# Retrieval Configuration
export RAG_TOP_K="5"                      # Documents to retrieve
export RAG_SIMILARITY_THRESHOLD="0.3"    # Min similarity (0.0-1.0)
export RAG_MAX_CONTEXT_TOKENS="4000"     # Max tokens for context

# API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export OLLAMA_BASE_URL="http://localhost:11434"
```

### Config File

Advanced configuration in `config/rag_config.py`:

```python
# Custom vector indices
VECTOR_INDICES = {
    "corpus": "data/vectors/collection",
    "ace": "data/vectors/ace_collection",
    "vicfm": "data/vectors/vicfm_collection",
    "jim": "data/vectors/jim_collection",
}

# Validate configuration
from config.rag_config import validate_config
status = validate_config()
print(status)
```

## Query Types & Prompts

The system automatically selects prompts based on query content:

### Vendor Queries

**Keywords**: `vendor`, `contract`, `procurement`, `axon`, `flock`

**Example**: "What Axon contracts exist?"

### Legal Queries

**Keywords**: `constitutional`, `amendment`, `legal`, `doctrine`, `Fourth Amendment`

**Example**: "What Fourth Amendment issues are present?"

### Anomaly Queries

**Keywords**: `anomaly`, `missing`, `gap`, `incomplete`, `error`

**Example**: "Show missing agenda items"

### Audit Queries

**Keywords**: `audit`, `analyze`, `review`, `report`, `summary`

**Example**: "Generate an audit summary"

### General Queries

Default for all other questions.

## Customizing Prompts

Edit `src/oraculus_di_auditor/rag_prompts.py` to customize system prompts:

```python
CUSTOM_PROMPT = """You are a specialized analyst...

Context:
{context}

Question: {question}

Instructions:
1. ...
2. ...
"""
```

## Multi-Index Routing (Future)

The `RAGRouter` class enables searching multiple indices:

```python
from oraculus_di_auditor.rag import RAGRouter

router = RAGRouter()
indices = router.route_query("vendor contracts with constitutional issues")
# Returns: ["corpus", "vicfm", "jim", "lexicon"]
```

**Note**: Full multi-index support is planned for future releases.

## Performance & Cost

### Token Usage

- **Query embedding**: ~10 tokens
- **Context retrieval**: ~2,000-4,000 tokens (configurable)
- **Response generation**: ~500-1,000 tokens

**Total per query**: ~2,500-5,000 tokens

### Cost Estimates (OpenAI gpt-4o-mini)

- **Input**: $0.150 per 1M tokens
- **Output**: $0.600 per 1M tokens

**Average cost per query**: $0.001-0.003 (0.1-0.3 cents)

### Optimization Tips

1. **Reduce top_k**: Fewer documents = less context
2. **Increase threshold**: Filter low-relevance results
3. **Use caching**: Cache common queries (future feature)
4. **Local models**: Use Ollama for free (slower, lower quality)

## Troubleshooting

### Error: "Vector index not found"

**Solution**: Run indexing first:
```bash
python scripts/ingest_and_index.py
```

### Error: "LLM not available"

**Solution**: Configure API key:
```bash
export OPENAI_API_KEY="sk-..."
```

Or use dry-run mode:
```bash
python scripts/rag_query.py --query "test" --dry-run
```

### Error: "Failed to load vocabulary"

**Solution**: Ensure vocabulary file exists:
```bash
ls -l data/vectors/collection_vocab.pkl
```

Re-run indexing if missing.

### Poor Answer Quality

**Solutions**:
1. Increase `top_k` to retrieve more context
2. Lower `threshold` to include more documents
3. Use more powerful model (`gpt-4` instead of `gpt-4o-mini`)
4. Customize prompts for your use case

### Rate Limiting

If hitting API rate limits:
1. Add delays between queries
2. Upgrade API tier with provider
3. Use local Ollama for unlimited queries

## Testing

Run RAG tests:

```bash
# Unit tests (no API calls)
python -m pytest tests/test_rag.py -v

# Integration test (requires OPENAI_API_KEY)
export OPENAI_API_KEY="sk-..."
python -m pytest tests/test_rag.py -v
```

## Example Queries

### Vendor Analysis
```bash
python scripts/rag_query.py --query \
  "How many sole-source contracts were awarded to Flock Safety between 2022-2024?"
```

### Legal Analysis
```bash
python scripts/rag_query.py --query \
  "Which constitutional doctrines are triggered by surveillance vendor anomalies?"
```

### Anomaly Investigation
```bash
python scripts/rag_query.py --query \
  "Show all agenda items mentioning body-worn cameras with missing minutes"
```

### Compliance Reporting
```bash
python scripts/rag_query.py --query \
  "Generate a summary of all Fourth Amendment risks in the corpus"
```

## Advanced Usage

### Custom Context Assembly

```python
from oraculus_di_auditor.rag_context import ContextAssembler

assembler = ContextAssembler(max_tokens=8000)  # Larger context
context = assembler.assemble(results)
```

### Custom LLM Provider

```python
from oraculus_di_auditor.llm_providers import BaseLLMProvider

class CustomProvider(BaseLLMProvider):
    def generate(self, prompt, context, **kwargs):
        # Your implementation
        pass
    
    def is_available(self):
        return True

rag = OracRAG()
rag.llm = CustomProvider()
```

## Security Considerations

1. **API Keys**: Never commit API keys to git. Use environment variables.
2. **Input Validation**: RAG endpoint validates query length and parameters.
3. **Rate Limiting**: Consider adding rate limiting to public endpoints.
4. **Context Sanitization**: Retrieved context is not sanitized - ensure corpus sources are trusted.
5. **Cost Control**: Monitor API usage to prevent unexpected bills.

## Future Enhancements

- [ ] Response caching for common queries
- [ ] Streaming responses
- [ ] Multi-index routing implementation
- [ ] Query history and analytics
- [ ] Feedback loop for answer quality
- [ ] Support for additional LLM providers
- [ ] Fine-tuned models for legal domain

## Support

For issues or questions:
1. Check this documentation
2. Review example queries
3. Test with `--dry-run` mode
4. Examine logs for error details
5. Open an issue on GitHub

## References

- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Ollama Documentation](https://ollama.ai/docs/)
- [RAG Architecture Overview](https://arxiv.org/abs/2005.11401)
