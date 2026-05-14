# LLM Fundamentals Learning Path

## Complete Guide to Understanding Large Language Models

This curriculum provides a comprehensive, ground-up understanding of LLM internals, from basic concepts to production systems.

---

## 📚 Learning Modules

### Module 1: Fundamentals of the LLM Landscape
**File:** `01_LLM_Fundamentals.md`

**Topics Covered:**
- Visual perception and natural language understanding
- How humans process language vs. how machines do it
- Tokenization: Breaking text into processable units
- Embeddings: Representing meaning as vectors
- Text generation: From probability distributions to coherent output
- End-to-end architecture: Connecting every layer

**Key Concepts:**
- Token → Embedding → Attention → Output
- Transformer architecture deep dive
- Self-attention mechanism
- Position encoding
- Layer normalization

---

### Module 2: Vector Databases and Similarity Search
**File:** `02_Vector_Databases.md`

**Topics Covered:**
- Why vector databases exist
- Embeddings as geometric meaning representation
- Similarity metrics (cosine, euclidean, dot product)
- Approximate Nearest Neighbor (ANN) algorithms
- HNSW (Hierarchical Navigable Small World) graphs
- Scaling similarity search to billions of vectors

**Key Concepts:**
- Semantic similarity through vector distance
- Indexing strategies for fast retrieval
- Trade-offs: accuracy vs. speed vs. memory
- Production considerations

---

### Module 3: Prompt Engineering Best Practices
**File:** `03_Prompt_Engineering.md`

**Topics Covered:**
- Prompt structure anatomy
- Zero-shot, few-shot, and chain-of-thought prompting
- System prompts vs. user prompts
- Temperature, top-p, and other sampling parameters
- Common failure modes and how to avoid them
- Grounding techniques for consistent outputs

**Key Concepts:**
- Prompt as program specification
- Context window management
- Instruction following vs. completion
- Debugging prompt failures

---

### Module 4: Building Custom LLM Applications
**File:** `04_Custom_LLM_Applications.md`

**Topics Covered:**
- **Path 1:** Training from scratch
  - When to do it (almost never)
  - Data requirements (trillions of tokens)
  - Compute costs ($millions)
  - Pre-training objectives

- **Path 2:** Fine-tuning foundation models
  - When to fine-tune
  - Dataset preparation
  - LoRA and parameter-efficient methods
  - Evaluation strategies

- **Path 3:** In-context learning (ICL)
  - Retrieval-augmented generation
  - Prompt engineering
  - Function calling
  - Agent frameworks

**Key Concepts:**
- Cost-benefit analysis of each approach
- When to use which path
- Practical implementation examples

---

### Module 5: Retrieval-Augmented Generation (RAG)
**File:** `05_RAG_Deep_Dive.md`

**Topics Covered:**
- RAG pipeline architecture
- Chunking strategies
- Embedding generation
- Retrieval mechanisms
- Context injection
- Generation with retrieved context
- Where RAG breaks down
- Production-ready implementation
- Advanced: GraphRAG architecture

**Key Concepts:**
- Naive RAG vs. Advanced RAG
- Chunk size optimization
- Retrieval relevance scoring
- Context window management
- Evaluation metrics

---

## 🎯 Learning Path Recommendations

### Beginner Track (Week 1-2)
1. Start with Module 1: LLM Fundamentals
2. Move to Module 2: Vector Databases
3. Practice with Module 3: Prompt Engineering

### Intermediate Track (Week 3-4)
4. Study Module 4: Custom LLM Applications
5. Deep dive into Module 5: RAG

### Advanced Track (Week 5+)
- Connect to real benchmark data (GraphRAG)
- Implement production RAG system
- Optimize for performance and cost

---

## 🛠️ Practical Components

Each module includes:
- ✅ Detailed explanations
- ✅ ASCII diagrams
- ✅ Code examples
- ✅ Real-world use cases
- ✅ Common pitfalls
- ✅ Best practices
- ✅ Hands-on exercises

---

## 📊 Connection to Real Work

This curriculum connects directly to the GraphRAG benchmark we just completed:

**Module 2** explains why we used vector databases (Neo4j, Neptune Analytics, OpenSearch)  
**Module 5** explains the unified vs. two-layer architecture we benchmarked  
**Real data:** 10 drugs, 10 diseases, 384-dimensional embeddings  
**Real results:** Unified architecture (74-195ms) vs. Two-layer (~430ms)

---

## 📁 Module Files

All detailed content is in individual markdown files:

```
/workshop/LLM/
├── README.md (this file)
├── 01_LLM_Fundamentals.md
├── 02_Vector_Databases.md
├── 03_Prompt_Engineering.md
├── 04_Custom_LLM_Applications.md
├── 05_RAG_Deep_Dive.md
├── diagrams/
│   ├── transformer_architecture.txt
│   ├── attention_mechanism.txt
│   ├── rag_pipeline.txt
│   └── vector_similarity.txt
└── examples/
    ├── tokenization_demo.py
    ├── embedding_visualization.py
    ├── prompt_templates.py
    └── rag_implementation.py
```

---

## 🚀 Getting Started

Start with:
```bash
cd /workshop/LLM
cat 01_LLM_Fundamentals.md
```

Each module builds on the previous one, creating a complete understanding of LLM systems from first principles to production deployment.

---

**Next:** Begin with Module 1 to understand the foundational concepts that power all LLM applications.
