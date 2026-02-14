-- Migration 013: Pre-Cluster Classification (Tagging) - Tag Index for document_chunks
-- Adds index for efficient tag-constrained retrieval (TCRR)
-- The metadata column already exists from migration 006

-- =====================================================
-- 1. Ensure metadata column exists (idempotent)
-- =====================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'document_chunks'
        AND column_name = 'metadata'
    ) THEN
        ALTER TABLE document_chunks
        ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;

        RAISE NOTICE 'Added metadata column to document_chunks';
    ELSE
        RAISE NOTICE 'metadata column already exists in document_chunks';
    END IF;
END $$;

-- =====================================================
-- 2. Create index for tag-based filtering (TCRR)
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata_tag
ON document_chunks ((metadata->>'tag'));

COMMENT ON INDEX idx_document_chunks_metadata_tag IS 
'Supports tag-constrained retrieval. Query: metadata->>''tag'' = ''Technical''';

-- =====================================================
-- Migration Complete
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Migration 013: Tag Index - COMPLETED';
    RAISE NOTICE 'document_chunks.metadata supports tag queries';
    RAISE NOTICE '=================================================';
END $$;
