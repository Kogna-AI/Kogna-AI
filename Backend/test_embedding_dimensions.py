"""
Quick test to check what dimensions Gemini embedding API actually returns
"""

import os
import sys
import asyncio

# Add Backend to path and load environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables (same as other scripts)
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import GoogleGenerativeAIEmbeddings

async def test_embedding_dimensions():
    """Test what dimension embeddings we actually get."""

    print("=" * 70)
    print("EMBEDDING DIMENSION TEST")
    print("=" * 70)

    # Initialize model (same as in memory_manager_v15.py)
    model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    test_text = "What industry are we in?"

    # Test 1: embed_query (single text)
    print("\n📝 Test 1: embed_query (single text)")
    print("-" * 70)

    try:
        embedding_single = model.embed_query(test_text)
        print(f"✓ embed_query returned: {len(embedding_single)} dimensions")
        print(f"  First 5 values: {embedding_single[:5]}")
        print(f"  Data type: {type(embedding_single)}")
    except Exception as e:
        print(f"❌ embed_query failed: {e}")

    # Test 2: embed_documents (batch, but with 1 text)
    print("\n📝 Test 2: embed_documents (batch with 1 text)")
    print("-" * 70)

    try:
        embeddings_batch = model.embed_documents([test_text])
        print(f"✓ embed_documents returned: {len(embeddings_batch)} embeddings")
        print(f"  First embedding: {len(embeddings_batch[0])} dimensions")
        print(f"  First 5 values: {embeddings_batch[0][:5]}")
        print(f"  Data type: {type(embeddings_batch)}, {type(embeddings_batch[0])}")
    except Exception as e:
        print(f"❌ embed_documents failed: {e}")

    # Test 3: embed_documents (batch with 4 texts)
    print("\n📝 Test 3: embed_documents (batch with 4 texts)")
    print("-" * 70)

    try:
        texts = [
            "What industry are we in?",
            "What are our risks?",
            "What is our revenue?",
            "Who are our competitors?"
        ]
        embeddings_batch_4 = model.embed_documents(texts)
        print(f"✓ embed_documents returned: {len(embeddings_batch_4)} embeddings")
        for i, emb in enumerate(embeddings_batch_4):
            print(f"  Embedding {i+1}: {len(emb)} dimensions")
    except Exception as e:
        print(f"❌ embed_documents failed: {e}")

    # Test 4: Check if LangChain version is the issue
    print("\n📝 Test 4: Check LangChain version")
    print("-" * 70)

    try:
        import langchain_google_genai
        version = getattr(langchain_google_genai, '__version__', 'unknown')
        print(f"✓ langchain-google-genai version: {version}")
    except Exception as e:
        print(f"⚠️  Could not determine version: {e}")

    # Test 5: Using async wrapper (same as memory_manager_v15.py)
    print("\n📝 Test 5: Async wrapper (same as memory manager)")
    print("-" * 70)

    try:
        loop = asyncio.get_event_loop()
        embedding_async = await loop.run_in_executor(None, model.embed_query, test_text)
        print(f"✓ Async embed_query returned: {len(embedding_async)} dimensions")
        print(f"  First 5 values: {embedding_async[:5]}")
    except Exception as e:
        print(f"❌ Async embed_query failed: {e}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    # Summary
    print("\n📊 SUMMARY:")
    print(f"  • Single text (embed_query): {len(embedding_single) if 'embedding_single' in locals() else 'FAILED'} dims")
    print(f"  • Batch 1 text (embed_documents): {len(embeddings_batch[0]) if 'embeddings_batch' in locals() else 'FAILED'} dims")
    print(f"  • Async wrapper: {len(embedding_async) if 'embedding_async' in locals() else 'FAILED'} dims")

    # Analysis
    if 'embedding_single' in locals():
        if len(embedding_single) == 768:
            print("\n✅ CORRECT: Getting expected 768 dimensions")
            print("   → The issue is elsewhere in the memory manager")
        elif len(embedding_single) == 3072:
            print("\n❌ CONFIRMED BUG: Getting 3072 dimensions from Gemini API")
            print("   → This is a LangChain or Gemini API issue")
            print("   → Possible fixes:")
            print("      1. Update langchain-google-genai to latest version")
            print("      2. Report bug to LangChain team")
            print("      3. Use direct Gemini API calls instead of LangChain wrapper")
        else:
            print(f"\n⚠️  UNEXPECTED: Getting {len(embedding_single)} dimensions")


if __name__ == "__main__":
    asyncio.run(test_embedding_dimensions())
