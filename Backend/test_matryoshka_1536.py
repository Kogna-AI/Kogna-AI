"""
Test Matryoshka Embeddings - Verify 1536 Dimensions
====================================================

Quick test to verify Gemini embeddings are returning 1536 dimensions
after Matryoshka configuration.
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_matryoshka_1536():
    """Test that embeddings return 1536 dimensions."""

    print("=" * 70)
    print("MATRYOSHKA EMBEDDING TEST (1536 Dimensions)")
    print("=" * 70)

    test_text = "What industry are we in?"

    # ========================================================================
    # Test 1: Google GenAI SDK with output_dimensionality=1536
    # ========================================================================

    print("\n📝 Test 1: Google GenAI SDK (with output_dimensionality)")
    print("-" * 70)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=test_text,
            config=types.EmbedContentConfig(output_dimensionality=1536)
        )

        embedding = list(result.embeddings[0].values)

        if len(embedding) == 1536:
            print(f"✅ SUCCESS: Got {len(embedding)} dimensions (expected 1536)")
            print(f"  First 5 values: {embedding[:5]}")
        else:
            print(f"❌ FAILED: Got {len(embedding)} dimensions (expected 1536)")

    except ImportError:
        print("❌ google-genai SDK not installed")
        print("   Install with: pip install google-genai")
    except Exception as e:
        print(f"❌ Error: {e}")

    # ========================================================================
    # Test 2: Memory Manager v1.5 (using our wrapper)
    # ========================================================================

    print("\n📝 Test 2: Memory Manager v1.5 GeminiEmbeddingProvider")
    print("-" * 70)

    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        from services.memory_manager_v15 import GeminiEmbeddingProvider

        provider = GeminiEmbeddingProvider(output_dimensionality=1536)
        embedding = await provider.embed(test_text)

        if len(embedding) == 1536:
            print(f"✅ SUCCESS: Got {len(embedding)} dimensions (expected 1536)")
            print(f"  First 5 values: {embedding[:5]}")
        else:
            print(f"❌ FAILED: Got {len(embedding)} dimensions (expected 1536)")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # ========================================================================
    # Test 3: Embedding Service (document processing)
    # ========================================================================

    print("\n📝 Test 3: Embedding Service (for documents)")
    print("-" * 70)

    try:
        from services.embedding_service import embeddings_model

        embedding = embeddings_model.embed_query(test_text)

        if len(embedding) == 1536:
            print(f"✅ SUCCESS: Got {len(embedding)} dimensions (expected 1536)")
            print(f"  First 5 values: {embedding[:5]}")
        else:
            print(f"❌ FAILED: Got {len(embedding)} dimensions (expected 1536)")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # ========================================================================
    # Test 4: Hierarchical Retriever
    # ========================================================================

    print("\n📝 Test 4: Hierarchical Retriever")
    print("-" * 70)

    try:
        from services.hierarchical_retriever import embeddings_model

        embedding = embeddings_model.embed_query(test_text)

        if len(embedding) == 1536:
            print(f"✅ SUCCESS: Got {len(embedding)} dimensions (expected 1536)")
            print(f"  First 5 values: {embedding[:5]}")
        else:
            print(f"❌ FAILED: Got {len(embedding)} dimensions (expected 1536)")

    except Exception as e:
        print(f"❌ Error: {e}")

    # ========================================================================
    # Summary
    # ========================================================================

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nNext step: Run the SQL migration to update Supabase to 1536 dimensions")
    print("File: Backend/services/dual_memory/UPDATE_EMBEDDING_DIMENSIONS.sql")


if __name__ == "__main__":
    asyncio.run(test_matryoshka_1536())
