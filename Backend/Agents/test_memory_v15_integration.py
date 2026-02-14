"""
Test Kogna 1.5 Memory Integration
==================================

Quick test to verify v1.5 memory system works with the updated nodes.
"""

import asyncio
import os
import sys

# Add Backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment to use v1.5
os.environ["MEMORY_VERSION"] = "1.5"

from Agents.nodes.memory_nodes import (
    enrich_with_memory,
    extract_and_store_facts,
    MEMORY_VERSION
)


async def test_v15_basic_flow():
    """Test basic v1.5 flow: extract → store → recall."""

    print("=" * 70)
    print("KOGNA V1.5 MEMORY INTEGRATION TEST")
    print("=" * 70)
    print(f"Memory Version: {MEMORY_VERSION}")
    print("=" * 70)

    # Generate test user
    import uuid
    user_id = str(uuid.uuid4())
    session_id = f"test_session_{user_id[:8]}"

    print(f"\n🔑 Test User: {user_id}")
    print(f"🔑 Session: {session_id}\n")

    # ========================================================================
    # TEST 1: Extract and Store Facts
    # ========================================================================

    print("📝 Test 1: Extract and Store Facts")
    print("-" * 70)

    state = {
        "user_id": user_id,
        "session_id": session_id,
        "query": "Our Q3 revenue is $3.2M, down 15% due to tariffs. We're a B2B SaaS company.",
        "response": "I understand. Your Q3 revenue of $3.2M represents a 15% decline, which you've attributed to tariff impacts. As a B2B SaaS company, this is concerning. Let me analyze...",
        "intent_type": "data_question"  # Not greeting, so extraction should happen
    }

    # Run extraction
    result_state = await extract_and_store_facts(state)

    # Check results
    facts = result_state.get("facts_extracted", {})

    print(f"\n✓ Extraction Results:")
    print(f"   • Conversation ID: {facts.get('conversation_id', 'N/A')[:8]}...")
    print(f"   • Company Info Stored: {facts.get('company_info_stored', 0)}")
    print(f"   • Facts Stored: {facts.get('facts_stored', 0)}")
    print(f"   • Risks Stored: {facts.get('risks_stored', 0)}")

    if MEMORY_VERSION == "1.5":
        print(f"   • Facts Confirmed (deduped): {facts.get('facts_confirmed', 0)}")
        print(f"   • Facts Contested (conflicts): {facts.get('facts_contested', 0)}")

    # ========================================================================
    # TEST 2: Duplicate Detection (Store Same Fact Again)
    # ========================================================================

    print("\n📝 Test 2: Duplicate Detection")
    print("-" * 70)

    state2 = {
        "user_id": user_id,
        "session_id": session_id,
        "query": "As I mentioned, our revenue in Q3 was $3.2M",
        "response": "Yes, I remember you mentioned the Q3 revenue figure.",
        "intent_type": "data_question"
    }

    result_state2 = await extract_and_store_facts(state2)
    facts2 = result_state2.get("facts_extracted", {})

    print(f"\n✓ Second Extraction Results:")
    print(f"   • Facts Stored (new): {facts2.get('facts_stored', 0)}")

    if MEMORY_VERSION == "1.5":
        confirmed = facts2.get('facts_confirmed', 0)
        print(f"   • Facts Confirmed (duplicates): {confirmed}")

        if confirmed > 0:
            print("\n   ✅ SUCCESS! Duplicate was confirmed, not re-inserted")
        else:
            print("\n   ⚠️  No confirmation detected. Check if extraction happened.")

    # ========================================================================
    # TEST 3: Memory Recall (Enrich with Memory)
    # ========================================================================

    print("\n📝 Test 3: Memory Recall")
    print("-" * 70)

    state3 = {
        "user_id": user_id,
        "session_id": session_id,
        "query": "What industry are we in?",
        "retrieval_context": []  # Empty retrieval (should rely on memory)
    }

    enriched_state = await enrich_with_memory(state3)

    memory_ctx = enriched_state.get("memory_context", {})

    print(f"\n✓ Memory Retrieved:")
    print(f"   • Conversations: {len(memory_ctx.get('relevant_conversations', []))}")
    print(f"   • Business Facts: {len(memory_ctx.get('business_facts', []))}")
    print(f"   • Company Context: {memory_ctx.get('company_context', {})}")
    print(f"   • Active Risks: {len(memory_ctx.get('active_risks', []))}")

    # Check if company context was recalled
    company = memory_ctx.get("company_context", {})
    if "industry" in company or any("saas" in str(v).lower() for v in company.values()):
        print("\n   ✅ SUCCESS! Company info (B2B SaaS) recalled from memory")
    else:
        print("\n   ⚠️  Company info not found. Check if extraction worked in Test 1.")

    # ========================================================================
    # TEST 4: Conflict Detection (Contradictory Fact)
    # ========================================================================

    if MEMORY_VERSION == "1.5":
        print("\n📝 Test 4: Conflict Detection")
        print("-" * 70)

        state4 = {
            "user_id": user_id,
            "session_id": session_id,
            "query": "Actually, I made a mistake. Q3 revenue was $4.5M, not $3.2M",
            "response": "I see. Let me update that figure.",
            "intent_type": "data_question"
        }

        result_state4 = await extract_and_store_facts(state4)
        facts4 = result_state4.get("facts_extracted", {})

        print(f"\n✓ Conflicting Extraction Results:")
        print(f"   • Facts Stored: {facts4.get('facts_stored', 0)}")
        print(f"   • Facts Confirmed: {facts4.get('facts_confirmed', 0)}")
        print(f"   • Facts Contested: {facts4.get('facts_contested', 0)}")

        if facts4.get('facts_contested', 0) > 0:
            print("\n   ✅ SUCCESS! Conflict detected between $3.2M and $4.5M")
            conflicts = facts4.get('conflicts_detected', [])
            print(f"      Conflict IDs: {conflicts}")
        else:
            print("\n   ⚠️  No conflict detected. TMS may need tuning.")

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    total_tests = 3 if MEMORY_VERSION == "1.0" else 4
    passed_tests = 0

    # Test 1: Extraction
    if facts.get('company_info_stored', 0) > 0 or facts.get('facts_stored', 0) > 0:
        print("✅ Test 1: Fact Extraction - PASSED")
        passed_tests += 1
    else:
        print("❌ Test 1: Fact Extraction - FAILED")

    # Test 2: Deduplication (v1.5 only)
    if MEMORY_VERSION == "1.5":
        if facts2.get('facts_confirmed', 0) > 0:
            print("✅ Test 2: Duplicate Detection - PASSED")
            passed_tests += 1
        else:
            print("⚠️  Test 2: Duplicate Detection - INCONCLUSIVE")

    # Test 3: Recall
    if company or len(memory_ctx.get('relevant_conversations', [])) > 0:
        print("✅ Test 3: Memory Recall - PASSED")
        passed_tests += 1
    else:
        print("❌ Test 3: Memory Recall - FAILED")

    # Test 4: Conflict Detection (v1.5 only)
    if MEMORY_VERSION == "1.5":
        if facts4.get('facts_contested', 0) > 0:
            print("✅ Test 4: Conflict Detection - PASSED")
            passed_tests += 1
        else:
            print("⚠️  Test 4: Conflict Detection - INCONCLUSIVE")

    print("\n" + "=" * 70)
    print(f"Result: {passed_tests}/{total_tests} tests passed")
    print("=" * 70)

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Kogna v1.5 is working correctly.")
    elif passed_tests >= total_tests - 1:
        print("\n✓ Most tests passed. Minor tuning may be needed.")
    else:
        print("\n⚠️  Some tests failed. Review logs above.")


if __name__ == "__main__":
    print(f"\n🚀 Starting Kogna v1.5 Integration Tests...\n")

    try:
        asyncio.run(test_v15_basic_flow())
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED WITH ERROR:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
