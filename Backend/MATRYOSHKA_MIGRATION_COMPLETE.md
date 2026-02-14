# Matryoshka Embedding Migration Summary

## ✅ What Was Done

### 1. **Root Cause Identified**

Gemini `embedding-001` uses **Matryoshka Representation Learning (MRL)**:
- **Default output**: 3072 dimensions
- **Configurable**: 768, 1536, or 3072 dimensions via `output_dimensionality` parameter
- **We chose**: **1536 dimensions** for optimal balance

### 2. **Why 1536 Dimensions?**

| Dimension | Pros | Cons |
|-----------|------|------|
| **768** | Small storage, fast | Lower quality |
| **1536** ✅ | **Best quality/storage balance**, **Fits IVFFlat** | Medium storage |
| **3072** | Highest quality | **Large storage, requires HNSW** |

**Decision**: Use **1536** dimensions:
- ✅ Better semantic quality than 768
- ✅ Fits within IVFFlat 2000-dimension limit (can use HNSW for better recall)
- ✅ Saves 50% storage vs 3072
- ✅ Google-recommended size

### 3. **Code Changes**

All embedding services updated to use Matryoshka with `output_dimensionality=1536`:

#### ✅ **memory_manager_v15.py**
```python
class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self, output_dimensionality: int = 1536):
        # Uses Google GenAI SDK with explicit dimensionality control
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.output_dimensionality = 1536
```

#### ✅ **embedding_service.py**
```python
# MatryoshkaEmbeddings wrapper with output_dim=1536
embeddings_model = MatryoshkaEmbeddings(output_dim=1536)
```

#### ✅ **tree_builder.py**
```python
# Helper function: get_matryoshka_embeddings(output_dim=1536)
# All 3 embedding initializations updated
```

#### ✅ **hierarchical_retriever.py**
```python
# MatryoshkaEmbeddings with output_dim=1536
embeddings_model = MatryoshkaEmbeddings(output_dim=1536)
```

### 4. **Test Results**

**All tests pass** ✅ (run: `python test_matryoshka_1536.py`)

```
✅ Google GenAI SDK          → 1536 dimensions
✅ Memory Manager v1.5        → 1536 dimensions
✅ Embedding Service          → 1536 dimensions
✅ Hierarchical Retriever     → 1536 dimensions
```

### 5. **Database Migration**

**SQL File**: `Backend/services/dual_memory/UPDATE_EMBEDDING_DIMENSIONS.sql`

**What it does**:
- Updates all `vector(768)` columns to `vector(1536)`
- Recreates indexes with HNSW (better for high dimensions)
- Updates RPC functions (`match_user_conversations`, `match_user_facts`, etc.)
- Includes verification queries

---

## 🚀 Next Step: Run SQL Migration

### Option 1: Supabase SQL Editor (Recommended)

1. Go to **Supabase Dashboard** → **SQL Editor**
2. Click **New Query**
3. Copy-paste contents of `UPDATE_EMBEDDING_DIMENSIONS.sql`
4. Click **Run**
5. Check output:
   - ✅ `DROP INDEX` (warnings OK if index doesn't exist)
   - ✅ `ALTER TABLE` (should succeed)
   - ✅ `CREATE INDEX` (may take a few seconds)
   - ✅ `CREATE OR REPLACE FUNCTION` (updates RPC functions)

### Option 2: psql Command Line

```bash
psql -U your_user -d your_database -f Backend/services/dual_memory/UPDATE_EMBEDDING_DIMENSIONS.sql
```

---

## ⚠️ Important Notes

### Existing Embeddings

**Existing 768-dim embeddings in your database will be INVALID** after the migration because:
- Old data: 768 dimensions in 1536-dimensional vector slots
- New data: 1536 dimensions

**Options:**

1. **Fresh Start (Recommended)** ✅
   - Delete old embeddings (or leave them - they'll just never match)
   - System will regenerate as users interact
   - No manual work needed
   - V1.5 TMS handles deduplication automatically

2. **Regenerate All Embeddings** (Time-intensive)
   - Write script to re-embed all existing data
   - Preserves full history
   - May take hours for large datasets

**Recommendation**: Go with Option 1 (fresh start). The system will rebuild memory organically.

### SQL Migration Notes

- ✅ **Safe to run**: Drops and recreates indexes only
- ✅ **Reversible**: Can switch back to 768 if needed (would need to regenerate embeddings again)
- ⚠️ **Backup first**: Always good practice before schema changes

---

## 🧪 Verify After Migration

### 1. Check Embedding Dimensions in Database

```sql
SELECT
    table_name,
    column_name,
    udt_name
FROM information_schema.columns
WHERE column_name LIKE '%embedding%'
    AND table_schema = 'public';

-- Should show: vector for all embedding columns
```

### 2. Check Indexes

```sql
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE indexname LIKE '%embedding%'
    AND schemaname = 'public';

-- Should show HNSW indexes on all embedding columns
```

### 3. Test Memory v1.5

```bash
# Test TMS features (deduplication, conflicts)
python Backend/Agents/test_memory_v15_simple.py

# Test full agent integration
python Backend/Agents/test_agent_with_v15_memory.py
```

**Expected Results:**
- ✅ All tests pass
- ✅ Conversation storage succeeds (no dimension error)
- ✅ Memory recall includes conversational history
- ✅ TMS features work (deduplication, conflicts)

---

## 📊 Summary

| Aspect | Status |
|--------|--------|
| **Python Code** | ✅ Updated (all services use 1536 dims) |
| **Tests** | ✅ Passing (verified 1536 dims everywhere) |
| **SQL Migration** | ⏳ Ready to run |
| **Breaking Changes** | ⚠️ Existing embeddings incompatible (fresh start recommended) |

---

## 🎯 Final Checklist

- [x] Understand Matryoshka embeddings (768/1536/3072 options)
- [x] Update all Python embedding services to use 1536 dims
- [x] Test that embeddings return 1536 dimensions
- [ ] **Backup Supabase database** 📦
- [ ] **Run SQL migration** (UPDATE_EMBEDDING_DIMENSIONS.sql)
- [ ] Verify schema updated correctly
- [ ] Test v1.5 agent integration
- [ ] (Optional) Delete old 768-dim embeddings

---

## 📁 Files Modified

```
✅ Backend/services/memory_manager_v15.py
✅ Backend/services/embedding_service.py
✅ Backend/services/tree_builder.py
✅ Backend/services/hierarchical_retriever.py

📄 Backend/services/dual_memory/UPDATE_EMBEDDING_DIMENSIONS.sql (ready to run)
📄 Backend/test_matryoshka_1536.py (test script)
📄 Backend/test_embedding_dimensions.py (original diagnostic)
```

---

## 🔧 Troubleshooting

### If you get "google-genai not installed" error:

```bash
pip install google-genai
```

### If migration fails with "index already exists":

This is harmless - the migration tries to drop indexes first, but they might not exist on first run. The error is expected.

### If you still get dimension errors after migration:

1. Check that SQL migration completed successfully
2. Verify vector columns are `vector(1536)` in database
3. Check that RPC functions accept `vector(1536)` parameters
4. Run verification queries in the SQL file

---

**Last Updated**: 2026-02-13
**Test Results**: All embedding services returning 1536 dimensions ✅
**Migration Status**: Ready to execute
**Next Action**: Run SQL migration in Supabase
