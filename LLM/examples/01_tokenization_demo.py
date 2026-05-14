#!/usr/bin/env python3
"""
Tokenization Demo - Understanding how text becomes numbers

This demonstrates the first step in LLM processing:
Text → Tokens → Token IDs
"""

def simple_whitespace_tokenizer(text):
    """Most basic tokenizer - split on whitespace"""
    return text.split()

def simple_character_tokenizer(text):
    """Character-level tokenization"""
    return list(text)

def simulate_bpe_tokenizer(text):
    """Simulates Byte Pair Encoding behavior"""
    # This is simplified - real BPE learns from corpus

    # Common subwords learned from data
    vocabulary = {
        "un": "SUB1",
        "##happy": "SUB2",
        "##ness": "SUB3",
        "the": "WORD1",
        "cat": "WORD2",
        "sat": "WORD3",
    }

    tokens = []
    words = text.lower().split()

    for word in words:
        if word in vocabulary:
            tokens.append(vocabulary[word])
        else:
            # Split unknown words into characters
            tokens.extend([c for c in word])

    return tokens

# Demo
if __name__ == "__main__":
    text = "The cat sat on the mat"

    print("="*60)
    print("TOKENIZATION DEMO")
    print("="*60)

    print(f"\nOriginal text: '{text}'")
    print(f"Character count: {len(text)}")

    # 1. Whitespace tokenization
    print("\n" + "─"*60)
    print("1. WHITESPACE TOKENIZATION")
    print("─"*60)
    tokens = simple_whitespace_tokenizer(text)
    print(f"Tokens: {tokens}")
    print(f"Token count: {len(tokens)}")
    print(f"Compression: {len(text)} chars → {len(tokens)} tokens")

    # 2. Character tokenization
    print("\n" + "─"*60)
    print("2. CHARACTER-LEVEL TOKENIZATION")
    print("─"*60)
    tokens = simple_character_tokenizer(text)
    print(f"Tokens: {tokens[:20]}... (showing first 20)")
    print(f"Token count: {len(tokens)}")
    print(f"Problem: Too many tokens! No semantic meaning.")

    # 3. Subword tokenization (BPE-style)
    print("\n" + "─"*60)
    print("3. SUBWORD (BPE-STYLE) TOKENIZATION")
    print("─"*60)
    tokens = simulate_bpe_tokenizer(text)
    print(f"Tokens: {tokens}")
    print(f"Token count: {len(tokens)}")
    print(f"Benefit: Known words as single tokens, unknown words split")

    # 4. Show token-to-ID mapping
    print("\n" + "─"*60)
    print("4. TOKEN TO ID MAPPING")
    print("─"*60)

    # Create vocabulary
    vocab = {
        "The": 464,
        "cat": 2479,
        "sat": 7731,
        "on": 319,
        "the": 262,
        "mat": 2611,
    }

    tokens = simple_whitespace_tokenizer(text)
    token_ids = [vocab.get(token, 0) for token in tokens]  # 0 = unknown

    print("Token → ID mapping:")
    for token, tid in zip(tokens, token_ids):
        print(f"  '{token}' → {tid}")

    print(f"\nFinal input to model: {token_ids}")

    # 5. Practical example - counting tokens
    print("\n" + "="*60)
    print("PRACTICAL: WHY TOKEN COUNT MATTERS")
    print("="*60)

    examples = [
        ("Hello world", 2),
        ("The quick brown fox jumps over the lazy dog", 9),
        ("Supercalifragilisticexpialidocious", 6),  # Would be split
    ]

    print("\nAPI costs are based on tokens, not characters!")
    print(f"{'Text':<50} | Tokens | Cost ($0.002/1K)")
    print("─"*80)

    for text, approx_tokens in examples:
        cost = (approx_tokens / 1000) * 0.002
        print(f"{text:<50} | {approx_tokens:>6} | ${cost:.6f}")

    # 6. Demonstrate context limits
    print("\n" + "="*60)
    print("CONTEXT WINDOW LIMITS")
    print("="*60)

    print("\nModels have maximum token limits:")
    print("  GPT-3.5 Turbo: 4,096 tokens")
    print("  GPT-4:         8,192 tokens")
    print("  GPT-4-32k:    32,768 tokens")
    print("  Claude 2:    100,000 tokens")

    print("\nExample calculation:")
    text = "The quick brown fox jumps over the lazy dog. " * 100
    approx_tokens = len(text.split())
    print(f"  Text: 100 repetitions of a sentence")
    print(f"  Approximate tokens: {approx_tokens}")
    print(f"  Fits in GPT-3.5? {approx_tokens <= 4096}")
    print(f"  Fits in GPT-4?   {approx_tokens <= 8192}")

    print("\n" + "="*60)
    print("KEY TAKEAWAYS:")
    print("="*60)
    print("✓ Tokenization converts text → numerical IDs")
    print("✓ Different languages = different token counts")
    print("✓ Subword tokenization (BPE) is the standard")
    print("✓ Token count determines cost AND context limits")
    print("✓ Rule of thumb: 1 token ≈ 4 characters (English)")
    print("="*60)
