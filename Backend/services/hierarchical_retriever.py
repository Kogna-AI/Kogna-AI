# services/hierarchical_retriever.py
"""
Hierarchical Retriever for Intelligent Knowledge Navigation

Combines tree structure (super-notes) with vector search (leaf notes)
to provide the right level of detail for any query.

Strategies:
- hybrid: Search all levels, rank by relevance
- tree_first: Start at high levels, drill down if needed
- vector_only: Traditional flat vector search (fallback)
"""

import logging
from typing import List, Dict, Optional
from supabase_connect import get_supabase_manager
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

logging.basicConfig(level=logging.INFO)
supabase = get_supabase_manager().client

# Initialize embeddings
embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


class HierarchicalRetriever:
    """
    Intelligent retrieval using hierarchical tree structure.
    Combines tree navigation with vector search.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        logging.info(f"✓ HierarchicalRetriever initialized for user {user_id}")
    
    async def retrieve(
        self,
        query: str,
        max_results: int = 10,
        strategy: str = "hybrid"  # "hybrid", "tree_first", "vector_only"
    ) -> Dict:
        """
        Main retrieval method with multiple strategies.
        
        Args:
            query: User's question
            max_results: Maximum number of results
            strategy: Retrieval strategy to use
            
        Returns:
            {
                'results': List[Dict],  # Retrieved content
                'strategy_used': str,   # Which strategy was used
                'levels_searched': List[int],  # Which levels were searched
                'total_results': int
            }
        """
        
        # Generate query embedding
        query_embedding = embeddings_model.embed_query(query)
        
        if strategy == "hybrid":
            return await self._hybrid_retrieval(query, query_embedding, max_results)
        elif strategy == "tree_first":
            return await self._tree_first_retrieval(query, query_embedding, max_results)
        else:
            return await self._vector_only_retrieval(query, query_embedding, max_results)
    
    async def _hybrid_retrieval(
        self,
        query: str,
        query_embedding: List[float],
        max_results: int
    ) -> Dict:
        """
        HYBRID STRATEGY: Search all levels, rank by relevance + level.
        
        This is the RECOMMENDED approach!
        """
        
        print(f"\n🔍 HYBRID RETRIEVAL: {query[:60]}...")
        
        all_results = []
        
        # ═════════════════════════════════════════════════════════════
        # STEP 1: Search Super-Notes (Tree)
        # ═════════════════════════════════════════════════════════════
        
        # Search Root (Level 99) - Highest overview
        root_results = await self._search_level(
            level=99,
            query_embedding=query_embedding,
            limit=1
        )
        
        for result in root_results:
            all_results.append({
                **result,
                'source': 'super_note',
                'relevance_boost': 0.5,  # Lower for root (too general)
                'level': 99
            })
        
        # Search Level 2 (Themes)
        level2_results = await self._search_level(
            level=2,
            query_embedding=query_embedding,
            limit=3
        )
        
        for result in level2_results:
            all_results.append({
                **result,
                'source': 'super_note',
                'relevance_boost': 1.0,  # Good balance
                'level': 2
            })
        
        # Search Level 1 (Topics)
        level1_results = await self._search_level(
            level=1,
            query_embedding=query_embedding,
            limit=5
        )
        
        for result in level1_results:
            all_results.append({
                **result,
                'source': 'super_note',
                'relevance_boost': 1.2,  # Higher for specific topics
                'level': 1
            })
        
        # ═════════════════════════════════════════════════════════════
        # STEP 2: Search Leaf Notes (Detailed Content)
        # ═════════════════════════════════════════════════════════════
        
        leaf_results = await self._search_leaf_notes(
            query_embedding=query_embedding,
            limit=max_results
        )
        
        for result in leaf_results:
            all_results.append({
                **result,
                'source': 'leaf_note',
                'relevance_boost': 1.5,  # Highest for detailed content
                'level': 0
            })
        
        # ═════════════════════════════════════════════════════════════
        # STEP 3: Rank and Filter
        # ═════════════════════════════════════════════════════════════
        
        # Apply relevance boost
        for result in all_results:
            result['final_score'] = result['similarity'] * result['relevance_boost']
        
        # Sort by final score
        all_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Take top results
        top_results = all_results[:max_results]
        
        # ═════════════════════════════════════════════════════════════
        # STEP 4: Enrich with Context
        # ═════════════════════════════════════════════════════════════
        
        enriched_results = []
        for result in top_results:
            enriched = await self._enrich_with_context(result)
            enriched_results.append(enriched)
        
        print(f"   ✓ Retrieved {len(enriched_results)} results")
        print(f"     • Root: {len([r for r in top_results if r['level'] == 99])}")
        print(f"     • Level 2: {len([r for r in top_results if r['level'] == 2])}")
        print(f"     • Level 1: {len([r for r in top_results if r['level'] == 1])}")
        print(f"     • Leaves: {len([r for r in top_results if r['level'] == 0])}")
        
        return {
            'results': enriched_results,
            'strategy_used': 'hybrid',
            'levels_searched': [99, 2, 1, 0],
            'total_results': len(enriched_results)
        }
    
    async def _search_level(
        self,
        level: int,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Dict]:
        """
        Search super-notes at a specific level using vector similarity.
        """
        try:
            # Use RPC function for vector search
            result = supabase.rpc('match_super_notes', {
                'query_embedding': query_embedding,
                'match_count': limit,
                'p_user_id': self.user_id,
                'p_level': level
            }).execute()
            
            return result.data or []
        
        except Exception as e:
            logging.error(f"Error searching level {level}: {e}")
            return []
    
    async def _search_leaf_notes(
        self,
        query_embedding: List[float],
        limit: int = 10
    ) -> List[Dict]:
        """
        Search document_notes (leaf notes) using vector similarity.
        """
        try:
            # Use vector search on document_notes
            result = supabase.rpc('match_document_notes', {
                'query_embedding': query_embedding,
                'match_count': limit,
                'p_user_id': self.user_id
            }).execute()
            
            return result.data or []
        
        except Exception as e:
            logging.error(f"Error searching leaf notes: {e}")
            return []
    
    async def _enrich_with_context(self, result: Dict) -> Dict:
        """
        Enrich result with hierarchical context (parent/children info).
        """
        enriched = result.copy()
        
        if result['source'] == 'super_note':
            # Add parent context
            parent_id = result.get('parent_id')
            if parent_id:
                try:
                    parent = supabase.table('super_notes').select(
                        'title, summary'
                    ).eq('id', parent_id).maybe_single().execute()
                    
                    if parent.data:
                        enriched['parent_context'] = {
                            'title': parent.data['title'],
                            'summary': parent.data.get('summary', '')[:200]
                        }
                except Exception as e:
                    logging.warning(f"Could not fetch parent: {e}")
            
            # Add child count
            child_ids = result.get('child_note_ids', [])
            enriched['child_count'] = len(child_ids)
        
        return enriched
    
    async def _tree_first_retrieval(
        self,
        query: str,
        query_embedding: List[float],
        max_results: int
    ) -> Dict:
        """
        TREE-FIRST STRATEGY: Start broad, drill down if needed.
        """
        
        print(f"\n🌳 TREE-FIRST RETRIEVAL: {query[:60]}...")
        
        results = []
        levels_searched = []
        
        # Try Level 2 first (themes)
        level2_results = await self._search_level(2, query_embedding, limit=3)
        
        if level2_results and level2_results[0]['similarity'] > 0.7:
            # Good match at Level 2
            results.extend(level2_results)
            levels_searched.append(2)
            print(f"   ✓ Found good match at Level 2")
        else:
            # Drill down to Level 1
            level1_results = await self._search_level(1, query_embedding, limit=5)
            results.extend(level1_results)
            levels_searched.append(1)
            
            if not level1_results or level1_results[0]['similarity'] < 0.6:
                # Still not satisfied, go to leaves
                leaf_results = await self._search_leaf_notes(query_embedding, max_results)
                results.extend(leaf_results)
                levels_searched.append(0)
                print(f"   ✓ Drilled down to leaf notes")
        
        # Enrich and return
        enriched = [await self._enrich_with_context(r) for r in results[:max_results]]
        
        return {
            'results': enriched,
            'strategy_used': 'tree_first',
            'levels_searched': levels_searched,
            'total_results': len(enriched)
        }
    
    async def _vector_only_retrieval(
        self,
        query: str,
        query_embedding: List[float],
        max_results: int
    ) -> Dict:
        """
        VECTOR-ONLY: Traditional flat vector search (fallback).
        """
        
        print(f"\n📝 VECTOR-ONLY RETRIEVAL: {query[:60]}...")
        
        # Just search leaf notes
        leaf_results = await self._search_leaf_notes(
            query_embedding=query_embedding,
            limit=max_results
        )
        
        print(f"   ✓ Retrieved {len(leaf_results)} leaf notes")
        
        return {
            'results': leaf_results,
            'strategy_used': 'vector_only',
            'levels_searched': [0],
            'total_results': len(leaf_results)
        }
    
    async def navigate_tree(
        self,
        node_id: str,
        direction: str = "down"  # "up", "down", "siblings"
    ) -> Dict:
        """
        Navigate the tree structure (for exploration).
        
        Args:
            node_id: Current node ID
            direction: Navigation direction
            
        Returns:
            Related nodes based on direction
        """
        
        # Get current node
        current = supabase.table('super_notes').select(
            '*'
        ).eq('id', node_id).maybe_single().execute()
        
        if not current.data:
            return {'nodes': [], 'direction': direction}
        
        current_node = current.data
        
        if direction == "down":
            # Get children
            child_ids = current_node.get('child_note_ids', [])
            
            if current_node['level'] == 1:
                # Children are leaf notes
                children = supabase.table('document_notes').select(
                    'id, title, summary'
                ).in_('id', child_ids).execute()
            else:
                # Children are super-notes
                children = supabase.table('super_notes').select(
                    'id, title, summary, level'
                ).in_('id', child_ids).execute()
            
            return {
                'nodes': children.data or [],
                'direction': 'down',
                'current_node': current_node
            }
        
        elif direction == "up":
            # Get parent
            parent_id = current_node.get('parent_id')
            if not parent_id:
                return {'nodes': [], 'direction': 'up'}
            
            parent = supabase.table('super_notes').select(
                'id, title, summary, level'
            ).eq('id', parent_id).maybe_single().execute()
            
            return {
                'nodes': [parent.data] if parent.data else [],
                'direction': 'up',
                'current_node': current_node
            }
        
        elif direction == "siblings":
            # Get siblings (same parent)
            parent_id = current_node.get('parent_id')
            if not parent_id:
                return {'nodes': [], 'direction': 'siblings'}
            
            siblings = supabase.table('super_notes').select(
                'id, title, summary, level'
            ).eq('parent_id', parent_id).neq('id', node_id).execute()
            
            return {
                'nodes': siblings.data or [],
                'direction': 'siblings',
                'current_node': current_node
            }


# =============================================================================
# SQL FUNCTIONS NEEDED (add to Supabase)
# =============================================================================

SQL_FUNCTIONS = """
-- Function to search super-notes by vector similarity
CREATE OR REPLACE FUNCTION match_super_notes(
    query_embedding vector(768),
    match_count int DEFAULT 10,
    p_user_id uuid DEFAULT NULL,
    p_level int DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    title text,
    summary text,
    level int,
    parent_id uuid,
    child_note_ids uuid[],
    topics text[],
    key_facts text[],
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        super_notes.id,
        super_notes.title,
        super_notes.summary,
        super_notes.level,
        super_notes.parent_id,
        super_notes.child_note_ids,
        super_notes.topics,
        super_notes.key_facts,
        1 - (super_notes.embedding <=> query_embedding) AS similarity
    FROM super_notes
    WHERE 
        (p_user_id IS NULL OR super_notes.user_id = p_user_id)
        AND (p_level IS NULL OR super_notes.level = p_level)
        AND super_notes.embedding IS NOT NULL
    ORDER BY super_notes.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to search document_notes by vector similarity
CREATE OR REPLACE FUNCTION match_document_notes(
    query_embedding vector(768),
    match_count int DEFAULT 10,
    p_user_id uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    title text,
    summary text,
    key_facts text[],
    topics text[],
    file_path text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_notes.id,
        document_notes.title,
        document_notes.summary,
        document_notes.key_facts,
        document_notes.topics,
        document_notes.file_path,
        1 - (document_notes.note_embedding <=> query_embedding) AS similarity
    FROM document_notes
    WHERE 
        (p_user_id IS NULL OR document_notes.user_id = p_user_id)
        AND document_notes.note_embedding IS NOT NULL
    ORDER BY document_notes.note_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
"""

# Print SQL functions for easy setup
if __name__ == "__main__":
    print("="*70)
    print("SQL FUNCTIONS TO ADD TO SUPABASE:")
    print("="*70)
    print(SQL_FUNCTIONS)
    print("="*70)
    print("\nCopy the above SQL and run it in Supabase SQL Editor")