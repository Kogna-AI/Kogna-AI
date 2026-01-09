# File: services/tree_updater.py
"""
Smart Tree Updater - Only regenerates affected branches
Works with FileChangeDetector to identify what changed
"""

import logging
from typing import List, Dict, Set, Optional
from supabase_connect import get_supabase_manager

logging.basicConfig(level=logging.INFO)
supabase = get_supabase_manager().client


class TreeUpdater:
    """
    Intelligently updates tree structure when new data arrives.
    Only regenerates affected branches instead of rebuilding entire tree.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    async def on_new_notes(
        self, 
        new_note_ids: List[str],
        file_hash: Optional[str] = None
    ) -> Dict:
        """
        Called when new notes are added to document_notes.
        Marks affected tree branches for regeneration.
        
        Args:
            new_note_ids: List of newly created note IDs
            file_hash: Optional file hash to track which file changed
            
        Returns:
            {
                'status': 'success',
                'branches_marked': int,
                'nodes_marked': int,
                'affected_topics': List[str]
            }
        """
        try:
            print(f"\n SMART TREE UPDATE")
            print(f"   User: {self.user_id}")
            print(f"   New notes: {len(new_note_ids)}")
            
            # Step 1: Get new notes
            new_notes = await self._fetch_notes(new_note_ids)
            
            if not new_notes:
                print("     No notes found")
                return {
                    'status': 'no_notes',
                    'branches_marked': 0,
                    'nodes_marked': 0
                }
            
            # Step 2: Identify affected topics
            affected_topics = self._extract_topics(new_notes)
            print(f"\n    New notes cover topics: {affected_topics}")
            
            # Step 3: Find affected Level 1 super-notes
            affected_branches = await self._find_affected_branches(affected_topics)
            
            if not affected_branches:
                print("     No existing branches affected - tree needs full rebuild")
                return {
                    'status': 'full_rebuild_needed',
                    'branches_marked': 0,
                    'nodes_marked': 0,
                    'affected_topics': list(affected_topics)
                }
            
            print(f"   ✓ Found {len(affected_branches)} affected branches")
            
            # Step 4: Mark branches for regeneration
            total_nodes_marked = 0
            for branch in affected_branches:
                nodes_marked = await self._mark_branch_for_regeneration(
                    branch['id'],
                    branch['title']
                )
                total_nodes_marked += nodes_marked
            
            print(f"\n    MARKED FOR REGENERATION:")
            print(f"      • Branches: {len(affected_branches)}")
            print(f"      • Total nodes: {total_nodes_marked}")
            
            return {
                'status': 'success',
                'branches_marked': len(affected_branches),
                'nodes_marked': total_nodes_marked,
                'affected_topics': list(affected_topics)
            }
        
        except Exception as e:
            logging.error(f"Tree update failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': str(e),
                'branches_marked': 0,
                'nodes_marked': 0
            }
    
    async def on_file_modified(
        self,
        old_file_hash: str,
        new_file_hash: str,
        deleted_note_ids: List[str],
        new_note_ids: List[str]
    ) -> Dict:
        """
        Called when a file is modified.
        Handles both deletions and additions.
        
        Args:
            old_file_hash: Hash of old version
            new_file_hash: Hash of new version
            deleted_note_ids: Notes from old version (to be removed)
            new_note_ids: Notes from new version (to be added)
        """
        try:
            print(f"\n FILE MODIFICATION UPDATE")
            print(f"   Old hash: {old_file_hash[:16]}...")
            print(f"   New hash: {new_file_hash[:16]}...")
            print(f"   Deleted notes: {len(deleted_note_ids)}")
            print(f"   New notes: {len(new_note_ids)}")
            
            # Step 1: Find branches that contained deleted notes
            old_branches = await self._find_branches_containing_notes(deleted_note_ids)
            
            # Step 2: Find branches that will contain new notes
            new_notes = await self._fetch_notes(new_note_ids)
            new_topics = self._extract_topics(new_notes)
            new_branches = await self._find_affected_branches(new_topics)
            
            # Step 3: Combine - mark all affected branches
            all_affected = {b['id']: b for b in (old_branches + new_branches)}.values()
            
            total_nodes_marked = 0
            for branch in all_affected:
                nodes_marked = await self._mark_branch_for_regeneration(
                    branch['id'],
                    branch['title']
                )
                total_nodes_marked += nodes_marked
            
            print(f"\n    FILE MODIFICATION HANDLED:")
            print(f"      • Affected branches: {len(all_affected)}")
            print(f"      • Nodes marked: {total_nodes_marked}")
            
            return {
                'status': 'success',
                'branches_marked': len(all_affected),
                'nodes_marked': total_nodes_marked
            }
        
        except Exception as e:
            logging.error(f"File modification update failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _fetch_notes(self, note_ids: List[str]) -> List[Dict]:
        """Fetch notes by IDs"""
        try:
            result = supabase.table('document_notes').select(
                'id, title, chunk_group, topics, entities'
            ).in_('id', note_ids).execute()
            
            return result.data or []
        except Exception as e:
            logging.error(f"Error fetching notes: {e}")
            return []
    
    def _extract_topics(self, notes: List[Dict]) -> Set[str]:
        """
        Extract all topics from notes.
        Uses both:
        - topics array (if exists)
        - entities.topics (fallback)
        """
        topics = set()
        
        for note in notes:
            # From topics array
            note_topics = note.get('topics', [])
            if note_topics:
                topics.update(note_topics)
            
            # From entities.topics (fallback)
            entities = note.get('entities', {})
            if isinstance(entities, dict):
                entity_topics = entities.get('topics', [])
                if entity_topics:
                    topics.update(entity_topics)
        
        return topics
    
    async def _find_affected_branches(
        self, 
        topics: Set[str]
    ) -> List[Dict]:
        """
        Find Level 1 super-notes that match any of the topics.
        These are the branches that need regeneration.
        """
        try:
            if not topics:
                return []
            
            # Get all Level 1 super-notes for this user
            result = supabase.table('super_notes').select(
                'id, title, topics, level'
            ).eq('user_id', self.user_id).eq('level', 1).execute()
            
            level1_nodes = result.data or []
            
            # Find which ones have overlapping topics
            affected = []
            for node in level1_nodes:
                node_topics = set(node.get('topics', []))
                
                # If any topic overlaps, this branch is affected
                if node_topics & topics:  # Set intersection
                    affected.append({
                        'id': node['id'],
                        'title': node['title'],
                        'matching_topics': list(node_topics & topics)
                    })
                    print(f"      • {node['title']}: {list(node_topics & topics)}")
            
            return affected
        
        except Exception as e:
            logging.error(f"Error finding affected branches: {e}")
            return []
    
    async def _find_branches_containing_notes(
        self,
        note_ids: List[str]
    ) -> List[Dict]:
        """
        Find super-notes that contain any of the given note IDs.
        Used when notes are deleted.
        """
        try:
            if not note_ids:
                return []
            
            # Get all super-notes
            result = supabase.table('super_notes').select(
                'id, title, child_note_ids, level'
            ).eq('user_id', self.user_id).execute()
            
            all_nodes = result.data or []
            
            # Find which ones contain deleted notes
            affected = []
            note_id_set = set(note_ids)
            
            for node in all_nodes:
                child_ids = set(node.get('child_note_ids', []))
                
                # If any child is a deleted note, mark this branch
                if child_ids & note_id_set:
                    affected.append({
                        'id': node['id'],
                        'title': node['title'],
                        'level': node['level']
                    })
            
            return affected
        
        except Exception as e:
            logging.error(f"Error finding branches with notes: {e}")
            return []
    
    async def _mark_branch_for_regeneration(
        self,
        super_note_id: str,
        title: str
    ) -> int:
        """
        Mark a super-note and all its ancestors for regeneration.
        Uses the SQL function we created earlier.
        
        Returns:
            Number of nodes marked
        """
        try:
            # Call SQL function
            result = supabase.rpc('mark_branch_for_regeneration', {
                'p_super_note_id': super_note_id
            }).execute()
            
            nodes_marked = result.data if result.data else 0
            
            print(f"      ✓ Marked branch: {title} ({nodes_marked} nodes)")
            
            return nodes_marked
        
        except Exception as e:
            logging.error(f"Error marking branch: {e}")
            return 0
    
    async def check_tree_health(self) -> Dict:
        """
        Check tree health and consistency.
        Returns stats about the tree.
        """
        try:
            # Get all super-notes
            result = supabase.table('super_notes').select(
                'id, level, needs_regeneration, created_at, last_regenerated_at'
            ).eq('user_id', self.user_id).execute()
            
            nodes = result.data or []
            
            # Calculate stats
            stats = {
                'total_nodes': len(nodes),
                'nodes_needing_regen': sum(1 for n in nodes if n.get('needs_regeneration')),
                'levels': {},
                'oldest_regen': None,
                'newest_regen': None
            }
            
            # Count by level
            for node in nodes:
                level = node.get('level', 0)
                stats['levels'][level] = stats['levels'].get(level, 0) + 1
            
            return {
                'status': 'healthy' if stats['nodes_needing_regen'] == 0 else 'needs_update',
                'stats': stats
            }
        
        except Exception as e:
            logging.error(f"Error checking tree health: {e}")
            return {'status': 'error', 'message': str(e)}


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

async def example_usage():
    """Example of how to use TreeUpdater"""
    
    user_id = "your-user-id"
    updater = TreeUpdater(user_id)
    
    # Scenario 1: New notes added
    new_note_ids = ["note-1", "note-2", "note-3"]
    result = await updater.on_new_notes(new_note_ids)
    print(f"Result: {result}")
    
    # Scenario 2: File modified
    result = await updater.on_file_modified(
        old_file_hash="abc123",
        new_file_hash="def456",
        deleted_note_ids=["old-1", "old-2"],
        new_note_ids=["new-1", "new-2", "new-3"]
    )
    print(f"Result: {result}")
    
    # Scenario 3: Check tree health
    health = await updater.check_tree_health()
    print(f"Tree health: {health}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())