-- ============================================================================
-- Migration 013: Add selected_file_ids column to user_connectors table
-- ============================================================================
-- This migration adds support for storing user-selected file IDs for
-- connectors (Google Drive, Jira, etc.), allowing users to choose specific
-- files to sync instead of syncing all files.
--
-- Column: selected_file_ids (JSONB)
-- - NULL value = sync all files (default behavior)
-- - Array of file IDs = sync only selected files
-- - Example: ["file_id_1", "file_id_2", "file_id_3"]
-- ============================================================================

-- Add selected_file_ids column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_connectors'
        AND column_name = 'selected_file_ids'
    ) THEN
        ALTER TABLE user_connectors
        ADD COLUMN selected_file_ids JSONB DEFAULT NULL;

        -- Add comment for documentation
        COMMENT ON COLUMN user_connectors.selected_file_ids IS
            'Array of file IDs to sync. NULL means sync all files. Example: ["file_id_1", "file_id_2"]';

        RAISE NOTICE 'Added selected_file_ids column to user_connectors table';
    ELSE
        RAISE NOTICE 'Column selected_file_ids already exists in user_connectors table';
    END IF;
END $$;

-- Create index for faster queries on connectors with file selection
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'user_connectors'
        AND indexname = 'idx_user_connectors_file_selection'
    ) THEN
        CREATE INDEX idx_user_connectors_file_selection
        ON user_connectors (user_id, service)
        WHERE selected_file_ids IS NOT NULL;

        RAISE NOTICE 'Created index idx_user_connectors_file_selection';
    ELSE
        RAISE NOTICE 'Index idx_user_connectors_file_selection already exists';
    END IF;
END $$;
