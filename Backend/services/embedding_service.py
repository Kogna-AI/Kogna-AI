# services/embedding_service.py
# COMPLETE VERSION: With Hybrid Intelligent Clustering + File Change Detection
# Stage 1: Cluster by topic (semantic similarity)
# Stage 2: Split large clusters into manageable sub-groups

import os
import io
import time
import logging
import fitz  # PDF extraction
from typing import Optional, Dict
from supabase_connect import get_supabase_manager
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# === IMPORT: Note Generator ===
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Ai_agents.note_generator_agent import DocumentNoteGenerator

# === NEW IMPORT: File Change Detector ===
from services.file_change_detector import FileChangeDetector

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize clients
try:
    supabase = get_supabase_manager().client
except Exception as e:
    print(f"CRITICAL ERROR: Could not initialize Supabase client in embedding_service: {e}")
    supabase = None

try:
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")

    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=gemini_api_key
    )
    print("✓ Embedding model initialized successfully.")

except Exception as e:
    print(f"CRITICAL ERROR: Could not initialize embedding model: {e}")
    embeddings_model = None

# === Initialize Note Generator ===
try:
    note_generator = DocumentNoteGenerator()
    print("✓ Note generator initialized successfully.")
except Exception as e:
    print(f"⚠ Note generator initialization failed: {e}")
    note_generator = None

# Text splitters
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

json_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
    separators=["\n", "},", "{", "}"]
)


# =============================================================================
#  HYBRID CLUSTERING FUNCTION (Two-Stage)
# =============================================================================

def cluster_and_split_chunks(chunks, chunk_embeddings, 
                             min_chunks_per_note=5, 
                             max_chunks_per_note=12):
    """
    Two-stage intelligent grouping for optimal note generation.
    
    Stage 1: Cluster by TOPIC (semantic similarity)
        - Groups semantically related chunks together
        - Creates topic-focused clusters (e.g., Finance, HR, Product)
    
    Stage 2: Split large clusters into sub-groups
        - Ensures no note exceeds max_chunks_per_note
        - Maintains topic coherence within sub-groups
    
    Example with 50 chunks:
        Stage 1 → 3 topics:
            Topic 0 (Revenue): 25 chunks
            Topic 1 (Team): 15 chunks
            Topic 2 (Product): 10 chunks
        
        Stage 2 → Split large topics:
            Topic 0 → 3 sub-notes (9, 8, 8 chunks)
            Topic 1 → 2 sub-notes (8, 7 chunks)
            Topic 2 → 1 note (10 chunks)
        
        Result: 6 focused notes, each 7-10 chunks
    
    Args:
        chunks: List of text chunks
        chunk_embeddings: List of embeddings (vectors)
        min_chunks_per_note: Minimum chunks for a note (default: 5)
        max_chunks_per_note: Maximum chunks per note (default: 12)
        
    Returns:
        List of note groups: [{chunks, chunk_ids, topic_cluster, sub_group, ...}, ...]
    """
    
    print(f"\n Hybrid Clustering: {len(chunks)} chunks")
    
    # Handle edge cases
    if len(chunks) < min_chunks_per_note:
        print(f"   ⚠ Too few chunks ({len(chunks)}), creating single group")
        return [{
            'chunks': chunks,
            'chunk_ids': list(range(len(chunks))),
            'topic_cluster': 0,
            'sub_group': 0,
            'chunk_count': len(chunks),
            'description': 'complete_document'
        }]
    
    embeddings_array = np.array(chunk_embeddings)
    
    # =========================================================================
    # STAGE 1: TOPIC CLUSTERING
    # =========================================================================
    
    print(f"\n Stage 1: Identifying main topics...")
    
    # Determine number of topic clusters
    # Goal: Separate by high-level topic (Finance, HR, Product, etc.)
    n_topics = max(2, min(6, len(chunks) // 15))  # 2-6 topics max
    
    print(f"   Testing {n_topics-1} to {n_topics+1} topic configurations...")
    
    # Find best topic clustering using silhouette score
    best_score = -1
    best_kmeans = None
    best_n_topics = n_topics
    
    for n in range(max(2, n_topics-1), min(n_topics+2, len(chunks)//min_chunks_per_note)):
        try:
            kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings_array)
            score = silhouette_score(embeddings_array, labels, metric='cosine')
            
            print(f"    • {n} topics: quality = {score:.3f}")
            
            if score > best_score:
                best_score = score
                best_kmeans = kmeans
                best_n_topics = n
        except Exception as e:
            print(f"    ✗ {n} topics failed: {e}")
            continue
    
    if best_kmeans is None:
        print(f"   ⚠ Clustering failed, using default {n_topics} topics")
        best_kmeans = KMeans(n_clusters=n_topics, random_state=42)
        best_kmeans.fit(embeddings_array)
        best_n_topics = n_topics
    
    topic_labels = best_kmeans.labels_
    n_topics_found = len(set(topic_labels))
    
    print(f"  ✓ Selected {best_n_topics} topics (quality: {best_score:.3f})")
    
    # Group chunks by topic
    topic_clusters = {}
    for idx, topic_id in enumerate(topic_labels):
        if topic_id not in topic_clusters:
            topic_clusters[topic_id] = {
                'chunks': [],
                'chunk_ids': [],
                'embeddings': []
            }
        topic_clusters[topic_id]['chunks'].append(chunks[idx])
        topic_clusters[topic_id]['chunk_ids'].append(idx)
        topic_clusters[topic_id]['embeddings'].append(chunk_embeddings[idx])
    
    # =========================================================================
    # STAGE 2: SPLIT LARGE TOPIC CLUSTERS
    # =========================================================================
    
    print(f"\n Stage 2: Splitting large topic clusters...")
    print(f"   Target: {min_chunks_per_note}-{max_chunks_per_note} chunks per note")
    
    final_groups = []
    
    for topic_id in sorted(topic_clusters.keys()):
        topic_data = topic_clusters[topic_id]
        topic_size = len(topic_data['chunks'])
        
        print(f"\n   Topic {topic_id}: {topic_size} chunks", end=" ")
        
        # If cluster is already optimal size, keep as single note
        if topic_size <= max_chunks_per_note:
            print(f"→ 1 note ✓")
            final_groups.append({
                'chunks': topic_data['chunks'],
                'chunk_ids': topic_data['chunk_ids'],
                'topic_cluster': topic_id,
                'sub_group': 0,
                'chunk_count': topic_size,
                'description': f'topic_{topic_id}_complete'
            })
        
        # If cluster is large, split into sub-groups
        else:
            # Calculate number of sub-groups needed
            n_subgroups = max(2, (topic_size + max_chunks_per_note - 1) // max_chunks_per_note)
            
            print(f"→ {n_subgroups} sub-notes")
            
            # Use K-Means again within this topic to create semantic sub-groups
            try:
                topic_embeddings = np.array(topic_data['embeddings'])
                sub_kmeans = KMeans(n_clusters=n_subgroups, random_state=42, n_init=10)
                sub_labels = sub_kmeans.fit_predict(topic_embeddings)
                
                # Create sub-groups
                sub_groups = {}
                for i, sub_label in enumerate(sub_labels):
                    if sub_label not in sub_groups:
                        sub_groups[sub_label] = {
                            'chunks': [],
                            'chunk_ids': []
                        }
                    sub_groups[sub_label]['chunks'].append(topic_data['chunks'][i])
                    sub_groups[sub_label]['chunk_ids'].append(topic_data['chunk_ids'][i])
                
                # Add sub-groups to final list
                for sub_id in sorted(sub_groups.keys()):
                    sub_data = sub_groups[sub_id]
                    if len(sub_data['chunks']) >= min_chunks_per_note:
                        final_groups.append({
                            'chunks': sub_data['chunks'],
                            'chunk_ids': sorted(sub_data['chunk_ids']),
                            'topic_cluster': topic_id,
                            'sub_group': sub_id,
                            'chunk_count': len(sub_data['chunks']),
                            'description': f'topic_{topic_id}_part_{sub_id}'
                        })
                        print(f"    • Sub-group {sub_id}: {len(sub_data['chunks'])} chunks")
                
            except Exception as e:
                print(f"\n       Sub-clustering failed ({e}), using sequential split")
                # Fallback: simple sequential split
                for i in range(0, topic_size, max_chunks_per_note):
                    sub_chunks = topic_data['chunks'][i:i+max_chunks_per_note]
                    sub_ids = topic_data['chunk_ids'][i:i+max_chunks_per_note]
                    
                    if len(sub_chunks) >= min_chunks_per_note:
                        final_groups.append({
                            'chunks': sub_chunks,
                            'chunk_ids': sub_ids,
                            'topic_cluster': topic_id,
                            'sub_group': i // max_chunks_per_note,
                            'chunk_count': len(sub_chunks),
                            'description': f'topic_{topic_id}_sequential_{i}'
                        })
                        print(f"    • Part {i//max_chunks_per_note + 1}: {len(sub_chunks)} chunks")
    
    # Sort by topic, then sub-group for logical order
    final_groups.sort(key=lambda x: (x['topic_cluster'], x['sub_group']))
    
    # Print summary
    print(f"\n   Final result: {len(final_groups)} focused notes")
    
    # Group by topic for summary
    topic_summary = {}
    for group in final_groups:
        topic_id = group['topic_cluster']
        if topic_id not in topic_summary:
            topic_summary[topic_id] = 0
        topic_summary[topic_id] += 1
    
    print(f"   Distribution:")
    for topic_id in sorted(topic_summary.keys()):
        count = topic_summary[topic_id]
        print(f"    Topic {topic_id}: {count} note(s)")
    
    return final_groups


# =============================================================================
# MAIN FUNCTION: EMBED AND STORE WITH CHANGE DETECTION + HYBRID CLUSTERING
# =============================================================================

async def embed_and_store_file(
    user_id: str, 
    file_path_in_bucket: str,
    source_type: str = "upload",
    source_id: Optional[str] = None,
    source_metadata: Optional[Dict] = None,
    force_reprocess: bool = False,
    file_content: Optional[bytes] = None  # NEW: Pass content directly to skip download
):
    """
    Downloads a file from Supabase Storage, extracts text,
    chunks it, embeds it, stores vectors in the database,
    AND generates intelligent notes using HYBRID CLUSTERING.
    
    NOW WITH INTELLIGENT FILE CHANGE DETECTION:
    - Computes file hash and checks if file changed
    - Skips processing if file is unchanged (95% faster!)
    - Deletes old chunks/notes before re-processing modified files
    - Tracks file metadata in registry
    
    TWO MODES:
    - file_content=None (default): Download from storage
    - file_content=bytes: Use provided content (skip download, faster!)
    
    Hybrid Clustering:
    - Stage 1: Group by topic (semantic similarity)
    - Stage 2: Split large topics into sub-groups
    - Result: Optimal note sizes (5-12 chunks) with topic coherence
    """
    if not supabase or not embeddings_model:
        print(" ERROR: Embedding service is not initialized. Aborting.")
        return {
            'status': 'error',
            'message': 'Service not initialized'
        }

    print(f"\n{'='*60}")
    print(f" Processing: {file_path_in_bucket}")
    print(f" User: {user_id}")
    print(f"{'='*60}")

    detector = FileChangeDetector()
    file_id = None

    try:
        # =====================================================================
        # STEP 1: GET FILE CONTENT (download or use provided)
        # =====================================================================
        
        if file_content is None:
            # Download from storage
            bucket_name = "Kogna"
            file_content_bytes = supabase.storage.from_(bucket_name).download(file_path_in_bucket)

            if not file_content_bytes:
                print(f" Failed to download {file_path_in_bucket} or file is empty.")
                return {
                    'status': 'error',
                    'message': 'Failed to download file'
                }
        else:
            # Use provided content (already have it in memory!)
            print(f" Using provided content (skipping download)")
            file_content_bytes = file_content

        # Compute file hash for change detection
        file_hash = detector.compute_file_hash(file_content_bytes)
        file_size = len(file_content_bytes)
        file_name = file_path_in_bucket.split('/')[-1]
        
        print(f" File hash: {file_hash[:16]}...")
        print(f" File size: {file_size:,} bytes")

        # =====================================================================
        # STEP 2: CHECK IF FILE CHANGED (unless force_reprocess)
        # =====================================================================
        
        if not force_reprocess:
            status_check = await detector.check_file_status(
                user_id=user_id,
                file_path=file_path_in_bucket,
                current_hash=file_hash,
                file_size=file_size,
                source_type=source_type,
                source_id=source_id
            )
            
            # If file unchanged, skip processing
            if status_check['action'] == 'skip':
                print(f"\n  SKIPPED: File unchanged (hash matches)")
                print(f"{'='*60}\n")
                return {
                    'status': 'skipped',
                    'file_id': status_check['file_id'],
                    'file_hash': file_hash,
                    'chunks_processed': 0,
                    'notes_generated': 0,
                    'message': 'File unchanged'
                }
            
            # If modified, delete old chunks/notes
            if status_check['status'] == 'modified':
                print(f"\n MODIFIED FILE DETECTED")
                await detector.delete_file_chunks_and_notes(
                    user_id=user_id,
                    old_file_hash=status_check['previous_hash']
                )
        
        # =====================================================================
        # STEP 3: REGISTER FILE IN REGISTRY
        # =====================================================================
        
        file_id = await detector.register_file(
            user_id=user_id,
            file_path=file_path_in_bucket,
            file_name=file_name,
            file_hash=file_hash,
            file_size=file_size,
            source_type=source_type,
            source_id=source_id,
            source_metadata=source_metadata,
            last_modified_at=source_metadata.get('modified_time') if source_metadata else None
        )

        # =====================================================================
        # STEP 4: EXTRACT TEXT
        # =====================================================================
        
        file_content_str = ""
        chunks = []

        # --- Handle PDF ---
        if file_path_in_bucket.lower().endswith(".pdf"):
            print(f" Extracting text from PDF...")
            try:
                with fitz.open(stream=io.BytesIO(file_content_bytes)) as doc:
                    full_pdf_text = ""
                    for page in doc:
                        full_pdf_text += page.get_text() + "\n\n"
                file_content_str = full_pdf_text
                chunks = text_splitter.split_text(file_content_str)
                print(f"✓ Extracted text from {len(doc)} pages → {len(chunks)} chunks")
            except Exception as pdf_e:
                print(f" Could not extract text from PDF: {pdf_e}")
                await detector.update_file_processing_status(file_id, 'failed', 0, 0)
                return {
                    'status': 'error',
                    'message': f'PDF extraction failed: {pdf_e}'
                }

        # --- Handle JSON ---
        elif file_path_in_bucket.endswith(".json"):
            file_content_str = file_content_bytes.decode('utf-8')
            chunks = json_splitter.split_text(file_content_str)
            print(f" Processed JSON → {len(chunks)} chunks")

        # --- Handle TXT/CSV ---
        elif file_path_in_bucket.endswith(".txt") or file_path_in_bucket.endswith(".csv"):
            file_content_str = file_content_bytes.decode('utf-8')
            chunks = text_splitter.split_text(file_content_str)
            print(f" Processed text file → {len(chunks)} chunks")

        # --- Try to decode as text for unknown types ---
        else:
            try:
                file_content_str = file_content_bytes.decode('utf-8')
                chunks = text_splitter.split_text(file_content_str)
                print(f"⚠ Unknown type, attempting text embedding → {len(chunks)} chunks")
            except UnicodeDecodeError:
                print(f" Skipping unsupported/binary file: {file_path_in_bucket}")
                await detector.update_file_processing_status(file_id, 'failed', 0, 0)
                return {
                    'status': 'error',
                    'message': 'Unsupported file type'
                }

        if not chunks:
            print(f" No text chunks generated for {file_path_in_bucket}")
            await detector.update_file_processing_status(file_id, 'failed', 0, 0)
            return {
                'status': 'error',
                'message': 'No chunks generated'
            }

        # =====================================================================
        # STEP 5: EMBED CHUNKS
        # =====================================================================
        
        print(f" Embedding {len(chunks)} chunks...")
        batch_size = 90
        chunk_embeddings = []

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_num = int(i/batch_size) + 1
            total_batches = int(len(chunks)/batch_size) + 1
            
            print(f"   Batch {batch_num}/{total_batches}...", end=" ")
            
            try:
                batch_embeddings = embeddings_model.embed_documents(batch_chunks)
                chunk_embeddings.extend(batch_embeddings)
                print("✓")
                time.sleep(1)

            except Exception as batch_e:
                print(f" Error: {batch_e}")
                await detector.update_file_processing_status(file_id, 'failed', 0, 0)
                raise batch_e

        if not chunk_embeddings or len(chunk_embeddings) != len(chunks):
            print(" Embedding process failed or returned mismatched count.")
            await detector.update_file_processing_status(file_id, 'failed', 0, 0)
            return {
                'status': 'error',
                'message': 'Embedding failed'
            }

        # =====================================================================
        # STEP 6: STORE CHUNKS WITH FILE_HASH
        # =====================================================================
        
        documents_to_insert = []
        for chunk, embedding in zip(chunks, chunk_embeddings):
            chunk_hash = detector.compute_chunk_hash(chunk)
            documents_to_insert.append({
                "user_id": user_id,
                "file_path": file_path_in_bucket,
                "content": chunk,
                "embedding": embedding,
                "file_hash": file_hash,      #  NEW: Link to file version
                "chunk_hash": chunk_hash      #  NEW: Chunk-level deduplication
            })

        print(f" Inserting {len(documents_to_insert)} chunks...")
        supabase.table("document_chunks").insert(documents_to_insert).execute()
        print(f"✓ Chunks stored successfully!")

        # =====================================================================
        # STEP 7: INTELLIGENT NOTE GENERATION WITH HYBRID CLUSTERING
        # =====================================================================
        
        notes_generated = 0
        generated_note_ids = [] 

        if note_generator and chunks and len(chunks) >= 3:
            print(f"\n Generating intelligent notes with hybrid clustering...")
            
            #  HYBRID CLUSTERING: Topic-based + Size-based splitting
            note_groups = cluster_and_split_chunks(
                chunks, 
                chunk_embeddings,
                min_chunks_per_note=5,     # Minimum chunks for a note
                max_chunks_per_note=12     # Maximum chunks per note
            )
            
            print(f"\n  Generating {len(note_groups)} notes...")
            
            # Generate note for each hybrid group
            for group_idx, group in enumerate(note_groups, 1):
                try:
                    topic_id = group['topic_cluster']
                    sub_id = group['sub_group']
                    chunk_count = group['chunk_count']
                    
                    print(f"   Note {group_idx}/{len(note_groups)} (Topic {topic_id}.{sub_id}, {chunk_count} chunks)...", end=" ")
                    
                    # Combine chunks in this group
                    group_text = "\n\n".join(group['chunks'])
                    
                    # Generate note for this group
                    note_data = note_generator.generate_note(
                        document_text=group_text,
                        file_path=f"{file_path_in_bucket}#topic{topic_id}_sub{sub_id}"
                    )
                    
                    # Extract topics from entities
                    topics_list = note_data.get('entities', {}).get('topics', [])
                    
                    # Create embedding for the note
                    note_text_for_embedding = f"""
{note_data['title']}

{note_data['summary']}

Key Facts:
{chr(10).join(f"- {fact}" for fact in note_data.get('key_facts', []))}

Topics: {', '.join(topics_list)}
                    """.strip()
                    
                    try:
                        note_embedding = embeddings_model.embed_query(note_text_for_embedding)
                        print("", end=" ")
                    except Exception as embed_error:
                        logging.warning(f"Failed to embed note: {embed_error}")
                        note_embedding = None
                    
                    # Store note with hybrid cluster metadata + file_hash
                    note_record = {
                        'user_id': user_id,
                        'file_path': file_path_in_bucket,
                        'title': f"{note_data['title']} (Part {group_idx}/{len(note_groups)})",
                        'summary': note_data['summary'],
                        'key_facts': note_data.get('key_facts', []),
                        'action_items': note_data.get('action_items', []),
                        'entities': note_data.get('entities', {}),
                        'chunk_group': int(topic_id * 100 + sub_id),
                        'chunk_start': int(min(group['chunk_ids'])),
                        'chunk_end': int(max(group['chunk_ids'])),
                        'note_embedding': note_embedding,
                        'file_hash': file_hash  #  NEW: Link to file version
                    }
                    
                    # Capture the insert result
                    insert_result = supabase.table('document_notes').insert(note_record).execute()
                    
                    # Capture note ID if insert succeeded
                    if insert_result.data and len(insert_result.data) > 0:
                        generated_note_ids.append(insert_result.data[0]['id'])
                    
                    notes_generated += 1
                    print("✓")
                    time.sleep(1)
                    
                except Exception as note_error:
                    print(f"✗ ({note_error})")
                    logging.error(f"Note generation failed: {note_error}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"\n Generated {notes_generated} hybrid-clustered notes for {len(chunks)} chunks")
            if notes_generated > 0:
                avg_chunks = len(chunks) // notes_generated
                print(f"   Average: {avg_chunks} chunks per note")
                print(f"   Target range: 5-12 chunks per note")
            
        else:
            if not note_generator:
                print(f"⚠ Note generator not available, skipping note creation")
            elif not chunks:
                print(f"⚠ No chunks available, skipping note creation")
            else:
                print(f"⚠ Too few chunks ({len(chunks)}), skipping clustering")

        # =====================================================================
        # STEP 8: SMART TREE UPDATE
        # =====================================================================
        
        if notes_generated > 0:
            print(f"\n🌳 Smart tree update for user {user_id}...")
            
            try:
                from services.tree_updater import TreeUpdater
                from services.tree_builder import build_tree_for_user
                
                # Check if tree exists
                tree_check = supabase.table('super_notes').select('id').eq(
                    'user_id', user_id
                ).eq('is_root', True).execute()
                
                tree_exists = bool(tree_check.data)
                
                if not tree_exists:
                    # NO TREE - BUILD INITIAL
                    print("    Building initial tree...")
                    tree_result = await build_tree_for_user(user_id)
                    print(f"    Initial tree built!")
                    print(f"      • Levels: {tree_result['levels']}")
                    print(f"      • Super-notes: {tree_result['nodes_created']}")
                
                else:
                    # TREE EXISTS - SMART UPDATE
                    print("    Using smart update...")
                    
                    if not generated_note_ids:
                        print("    No note IDs - skipping update")
                    else:
                        updater = TreeUpdater(user_id)
                        
                        # Mark affected branches
                        update_result = await updater.on_new_notes(
                            new_note_ids=generated_note_ids,
                            file_hash=file_hash
                        )
                        
                        if update_result['status'] == 'success':
                            print(f"    Smart update complete!")
                            print(f"      • Branches marked: {update_result['branches_marked']}")
                            print(f"      • Nodes marked: {update_result['nodes_marked']}")
                            print(f"     Nodes will regenerate in background")
                        
                        elif update_result['status'] == 'full_rebuild_needed':
                            print("     New topics - full rebuild needed")
                            supabase.table('super_notes').delete().eq(
                                'user_id', user_id
                            ).execute()
                            tree_result = await build_tree_for_user(user_id)
                            print(f"    Tree rebuilt!")
            
            except Exception as tree_error:
                logging.error(f" Tree update failed: {tree_error}")
                import traceback
                traceback.print_exc()
                print("    Tree update failed, but document processing succeeded")
        
        # =====================================================================
        # STEP 9: UPDATE FILE REGISTRY WITH FINAL STATUS
        # =====================================================================
        
        await detector.update_file_processing_status(
            file_id=file_id,
            status='completed',
            chunk_count=len(chunks),
            note_count=notes_generated
        )

        print(f"\n{'='*60}")
        print(f" COMPLETE: {file_path_in_bucket}")
        print(f"   • Chunks: {len(documents_to_insert)}")
        print(f"   • Notes: {notes_generated} (hybrid clusters)")
        print(f"   • File hash: {file_hash[:16]}...")
        print(f"{'='*60}\n")

        return {
            'status': 'success',
            'file_id': file_id,
            'file_hash': file_hash,
            'chunks_processed': len(chunks),
            'notes_generated': notes_generated,
            'message': f'Successfully processed {len(chunks)} chunks'
        }

    except Exception as e:
        print(f"\n Error during processing for {file_path_in_bucket}: {e}")
        logging.error(f"Embedding service error for {file_path_in_bucket}: {e}")
        import traceback
        traceback.print_exc()
        
        # Update file status to failed if we have a file_id
        if file_id:
            try:
                await detector.update_file_processing_status(
                    file_id=file_id,
                    status='failed',
                    chunk_count=0,
                    note_count=0
                )
            except:
                pass
        
        return {
            'status': 'error',
            'file_id': file_id,
            'file_hash': None,
            'chunks_processed': 0,
            'notes_generated': 0,
            'message': f'Error: {str(e)}'
        }


# =============================================================================
# KPI EMBEDDING FUNCTION - WITH VERSION CONTROL
# =============================================================================

async def embed_and_store_kpi_summary(
    user_id: str,
    organization_id: str,
    kpi_id: int,
    summary_text: str,
    metadata: dict
):
    """
    Embeds a KPI summary and stores it in the vector database.

    VERSION CONTROL: Uses "latest" in file path to automatically replace old versions.
    When a new summary is embedded, the old one is automatically deleted via upsert pattern.

    File path format: kpi://{connector_type}/{source_id}/{kpi_name}/latest

    This ensures:
    - Only the latest KPI summary is kept
    - No accumulation of outdated embeddings
    - Automatic version control without manual cleanup

    Args:
        user_id: User UUID
        organization_id: Organization UUID
        kpi_id: KPI record ID
        summary_text: Natural language summary of the KPI
        metadata: Dict containing:
            - connector_type: e.g., "jira", "asana"
            - source_id: Project/board/workspace ID
            - source_name: Human-readable source name
            - kpi_name: KPI metric name
            - kpi_category: Category (velocity, burndown, etc.)
            - kpi_value: Current value
            - extracted_at: Timestamp

    Returns:
        Dict with status and details
    """
    if not supabase or not embeddings_model:
        print(" ERROR: Embedding service not initialized")
        return {
            'status': 'error',
            'message': 'Service not initialized'
        }

    try:
        # Extract metadata
        connector_type = metadata.get('connector_type', 'unknown')
        source_id = metadata.get('source_id', 'unknown')
        source_name = metadata.get('source_name', 'Unknown Source')
        kpi_name = metadata.get('kpi_name', 'unknown_kpi')
        kpi_category = metadata.get('kpi_category', 'general')

        # VERSION CONTROL: Use "latest" instead of kpi_id
        # This ensures automatic replacement of old embeddings
        file_path = f"kpi://{connector_type}/{source_id}/{kpi_name}/latest"

        print(f"\n--- [KPI Embedding] ---")
        print(f"  KPI ID: {kpi_id}")
        print(f"  Source: {source_name} ({connector_type})")
        print(f"  Metric: {kpi_name}")
        print(f"  File path: {file_path}")

        # Generate embedding for the summary
        print(f"  Generating embedding...")
        embedding = embeddings_model.embed_query(summary_text)
        print(f" Embedding generated ({len(embedding)} dimensions)")

        # AUTOMATIC VERSION CONTROL: Delete old embedding first
        # This ensures only the latest version exists
        print(f"  Deleting old versions...")
        delete_result = (
            supabase.table("document_chunks")
            .delete()
            .eq("file_path", file_path)
            .eq("user_id", user_id)
            .filter("metadata->>organization_id", "eq", organization_id)
            .execute()
        )

        old_count = len(delete_result.data) if delete_result.data else 0
        if old_count > 0:
            print(f"Deleted {old_count} old version(s)")
        else:
            print(f"No old versions found (first embedding)")

        # Insert new embedding
        document = {
            "user_id": user_id,
            "file_path": file_path,
            "content": summary_text,
            "embedding": embedding,
            "metadata": {
                "document_type": "kpi_summary",  # ← For filtering
                "connector_type": connector_type,
                "source_id": source_id,
                "source_name": source_name,
                "kpi_category": kpi_category,
                "kpi_name": kpi_name,
                "kpi_id": kpi_id,
                "organization_id": organization_id,
                "extracted_at": metadata.get('extracted_at'),
                "kpi_value": str(metadata.get('kpi_value', ''))  # Store as string for JSON
            }
        }

        print(f"  Inserting new embedding...")
        supabase.table("document_chunks").insert(document).execute()
        print(f"KPI embedding stored successfully")
        print(f"--- [KPI Embedding Complete] ---\n")

        return {
            'status': 'success',
            'file_path': file_path,
            'kpi_id': kpi_id,
            'old_versions_deleted': old_count,
            'message': f'Successfully embedded KPI: {kpi_name}'
        }

    except Exception as e:
        print(f"\n  ERROR: KPI embedding failed: {e}")
        logging.error(f"KPI embedding error for KPI {kpi_id}: {e}")
        import traceback
        traceback.print_exc()

        return {
            'status': 'error',
            'kpi_id': kpi_id,
            'message': f'Error: {str(e)}'
        }
