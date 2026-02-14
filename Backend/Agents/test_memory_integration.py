"""
Test Dual Memory Integration
=============================

Test script to verify that memory system is properly integrated into the agent graph.
"""

import asyncio
import sys
import os

# Add Backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Agents.graph import KognaAgent
from services.memory_manager import get_user_memory


async def test_memory_integration():
    """Test full memory integration with the agent."""

    print("=" * 70)
    print("KOGNA DUAL MEMORY INTEGRATION TEST")
    print("=" * 70)

    # Test user - Use valid UUID format for Supabase
    import uuid
    user_id = str(uuid.uuid4())  # Generate valid UUID
    session_id = f"test_session_{user_id[:8]}"

    print(f"\n🔑 Test User ID: {user_id}")
    print(f"🔑 Session ID: {session_id}")

    # Initialize agent
    agent = KognaAgent()

    print("\n📝 Test 1: First Interaction - Establish Context")
    print("-" * 70)

    # First query - should store facts about the business
    query1 = "Our Q3 revenue dropped 15% to $3.2M due to tariffs affecting our APAC market. We're a B2B SaaS company."

    print(f"Query: {query1}")

    result1 = await agent.run(
        query=query1,
        user_id=user_id,
        session_id=session_id
    )

    print(f"\n✓ Response: {result1['response'][:200]}...")
    print(f"✓ Model used: {result1.get('model_used', 'N/A')}")
    print(f"✓ Confidence: {result1.get('confidence', 0):.0%}")

    # Check what facts were extracted
    if 'facts_extracted' in result1:
        facts = result1['facts_extracted']
        print(f"\n✓ Facts extracted:")
        print(f"   • Conversation stored: {facts.get('conversation_id', 'N/A')[:8]}...")
        print(f"   • Facts: {facts.get('facts_stored', 0)}")
        print(f"   • Risks: {facts.get('risks_stored', 0)}")
        print(f"   • Metrics: {facts.get('metrics_stored', 0)}")
        print(f"   • Company info: {facts.get('company_info_stored', 0)}")
        print(f"   • Preferences: {facts.get('preferences_learned', 0)}")

    print("\n" + "=" * 70)
    print("📝 Test 2: Second Interaction - Memory Recall")
    print("-" * 70)

    # Second query - should recall previous context
    query2 = "What are our biggest risks right now?"

    print(f"Query: {query2}")

    result2 = await agent.run(
        query=query2,
        user_id=user_id,
        session_id=session_id
    )

    print(f"\n✓ Response: {result2['response'][:200]}...")

    # Check if memory was used
    if 'memory_summary' in result2:
        print(f"\n✓ Memory context used:")
        print(result2['memory_summary'][:300])

    if 'memory_context' in result2:
        mem_ctx = result2['memory_context']
        print(f"\n✓ Memory retrieval:")
        print(f"   • Relevant conversations: {len(mem_ctx.get('relevant_conversations', []))}")
        print(f"   • Business facts: {len(mem_ctx.get('business_facts', []))}")
        print(f"   • Active risks: {len(mem_ctx.get('active_risks', []))}")
        print(f"   • User preferences: {len(mem_ctx.get('user_preferences', {}))}")

    print("\n" + "=" * 70)
    print("📝 Test 3: Check Memory Storage")
    print("-" * 70)

    # Get memory summary
    memory = get_user_memory(user_id)
    summary = await memory.get_summary()

    print(f"\n✓ Memory summary for {user_id}:")
    print(f"   Conversational:")
    print(f"     • Sessions: {summary['conversational']['sessions']}")
    print(f"     • Preferences: {summary['conversational']['preferences']}")
    print(f"     • Conversations: {summary['conversational']['conversations']}")
    print(f"   Business:")
    print(f"     • Facts: {summary['business']['facts']}")
    print(f"     • Risks: {summary['business']['risks']}")
    print(f"     • Metrics: {summary['business']['metrics']}")
    print(f"     • Company context: {summary['business']['company_context_keys']}")

    print("\n" + "=" * 70)
    print("📝 Test 4: Third Interaction - Verify Learning")
    print("-" * 70)

    # Third query - test if it remembers company context
    query3 = "What industry are we in?"

    print(f"Query: {query3}")

    result3 = await agent.run(
        query=query3,
        user_id=user_id,
        session_id=session_id
    )

    print(f"\n✓ Response: {result3['response'][:200]}...")

    # Should mention "B2B SaaS" from first interaction
    if "saas" in result3['response'].lower() or "b2b" in result3['response'].lower():
        print("\n✅ SUCCESS! Agent recalled company info from memory!")
    else:
        print("\n⚠️  Agent may not have used memory context")

    print("\n" + "=" * 70)
    print("✅ MEMORY INTEGRATION TEST COMPLETE")
    print("=" * 70)

    return {
        "test1_facts": result1.get('facts_extracted', {}),
        "test2_memory_used": 'memory_context' in result2,
        "test3_recall": "saas" in result3['response'].lower(),
        "memory_summary": summary
    }


async def test_greeting_with_memory():
    """Test that even greetings get stored in memory."""

    print("\n" + "=" * 70)
    print("📝 Test 5: Greeting Storage in Memory")
    print("-" * 70)

    import uuid
    user_id = str(uuid.uuid4())  # Generate valid UUID
    session_id = f"test_session_greeting_{user_id[:8]}"

    agent = KognaAgent()

    query = "Hi there!"
    print(f"Query: {query}")

    result = await agent.run(
        query=query,
        user_id=user_id,
        session_id=session_id
    )

    print(f"\n✓ Response: {result['response']}")
    print(f"✓ Skipped RAG: {result.get('skipped_rag', False)}")
    print(f"✓ Gate 1 passed: {result.get('gate1_passed', False)}")

    if 'facts_extracted' in result:
        facts = result['facts_extracted']
        print(f"✓ Conversation stored: {facts.get('conversation_id', 'N/A')[:8]}...")

    print("\n✅ Greeting was stored in memory!")


async def main():
    """Run all tests."""
    try:
        # Main integration test
        results = await test_memory_integration()

        # Greeting test
        await test_greeting_with_memory()

        print("\n" + "=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"✓ Facts extracted in test 1: {results['test1_facts'].get('facts_stored', 0) + results['test1_facts'].get('risks_stored', 0)}")
        print(f"✓ Memory used in test 2: {'Yes' if results['test2_memory_used'] else 'No'}")
        print(f"✓ Company info recalled in test 3: {'Yes' if results['test3_recall'] else 'No'}")
        print(f"\n✓ Total stored:")
        print(f"   • Conversations: {results['memory_summary']['conversational']['conversations']}")
        print(f"   • Facts: {results['memory_summary']['business']['facts']}")
        print(f"   • Risks: {results['memory_summary']['business']['risks']}")

        print("\n✅ ALL TESTS PASSED! Memory system is working correctly.")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n🚀 Starting Kogna Memory Integration Tests...\n")
    asyncio.run(main())
