"""
Unit tests for services/etl/base_etl.py

Tests ETL utilities: storage paths, embedding queue, sync job management.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from collections import deque


class TestBuildStoragePath:
    """Tests for build_storage_path function."""

    def test_full_rbac_path(self):
        """Should build full RBAC path with org and team."""
        from services.etl.base_etl import build_storage_path

        result = build_storage_path(
            user_id="user-123",
            connector_type="jira",
            filename="issues.json",
            organization_id="org-456",
            team_id="team-789"
        )

        assert result == "org-456/team-789/jira/user-123/issues.json"

    def test_rbac_path_no_team(self):
        """Should use 'no-team' folder when team_id is None."""
        from services.etl.base_etl import build_storage_path

        result = build_storage_path(
            user_id="user-123",
            connector_type="google",
            filename="files.json",
            organization_id="org-456",
            team_id=None
        )

        assert result == "org-456/no-team/google/user-123/files.json"

    def test_legacy_path_no_org(self):
        """Should use legacy path when organization_id is None."""
        from services.etl.base_etl import build_storage_path

        result = build_storage_path(
            user_id="user-123",
            connector_type="asana",
            filename="tasks.json"
        )

        assert result == "user-123/asana/tasks.json"

    def test_different_connector_types(self):
        """Should work with various connector types."""
        from services.etl.base_etl import build_storage_path

        connectors = ["jira", "google", "asana", "microsoft-excel", "microsoft-teams"]

        for connector in connectors:
            result = build_storage_path(
                user_id="user-123",
                connector_type=connector,
                filename="data.json",
                organization_id="org-1"
            )
            assert connector in result
            assert "data.json" in result


class TestQueueEmbedding:
    """Tests for queue_embedding function."""

    def test_queue_embedding_basic(self):
        """Should add item to embedding queue."""
        from services.etl.base_etl import embedding_queue, queue_embedding

        # Clear the queue first
        embedding_queue.clear()

        queue_embedding(
            user_id="user-123",
            file_path="path/to/file.json",
            source_type="jira",
            source_id="PROJ-123"
        )

        assert len(embedding_queue) == 1
        item = embedding_queue[0]
        assert item["user_id"] == "user-123"
        assert item["file_path"] == "path/to/file.json"
        assert item["source_type"] == "jira"
        assert item["source_id"] == "PROJ-123"

    def test_queue_embedding_with_metadata(self):
        """Should include source metadata."""
        from services.etl.base_etl import embedding_queue, queue_embedding

        embedding_queue.clear()

        metadata = {"project_name": "Test Project", "issue_count": 42}

        queue_embedding(
            user_id="user-123",
            file_path="path/to/file.json",
            source_type="jira",
            source_metadata=metadata
        )

        item = embedding_queue[0]
        assert item["source_metadata"] == metadata

    def test_queue_multiple_items(self):
        """Should queue multiple items in order."""
        from services.etl.base_etl import embedding_queue, queue_embedding

        embedding_queue.clear()

        queue_embedding("user-1", "file1.json", "jira")
        queue_embedding("user-2", "file2.json", "google")
        queue_embedding("user-3", "file3.json", "asana")

        assert len(embedding_queue) == 3
        assert embedding_queue[0]["user_id"] == "user-1"
        assert embedding_queue[1]["user_id"] == "user-2"
        assert embedding_queue[2]["user_id"] == "user-3"


class TestProcessEmbeddingQueueBatch:
    """Tests for process_embedding_queue_batch function."""

    @pytest.mark.asyncio
    async def test_empty_queue(self):
        """Should handle empty queue gracefully."""
        from services.etl.base_etl import embedding_queue, process_embedding_queue_batch

        embedding_queue.clear()

        # Create mock module
        mock_module = MagicMock()
        mock_module.embed_and_store_file = AsyncMock(return_value={"status": "success"})

        with patch.dict("sys.modules", {"services.embedding_service": mock_module}):
            result = await process_embedding_queue_batch()

        assert result["processed"] == 0
        assert result["skipped"] == 0
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_processes_all_items(self):
        """Should process all items in queue."""
        from services.etl.base_etl import embedding_queue, queue_embedding, process_embedding_queue_batch

        embedding_queue.clear()
        queue_embedding("user-1", "file1.json", "jira")
        queue_embedding("user-2", "file2.json", "google")

        mock_embed = AsyncMock(return_value={"status": "success"})
        mock_module = MagicMock()
        mock_module.embed_and_store_file = mock_embed

        with patch.dict("sys.modules", {"services.embedding_service": mock_module}):
            result = await process_embedding_queue_batch()

        assert result["processed"] == 2
        assert mock_embed.call_count == 2
        assert len(embedding_queue) == 0  # Queue should be empty

    @pytest.mark.asyncio
    async def test_counts_skipped_items(self):
        """Should count skipped items correctly."""
        from services.etl.base_etl import embedding_queue, queue_embedding, process_embedding_queue_batch

        embedding_queue.clear()
        queue_embedding("user-1", "file1.json", "jira")
        queue_embedding("user-2", "file2.json", "google")

        mock_embed = AsyncMock(return_value={"status": "skipped"})
        mock_module = MagicMock()
        mock_module.embed_and_store_file = mock_embed

        with patch.dict("sys.modules", {"services.embedding_service": mock_module}):
            result = await process_embedding_queue_batch()

        assert result["processed"] == 0
        assert result["skipped"] == 2

    @pytest.mark.asyncio
    async def test_handles_failures(self):
        """Should count failed items and continue processing."""
        from services.etl.base_etl import embedding_queue, queue_embedding, process_embedding_queue_batch

        embedding_queue.clear()
        queue_embedding("user-1", "file1.json", "jira")
        queue_embedding("user-2", "file2.json", "google")

        mock_embed = AsyncMock(side_effect=Exception("Embedding failed"))
        mock_module = MagicMock()
        mock_module.embed_and_store_file = mock_embed

        with patch.dict("sys.modules", {"services.embedding_service": mock_module}):
            result = await process_embedding_queue_batch()

        assert result["failed"] == 2
        assert len(embedding_queue) == 0  # Queue should still be emptied


class TestSmartUploadAndEmbed:
    """Tests for smart_upload_and_embed function."""

    @pytest.mark.asyncio
    async def test_successful_upload(self):
        """Should upload file and queue for processing."""
        from services.etl.base_etl import embedding_queue

        embedding_queue.clear()

        with patch("services.etl.base_etl.supabase") as mock_supabase:
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage
            mock_storage.upload.return_value = MagicMock()

            from services.etl.base_etl import smart_upload_and_embed

            result = await smart_upload_and_embed(
                user_id="user-123",
                bucket_name="Kogna",
                file_path="test/file.json",
                content=b'{"test": "data"}',
                mime_type="application/json",
                source_type="jira",
                source_id="PROJ-123"
            )

        assert result["status"] == "queued"
        assert "uploaded and queued" in result["message"]
        assert len(embedding_queue) == 1

    @pytest.mark.asyncio
    async def test_upload_failure(self):
        """Should return error status on upload failure."""
        from services.etl.base_etl import embedding_queue

        embedding_queue.clear()

        with patch("services.etl.base_etl.supabase") as mock_supabase:
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage
            mock_storage.upload.side_effect = Exception("Upload failed")

            from services.etl.base_etl import smart_upload_and_embed

            result = await smart_upload_and_embed(
                user_id="user-123",
                bucket_name="Kogna",
                file_path="test/file.json",
                content=b'{"test": "data"}',
                mime_type="application/json",
                source_type="jira"
            )

        assert result["status"] == "error"
        assert "Upload failed" in result["message"]
        assert len(embedding_queue) == 0

    @pytest.mark.asyncio
    async def test_includes_rbac_metadata(self):
        """Should include org/team in metadata when provided."""
        from services.etl.base_etl import embedding_queue

        embedding_queue.clear()

        with patch("services.etl.base_etl.supabase") as mock_supabase:
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage

            from services.etl.base_etl import smart_upload_and_embed

            await smart_upload_and_embed(
                user_id="user-123",
                bucket_name="Kogna",
                file_path="test/file.json",
                content=b'{"test": "data"}',
                mime_type="application/json",
                source_type="jira",
                organization_id="org-456",
                team_id="team-789"
            )

        item = embedding_queue[0]
        assert item["source_metadata"]["organization_id"] == "org-456"
        assert item["source_metadata"]["team_id"] == "team-789"


class TestCreateSyncJob:
    """Tests for create_sync_job function."""

    @pytest.mark.asyncio
    async def test_creates_job_record(self):
        """Should create sync job and return job_id."""
        with patch("services.etl.base_etl.supabase") as mock_supabase:
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.insert.return_value = mock_table
            mock_table.execute.return_value = MagicMock(
                data=[{"id": "job-123"}]
            )

            from services.etl.base_etl import create_sync_job

            result = await create_sync_job(
                user_id="user-123",
                service="jira",
                organization_id="org-456",
                team_id="team-789"
            )

        assert result == "job-123"

    @pytest.mark.asyncio
    async def test_handles_db_error(self):
        """Should return None on database error."""
        with patch("services.etl.base_etl.supabase") as mock_supabase:
            mock_supabase.table.side_effect = Exception("DB error")

            from services.etl.base_etl import create_sync_job

            result = await create_sync_job(
                user_id="user-123",
                service="jira"
            )

        assert result is None


class TestCompleteSyncJob:
    """Tests for complete_sync_job function."""

    @pytest.mark.asyncio
    async def test_marks_job_completed(self):
        """Should update job status to completed."""
        with patch("services.etl.base_etl.supabase") as mock_supabase:
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock()

            from services.etl.base_etl import complete_sync_job

            await complete_sync_job(
                user_id="user-123",
                service="jira",
                success=True,
                files_count=10,
                skipped_count=5
            )

        # Verify update was called with correct status
        mock_table.update.assert_called_once()
        update_args = mock_table.update.call_args[0][0]
        assert update_args["status"] == "completed"
        assert update_args["files_processed"] == 10
        assert update_args["files_skipped"] == 5

    @pytest.mark.asyncio
    async def test_marks_job_failed(self):
        """Should update job status to failed with error message."""
        with patch("services.etl.base_etl.supabase") as mock_supabase:
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock()

            from services.etl.base_etl import complete_sync_job

            await complete_sync_job(
                user_id="user-123",
                service="jira",
                success=False,
                error="Connection timeout"
            )

        update_args = mock_table.update.call_args[0][0]
        assert update_args["status"] == "failed"
        assert "Connection timeout" in update_args["error_message"]


class TestEnsureValidToken:
    """Tests for ensure_valid_token function."""

    @pytest.mark.asyncio
    async def test_returns_valid_token(self):
        """Should return token if not expired."""
        import time

        with patch("services.etl.base_etl.supabase") as mock_supabase:
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.order.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.maybe_single.return_value = mock_table
            mock_table.execute.return_value = MagicMock(
                data={
                    "id": "conn-123",
                    "access_token": "valid-token",
                    "refresh_token": "refresh-token",
                    "expires_at": int(time.time()) + 3600  # Expires in 1 hour
                }
            )

            from services.etl.base_etl import ensure_valid_token

            result = await ensure_valid_token("user-123", "jira")

        assert result == "valid-token"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_connector(self):
        """Should return None when connector not found."""
        with patch("services.etl.base_etl.supabase") as mock_supabase:
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.order.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.maybe_single.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=None)

            from services.etl.base_etl import ensure_valid_token

            result = await ensure_valid_token("user-123", "jira")

        assert result is None


class TestGetUserContext:
    """Tests for get_user_context function."""

    @pytest.mark.asyncio
    async def test_returns_user_context(self):
        """Should return org_id and team_ids."""
        with patch("services.etl.base_etl.supabase") as mock_supabase:
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.order.return_value = mock_table
            mock_table.maybe_single.return_value = mock_table

            # First call for users table
            mock_table.execute.side_effect = [
                MagicMock(data={"organization_id": "org-123"}),
                MagicMock(data=[
                    {"team_id": "team-1", "is_primary": True},
                    {"team_id": "team-2", "is_primary": False}
                ])
            ]

            from services.etl.base_etl import get_user_context

            result = await get_user_context("user-123")

        assert result["organization_id"] == "org-123"
        assert result["team_id"] == "team-1"
        assert result["team_ids"] == ["team-1", "team-2"]

    @pytest.mark.asyncio
    async def test_handles_user_not_found(self):
        """Should return None values when user not found."""
        with patch("services.etl.base_etl.supabase") as mock_supabase:
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.maybe_single.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=None)

            from services.etl.base_etl import get_user_context

            result = await get_user_context("nonexistent-user")

        assert result["organization_id"] is None
        assert result["team_id"] is None
        assert result["team_ids"] == []
