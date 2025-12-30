# services/embedding_service.py
# COMPLETE VERSION: With Hybrid Intelligent Clustering
# Stage 1: Cluster by topic (semantic similarity)
# Stage 2: Split large clusters into manageable sub-groups

import os
import io
import time
import logging
import fitz  # PDF extraction
from supabase_connect import get_supabase_manager
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# === NEW IMPORT: Note Generator ===
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Ai_agents.note_generator_agent import DocumentNoteGenerator

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
        model="models/embedding-001", 
        google_api_key=gemini_api_key
    )
    print(" Embedding model initialized successfully.")

except Exception as e:
    print(f"CRITICAL ERROR: Could not initialize embedding model: {e}")
    embeddings_model = None

# === NEW: Initialize Note Generator ===
try:
    note_generator = DocumentNoteGenerator()
    print(" Note generator initialized successfully.")
except Exception as e:
    print(f"  Note generator initialization failed: {e}")
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
# ✨ HYBRID CLUSTERING FUNCTION (Two-Stage)
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
        print(f"     Too few chunks ({len(chunks)}), creating single group")
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
    
    print(f"    Testing {n_topics-1} to {n_topics+1} topic configurations...")
    
    # Find best topic clustering using silhouette score
    best_score = -1
    best_kmeans = None
    best_n_topics = n_topics
    
    for n in range(max(2, n_topics-1), min(n_topics+2, len(chunks)//min_chunks_per_note)):
        try:
            kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings_array)
            score = silhouette_score(embeddings_array, labels, metric='cosine')
            
            print(f"      • {n} topics: quality = {score:.3f}")
            
            if score > best_score:
                best_score = score
                best_kmeans = kmeans
                best_n_topics = n
        except Exception as e:
            print(f"      ✗ {n} topics failed: {e}")
            continue
    
    if best_kmeans is None:
        print(f"     Clustering failed, using default {n_topics} topics")
        best_kmeans = KMeans(n_clusters=n_topics, random_state=42)
        best_kmeans.fit(embeddings_array)
        best_n_topics = n_topics
    
    topic_labels = best_kmeans.labels_
    n_topics_found = len(set(topic_labels))
    
    print(f"    Selected {best_n_topics} topics (quality: {best_score:.3f})")
    
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
        
        print(f"\n    Topic {topic_id}: {topic_size} chunks", end=" ")
        
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
                        print(f"      • Sub-group {sub_id}: {len(sub_data['chunks'])} chunks")
                
            except Exception as e:
                print(f"\n        Sub-clustering failed ({e}), using sequential split")
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
                        print(f"      • Part {i//max_chunks_per_note + 1}: {len(sub_chunks)} chunks")
    
    # Sort by topic, then sub-group for logical order
    final_groups.sort(key=lambda x: (x['topic_cluster'], x['sub_group']))
    
    # Print summary
    print(f"\n    Final result: {len(final_groups)} focused notes")
    
    # Group by topic for summary
    topic_summary = {}
    for group in final_groups:
        topic_id = group['topic_cluster']
        if topic_id not in topic_summary:
            topic_summary[topic_id] = 0
        topic_summary[topic_id] += 1
    
    print(f"    Distribution:")
    for topic_id in sorted(topic_summary.keys()):
        count = topic_summary[topic_id]
        print(f"      Topic {topic_id}: {count} note(s)")
    
    return final_groups


# =============================================================================
# MAIN FUNCTION: EMBED AND STORE WITH HYBRID CLUSTERING
# =============================================================================

async def embed_and_store_file(user_id: str, file_path_in_bucket: str):
    """
    Downloads a file from Supabase Storage, extracts text,
    chunks it, embeds it, stores vectors in the database,
    AND generates intelligent notes using HYBRID CLUSTERING.
    
    Hybrid Clustering:
    - Stage 1: Group by topic (semantic similarity)
    - Stage 2: Split large topics into sub-groups
    - Result: Optimal note sizes (5-12 chunks) with topic coherence
    """
    if not supabase or not embeddings_model:
        print(" ERROR: Embedding service is not initialized. Aborting.")
        return

    print(f"\n{'='*60}")
    print(f" Processing: {file_path_in_bucket}")
    print(f" User: {user_id}")
    print(f"{'='*60}")

    try:
        # 1. Download the file from Storage
        bucket_name = "Kogna"
        file_content_bytes = supabase.storage.from_(bucket_name).download(file_path_in_bucket)

        if not file_content_bytes:
            print(f"  Failed to download {file_path_in_bucket} or file is empty.")
            return

        # 2. Extract Text based on file type
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
                print(f" Extracted text from {len(doc)} pages → {len(chunks)} chunks")
            except Exception as pdf_e:
                print(f" Could not extract text from PDF: {pdf_e}")
                return

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
                print(f"  Unknown type, attempting text embedding → {len(chunks)} chunks")
            except UnicodeDecodeError:
                print(f"  Skipping unsupported/binary file: {file_path_in_bucket}")
                return

        if not chunks:
            print(f"  No text chunks generated for {file_path_in_bucket}")
            return

        # 3. Embed the chunks in batches
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
                raise batch_e

        if not chunk_embeddings or len(chunk_embeddings) != len(chunks):
            print(" Embedding process failed or returned mismatched count.")
            return

        # 4. Prepare data for Supabase
        documents_to_insert = [
            {
                "user_id": user_id,
                "file_path": file_path_in_bucket,
                "content": chunk,
                "embedding": embedding
            }
            for chunk, embedding in zip(chunks, chunk_embeddings)
        ]

        # 5. Store chunks in database
        print(f"  Deleting old chunks...")
        supabase.table("document_chunks").delete().eq("file_path", file_path_in_bucket).execute()

        print(f" Inserting {len(documents_to_insert)} chunks...")
        supabase.table("document_chunks").insert(documents_to_insert).execute()

        print(f" Chunks stored successfully!")

        # =================================================================
        # === ✨ INTELLIGENT NOTE GENERATION WITH HYBRID CLUSTERING ✨ ===
        # =================================================================
        
        if note_generator and chunks and len(chunks) >= 3:
            print(f"\n Generating intelligent notes with hybrid clustering...")
            
            # Delete old notes for this file
            try:
                supabase.table('document_notes')\
                    .delete()\
                    .eq('user_id', user_id)\
                    .eq('file_path', file_path_in_bucket)\
                    .execute()
            except Exception as e:
                print(f"  Warning: Could not delete old notes: {e}")
            
            # ✨ HYBRID CLUSTERING: Topic-based + Size-based splitting
            note_groups = cluster_and_split_chunks(
                chunks, 
                chunk_embeddings,
                min_chunks_per_note=5,     # Minimum chunks for a note
                max_chunks_per_note=12     # Maximum chunks per note
            )
            
            notes_generated = 0
            
            print(f"\n Generating {len(note_groups)} notes...")
            
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
                    
                    # Store note with hybrid cluster metadata
                    note_record = {
                        'user_id': user_id,
                        'file_path': file_path_in_bucket,
                        'title': f"{note_data['title']} (Part {group_idx}/{len(note_groups)})",
                        'summary': note_data['summary'],
                        'key_facts': note_data.get('key_facts', []),
                        'action_items': note_data.get('action_items', []),
                        'entities': note_data.get('entities', {}),
                        'chunk_group': int(topic_id * 100 + sub_id),  # Convert to Python int
                        'chunk_start': int(min(group['chunk_ids'])),   # Convert to Python int
                        'chunk_end': int(max(group['chunk_ids'])),     # Convert to Python int
                        'note_embedding': note_embedding
                    }
                    
                    supabase.table('document_notes').insert(note_record).execute()
                    
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
                print(f"  Note generator not available, skipping note creation")
            elif not chunks:
                print(f"  No chunks available, skipping note creation")
            else:
                print(f"  Too few chunks ({len(chunks)}), skipping clustering")
        
        # =================================================================
        # === END NOTE GENERATION ===
        # =================================================================

        print(f"\n{'='*60}")
        print(f" COMPLETE: {file_path_in_bucket}")
        print(f"   • Chunks: {len(documents_to_insert)}")
        print(f"   • Notes: {notes_generated if note_generator and chunks else 0} (hybrid clusters)")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n Error during processing for {file_path_in_bucket}: {e}")
        logging.error(f"Embedding service error for {file_path_in_bucket}: {e}")
        import traceback
        traceback.print_exc()