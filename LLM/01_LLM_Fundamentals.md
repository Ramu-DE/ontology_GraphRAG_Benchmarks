# Module 1: Fundamentals of the LLM Landscape

## Table of Contents
1. [Visual Perception and Natural Language Understanding](#visual-perception-and-natural-language-understanding)
2. [Tokenization](#tokenization)
3. [Embeddings](#embeddings)
4. [How LLMs Generate Text](#how-llms-generate-text)
5. [End-to-End Architecture](#end-to-end-architecture)
6. [The Transformer Architecture](#the-transformer-architecture)

---

## Visual Perception and Natural Language Understanding

### How Humans Process Language

```
Human Language Processing:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Input: "The cat sat on the mat"                          │
│                                                             │
│  Brain Processing:                                         │
│  1. Sound waves → Phonemes                                 │
│  2. Phonemes → Words                                       │
│  3. Words → Syntax tree                                    │
│  4. Syntax + Context → Meaning                            │
│  5. Meaning + World knowledge → Understanding             │
│                                                             │
│  All in ~200 milliseconds!                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Insight:** Humans use:
- **Context:** Previous conversation, world knowledge
- **Inference:** Fill in missing information
- **Ambiguity resolution:** "Bat" = animal or sports equipment?
- **Pragmatics:** Understanding intent beyond literal meaning

### How Machines Process Language

```
Machine Language Processing (Traditional NLP):
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Input: "The cat sat on the mat"                          │
│                                                             │
│  Traditional NLP Pipeline:                                 │
│  1. Tokenization:      ["The", "cat", "sat", "on", ...]   │
│  2. POS Tagging:       [DET, NOUN, VERB, PREP, ...]       │
│  3. Parsing:           Syntax tree                         │
│  4. Named Entities:    Identify cats, locations, etc.     │
│  5. Rule-based logic:  Hand-crafted rules                 │
│                                                             │
│  Problem: Brittle, doesn't generalize!                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**vs. Modern LLM Approach:**

```
LLM Processing (Neural, End-to-End):
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Input: "The cat sat on the mat"                          │
│                                                             │
│  LLM Processing:                                           │
│  1. Tokenization:      [464, 2479, 7731, 319, 262, ...]   │
│  2. Embeddings:        [[0.2, -0.1, ...], [0.5, ...]]    │
│  3. Transformer:       Self-attention + feedforward       │
│  4. Probability dist:  P(next_token | context)           │
│  5. Sample/Decode:     Generate next token                │
│                                                             │
│  Learned patterns from billions of examples!               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Difference:** 
- Traditional NLP: Rules + Linguistics + Hand-crafted features
- LLMs: Pattern learning from massive data through self-supervision

---

## Tokenization

### What is Tokenization?

Tokenization converts text into numerical units that a model can process.

```
Text → Tokens → Token IDs → Model Input

Example:
"Hello, world!" 
    ↓
["Hello", ",", " world", "!"]
    ↓
[15496, 11, 995, 0]
```

### Why Not Character-Level?

```
Character-Level Problems:
┌──────────────────────────────────────────┐
│ Text: "understanding"                    │
│ Chars: [u,n,d,e,r,s,t,a,n,d,i,n,g]     │
│ Length: 13 tokens                        │
│                                          │
│ Problems:                                │
│ • Very long sequences                   │
│ • Weak semantic units                   │
│ • Expensive to process                  │
└──────────────────────────────────────────┘

Token-Level (Subword):
┌──────────────────────────────────────────┐
│ Text: "understanding"                    │
│ Tokens: ["under", "stand", "ing"]      │
│ Length: 3 tokens                         │
│                                          │
│ Benefits:                                │
│ • Shorter sequences                     │
│ • Better semantic units                 │
│ • Handles rare words                    │
└──────────────────────────────────────────┘
```

### Common Tokenization Algorithms

#### 1. Byte Pair Encoding (BPE)

```
BPE Algorithm:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ Start with characters: [l, o, w, e, r]                     │
│                                                             │
│ Iteration 1: Find most frequent pair → "lo"               │
│   Merge: [lo, w, e, r]                                    │
│                                                             │
│ Iteration 2: Find most frequent pair → "er"               │
│   Merge: [lo, w, er]                                      │
│                                                             │
│ Iteration 3: Find most frequent pair → "low"              │
│   Merge: [low, er]                                        │
│                                                             │
│ Result: Build vocabulary of common subwords               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Example:**
```python
# Input text
text = "lower lowest"

# BPE learns:
vocabulary = {
    "l": 0,
    "o": 1,
    "w": 2,
    "e": 3,
    "r": 4,
    "s": 5,
    "t": 6,
    "lo": 7,      # Merged
    "low": 8,     # Merged
    "er": 9,      # Merged
    "est": 10,    # Merged
    "lower": 11,  # Merged
    "lowest": 12  # Merged
}

# Tokenization
"lower" → [11] or [8, 9]  # Flexible!
"lowest" → [12] or [8, 10]
```

#### 2. WordPiece (BERT)

```
WordPiece:
┌─────────────────────────────────────────────────────────────┐
│ Similar to BPE but uses likelihood instead of frequency    │
│                                                             │
│ Example: "unhappiness"                                      │
│   → ["un", "##happiness"]                                  │
│   → ["un", "##happi", "##ness"]                           │
│                                                             │
│ ## prefix indicates subword continuation                   │
└─────────────────────────────────────────────────────────────┘
```

#### 3. SentencePiece (T5, LLaMA)

```
SentencePiece:
┌─────────────────────────────────────────────────────────────┐
│ Treats text as raw bytes (no pre-tokenization)            │
│                                                             │
│ Benefits:                                                   │
│ • Language agnostic                                        │
│ • No whitespace assumptions                                │
│ • Handles any Unicode                                      │
│                                                             │
│ Example: "Hello world"                                      │
│   → ["▁Hello", "▁world"]  (▁ = space marker)             │
└─────────────────────────────────────────────────────────────┘
```

### Tokenization Impact on LLMs

```
Token Count = Cost & Context
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ Input: "The quick brown fox jumps"                         │
│                                                             │
│ GPT-3/4 Tokenization: [464, 2068, 7586, 21831, 35308]    │
│ Count: 5 tokens                                            │
│                                                             │
│ Why it matters:                                            │
│ • API cost = tokens × price_per_token                     │
│ • Context limit = max_tokens (e.g., 8192)                │
│ • Latency = tokens × time_per_token                       │
│                                                             │
│ Rule of thumb: 1 token ≈ 4 characters (English)          │
│                1 token ≈ ¾ word (English)                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Critical Insights:**
```
Different Languages = Different Token Counts!

English: "Hello, how are you?" → 5 tokens
Chinese: "你好，你好吗？" → 8 tokens (more expensive!)
Code:    "def hello():" → 4 tokens

Special Characters:
"😀" → 1-3 tokens (depends on tokenizer)
"​​​" (zero-width spaces) → Silent tokens!
```

---

## Embeddings

### What Are Embeddings?

Embeddings convert discrete tokens into continuous vector representations.

```
Embedding Transform:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ Token ID (discrete) → Embedding Vector (continuous)        │
│                                                             │
│ Example:                                                    │
│ Token: "cat" (ID: 2479)                                    │
│   ↓                                                         │
│ Embedding: [0.2, -0.5, 0.8, ..., 0.1]  (768 dimensions)  │
│                                                             │
│ Token: "dog" (ID: 3290)                                    │
│   ↓                                                         │
│ Embedding: [0.3, -0.4, 0.7, ..., 0.2]  (768 dimensions)  │
│                                                             │
│ Similar meanings → Similar vectors!                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Embedding as Geometry

```
Semantic Similarity in Vector Space:
┌─────────────────────────────────────────────────────────────┐
│                    Embedding Space (simplified to 2D)       │
│                                                             │
│        Animal                                               │
│          │                                                  │
│    ┌─────┼─────┐                                          │
│    │     │     │                                          │
│   dog   cat  mouse                                         │
│                                                             │
│                                                             │
│        Fruit                                                │
│          │                                                  │
│    ┌─────┼─────┐                                          │
│    │     │     │                                          │
│  apple orange banana                                       │
│                                                             │
│ Distance = Similarity                                       │
│ • cos(dog, cat) = 0.95 (very similar)                     │
│ • cos(dog, apple) = 0.02 (unrelated)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Embedding Dimensions

```
Typical Embedding Sizes:
┌────────────────────┬───────────────┬─────────────────────┐
│ Model              │ Dimensions    │ Use Case            │
├────────────────────┼───────────────┼─────────────────────┤
│ Word2Vec           │ 100-300       │ Simple word vectors │
│ BERT-base          │ 768           │ Contextual embed    │
│ BERT-large         │ 1024          │ Better quality      │
│ GPT-3              │ 12,288        │ Very rich context   │
│ GPT-4              │ ~12,288       │ State-of-the-art    │
│ all-MiniLM-L6-v2   │ 384           │ Fast retrieval      │
└────────────────────┴───────────────┴─────────────────────┘

Trade-off: More dimensions = richer representation but slower
```

### How Embeddings Are Learned

```
Embedding Learning:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ Goal: Predict next word from context                       │
│                                                             │
│ Input:  "The cat sat on the ___"                          │
│ Target: "mat"                                              │
│                                                             │
│ Process:                                                    │
│ 1. Random initialize embeddings                           │
│ 2. Forward pass: Use embeddings to predict                │
│ 3. Compute loss: How wrong was prediction?                │
│ 4. Backprop: Update embeddings to reduce error            │
│ 5. Repeat billions of times                               │
│                                                             │
│ Result: Embeddings capture semantic relationships!        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Famous Embedding Properties

```
Vector Arithmetic (Word2Vec):
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ king - man + woman ≈ queen                                 │
│                                                             │
│ paris - france + germany ≈ berlin                          │
│                                                             │
│ walking - walk + swim ≈ swimming                           │
│                                                             │
│ Why? Embeddings encode semantic relationships as vectors!  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## How LLMs Generate Text

### The Core Mechanism

```
Text Generation Process:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ Input: "The cat sat on"                                    │
│                                                             │
│ Step 1: Model outputs probability distribution             │
│   P("the" | context) = 0.60                                │
│   P("a" | context)   = 0.25                                │
│   P("my" | context)  = 0.10                                │
│   P("his" | context) = 0.03                                │
│   P("mat" | context) = 0.01                                │
│   ... (50,000 more tokens)                                 │
│                                                             │
│ Step 2: Sample from distribution                           │
│   Selected: "the"                                          │
│                                                             │
│ Step 3: Append to input, repeat                           │
│   New input: "The cat sat on the"                         │
│                                                             │
│ Continue until:                                            │
│ • Max tokens reached                                       │
│ • [EOS] token generated                                    │
│ • Stop sequence encountered                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Sampling Strategies

#### 1. Greedy Decoding

```
Greedy: Always pick highest probability
┌─────────────────────────────────────────────────────────────┐
│ Input: "The weather is"                                     │
│                                                             │
│ Probabilities:                                              │
│   "nice" → 0.40 ← Pick this!                              │
│   "sunny" → 0.30                                           │
│   "great" → 0.20                                           │
│                                                             │
│ Result: Deterministic but boring                           │
│ "The weather is nice and the sun is shining..."           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 2. Temperature Sampling

```
Temperature: Control randomness
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ Original probabilities:                                     │
│   P = [0.40, 0.30, 0.20, 0.10]                            │
│                                                             │
│ Temperature = 0.1 (More deterministic):                    │
│   P = [0.95, 0.03, 0.01, 0.01]                            │
│                                                             │
│ Temperature = 1.0 (Unchanged):                             │
│   P = [0.40, 0.30, 0.20, 0.10]                            │
│                                                             │
│ Temperature = 2.0 (More random):                           │
│   P = [0.28, 0.25, 0.24, 0.23]                            │
│                                                             │
│ Formula: P_i = exp(logit_i / T) / Σ exp(logit_j / T)      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 3. Top-k Sampling

```
Top-k: Only consider top k tokens
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ All probabilities (50,000 tokens):                         │
│   "nice"    → 0.40                                         │
│   "sunny"   → 0.30                                         │
│   "great"   → 0.20                                         │
│   "lovely"  → 0.05                                         │
│   "purple"  → 0.001  ← Nonsense!                          │
│   ...                                                       │
│                                                             │
│ Top-k = 3: Only consider [nice, sunny, great]            │
│   Renormalize: [0.44, 0.33, 0.23]                        │
│   Sample from this                                         │
│                                                             │
│ Prevents sampling very unlikely (nonsense) tokens          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 4. Top-p (Nucleus) Sampling

```
Top-p: Sample from smallest set with cumulative probability p
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ Probabilities (sorted):                                     │
│   "nice"    → 0.40  | Cumulative: 0.40                    │
│   "sunny"   → 0.30  | Cumulative: 0.70                    │
│   "great"   → 0.20  | Cumulative: 0.90 ← Stop here (p=0.9)│
│   "lovely"  → 0.05  | Cumulative: 0.95                    │
│   ...                                                       │
│                                                             │
│ Nucleus = {nice, sunny, great}                             │
│ Sample only from these                                      │
│                                                             │
│ Adaptive: Keeps more tokens when distribution is flat      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Generation Parameters Comparison

```
┌─────────────┬──────────────┬────────────────┬─────────────┐
│ Parameter   │ Low Value    │ High Value     │ Use Case    │
├─────────────┼──────────────┼────────────────┼─────────────┤
│ Temperature │ Deterministic│ Random         │ Code: 0.2   │
│  (0.0-2.0)  │ Repetitive   │ Creative       │ Story: 0.8  │
├─────────────┼──────────────┼────────────────┼─────────────┤
│ Top-p       │ Conservative │ Diverse        │ Default 0.9 │
│  (0.0-1.0)  │              │                │             │
├─────────────┼──────────────┼────────────────┼─────────────┤
│ Top-k       │ Limited      │ More options   │ 40-50       │
│  (1-100)    │              │                │             │
└─────────────┴──────────────┴────────────────┴─────────────┘
```

---

## End-to-End Architecture

### The Complete Pipeline

```
LLM End-to-End Processing:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  INPUT TEXT: "Explain quantum computing"                   │
│       ↓                                                     │
│  ┌─────────────────────────────────────────────┐          │
│  │ 1. TOKENIZATION                             │          │
│  │    ["Explain", " quantum", " computing"]    │          │
│  │    → [5549, 14903, 14492]                  │          │
│  └─────────────────────────────────────────────┘          │
│       ↓                                                     │
│  ┌─────────────────────────────────────────────┐          │
│  │ 2. EMBEDDING LOOKUP                         │          │
│  │    5549 → [0.2, -0.1, 0.5, ...]  (768-d)  │          │
│  │    14903 → [0.1, 0.3, -0.2, ...] (768-d)  │          │
│  │    14492 → [-0.1, 0.2, 0.4, ...] (768-d)  │          │
│  └─────────────────────────────────────────────┘          │
│       ↓                                                     │
│  ┌─────────────────────────────────────────────┐          │
│  │ 3. POSITIONAL ENCODING                      │          │
│  │    Add position information to each token    │          │
│  │    embedding[0] += pos_encoding(0)          │          │
│  │    embedding[1] += pos_encoding(1)          │          │
│  └─────────────────────────────────────────────┘          │
│       ↓                                                     │
│  ┌─────────────────────────────────────────────┐          │
│  │ 4. TRANSFORMER LAYERS (x N)                 │          │
│  │    • Self-Attention (understand context)    │          │
│  │    • Feed-Forward (transform features)      │          │
│  │    • Layer Normalization                    │          │
│  │    • Residual Connections                   │          │
│  └─────────────────────────────────────────────┘          │
│       ↓                                                     │
│  ┌─────────────────────────────────────────────┐          │
│  │ 5. OUTPUT PROJECTION                        │          │
│  │    768-d → 50,000-d (vocabulary size)      │          │
│  │    Logits: [2.1, -0.5, 3.4, ..., 0.2]     │          │
│  └─────────────────────────────────────────────┘          │
│       ↓                                                     │
│  ┌─────────────────────────────────────────────┐          │
│  │ 6. SOFTMAX                                  │          │
│  │    Convert logits → probabilities           │          │
│  │    P = softmax(logits / temperature)        │          │
│  └─────────────────────────────────────────────┘          │
│       ↓                                                     │
│  ┌─────────────────────────────────────────────┐          │
│  │ 7. SAMPLING                                 │          │
│  │    Select next token from distribution      │          │
│  │    Next token: "Quantum" (ID: 29565)       │          │
│  └─────────────────────────────────────────────┘          │
│       ↓                                                     │
│  OUTPUT TEXT: "Quantum computing is..."                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## The Transformer Architecture

### High-Level Overview

```
Transformer Block:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    INPUT EMBEDDINGS                         │
│                           ↓                                 │
│              ┌────────────────────────┐                    │
│              │  Position Encoding      │                    │
│              └────────────────────────┘                    │
│                           ↓                                 │
│       ╔══════════════════════════════════════╗            │
│       ║   TRANSFORMER LAYER 1                ║            │
│       ║  ┌────────────────────────────────┐ ║            │
│       ║  │ Multi-Head Self-Attention      │ ║            │
│       ║  └────────────────────────────────┘ ║            │
│       ║              ↓                       ║            │
│       ║  ┌────────────────────────────────┐ ║            │
│       ║  │ Add & Norm (Layer Norm)        │ ║            │
│       ║  └────────────────────────────────┘ ║            │
│       ║              ↓                       ║            │
│       ║  ┌────────────────────────────────┐ ║            │
│       ║  │ Feed Forward Network           │ ║            │
│       ║  └────────────────────────────────┘ ║            │
│       ║              ↓                       ║            │
│       ║  ┌────────────────────────────────┐ ║            │
│       ║  │ Add & Norm (Layer Norm)        │ ║            │
│       ║  └────────────────────────────────┘ ║            │
│       ╚══════════════════════════════════════╝            │
│                           ↓                                 │
│       ╔══════════════════════════════════════╗            │
│       ║   TRANSFORMER LAYER 2                ║            │
│       ║          (same structure)             ║            │
│       ╚══════════════════════════════════════╝            │
│                           ↓                                 │
│                         ...                                 │
│                           ↓                                 │
│       ╔══════════════════════════════════════╗            │
│       ║   TRANSFORMER LAYER N                ║            │
│       ║          (same structure)             ║            │
│       ╚══════════════════════════════════════╝            │
│                           ↓                                 │
│              ┌────────────────────────┐                    │
│              │  Output Projection      │                    │
│              │  (Linear + Softmax)     │                    │
│              └────────────────────────┘                    │
│                           ↓                                 │
│                  NEXT TOKEN PROBABILITIES                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Typical sizes:
- GPT-3: 96 layers
- GPT-4: ~120 layers (estimated)
- LLaMA 2 70B: 80 layers
```

### Self-Attention Mechanism (The Magic!)

```
Self-Attention: How tokens "talk" to each other
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ Input sequence: ["The", "cat", "sat"]                      │
│                                                             │
│ For each token, compute:                                   │
│ 1. Query (Q): What am I looking for?                      │
│ 2. Key (K):   What do I offer?                            │
│ 3. Value (V): What information do I have?                 │
│                                                             │
│ Example: Token "sat"                                       │
│   Q: "I'm a verb, looking for my subject"                 │
│   K: "I am a verb"                                         │
│   V: [actual embedding vector]                            │
│                                                             │
│ Attention Score = Q · K^T                                  │
│                                                             │
│ "sat" paying attention to:                                 │
│   - "The"  : low score (not relevant)                     │
│   - "cat"  : HIGH score (subject!)                        │
│   - "sat"  : medium (self-attention)                      │
│                                                             │
│ Output = weighted sum of Values based on attention scores  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Detailed Attention Computation:**

```
Mathematical Flow:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ Input: X = [x₁, x₂, x₃]  (sequence of 3 token embeddings) │
│                                                             │
│ Step 1: Linear Projections                                 │
│   Q = X · W_Q    (Query matrix)                           │
│   K = X · W_K    (Key matrix)                             │
│   V = X · W_V    (Value matrix)                           │
│                                                             │
│ Step 2: Compute Attention Scores                           │
│   Scores = Q · K^T / √d_k                                 │
│                                                             │
│   Example (3x3 attention matrix):                          │
│        The    cat    sat                                   │
│   The  [0.3   0.1   0.1]                                  │
│   cat  [0.2   0.6   0.1]                                  │
│   sat  [0.1   0.8   0.2]  ← "sat" attends to "cat"       │
│                                                             │
│ Step 3: Softmax (make it probabilities)                    │
│   Attention = softmax(Scores)                              │
│                                                             │
│ Step 4: Weighted Sum                                       │
│   Output = Attention · V                                   │
│                                                             │
│ Result: Each token now has context from relevant tokens!   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Head Attention

```
Why Multiple Heads?
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ Single attention = Single perspective                       │
│ Multi-head = Multiple perspectives simultaneously          │
│                                                             │
│ Example: "The cat sat on the mat"                         │
│                                                             │
│ Head 1: Syntax (subject-verb relationships)                │
│   "sat" → "cat" (who sat?)                                │
│                                                             │
│ Head 2: Semantics (meaning relationships)                  │
│   "cat" → "mat" (cat and mat are related)                 │
│                                                             │
│ Head 3: Position (nearby words)                            │
│   "cat" → "The" (adjacent)                                │
│                                                             │
│ Head 4-8: Other patterns learned from data                 │
│                                                             │
│ Concat all heads → Linear projection → Output             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Feed-Forward Network

```
FFN: Transform features independently for each position
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ After attention, each token embedding goes through:        │
│                                                             │
│   FFN(x) = max(0, x·W₁ + b₁)·W₂ + b₂                     │
│                                                             │
│ Structure:                                                  │
│   Input:  d_model (e.g., 768)                             │
│      ↓                                                      │
│   Dense layer: d_model → d_ff (e.g., 3072)               │
│      ↓                                                      │
│   ReLU activation                                          │
│      ↓                                                      │
│   Dense layer: d_ff → d_model (e.g., 768)                │
│                                                             │
│ Purpose: Add non-linearity and processing capacity         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Layer Normalization & Residual Connections

```
Stabilizing Training:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│ Residual Connection (Skip Connection):                     │
│                                                             │
│     Input (x)                                              │
│       │                                                     │
│       ├──────────────────┐                                │
│       │                  │                                 │
│       ↓                  │                                 │
│   Attention              │                                 │
│       │                  │                                 │
│       ↓                  │                                 │
│    Add ←─────────────────┘                                │
│       │                                                     │
│       ↓                                                     │
│  Layer Norm                                                │
│       │                                                     │
│       ↓                                                     │
│     Output                                                 │
│                                                             │
│ Benefits:                                                   │
│ • Gradient flow: Helps training deep networks             │
│ • Stability: Prevents vanishing gradients                 │
│                                                             │
│ Layer Norm: Normalize across features for each token      │
│   mean = 0, variance = 1                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Model Sizes and Parameters

```
LLM Size Comparison:
┌──────────────┬──────────────┬─────────┬──────────────────┐
│ Model        │ Parameters   │ Layers  │ Hidden Size      │
├──────────────┼──────────────┼─────────┼──────────────────┤
│ GPT-2 Small  │ 117M         │ 12      │ 768              │
│ GPT-2 Large  │ 1.5B         │ 36      │ 1600             │
│ GPT-3        │ 175B         │ 96      │ 12,288           │
│ GPT-4        │ ~1.76T       │ ~120    │ ~18,000 (est.)   │
│ LLaMA 2 7B   │ 7B           │ 32      │ 4096             │
│ LLaMA 2 70B  │ 70B          │ 80      │ 8192             │
│ Claude 3     │ Unknown      │ Unknown │ Unknown          │
└──────────────┴──────────────┴─────────┴──────────────────┘

Parameters = Size of model weights stored in memory
More parameters ≠ always better (diminishing returns)
```

---

## Key Takeaways

✅ **Tokenization:** Text → Subword tokens → IDs  
✅ **Embeddings:** IDs → Dense vectors capturing meaning  
✅ **Attention:** Tokens "communicate" to understand context  
✅ **Transformers:** Stack of attention + FFN layers  
✅ **Generation:** Predict next token, sample, repeat  

**Next Module:** Vector Databases and Similarity Search - Why embeddings matter for retrieval!

---

## Practice Exercises

1. **Tokenization:** Try different texts with GPT tokenizer: https://platform.openai.com/tokenizer
2. **Embeddings:** Visualize word embeddings: https://projector.tensorflow.org/
3. **Attention:** Play with attention visualization: https://github.com/jessevig/bertviz
4. **Generation:** Experiment with temperature and top-p in ChatGPT settings

---

**Continue to:** `02_Vector_Databases.md`
