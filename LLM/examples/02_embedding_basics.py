#!/usr/bin/env python3
"""
Embedding Basics - How meaning becomes geometry

This demonstrates:
- What embeddings are
- How similar meanings have similar vectors
- Vector arithmetic (king - man + woman = queen)
"""

import numpy as np
from typing import List, Tuple

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)

def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate Euclidean distance between two vectors"""
    return np.linalg.norm(vec1 - vec2)

# Demo
if __name__ == "__main__":
    print("="*60)
    print("EMBEDDING BASICS DEMO")
    print("="*60)

    # Simplified 3D embeddings for demonstration
    # In reality: 384, 768, or even 12,288 dimensions!

    print("\n1. WHAT ARE EMBEDDINGS?")
    print("─"*60)

    embeddings = {
        # Animals (similar to each other)
        "cat":   np.array([0.8, 0.9, 0.1]),
        "dog":   np.array([0.85, 0.88, 0.15]),
        "mouse": np.array([0.75, 0.82, 0.2]),

        # Fruits (similar to each other)
        "apple":  np.array([0.1, 0.2, 0.9]),
        "orange": np.array([0.15, 0.25, 0.88]),
        "banana": np.array([0.2, 0.18, 0.85]),

        # Actions
        "run":   np.array([0.5, 0.1, 0.5]),
        "walk":  np.array([0.52, 0.15, 0.48]),
        "jump":  np.array([0.48, 0.08, 0.53]),
    }

    print("Word embeddings (3D for visualization):")
    print(f"{'Word':<10} | {'Vector':<30}")
    print("─"*45)
    for word, vec in embeddings.items():
        print(f"{word:<10} | {vec}")

    # 2. Similarity between words
    print("\n2. SEMANTIC SIMILARITY = GEOMETRIC PROXIMITY")
    print("─"*60)

    pairs = [
        ("cat", "dog"),      # Both animals - should be similar
        ("cat", "apple"),    # Different categories - should be different
        ("apple", "orange"), # Both fruits - should be similar
        ("run", "walk"),     # Both actions - should be similar
        ("cat", "run"),      # Different types - should be different
    ]

    print(f"{'Word 1':<10} | {'Word 2':<10} | Cosine Similarity | Interpretation")
    print("─"*75)

    for word1, word2 in pairs:
        vec1 = embeddings[word1]
        vec2 = embeddings[word2]
        similarity = cosine_similarity(vec1, vec2)

        if similarity > 0.9:
            interpretation = "Very similar"
        elif similarity > 0.7:
            interpretation = "Somewhat similar"
        elif similarity > 0.4:
            interpretation = "Slightly related"
        else:
            interpretation = "Different"

        print(f"{word1:<10} | {word2:<10} | {similarity:>17.3f} | {interpretation}")

    # 3. Vector arithmetic
    print("\n3. VECTOR ARITHMETIC (The Magic!)")
    print("─"*60)

    # Simplified example: animal relationships
    print("\nExample: cat - mouse + fruit = ?")
    print("(Moving from small animal to fruit category)")

    result = embeddings["cat"] - embeddings["mouse"] + embeddings["apple"]

    print(f"\nCalculation:")
    print(f"  cat:   {embeddings['cat']}")
    print(f"  mouse: {embeddings['mouse']}")
    print(f"  apple: {embeddings['apple']}")
    print(f"  ────────────────────────────────")
    print(f"  result: {result}")

    # Find closest word to result
    print(f"\nFinding closest word to result:")
    similarities = []
    for word, vec in embeddings.items():
        if word not in ["cat", "mouse", "apple"]:
            sim = cosine_similarity(result, vec)
            similarities.append((word, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)

    print(f"{'Word':<10} | Similarity to Result")
    print("─"*35)
    for word, sim in similarities[:5]:
        print(f"{word:<10} | {sim:.3f}")

    # 4. Visualizing embedding space
    print("\n4. EMBEDDING SPACE VISUALIZATION")
    print("─"*60)

    print("\nImagine a 3D space where similar words cluster together:")
    print("""
        Z axis (Fruit dimension)
        ↑
        │     • banana
        │   • apple
        │  • orange
        │
        │
        └─────────────────→ X axis (Animal dimension)
       /         • cat
      /        • dog
     /       • mouse
    ↓
    Y axis (Action dimension)
        • run
        • walk
        • jump
    """)

    print("\nKey insights:")
    print("  • Similar meanings = nearby in space")
    print("  • Directions encode relationships")
    print("  • Can perform algebraic operations")

    # 5. Real-world embeddings
    print("\n5. REAL-WORLD EMBEDDING SIZES")
    print("─"*60)

    models = [
        ("Word2Vec", 300),
        ("BERT-base", 768),
        ("BERT-large", 1024),
        ("GPT-3", 12288),
        ("all-MiniLM-L6-v2", 384),
    ]

    print(f"{'Model':<20} | Dimensions | Storage per word")
    print("─"*60)
    for model, dims in models:
        storage = dims * 4  # 4 bytes per float32
        print(f"{model:<20} | {dims:>10} | {storage:>6} bytes")

    # 6. Why embeddings matter for RAG
    print("\n6. WHY EMBEDDINGS MATTER FOR RAG")
    print("─"*60)

    print("""
RAG (Retrieval-Augmented Generation) workflow:

1. User query: "What treats cancer?"
   ↓
2. Convert to embedding: [0.2, -0.1, 0.5, ...]
   ↓
3. Search database for similar embeddings
   ↓
4. Find: "Pembrolizumab treats cancer" (high similarity!)
   ↓
5. Feed retrieved context to LLM for generation

Embeddings enable semantic search - not just keyword matching!
    """)

    print("\n" + "="*60)
    print("KEY TAKEAWAYS:")
    print("="*60)
    print("✓ Embeddings convert words → vectors")
    print("✓ Similar meanings = similar vectors (cosine similarity)")
    print("✓ Vector arithmetic encodes relationships")
    print("✓ Higher dimensions = richer representations")
    print("✓ Embeddings power semantic search in RAG systems")
    print("="*60)

    # Bonus: Connection to your benchmark
    print("\n" + "="*60)
    print("CONNECTION TO YOUR GRAPHRAG BENCHMARK:")
    print("="*60)
    print("""
In your benchmark, you used 384-dimensional embeddings:
  • Each drug → 384-D vector
  • Vector search finds similar drugs
  • Neo4j + Neptune Analytics: Native vector search (fast!)
  • OpenSearch: Separate vector DB (two-layer friction)

This is why unified architecture (like Neo4j) is faster:
  Embeddings + Graph in ONE database = No serialization overhead!
    """)
