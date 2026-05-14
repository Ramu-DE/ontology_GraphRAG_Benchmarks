# Module 1: Step-by-Step Learning Guide

## How to Master LLM Fundamentals

This guide walks you through Module 1 from ground-up understanding.

---

## Learning Path (Recommended Order)

### Day 1: Understand the Big Picture

**1. Read the Overview (30 minutes)**
```bash
cd /workshop/LLM
cat 01_LLM_Fundamentals.md | less
```

**Focus on:**
- How humans vs. machines process language
- The shift from rule-based NLP to neural LLMs
- The end-to-end pipeline overview

**Key Question to Answer:**
> "What makes LLMs different from traditional NLP?"

---

### Day 2: Deep Dive into Tokenization

**1. Read Tokenization Section (20 minutes)**
- Section in `01_LLM_Fundamentals.md`

**2. Run Tokenization Demo (15 minutes)**
```bash
python3 examples/01_tokenization_demo.py
```

**3. Hands-On Exercise:**
Try different texts and see how they tokenize:

```python
# Install tiktoken (OpenAI's tokenizer)
pip install tiktoken

# Try it:
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer

texts = [
    "Hello, world!",
    "The quick brown fox jumps over the lazy dog",
    "你好世界",  # Chinese
    "def hello(): print('hi')",  # Code
]

for text in texts:
    tokens = enc.encode(text)
    print(f"\nText: {text}")
    print(f"Tokens: {tokens}")
    print(f"Count: {len(tokens)}")
```

**Key Questions to Answer:**
> "Why do we use subword tokenization instead of word-level?"
> "How does tokenization affect API costs?"

---

### Day 3: Understand Embeddings

**1. Read Embeddings Section (30 minutes)**
- Section in `01_LLM_Fundamentals.md`

**2. Run Embedding Demo (15 minutes)**
```bash
python3 examples/02_embedding_basics.py
```

**3. Visualize Real Embeddings:**

```python
# Install sentence-transformers
pip install sentence-transformers

from sentence_transformers import SentenceTransformer
import numpy as np

# Load a real embedding model (384 dimensions)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create embeddings
sentences = [
    "The cat sat on the mat",
    "The dog slept on the rug",
    "Quantum computing uses qubits",
]

embeddings = model.encode(sentences)

print(f"Shape: {embeddings.shape}")  # (3, 384)
print(f"Embedding for sentence 1:\n{embeddings[0][:10]}...")  # First 10 dims

# Calculate similarities
from sklearn.metrics.pairwise import cosine_similarity
similarities = cosine_similarity(embeddings)

print("\nSimilarity matrix:")
print(similarities)
```

**Key Questions to Answer:**
> "What does each dimension in an embedding represent?"
> "Why do similar sentences have similar embeddings?"

---

### Day 4: Text Generation Mechanics

**1. Read Text Generation Section (30 minutes)**
- Section in `01_LLM_Fundamentals.md`

**2. Understand Sampling:**

```
Probability Distribution → Sampling Strategy → Next Token

Key parameters:
  • Temperature: 0.0 (deterministic) to 2.0 (random)
  • Top-p: 0.9 (keep 90% probability mass)
  • Top-k: 40 (consider top 40 tokens)
```

**3. Interactive Exercise:**

Try ChatGPT with different parameters:
- **Temperature 0.2:** "Write a Python function to sort a list"
  → Consistent, focused code

- **Temperature 1.0:** "Tell me a creative story"
  → More varied, creative output

**Key Questions to Answer:**
> "When should I use low temperature vs. high temperature?"
> "What's the difference between top-k and top-p sampling?"

---

### Day 5: Transformer Architecture

**1. Read Transformer Section (45 minutes)**
- Section in `01_LLM_Fundamentals.md`
- Focus on Self-Attention mechanism

**2. Visualize Attention:**

Visit: https://github.com/jessevig/bertviz

Or use this simple demo:

```python
import numpy as np

def simple_attention_demo():
    """Simplified attention calculation"""

    # Input sequence: "The cat sat"
    # Simplified embeddings (3D instead of 768D)
    embeddings = {
        "The": np.array([0.1, 0.2, 0.3]),
        "cat": np.array([0.8, 0.9, 0.1]),
        "sat": np.array([0.5, 0.1, 0.5]),
    }

    print("Self-Attention Demo")
    print("="*60)

    # For token "sat", calculate attention to all tokens
    query = embeddings["sat"]  # What "sat" is looking for

    print("\nQuery (sat looking for its subject):")
    print(query)

    print("\nAttention scores:")
    for word, vec in embeddings.items():
        # Attention score = dot product
        score = np.dot(query, vec)
        print(f"  sat → {word}: {score:.3f}")

    # Softmax to get probabilities
    scores = [np.dot(query, vec) for vec in embeddings.values()]
    attention = np.exp(scores) / np.sum(np.exp(scores))

    print("\nAttention weights (after softmax):")
    for word, weight in zip(embeddings.keys(), attention):
        print(f"  sat → {word}: {weight:.3f}")

    print("\n'sat' pays most attention to 'cat' (its subject)!")

simple_attention_demo()
```

**Key Questions to Answer:**
> "What does attention allow tokens to do?"
> "Why do we need multiple attention heads?"

---

## Self-Assessment Checklist

After completing Module 1, you should be able to:

**Tokenization:**
- [ ] Explain why we use subword tokenization
- [ ] Calculate approximate token count for any text
- [ ] Understand BPE algorithm at high level
- [ ] Know how tokenization affects costs and context limits

**Embeddings:**
- [ ] Explain what embeddings represent
- [ ] Understand cosine similarity
- [ ] Describe why "similar meanings = similar vectors"
- [ ] Know typical embedding dimensions for different models

**Text Generation:**
- [ ] Explain how LLMs generate text token-by-token
- [ ] Understand temperature, top-k, and top-p parameters
- [ ] Choose appropriate sampling strategy for different tasks
- [ ] Describe the difference between greedy and sampling

**Transformer Architecture:**
- [ ] Explain the role of self-attention
- [ ] Understand why we need position encoding
- [ ] Describe the flow: Input → Embedding → Attention → Output
- [ ] Know what makes transformers different from RNNs

---

## Practice Problems

### Problem 1: Token Counting

**Question:** You have a 10-page document (~5,000 words). How many tokens approximately?

<details>
<summary>Answer</summary>

Rule of thumb: 1 word ≈ 1.3 tokens (English)

5,000 words × 1.3 = ~6,500 tokens

This fits in:
- ✓ GPT-4 (8K context)
- ✗ GPT-3.5 (4K context) - would need chunking

Cost (at $0.03/1K input tokens):
6.5 × $0.03 = $0.195 per request

</details>

---

### Problem 2: Similarity Search

**Question:** You have drug embeddings. How do you find the 3 most similar drugs to "Pembrolizumab"?

<details>
<summary>Answer</summary>

```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 1. Get query embedding
query_embedding = model.encode("Pembrolizumab")

# 2. Calculate similarity to all drugs
similarities = cosine_similarity(
    query_embedding.reshape(1, -1),
    all_drug_embeddings
)

# 3. Get top 3 (excluding itself)
top_3_indices = np.argsort(similarities[0])[-4:-1][::-1]
top_3_drugs = [drugs[i] for i in top_3_indices]
```

This is exactly what happens in vector search!

</details>

---

### Problem 3: Generation Strategy

**Question:** What temperature and sampling strategy would you use for:
a) Generating Python code
b) Writing creative fiction
c) Translating text

<details>
<summary>Answer</summary>

a) **Code generation:**
   - Temperature: 0.2 (low - want deterministic, correct code)
   - Top-p: 0.95
   - Reason: Code has strict syntax, need consistency

b) **Creative fiction:**
   - Temperature: 0.9 (high - want variety and creativity)
   - Top-p: 0.95
   - Reason: Creativity benefits from randomness

c) **Translation:**
   - Temperature: 0.3 (low-medium - want accuracy but some flexibility)
   - Top-p: 0.9
   - Reason: Translation should be accurate but handle idioms

</details>

---

## Common Misconceptions

### ❌ Misconception 1: "More tokens = better understanding"

**Reality:** Token count is just sequence length. Quality of understanding depends on model architecture and training.

---

### ❌ Misconception 2: "Embeddings store word definitions"

**Reality:** Embeddings store patterns of co-occurrence learned from data. They capture how words are used, not dictionary definitions.

---

### ❌ Misconception 3: "Temperature controls intelligence"

**Reality:** Temperature controls randomness in sampling. The model's capabilities are fixed; temperature just affects output diversity.

---

### ❌ Misconception 4: "Attention is like human attention"

**Reality:** Self-attention is a mathematical mechanism for weighting relationships between tokens. It's inspired by but not identical to human attention.

---

## Connect to Your GraphRAG Work

Now that you understand fundamentals, see how they apply to your benchmark:

```
Your GraphRAG Benchmark Used:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Tokenization:
   Drug names → Tokens → Model input

2. Embeddings (384-D):
   "Pembrolizumab" → [0.2, -0.1, 0.5, ..., 0.1]
   
3. Vector Search:
   Find similar drugs using cosine similarity

4. Graph Traversal:
   Follow TREATS relationships

5. Generation (implicit):
   Could generate drug descriptions using LLM
```

**Key Insight from Benchmark:**
```
Unified (Neo4j/Neptune Analytics): Embeddings + Graph = Fast
Two-Layer (Neptune + OpenSearch): Serialize embeddings = Slow

Friction comes from moving embeddings between systems!
```

---

## Next Steps

Once you've mastered Module 1:

✅ **You understand:** How LLMs work internally  
✅ **You can:** Explain tokenization, embeddings, generation  
✅ **You're ready for:** Module 2 (Vector Databases)

**Continue to:** `02_Vector_Databases.md` when ready!

---

## Quick Reference

### Essential Formulas

**Cosine Similarity:**
```
cos(A, B) = (A · B) / (||A|| × ||B||)
Range: -1 (opposite) to 1 (identical)
```

**Softmax (for attention):**
```
softmax(x_i) = exp(x_i) / Σ exp(x_j)
Converts scores → probabilities
```

**Attention Score:**
```
Attention(Q, K, V) = softmax(QK^T / √d_k) × V
Q = Query, K = Key, V = Value
```

### Key Metrics

- **Token count:** ~1.3 tokens per word (English)
- **Embedding dims:** 384 (fast) to 12,288 (rich)
- **Context limit:** 4K-100K tokens (model-dependent)
- **Attention heads:** 8-96 (model-dependent)

---

**Happy Learning! 🚀**

Questions? Review the main module file or run the demo scripts!
