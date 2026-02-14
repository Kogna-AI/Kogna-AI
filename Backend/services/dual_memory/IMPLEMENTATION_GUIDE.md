# Dual Memory System - Implementation Guide

## 📁 Step 1: Copy Memory Files

Place the following files in `Backend/services/dual_memory/`:

1. **memory_system.py** - Core memory system (you already have this)
2. **fact_extraction.py** - Fact extraction logic (you already have this)

```bash
# Your dual_memory folder should look like:
Backend/services/dual_memory/
├── __init__.py  ✅ (created)
├── memory_system.py  ⚠️ (paste the file you received from Claude web)
├── fact_extraction.py  ⚠️ (paste the file you received from Claude web)
└── IMPLEMENTATION_GUIDE.md  ✅ (this file)
```

---

## 🗄️ Step 2: Create Supabase Tables

Run this SQL in your Supabase SQL Editor to create the required tables:

```sql
-- ===================================================================
-- USER CONVERSATIONAL MEMORY TABLE
-- ===================================================================
CREATE TABLE IF NOT EXISTS user_conversational_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    query TEXT NOT NULL,
    response_summary TEXT,
    entities TEXT[],
    embedding vector(768),  -- Gemini embedding dimension
    was_helpful BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    CONSTRAINT unique_conversation_entry UNIQUE (user_id, session_id, created_at)
);

CREATE INDEX IF NOT EXISTS idx_conversational_memory_user ON user_conversational_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_conversational_memory_session ON user_conversational_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_conversational_memory_created ON user_conversational_memory(created_at DESC);

-- Vector search index
CREATE INDEX IF NOT EXISTS idx_conversational_memory_embedding ON user_conversational_memory
USING ivfflat (embedding vector_cosine_ops);


-- ===================================================================
-- USER BUSINESS FACTS TABLE
-- ===================================================================
CREATE TABLE IF NOT EXISTS user_business_facts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    fact_type TEXT NOT NULL,  -- company_info, metric_value, metric_definition, etc.
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    value JSONB NOT NULL,  -- Flexible storage for any value type
    confidence FLOAT DEFAULT 0.8,
    source_text TEXT,
    source_conversation_id UUID REFERENCES user_conversational_memory(id),
    embedding vector(768),
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_to TIMESTAMP WITH TIME ZONE,  -- NULL means still valid
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_business_facts_user ON user_business_facts(user_id);
CREATE INDEX IF NOT EXISTS idx_business_facts_type ON user_business_facts(fact_type);
CREATE INDEX IF NOT EXISTS idx_business_facts_valid ON user_business_facts(valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_business_facts_embedding ON user_business_facts
USING ivfflat (embedding vector_cosine_ops);


-- ===================================================================
-- USER RISKS TABLE
-- ===================================================================
CREATE TABLE IF NOT EXISTS user_risks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,  -- financial, operational, compliance, strategic, market
    severity TEXT NOT NULL,  -- critical, high, medium, low, unknown
    cause TEXT,
    impact TEXT,
    mitigation TEXT,
    owner TEXT,
    embedding vector(768),
    source_conversation_id UUID REFERENCES user_conversational_memory(id),
    identified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_to TIMESTAMP WITH TIME ZONE,  -- NULL means risk is still active
    last_mentioned TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risks_user ON user_risks(user_id);
CREATE INDEX IF NOT EXISTS idx_risks_category ON user_risks(category);
CREATE INDEX IF NOT EXISTS idx_risks_severity ON user_risks(severity);
CREATE INDEX IF NOT EXISTS idx_risks_valid ON user_risks(valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_risks_embedding ON user_risks
USING ivfflat (embedding vector_cosine_ops);


-- ===================================================================
-- USER METRIC DEFINITIONS TABLE
-- ===================================================================
CREATE TABLE IF NOT EXISTS user_metric_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    user_definition TEXT NOT NULL,
    calculation TEXT,
    context TEXT,
    embedding vector(768),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_metric_per_user UNIQUE (user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_metric_definitions_user ON user_metric_definitions(user_id);
CREATE INDEX IF NOT EXISTS idx_metric_definitions_name ON user_metric_definitions(name);
CREATE INDEX IF NOT EXISTS idx_metric_definitions_embedding ON user_metric_definitions
USING ivfflat (embedding vector_cosine_ops);


-- ===================================================================
-- USER PREFERENCES TABLE
-- ===================================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    learned_from_count INTEGER DEFAULT 1,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_preference_per_user UNIQUE (user_id, key)
);

CREATE INDEX IF NOT EXISTS idx_preferences_user ON user_preferences(user_id);


-- ===================================================================
-- USER COMPANY CONTEXT TABLE
-- ===================================================================
CREATE TABLE IF NOT EXISTS user_company_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_to TIMESTAMP WITH TIME ZONE,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_conversation_id UUID REFERENCES user_conversational_memory(id),

    CONSTRAINT unique_context_per_user UNIQUE (user_id, key)
);

CREATE INDEX IF NOT EXISTS idx_company_context_user ON user_company_context(user_id);


-- ===================================================================
-- VECTOR SEARCH FUNCTIONS
-- ===================================================================

-- Search conversational memory
CREATE OR REPLACE FUNCTION match_user_conversations(
    query_embedding vector(768),
    match_count int DEFAULT 10,
    p_user_id uuid DEFAULT NULL,
    p_session_id text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    session_id text,
    query text,
    response_summary text,
    entities text[],
    was_helpful boolean,
    created_at timestamp with time zone,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        user_conversational_memory.id,
        user_conversational_memory.session_id,
        user_conversational_memory.query,
        user_conversational_memory.response_summary,
        user_conversational_memory.entities,
        user_conversational_memory.was_helpful,
        user_conversational_memory.created_at,
        1 - (user_conversational_memory.embedding <=> query_embedding) AS similarity
    FROM user_conversational_memory
    WHERE
        (p_user_id IS NULL OR user_conversational_memory.user_id = p_user_id)
        AND (p_session_id IS NULL OR user_conversational_memory.session_id = p_session_id)
        AND user_conversational_memory.embedding IS NOT NULL
    ORDER BY user_conversational_memory.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- Search business facts
CREATE OR REPLACE FUNCTION match_user_facts(
    query_embedding vector(768),
    match_count int DEFAULT 10,
    p_user_id uuid DEFAULT NULL,
    p_fact_types text[] DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    fact_type text,
    subject text,
    predicate text,
    value jsonb,
    confidence float,
    source_text text,
    valid_from timestamp with time zone,
    valid_to timestamp with time zone,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        user_business_facts.id,
        user_business_facts.fact_type,
        user_business_facts.subject,
        user_business_facts.predicate,
        user_business_facts.value,
        user_business_facts.confidence,
        user_business_facts.source_text,
        user_business_facts.valid_from,
        user_business_facts.valid_to,
        1 - (user_business_facts.embedding <=> query_embedding) AS similarity
    FROM user_business_facts
    WHERE
        (p_user_id IS NULL OR user_business_facts.user_id = p_user_id)
        AND (p_fact_types IS NULL OR user_business_facts.fact_type = ANY(p_fact_types))
        AND user_business_facts.embedding IS NOT NULL
        AND user_business_facts.valid_to IS NULL  -- Only active facts
    ORDER BY user_business_facts.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- ===================================================================
-- ROW LEVEL SECURITY (RLS)
-- ===================================================================

-- Enable RLS on all tables
ALTER TABLE user_conversational_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_business_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_risks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_metric_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_company_context ENABLE ROW LEVEL SECURITY;

-- Policies: Users can only access their own data
CREATE POLICY "Users can view own conversational memory" ON user_conversational_memory
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own conversational memory" ON user_conversational_memory
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own business facts" ON user_business_facts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own business facts" ON user_business_facts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own business facts" ON user_business_facts
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own risks" ON user_risks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own risks" ON user_risks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own risks" ON user_risks
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own metric definitions" ON user_metric_definitions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own metric definitions" ON user_metric_definitions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own metric definitions" ON user_metric_definitions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own preferences" ON user_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences" ON user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences" ON user_preferences
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own company context" ON user_company_context
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own company context" ON user_company_context
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own company context" ON user_company_context
    FOR UPDATE USING (auth.uid() = user_id);
```

---

## 📝 Step 3: Update Your Requirements

Add to `Backend/requirements.txt`:

```txt
# Already have these (verify):
# langchain-google-genai
# supabase
# pydantic

# No new requirements needed!
```

---

## ✅ Step 4: Verification

After creating tables, verify in Supabase SQL Editor:

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'user_%memory%' OR table_name LIKE 'user_%';

-- Expected output:
-- user_conversational_memory
-- user_business_facts
-- user_risks
-- user_metric_definitions
-- user_preferences
-- user_company_context
```

---

## 🎯 Next Steps

Once you've completed Steps 1-4, we'll:

1. Create memory graph nodes
2. Integrate into Agents/graph.py
3. Test with sample queries

Let me know when you're ready!
