-- ============================================================================
-- Migration 013: Add Session Metadata for Multi-Session History
-- ============================================================================
-- Purpose: Add metadata columns to sessions table for session list display,
--          sorting, and preview. Creates indexes and triggers for auto-updates.
-- Date: 2026-02-13
-- ============================================================================

-- ============================================================================
-- STEP 1: ADD METADATA COLUMNS TO SESSIONS TABLE
-- ============================================================================

ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS last_message_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS message_count INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS preview_text TEXT,
ADD COLUMN IF NOT EXISTS auto_title TEXT;

-- ============================================================================
-- STEP 2: CREATE INDEXES FOR OPTIMIZED QUERIES
-- ============================================================================

-- Index for sorting sessions by user and last activity
CREATE INDEX IF NOT EXISTS idx_sessions_user_last_message
ON sessions(user_id, last_message_at DESC NULLS LAST);

-- Index for sorting by creation date (verify it exists)
CREATE INDEX IF NOT EXISTS idx_sessions_user_created
ON sessions(user_id, created_at DESC);

-- Index for message retrieval by session
CREATE INDEX IF NOT EXISTS idx_messages_session_created
ON messages(session_id, created_at ASC);

-- ============================================================================
-- STEP 3: BACKFILL EXISTING DATA
-- ============================================================================

-- Backfill last_message_at from messages table
UPDATE sessions s
SET last_message_at = (
    SELECT MAX(created_at)
    FROM messages m
    WHERE m.session_id = s.id
)
WHERE last_message_at IS NULL;

-- Backfill message_count
UPDATE sessions s
SET message_count = (
    SELECT COUNT(*)
    FROM messages m
    WHERE m.session_id = s.id
)
WHERE message_count = 0 OR message_count IS NULL;

-- Backfill preview_text (first user message content)
UPDATE sessions s
SET preview_text = (
    SELECT content
    FROM messages m
    WHERE m.session_id = s.id AND m.role = 'user'
    ORDER BY created_at ASC
    LIMIT 1
)
WHERE preview_text IS NULL;

-- Backfill auto_title (first 50 chars of preview text)
UPDATE sessions s
SET auto_title = LEFT(preview_text, 50)
WHERE auto_title IS NULL AND preview_text IS NOT NULL;

-- ============================================================================
-- STEP 4: CREATE TRIGGER FUNCTION FOR AUTO-UPDATES
-- ============================================================================

-- Function to update session metadata when new message is inserted
CREATE OR REPLACE FUNCTION update_session_metadata()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions
    SET
        message_count = message_count + 1,
        last_message_at = NEW.created_at,
        -- Set preview and title from first user message (only if not already set)
        preview_text = COALESCE(
            preview_text,
            CASE WHEN NEW.role = 'user' THEN NEW.content END
        ),
        auto_title = COALESCE(
            auto_title,
            CASE WHEN NEW.role = 'user' THEN LEFT(NEW.content, 50) END
        )
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger (drop first if exists to allow re-running migration)
DROP TRIGGER IF EXISTS trg_update_session_metadata ON messages;

CREATE TRIGGER trg_update_session_metadata
AFTER INSERT ON messages
FOR EACH ROW EXECUTE FUNCTION update_session_metadata();

-- ============================================================================
-- STEP 5: VERIFICATION QUERIES
-- ============================================================================

-- Check new columns exist
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'sessions'
  AND column_name IN ('last_message_at', 'message_count', 'preview_text', 'auto_title')
ORDER BY column_name;

-- Check indexes were created
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('sessions', 'messages')
  AND indexname LIKE '%session%'
ORDER BY tablename, indexname;

-- Check trigger was created
SELECT
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_name = 'trg_update_session_metadata';

-- Sample session data with new fields
SELECT
    id,
    user_id,
    title,
    auto_title,
    message_count,
    last_message_at,
    LEFT(preview_text, 50) as preview_snippet,
    created_at
FROM sessions
ORDER BY last_message_at DESC NULLS LAST
LIMIT 5;

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================

-- Uncomment to rollback:
/*
DROP TRIGGER IF EXISTS trg_update_session_metadata ON messages;
DROP FUNCTION IF EXISTS update_session_metadata();

ALTER TABLE sessions
DROP COLUMN IF EXISTS last_message_at,
DROP COLUMN IF EXISTS message_count,
DROP COLUMN IF EXISTS preview_text,
DROP COLUMN IF EXISTS auto_title;

DROP INDEX IF EXISTS idx_sessions_user_last_message;
DROP INDEX IF EXISTS idx_sessions_user_created;
DROP INDEX IF EXISTS idx_messages_session_created;
*/

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
