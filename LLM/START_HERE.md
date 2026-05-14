# Start Here: Module 1 Learning Path

## 🎯 Your Goal
Build ground-up understanding of how Large Language Models work internally.

---

## 📚 Three Files to Begin With:

### 1. **Main Content** → `01_LLM_Fundamentals.md`
Complete guide with detailed explanations and ASCII diagrams covering:
- Tokenization (text → numbers)
- Embeddings (meaning → vectors)
- Text generation (probabilities → text)
- Transformer architecture (self-attention mechanism)

**Start here first!**

### 2. **Learning Guide** → `MODULE_1_LEARNING_GUIDE.md`
Step-by-step learning path with:
- Day-by-day study plan
- Hands-on exercises
- Self-assessment checklist
- Practice problems with solutions
- Connection to your GraphRAG benchmark

**Use this as your roadmap!**

### 3. **Interactive Demos** → `examples/`
Python scripts you can run:
- `01_tokenization_demo.py` - See how text becomes tokens
- `02_embedding_basics.py` - Understand vector representations

**Run these to see concepts in action!**

---

## 🚀 Quick Start (30 minutes)

```bash
# 1. Read the overview
cd /workshop/LLM
head -200 01_LLM_Fundamentals.md

# 2. Run tokenization demo
python3 examples/01_tokenization_demo.py

# 3. Run embedding demo
python3 examples/02_embedding_basics.py

# 4. Read the learning guide
cat MODULE_1_LEARNING_GUIDE.md
```

---

## 📖 Recommended Learning Order:

**Week 1: Foundation**
```
Day 1: Read overview + understand the big picture
Day 2: Deep dive into tokenization + run demo
Day 3: Master embeddings + run demo
Day 4: Understand text generation mechanics
Day 5: Study transformer architecture
```

**Week 2: Practice**
```
- Complete hands-on exercises
- Answer practice problems
- Connect concepts to your GraphRAG work
- Self-assessment checklist
```

---

## ✅ Success Criteria

You'll know you've mastered Module 1 when you can:

1. **Explain** how "Hello, world!" becomes numbers a model can process
2. **Calculate** approximate token count for any text
3. **Describe** why similar words have similar embedding vectors
4. **Understand** how attention helps tokens "communicate"
5. **Choose** appropriate temperature settings for different tasks
6. **Connect** these concepts to your GraphRAG benchmark results

---

## 🔗 Connection to Your Work

Your GraphRAG benchmark already used these concepts:

```
Your Benchmark:
  Drug: "Pembrolizumab"
    ↓ Tokenization
  Tokens: [23,Pem, brol, izumab]
    ↓ Embedding
  Vector: [0.2, -0.1, ..., 0.5] (384-D)
    ↓ Vector Search
  Similar drugs found!
    ↓ Graph Traversal
  Diseases treated found!

Module 1 explains HOW each step works internally!
```

---

## 💡 Key Insight from Your Benchmark

```
Unified Architecture (Neo4j/Neptune Analytics):
  Embeddings + Graph in ONE system
  Result: 74-195ms, 0ms friction ✓

Two-Layer (Neptune + OpenSearch):
  Embeddings in OpenSearch → Serialize → Neptune
  Result: ~430ms, 30ms friction ✗

Understanding embeddings explains WHY unified is faster!
```

---

## 📁 File Structure

```
/workshop/LLM/
├── START_HERE.md                    ← You are here
├── README.md                        ← Overview of all modules
├── 01_LLM_Fundamentals.md          ← Main content (read first)
├── MODULE_1_LEARNING_GUIDE.md      ← Your study roadmap
├── examples/
│   ├── 01_tokenization_demo.py     ← Hands-on demo
│   └── 02_embedding_basics.py      ← Hands-on demo
└── diagrams/
    └── (visual aids coming soon)
```

---

## 🎓 What's Next?

After mastering Module 1, you'll be ready for:

**Module 2:** Vector Databases & Similarity Search
- Why vector databases exist
- HNSW algorithm (used in your benchmark!)
- Scaling to billions of vectors

**Module 5:** RAG (Retrieval-Augmented Generation)
- Complete RAG pipeline
- Unified vs. Two-layer architecture (your benchmark!)
- Production implementation

---

## 🤔 Questions While Learning?

**Stuck on tokenization?**
→ Run `01_tokenization_demo.py` and experiment with different texts

**Confused about embeddings?**
→ Run `02_embedding_basics.py` and visualize the vectors

**Need more examples?**
→ Check MODULE_1_LEARNING_GUIDE.md for practice problems

**Want to connect to real work?**
→ See how your GraphRAG benchmark used these concepts

---

## ⚡ Quick Reference

**Essential Concepts:**
- **Token:** Subword unit (1 token ≈ 4 chars in English)
- **Embedding:** Vector representation (384-12,288 dimensions)
- **Attention:** Mechanism for tokens to "talk" to each other
- **Temperature:** Controls randomness (0 = deterministic, 2 = random)

**Your Benchmark Used:**
- 384-dimensional embeddings
- HNSW vector search
- Cosine similarity
- Graph + Vector unified architecture

---

**Ready to start? Open `01_LLM_Fundamentals.md`!**

```bash
cat 01_LLM_Fundamentals.md | less
```

Happy learning! 🚀
