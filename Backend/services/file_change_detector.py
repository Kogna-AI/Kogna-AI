# File: services/file_change_detector.py

import hashlib
import logging
from typing import Optional, Dict, Tuple
from supabase_connect import get_supabase_manager

supabase = get_supabase_manager().client
logging.basicConfig(level=logging.INFO)


class FileChangeDetector:
    """
    Detects file changes and determines if re-processing is needed.
    """
    
    @staticmethod
    def compute_file_hash(content: bytes) -> str:
        """Compute SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def compute_chunk_hash(text: str) -> str:
        """Compute SHA-256 hash of chunk text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    async def check_file_status(
        self, 
        user_id: str, 
        file_path: str,
        current_hash: str,
        file_size: int,
        source_type: str,
        source_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Check if file needs processing.
        
        Returns:
            {
                'status': 'new' | 'unchanged' | 'modified',
                'file_id': UUID (if exists),
                'previous_hash': str (if exists),
                'action': 'process' | 'skip' | 'update'
            }
        """
        try:
            # Check if file exists in registry
            result = supabase.table('ingested_files') \
                .select('*') \
                .eq('user_id', user_id) \
                .eq('file_path', file_path) \
                .maybe_single() \
                .execute()
            
            existing = result.data
            
            if not existing:
                # New file
                logging.info(f"🆕 NEW FILE: {file_path}")
                return {
                    'status': 'new',
                    'file_id': None,
                    'previous_hash': None,
                    'action': 'process'
                }
            
            # File exists - compare hashes
            if existing['file_hash'] == current_hash:
                # Unchanged
                logging.info(f"✓ UNCHANGED: {file_path} (hash: {current_hash[:8]}...)")
                return {
                    'status': 'unchanged',
                    'file_id': existing['id'],
                    'previous_hash': existing['file_hash'],
                    'action': 'skip'
                }
            else:
                # Modified
                logging.info(f"🔄 MODIFIED: {file_path}")
                logging.info(f"   Old hash: {existing['file_hash'][:8]}...")
                logging.info(f"   New hash: {current_hash[:8]}...")
                return {
                    'status': 'modified',
                    'file_id': existing['id'],
                    'previous_hash': existing['file_hash'],
                    'action': 'update'
                }
        
        except Exception as e:
            logging.error(f"Error checking file status: {e}")
            return {
                'status': 'error',
                'file_id': None,
                'previous_hash': None,
                'action': 'process'  # Default to processing on error
            }
    
    async def register_file(
        self,
        user_id: str,
        file_path: str,
        file_name: str,
        file_hash: str,
        file_size: int,
        source_type: str,
        source_id: Optional[str] = None,
        source_metadata: Optional[Dict] = None,
        last_modified_at: Optional[str] = None
    ) -> str:
        """
        Register new file or update existing file record.
        
        Returns:
            file_id (UUID)
        """
        try:
            # Upsert file record
            record = {
                'user_id': user_id,
                'file_path': file_path,
                'file_name': file_name,
                'file_hash': file_hash,
                'file_size': file_size,
                'source_type': source_type,
                'source_id': source_id,
                'source_metadata': source_metadata or {},
                'last_modified_at': last_modified_at,
                'last_ingested_at': 'now()',
                'embedding_status': 'processing'
            }
            
            result = supabase.table('ingested_files') \
                .upsert(record, on_conflict='user_id,file_path') \
                .execute()
            
            file_id = result.data[0]['id']
            logging.info(f"📝 Registered file: {file_path} (ID: {file_id})")
            return file_id
        
        except Exception as e:
            logging.error(f"Error registering file: {e}")
            raise
    
    async def update_file_processing_status(
        self,
        file_id: str,
        status: str,
        chunk_count: int = 0,
        note_count: int = 0
    ):
        """Update file processing status"""
        try:
            supabase.table('ingested_files') \
                .update({
                    'embedding_status': status,
                    'chunk_count': chunk_count,
                    'note_count': note_count
                }) \
                .eq('id', file_id) \
                .execute()
            
            logging.info(f"✓ Updated file status: {status} ({chunk_count} chunks, {note_count} notes)")
        
        except Exception as e:
            logging.error(f"Error updating file status: {e}")
    
    async def delete_file_chunks_and_notes(
        self,
        user_id: str,
        old_file_hash: str
    ):
        """
        Delete all chunks and notes for a file based on its hash.
        Used when file is modified - deletes old version data.
        """
        try:
            # Delete chunks by file_hash
            chunk_result = supabase.table('document_chunks') \
                .delete() \
                .eq('user_id', user_id) \
                .eq('file_hash', old_file_hash) \
                .execute()
            
            chunks_deleted = len(chunk_result.data) if chunk_result.data else 0
            
            # Delete notes by file_hash
            note_result = supabase.table('document_notes') \
                .delete() \
                .eq('user_id', user_id) \
                .eq('file_hash', old_file_hash) \
                .execute()
            
            notes_deleted = len(note_result.data) if note_result.data else 0
            
            logging.info(f"🗑️  Deleted old data for hash {old_file_hash[:8]}...: {chunks_deleted} chunks, {notes_deleted} notes")
            
            return {
                'chunks_deleted': chunks_deleted,
                'notes_deleted': notes_deleted
            }
        
        except Exception as e:
            logging.error(f"Error deleting file data: {e}")
            return {'chunks_deleted': 0, 'notes_deleted': 0}
    
    async def get_file_info(
        self,
        user_id: str,
        file_path: str
    ) -> Optional[Dict]:
        """Get file information from registry"""
        try:
            result = supabase.table('ingested_files') \
                .select('*') \
                .eq('user_id', user_id) \
                .eq('file_path', file_path) \
                .maybe_single() \
                .execute()
            
            return result.data
        
        except Exception as e:
            logging.error(f"Error getting file info: {e}")
            return None
    
    async def get_files_by_source(
        self,
        user_id: str,
        source_type: str,
        source_id: Optional[str] = None
    ) -> list:
        """Get all files from a specific source"""
        try:
            query = supabase.table('ingested_files') \
                .select('*') \
                .eq('user_id', user_id) \
                .eq('source_type', source_type)
            
            if source_id:
                query = query.eq('source_id', source_id)
            
            result = query.execute()
            return result.data or []
        
        except Exception as e:
            logging.error(f"Error getting files by source: {e}")
            return []