# services/tree_builder.py
"""
Hierarchical Tree Builder for Knowledge Organization

Builds multi-level tree structure from existing clustered notes.
Uses SEMANTIC TOPICS (not chunk_group) for proper cross-document clustering.
Uses SuperNoteGenerator for strategic insights (not just indexing).

Architecture:
    Level 0: Leaf notes (existing document_notes)
    Level 1: Topic super-notes (aggregate notes by semantic topic)
    Level 2: Theme super-notes (cluster related topics)
    Level 99: Root (overall knowledge overview)

Example:
    16 leaf notes across 3 documents:
    
    Level 99 (Root):
    └── "Kogna AI: Capital-Efficient Pre-Seed Strategy"
    
    Level 2 (Themes):
    ├── "Financial Strategy & Growth"
    └── "Operations & Team"
    
    Level 1 (Topics):
    ├── "Finance" (5 notes from different docs)
    ├── "Team" (4 notes from different docs)
    └── "Product" (7 notes from different docs)
    
    Level 0 (Leaves):
    ├── Doc1: "Q3 Revenue" (topic: finance)
    ├── Doc2: "Investor Meetings" (topic: finance)
    ├── Doc1: "Team Growth" (topic: team)
    ├── Doc3: "Hiring Plan" (topic: team)
    └── ... (16 total)
"""

import logging
import time
from typing import List, Dict, Optional
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from supabase_connect import get_supabase_manager

# Import both generators
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Ai_agents.note_generator_agent import DocumentNoteGenerator
from Ai_agents.super_note_generator_agent import SuperNoteGenerator

logging.basicConfig(level=logging.INFO)

# Initialize clients
supabase = get_supabase_manager().client


class HierarchicalTreeBuilder:
    """
    Builds hierarchical tree structure with SYNTHESIS (not indexing)
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.supabase = supabase
        
        # Two different generators for two different jobs
        self.note_generator = DocumentNoteGenerator()  # For leaf notes (not used here)
        self.super_note_generator = SuperNoteGenerator()  # For super-notes (synthesis!)
        
        print("✓ Tree builder initialized with SuperNoteGenerator")
    
    async def build_tree(self) -> Dict:
        """
        Main entry point: Build complete tree from leaf notes to root
        
        Returns:
            {
                'root_id': UUID,
                'levels': int,
                'nodes_created': int,
                'structure': {...}
            }
        """
        
        print(f"\n{'='*70}")
        print(f" BUILDING HIERARCHICAL TREE")
        print(f"   User: {self.user_id}")
        print(f"{'='*70}\n")
        
        try:
            # ================================================================
            # STEP 1: Load existing leaf notes (Level 0)
            # ================================================================
            
            print(" Step 1: Loading leaf notes...")
            leaf_notes = await self._load_leaf_notes()
            
            if not leaf_notes:
                print("     No notes found for this user")
                return {
                    'status': 'error',
                    'message': 'No notes found'
                }
            
            print(f"   ✓ Loaded {len(leaf_notes)} leaf notes\n")
            
            # ================================================================
            # STEP 2: Group notes by SEMANTIC TOPIC (cross-document)
            # ================================================================
            
            print("🔍 Step 2: Grouping notes by semantic topics...")
            topic_groups = self._group_notes_by_topic(leaf_notes)
            
            print(f"   ✓ Found {len(topic_groups)} semantic topic groups")
            for topic, notes in sorted(topic_groups.items()):
                print(f"     • '{topic}': {len(notes)} notes")
            print()
            
            # ================================================================
            # STEP 3: Create Level 1 super-notes (Topic syntheses)
            # ================================================================
            
            print(" Step 3: Creating Level 1 super-notes (Topics)...")
            level1_nodes = await self._create_level1_super_notes(topic_groups)
            
            print(f"   ✓ Created {len(level1_nodes)} Level 1 super-notes\n")
            
            # ================================================================
            # STEP 4: Build higher levels hierarchically
            # ================================================================
            
            current_level_nodes = level1_nodes
            current_level = 2
            all_nodes_created = len(level1_nodes)
            
            # Continue building levels until we reach root (1 node)
            while len(current_level_nodes) > 1:
                print(f" Step {current_level + 2}: Creating Level {current_level} super-notes...")
                
                next_level_nodes = await self._create_next_level(
                    current_level_nodes, 
                    current_level
                )
                
                print(f"   ✓ Created {len(next_level_nodes)} Level {current_level} super-notes\n")
                
                all_nodes_created += len(next_level_nodes)
                current_level_nodes = next_level_nodes
                current_level += 1
                
                # Safety: prevent infinite loops
                if current_level > 10:
                    print("     Max depth reached, creating root manually")
                    break
            
            # ================================================================
            # STEP 5: Create root node (if not already single node)
            # ================================================================
            
            if len(current_level_nodes) > 1:
                print(f" Step {current_level + 2}: Creating Root node...")
                root_id = await self._create_root_node(current_level_nodes)
                all_nodes_created += 1
            else:
                root_id = current_level_nodes[0]['id']
                # Mark as root
                self.supabase.table('super_notes').update({
                    'is_root': True,
                    'level': 99
                }).eq('id', root_id).execute()
            
            print(f"   ✓ Root node created: {root_id}\n")
            
            # ================================================================
            # STEP 6: Build structure summary
            # ================================================================
            
            structure = await self._build_structure_summary(root_id)
            
            print(f"{'='*70}")
            print(f" TREE BUILT SUCCESSFULLY!")
            print(f"   Root ID: {root_id}")
            print(f"   Total Levels: {current_level}")
            print(f"   Nodes Created: {all_nodes_created}")
            print(f"   Leaf Notes: {len(leaf_notes)}")
            print(f"{'='*70}\n")
            
            return {
                'status': 'success',
                'root_id': root_id,
                'levels': current_level,
                'nodes_created': all_nodes_created,
                'leaf_notes': len(leaf_notes),
                'structure': structure
            }
            
        except Exception as e:
            logging.error(f" Tree building failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _load_leaf_notes(self) -> List[Dict]:
        """
        Load all document_notes for this user.
        These are Level 0 (leaf nodes).
        """
        
        response = self.supabase.table('document_notes').select(
            'id, title, summary, key_facts, entities, '
            'chunk_group, note_embedding, topics, '
            'file_path, created_at'
        ).eq('user_id', self.user_id).execute()
        
        notes = response.data
        
        # Filter out notes without embeddings
        valid_notes = [n for n in notes if n.get('note_embedding')]
        
        if len(valid_notes) < len(notes):
            print(f"     Filtered out {len(notes) - len(valid_notes)} notes without embeddings")
        
        return valid_notes
    
    def _group_notes_by_topic(self, notes: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group notes by SEMANTIC TOPICS (not chunk_group).
        
        This enables proper cross-document clustering where notes about
        the same topic (e.g., 'finance') from different documents are
        grouped together.
        
        OLD WAY (WRONG):
            Group by chunk_group → Each doc has chunk_group=0
            → All notes mixed incorrectly
        
        NEW WAY (CORRECT):
            Group by semantic topic → Find notes about 'finance'
            → Proper cross-document grouping
        """
        from collections import defaultdict
        
        topic_groups = defaultdict(list)
        
        for note in notes:
            # Extract topics (try multiple sources)
            topics = note.get('topics', [])
            
            # Fallback: try entities.topics
            if not topics:
                entities = note.get('entities', {})
                topics = entities.get('topics', [])
            
            # Last resort: categorize as general
            if not topics:
                topics = ['general']
            
            # Use primary topic (first one) and normalize
            primary_topic = topics[0].lower().strip()
            
            # Group by this topic
            topic_groups[primary_topic].append(note)
        
        return dict(topic_groups)
    
    async def _create_level1_super_notes(self, topic_groups: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Create Level 1 super-notes by SYNTHESIZING notes from each topic.
        
        Uses SuperNoteGenerator for insights (not just indexing).
        """
        
        level1_nodes = []
        
        for idx, (topic, child_notes) in enumerate(sorted(topic_groups.items()), 1):
            print(f"   [{idx}/{len(topic_groups)}] Topic '{topic}' ({len(child_notes)} notes)...", end=" ")
            
            try:
                # Get parent context (none for Level 1)
                parent_context = None
                
                # Generate SYNTHESIS super-note
                print("🧠", end=" ")
                
                note_content = self.super_note_generator.generate_super_note(
                    child_notes=child_notes,
                    level=1,
                    parent_context=parent_context
                )
                
                # Extract content
                super_note_title = note_content.get('title', f'Topic: {topic.title()}')
                super_note_summary = note_content.get('summary', '')
                
                # Combine insights into key_facts
                key_insights = note_content.get('key_insights', [])
                implications = note_content.get('strategic_implications', [])
                patterns = note_content.get('patterns', [])
                trends = note_content.get('trends', [])
                key_facts_raw = note_content.get('key_facts', [])
                
                super_note_key_facts = []
                
                if key_insights:
                    super_note_key_facts.extend([f" {i}" for i in key_insights[:3]])
                if patterns:
                    super_note_key_facts.extend([f" {p}" for p in patterns[:2]])
                if implications:
                    super_note_key_facts.extend([f" {i}" for i in implications[:2]])
                if trends:
                    super_note_key_facts.extend([f" {t}" for t in trends[:2]])
                if key_facts_raw:
                    super_note_key_facts.extend([f" {f}" for f in key_facts_raw[:2]])
                
                # Collect topics from children
                all_topics = set()
                for child in child_notes:
                    child_topics = child.get('topics', [])
                    if child_topics:
                        all_topics.update(child_topics)
                
                super_note_topics = list(all_topics)[:5]
                
                # Create embedding
                print("🔗", end=" ")
                
                note_text_for_embedding = f"""
{super_note_title}

{super_note_summary}

Insights:
{chr(10).join(super_note_key_facts)}

Topics: {', '.join(super_note_topics)}
                """.strip()
                
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                
                embeddings_model = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=os.getenv("GOOGLE_API_KEY")
                )
                
                embedding = embeddings_model.embed_query(note_text_for_embedding)
                
                # Store in database
                node_id = await self._store_super_note(
                    title=super_note_title,
                    summary=super_note_summary,
                    key_facts=super_note_key_facts,
                    topics=super_note_topics,
                    child_note_ids=[n['id'] for n in child_notes],
                    level=1,
                    parent_id=None,
                    embedding=embedding,
                    is_root=False
                )
                
                level1_nodes.append({
                    'id': node_id,
                    'level': 1,
                    'embedding': embedding,
                    'child_count': len(child_notes),
                    'title': super_note_title
                })
                
                print(f"✓")
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"✗ Error: {e}")
                logging.error(f"Failed to create super-note for topic '{topic}': {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return level1_nodes
    
    async def _create_next_level(self, current_nodes: List[Dict], level: int) -> List[Dict]:
        """
        Create next level by clustering current level nodes.
        Uses SuperNoteGenerator for synthesis.
        
        Example:
            5 Level 1 nodes → Cluster into 2 groups → 2 Level 2 nodes
        """
        
        if len(current_nodes) == 1:
            return current_nodes
        
        # Extract embeddings
        embeddings = np.array([node['embedding'] for node in current_nodes])
        
        # Determine number of clusters for this level
        # Aim to reduce nodes by ~50% each level
        n_clusters = max(1, len(current_nodes) // 2)
        n_clusters = min(n_clusters, 5)  # Cap at 5 groups per level
        
        if n_clusters == 1:
            # Only one cluster - these nodes will become children of root
            return current_nodes
        
        print(f"   Clustering {len(current_nodes)} nodes into {n_clusters} groups...")
        
        # Hierarchical clustering
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric='cosine',
            linkage='average'
        )
        
        labels = clustering.fit_predict(embeddings)
        
        # Group nodes by cluster
        groups = {}
        for idx, node in enumerate(current_nodes):
            label = labels[idx]
            if label not in groups:
                groups[label] = []
            groups[label].append(node)
        
        # Create super-note for each group
        next_level_nodes = []
        
        for group_id, nodes_in_group in groups.items():
            print(f"   Group {group_id}: {len(nodes_in_group)} nodes...", end=" ")
            
            try:
                # Fetch the actual super-notes (children) with their content
                child_super_notes = await self._fetch_super_notes_by_ids(
                    [n['id'] for n in nodes_in_group]
                )
                
                if not child_super_notes:
                    print("✗ No child notes found")
                    continue
                
                # Get parent context (none for now, could add later)
                parent_context = None
                
                # Generate SYNTHESIS super-note
                print("🧠", end=" ")
                
                note_content = self.super_note_generator.generate_super_note(
                    child_notes=child_super_notes,
                    level=level,
                    parent_context=parent_context
                )
                
                # Extract content
                super_note_title = note_content.get('title', f'Level {level} Theme')
                super_note_summary = note_content.get('summary', '')
                
                # Combine insights
                key_insights = note_content.get('key_insights', [])
                implications = note_content.get('strategic_implications', [])
                patterns = note_content.get('patterns', [])
                trends = note_content.get('trends', [])
                
                super_note_key_facts = []
                
                if key_insights:
                    super_note_key_facts.extend([f" {i}" for i in key_insights[:3]])
                if patterns:
                    super_note_key_facts.extend([f" {p}" for p in patterns[:2]])
                if implications:
                    super_note_key_facts.extend([f" {i}" for i in implications[:2]])
                if trends:
                    super_note_key_facts.extend([f" {t}" for t in trends[:2]])
                
                # Collect topics
                all_topics = set()
                for child in child_super_notes:
                    child_topics = child.get('topics', [])
                    if child_topics:
                        all_topics.update(child_topics)
                
                super_note_topics = list(all_topics)[:5]
                
                # Create embedding
                print("🔗", end=" ")
                
                note_text_for_embedding = f"""
{super_note_title}

{super_note_summary}

Insights:
{chr(10).join(super_note_key_facts)}

Topics: {', '.join(super_note_topics)}
                """.strip()
                
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                
                embeddings_model = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=os.getenv("GOOGLE_API_KEY")
                )
                
                embedding = embeddings_model.embed_query(note_text_for_embedding)
                
                # Store
                node_id = await self._store_super_note(
                    title=super_note_title,
                    summary=super_note_summary,
                    key_facts=super_note_key_facts,
                    topics=super_note_topics,
                    child_note_ids=[n['id'] for n in nodes_in_group],
                    level=level,
                    parent_id=None,
                    embedding=embedding,
                    is_root=False
                )
                
                next_level_nodes.append({
                    'id': node_id,
                    'level': level,
                    'embedding': embedding,
                    'child_count': len(nodes_in_group),
                    'title': super_note_title
                })
                
                print(f"✓")
                time.sleep(0.5)
                
            except Exception as e:
                print(f"✗ Error: {e}")
                logging.error(f"Failed to create Level {level} super-note: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return next_level_nodes
    
    async def _create_root_node(self, final_nodes: List[Dict]) -> str:
        """
        Create root node from remaining nodes.
        Uses SuperNoteGenerator with level=99 for executive summary.
        """
        
        print("   Creating root synthesis...", end=" ")
        
        # Fetch child super-notes
        child_super_notes = await self._fetch_super_notes_by_ids(
            [n['id'] for n in final_nodes]
        )
        
        # Generate ROOT super-note (executive summary)
        print("🧠", end=" ")
        
        note_content = self.super_note_generator.generate_super_note(
            child_notes=child_super_notes,
            level=99,  # Special level for root
            parent_context=None
        )
        
        # Extract content
        super_note_title = note_content.get('title', 'Knowledge Overview')
        super_note_summary = note_content.get('summary', '')
        
        # Combine insights
        key_insights = note_content.get('key_insights', [])
        implications = note_content.get('strategic_implications', [])
        patterns = note_content.get('patterns', [])
        
        super_note_key_facts = []
        
        if key_insights:
            super_note_key_facts.extend([f" {i}" for i in key_insights[:5]])
        if patterns:
            super_note_key_facts.extend([f" {p}" for p in patterns[:3]])
        if implications:
            super_note_key_facts.extend([f" {i}" for i in implications[:3]])
        
        # Collect all topics
        all_topics = set()
        for child in child_super_notes:
            child_topics = child.get('topics', [])
            if child_topics:
                all_topics.update(child_topics)
        
        super_note_topics = list(all_topics)[:10]  # More topics for root
        
        # Create embedding
        print("🔗", end=" ")
        
        note_text_for_embedding = f"""
{super_note_title}

{super_note_summary}

Key Insights:
{chr(10).join(super_note_key_facts)}

Topics: {', '.join(super_note_topics)}
        """.strip()
        
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        embedding = embeddings_model.embed_query(note_text_for_embedding)
        
        # Store root node
        root_id = await self._store_super_note(
            title=super_note_title,
            summary=super_note_summary,
            key_facts=super_note_key_facts,
            topics=super_note_topics,
            child_note_ids=[n['id'] for n in final_nodes],
            level=99,
            parent_id=None,
            embedding=embedding,
            is_root=True
        )
        
        print("✓")
        
        return root_id
    
    async def _store_super_note(
        self,
        title: str,
        summary: str,
        key_facts: List[str],
        topics: List[str],
        child_note_ids: List[str],
        level: int,
        parent_id: Optional[str],
        embedding: List[float],
        is_root: bool = False
    ) -> str:
        """
        Store super-note in database
        """
        
        result = self.supabase.table('super_notes').insert({
            'user_id': self.user_id,
            'level': level,
            'title': title,
            'summary': summary,
            'key_facts': key_facts,
            'topics': topics,
            'child_note_ids': child_note_ids,
            'parent_id': parent_id,
            'embedding': embedding,
            'is_root': is_root,
            'needs_regeneration': False,
            'regeneration_priority': 0.0
        }).execute()
        
        return result.data[0]['id']
    
    async def _fetch_super_notes_by_ids(self, node_ids: List[str]) -> List[Dict]:
        """
        Fetch super-notes by IDs (for building higher levels)
        """
        
        if not node_ids:
            return []
        
        result = self.supabase.table('super_notes').select(
            'id, title, summary, key_facts, topics'
        ).in_('id', node_ids).execute()
        
        return result.data or []
    
    async def _build_structure_summary(self, root_id: str) -> Dict:
        """
        Build a summary of the tree structure
        """
        
        # Count nodes at each level
        levels_count = {}
        
        result = self.supabase.table('super_notes').select(
            'level'
        ).eq('user_id', self.user_id).execute()
        
        for node in result.data:
            level = node['level']
            levels_count[level] = levels_count.get(level, 0) + 1
        
        return {
            'root_id': root_id,
            'levels': levels_count,
            'total_super_notes': sum(levels_count.values())
        }


# =============================================================================
# PUBLIC API
# =============================================================================

async def build_tree_for_user(user_id: str) -> Dict:
    """
    Public entry point: Build hierarchical tree for a user
    
    Args:
        user_id: User ID
        
    Returns:
        {
            'status': 'success' | 'error',
            'root_id': UUID,
            'levels': int,
            'nodes_created': int,
            'structure': {...}
        }
    """
    
    builder = HierarchicalTreeBuilder(user_id)
    result = await builder.build_tree()
    return result


# =============================================================================
# TEST/DEBUG
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test with your user ID
        user_id = "your-user-id-here"
        
        print("Testing tree builder with SuperNoteGenerator...\n")
        
        result = await build_tree_for_user(user_id)
        
        print("\n" + "="*70)
        print("RESULT:")
        print("="*70)
        print(f"Status: {result['status']}")
        
        if result['status'] == 'success':
            print(f"Root ID: {result['root_id']}")
            print(f"Levels: {result['levels']}")
            print(f"Nodes Created: {result['nodes_created']}")
            print(f"Structure: {result['structure']}")
        else:
            print(f"Error: {result.get('message')}")
    
    asyncio.run(test())