# 🚀 Kogna 1.5 Implementation Guide

**Upgrading from Kogna 1.0 → 1.5: Enhanced Memory with Truth Maintenance**

---

## Executive Summary

**Goal**: Upgrade Kogna's memory system to prevent data corruption, reduce hallucinations, and improve reliability for Business Intelligence use cases.

**Approach**: Additive upgrades—no breaking changes to existing code. The v1.5 system runs **alongside** v1.0 until migration is complete.

**Timeline**: 6-8 weeks for full implementation.

---

## 📊 What Changes in the Data Intake Pipeline?

### Current Flow (Kogna 1.0)
```
User Query
    ↓
Agent Graph (classify → retrieve → specialist → respond)
    ↓
extract_and_store_facts (async)
    ↓
Direct INSERT into Supabase (no verification)
    ↓
Memory stored (potentially with conflicts/duplicates)
```

### New Flow (Kogna 1.5)
```
User Query
    ↓
Agent Graph (classify → retrieve → specialist → respond)
    ↓
EnhancedFactExtractor (2-pass: Extract → Self-Critique)
    ↓
TruthMaintenanceSystem (Deduplication + Conflict Detection)
    ↓  ↓  ↓
    |  |  └─→ CONFLICT → Flag for user review
    |  └─→ DUPLICATE → Confirm (boost confidence)
    └─→ NEW → Insert with metadata
    ↓
Memory stored (verified, conflict-free)
```

### Key Differences

| **Aspect**                  | **Kogna 1.0**                     | **Kogna 1.5**                              |
|-----------------------------|-----------------------------------|--------------------------------------------|
| **Fact Extraction**         | Single-pass LLM call              | Two-pass (Extract → Critique)              |
| **Storage**                 | Blind INSERT                      | TMS verification before INSERT             |
| **Deduplication**           | None                              | Automatic (semantic similarity matching)   |
| **Conflict Handling**       | Overwrites / Appends blindly      | Detects conflicts, flags for resolution    |
| **Metadata Tracked**        | Basic (value, embedding)          | Rich (source, confidence, verification_status) |
| **Source Authority**        | Not tracked                       | Tracked (ERP > PDF > CHAT)                 |
| **Confidence Scoring**      | Not tracked                       | Tracked (0.0 to 1.0)                       |
| **Temporal Validity**       | valid_from only                   | valid_from + valid_to (supports deprecation) |

---

## 🗂️ File Structure

### New Files Created
```
Backend/
├── services/
│   ├── dual_memory/
│   │   ├── fact_extraction_v15.py          ✨ NEW: Self-reflective extraction
│   │   ├── truth_maintenance.py            ✨ NEW: Conflict detection & resolution
│   │   └── UPGRADE_SCHEMA_TO_V1.5.sql      ✨ NEW: Database migration script
│   └── memory_manager_v15.py               ✨ NEW: Enhanced memory manager
│
└── KOGNA_V1.5_IMPLEMENTATION_GUIDE.md      ✨ NEW: This guide
```

### Modified Files (Later)
```
Backend/Agents/nodes/memory_nodes.py        🔄 UPDATE: Use memory_manager_v15
Backend/Agents/test_memory_integration.py   🔄 UPDATE: Add v1.5 tests
```

---

## 📝 Step-by-Step Implementation Plan

### **Phase 1: Database Migration** (Week 1)

#### Task 1.1: Run Schema Upgrade
```bash
# In Supabase SQL Editor, run:
Backend/services/dual_memory/UPGRADE_SCHEMA_TO_V1.5.sql
```

**What this does:**
- Adds `source_authority`, `confidence_score`, `verification_status`, `valid_to` to existing tables
- Creates `fact_conflicts` table for tracking contested facts
- Creates `sql_memory` table for procedural memory (Text-to-SQL templates)
- Creates new RPC functions for hybrid search

**Verification:**
```sql
-- Check that new columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'user_business_facts'
  AND column_name IN ('source_authority', 'confidence_score', 'verification_status');
```

#### Task 1.2: Backfill Existing Data
```sql
-- Set defaults for existing rows (already in migration script)
UPDATE user_business_facts
SET
    source_authority = 'UNKNOWN',
    confidence_score = 0.7,
    verification_status = 'PROVISIONAL'
WHERE source_authority IS NULL;
```

---

### **Phase 2: Code Integration** (Weeks 2-3)

#### Task 2.1: Update Memory Nodes
**File**: `Backend/Agents/nodes/memory_nodes.py`

**Change 1**: Import v1.5 memory manager
```python
# OLD (Kogna 1.0)
from services.memory_manager import get_user_memory

# NEW (Kogna 1.5)
from services.memory_manager_v15 import get_user_memory  # Enhanced version
```

**Change 2**: Pass source_type to process_interaction
```python
# In extract_and_store_facts node:

# Determine source type based on context
source_type = state.get("source_type", "CHAT")  # Default to CHAT
if state.get("from_pdf"):
    source_type = "PDF"
elif state.get("from_erp"):
    source_type = "ERP"

# Process interaction with source tracking
result = await memory.process_interaction(
    query=state["query"],
    response=state["response"],
    session_id=state["session_id"],
    source_type=source_type,  # ✨ NEW parameter
    auto_extract=True
)

# ✨ NEW: Log storage report
if result.get("facts_contested", 0) > 0:
    logger.warning(f"⚠️  {result['facts_contested']} facts flagged as CONTESTED")
```

#### Task 2.2: Update Graph to Handle Conflicts
**File**: `Backend/Agents/graph.py`

**Add a conflict resolution node** (optional but recommended):
```python
async def check_for_conflicts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if user has pending memory conflicts.
    If so, inject a warning into the response.
    """

    memory = get_user_memory(state["user_id"])
    pending_conflicts = await memory.storage.get_pending_conflicts()

    if pending_conflicts and len(pending_conflicts) > 0:
        # Add warning to context
        conflict_warning = f"\n\n⚠️ **Memory Notice**: I have {len(pending_conflicts)} conflicting facts that need your review."

        state["conflict_warning"] = conflict_warning
        state["pending_conflicts"] = pending_conflicts

    return state
```

**Add to graph flow:**
```python
# After enrich_with_memory, before gate2
graph.add_node("check_conflicts", check_for_conflicts)
graph.add_edge("enrich_with_memory", "check_conflicts")
graph.add_edge("check_conflicts", "gate2")
```

---

### **Phase 3: Testing** (Week 4)

#### Task 3.1: Create V1.5 Test Suite
**File**: `Backend/Agents/test_memory_v15.py`

```python
"""
Test Kogna 1.5 Memory Features
"""

import asyncio
from services.memory_manager_v15 import get_user_memory

async def test_deduplication():
    """Test that duplicate facts are confirmed, not duplicated."""

    user_id = "test_user_123"
    memory = get_user_memory(user_id)

    # First interaction: Extract "Revenue = $3.2M"
    result1 = await memory.process_interaction(
        query="Our Q3 revenue is $3.2M",
        response="I'll analyze that",
        session_id="session_1",
        source_type="CHAT"
    )

    # Second interaction: Same fact
    result2 = await memory.process_interaction(
        query="As I mentioned, Q3 revenue was $3.2M",
        response="Got it",
        session_id="session_1",
        source_type="CHAT"
    )

    # Should have CONFIRMED, not duplicated
    assert result2['facts_confirmed'] > 0, "Duplicate fact should be CONFIRMED"
    assert result2['facts_stored'] == 0, "Should not create duplicate"

    print("✓ Deduplication test passed")


async def test_conflict_detection():
    """Test that contradictory facts are flagged."""

    user_id = "test_user_456"
    memory = get_user_memory(user_id)

    # First: Revenue = $3.2M
    result1 = await memory.process_interaction(
        query="Q3 revenue is $3.2M",
        response="OK",
        session_id="session_1",
        source_type="CHAT"
    )

    # Second: Revenue = $4.5M (contradicts!)
    result2 = await memory.process_interaction(
        query="Wait, Q3 revenue was actually $4.5M",
        response="Let me check",
        session_id="session_1",
        source_type="CHAT"
    )

    # Should detect conflict
    assert result2['facts_contested'] > 0, "Conflict should be detected"
    assert len(result2['conflicts_detected']) > 0, "Conflict ID should be returned"

    # Check pending conflicts
    context = await memory.get_context(query="What is revenue?", session_id="session_1")
    assert 'pending_conflicts' in context, "Pending conflicts should be in context"

    print("✓ Conflict detection test passed")


async def test_source_authority():
    """Test that higher-authority sources override lower ones."""

    user_id = "test_user_789"
    memory = get_user_memory(user_id)

    # First: Industry = "SaaS" from CHAT (low authority)
    result1 = await memory.process_interaction(
        query="We're a SaaS company",
        response="OK",
        session_id="session_1",
        source_type="CHAT"
    )

    # Second: Industry = "Cloud Infrastructure" from ERP (high authority)
    result2 = await memory.storage.save_company_context(
        key="industry",
        value="Cloud Infrastructure",
        source_authority="ERP",
        confidence=0.95
    )

    # ERP should override CHAT
    assert result2['action'] == 'UPDATED', "Higher authority should override"

    # Verify
    context = await memory.storage.get_company_context()
    assert context['industry'] == "Cloud Infrastructure", "ERP value should be active"

    print("✓ Source authority test passed")


if __name__ == "__main__":
    asyncio.run(test_deduplication())
    asyncio.run(test_conflict_detection())
    asyncio.run(test_source_authority())

    print("\n✅ ALL V1.5 TESTS PASSED")
```

**Run tests:**
```bash
cd Backend
python Agents/test_memory_v15.py
```

---

### **Phase 4: Gradual Rollout** (Weeks 5-6)

#### Task 4.1: Deploy in Parallel
- Keep v1.0 running for existing users
- Enable v1.5 for **new users only** (or test users)
- Monitor error rates and conflict detection rates

**Configuration flag** (add to `.env`):
```bash
# Memory system version
MEMORY_VERSION=1.5  # or "1.0" for old system
```

**Update memory_nodes.py to use flag:**
```python
import os

MEMORY_VERSION = os.getenv("MEMORY_VERSION", "1.0")

if MEMORY_VERSION == "1.5":
    from services.memory_manager_v15 import get_user_memory
else:
    from services.memory_manager import get_user_memory  # Old version
```

#### Task 4.2: Migration Dashboard
Create a simple admin endpoint to monitor migration:
```python
@app.get("/admin/memory/stats")
async def memory_stats(user_id: str):
    """Get memory system stats for a user."""

    memory = get_user_memory(user_id)

    stats = {
        "pending_conflicts": len(await memory.storage.get_pending_conflicts()),
        "total_facts": await get_fact_count(user_id),
        "verified_facts": await get_verified_fact_count(user_id),
        "contested_facts": await get_contested_fact_count(user_id),
    }

    return stats
```

---

### **Phase 5: Procedural Memory (SQL Templates)** (Weeks 7-8)

This is the **"nice-to-have"** Tier 2 feature for improving Text-to-SQL.

#### Task 5.1: Capture Successful Queries
**When a SQL query succeeds**, store it in `sql_memory`:

**File**: Wherever you execute SQL queries (e.g., `sql_agent.py`)

```python
async def execute_sql_query(query: str, natural_question: str, user_id: str):
    """Execute SQL and store successful queries as templates."""

    try:
        # Execute query
        result = await db.execute(query)

        # Success! Store as procedural memory
        await store_sql_template(
            user_id=user_id,
            natural_question=natural_question,
            sql_template=query,
            execution_time_ms=result.execution_time
        )

        return result

    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        # Don't store failed queries
        raise


async def store_sql_template(user_id, natural_question, sql_template, execution_time_ms):
    """Store successful SQL query as a reusable template."""

    from services.memory_manager_v15 import GeminiEmbeddingProvider

    # Generate embedding for the natural question
    embedding_provider = GeminiEmbeddingProvider()
    question_embedding = await embedding_provider.embed(natural_question)

    # Extract tables/columns from SQL
    tables_used = extract_tables_from_sql(sql_template)

    # Store in sql_memory table
    supabase.table("sql_memory").insert({
        "user_id": user_id,
        "natural_question": natural_question,
        "natural_question_embedding": question_embedding,
        "sql_template": sql_template,
        "tables_used": tables_used,
        "avg_execution_time_ms": execution_time_ms,
        "success_count": 1
    }).execute()
```

#### Task 5.2: Retrieve Templates for New Queries
**Before generating SQL**, check if we have a similar query:

```python
async def generate_sql(natural_question: str, user_id: str):
    """Generate SQL using procedural memory (Case-Based Reasoning)."""

    # Search for similar past queries
    embedding = await embedding_provider.embed(natural_question)

    similar_queries = supabase.rpc('match_sql_templates', {
        'query_embedding': embedding,
        'match_count': 3,
        'p_user_id': user_id
    }).execute()

    if similar_queries.data and len(similar_queries.data) > 0:
        # Found a similar query! Use it as a template
        best_match = similar_queries.data[0]

        # Use as few-shot example for LLM
        prompt = f"""
        I previously solved a similar query:
        Question: {best_match['natural_question']}
        SQL: {best_match['sql_template']}

        Now adapt this to answer:
        Question: {natural_question}
        SQL:
        """

        # Generate adapted SQL
        return await llm.generate(prompt)

    else:
        # No similar query found, generate from scratch
        return await generate_sql_from_scratch(natural_question)
```

---

## 🎯 Success Metrics

Track these metrics to measure v1.5 effectiveness:

| **Metric**                          | **Target**     | **How to Measure**                                  |
|-------------------------------------|----------------|-----------------------------------------------------|
| **Conflict Detection Rate**         | 5-10% of facts | Count rows in `fact_conflicts` per day              |
| **Duplicate Prevention Rate**       | 30-40% of facts| Count facts_confirmed / total_extraction_attempts   |
| **Fact Extraction Accuracy**        | >85%           | Manual review of 50 random extractions              |
| **User-Reported Memory Errors**     | <1% per week   | Support tickets mentioning "wrong number" or "incorrect fact" |
| **SQL Template Reuse Rate**         | 20-30%         | Count queries using templates vs. from-scratch      |

---

## 🐛 Troubleshooting

### Problem: Schema migration fails
**Solution**: Check if foreign key constraints are blocking the ALTER TABLE. You may need to temporarily drop them:
```sql
-- Temporarily drop FK constraints (if needed)
ALTER TABLE user_business_facts DROP CONSTRAINT IF EXISTS user_business_facts_user_id_fkey;

-- Run migration
ALTER TABLE user_business_facts ADD COLUMN source_authority TEXT;

-- Restore FK (optional, v1.0 removed them for flexibility)
-- ALTER TABLE user_business_facts ADD FOREIGN KEY (user_id) REFERENCES auth.users(id);
```

### Problem: LLM extraction returns invalid JSON
**Solution**: Add retry logic with error correction:
```python
# In fact_extraction_v15.py
try:
    extracted_json = response.choices[0].message.content
    extracted_facts = json.loads(extracted_json)
except json.JSONDecodeError as e:
    logger.warning(f"Invalid JSON from LLM, attempting fix: {e}")
    # Try to fix common JSON errors
    fixed_json = fix_json_errors(extracted_json)
    extracted_facts = json.loads(fixed_json)
```

### Problem: Too many conflicts flagged
**Solution**: Adjust conflict detection thresholds in `truth_maintenance.py`:
```python
# Make conflict detection less sensitive
def _values_are_compatible(self, val1: str, val2: str) -> bool:
    # Increase tolerance from 5% to 10%
    return abs(n1 - n2) / max(n1, n2) < 0.10  # Was 0.05
```

---

## 📚 Next Steps After V1.5

Once V1.5 is stable, you can plan for **V2.0 (GraphRAG)**:

1. **Migrate from flat tables to graph** (`entity_nodes`, `semantic_edges`)
2. **Implement graph traversal** for "Why?" questions
3. **Add causal reasoning** (Tariffs → COGS → Profitability)

But that's a future project. **V1.5 should be your focus for the next 2 months.**

---

## ✅ Checklist

- [ ] Run UPGRADE_SCHEMA_TO_V1.5.sql in Supabase
- [ ] Verify new columns exist (`source_authority`, `confidence_score`, etc.)
- [ ] Update `memory_nodes.py` to import `memory_manager_v15`
- [ ] Add `source_type` parameter to `process_interaction()` calls
- [ ] Create `test_memory_v15.py` and run all tests
- [ ] Deploy v1.5 in parallel with v1.0 (use `MEMORY_VERSION` flag)
- [ ] Monitor conflict detection rates
- [ ] Gradually migrate users from v1.0 to v1.5
- [ ] Implement SQL template storage (procedural memory)
- [ ] Celebrate! 🎉

---

**Questions?** Review the architectural analysis document or consult the code comments in:
- `fact_extraction_v15.py` - Self-reflective extraction logic
- `truth_maintenance.py` - Conflict detection algorithms
- `memory_manager_v15.py` - Integration layer

**Good luck!** 🚀
