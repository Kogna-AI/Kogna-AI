# In services/embedding_service.py

import os
import io
import time
import fitz  # <-- Add this import
from supabase_connect import get_supabase_manager
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# (Your initial client setup and splitters are unchanged)
try:
    supabase = get_supabase_manager().client
except Exception as e:
    print(f"CRITICAL ERROR: Could not initialize Supabase client in embedding_service: {e}")
    supabase = None

try:
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")

    embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=gemini_api_key)
    print("Embedding model initialized successfully.")

except Exception as e:
    print(f"CRITICAL ERROR: Could not initialize embedding model: {e}")
    embeddings_model = None


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

json_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
    separators=["\n", "},", "{", "}"]
)


async def embed_and_store_file(user_id: str, file_path_in_bucket: str):
    """
    Downloads a file from Supabase Storage, extracts text if PDF,
    chunks it, embeds it, and stores the vectors in the database.
    """
    if not supabase or not embeddings_model:
        print("ERROR: Embedding service is not initialized. Aborting.")
        return

    print(f"--- Embedding file: {file_path_in_bucket} for user {user_id} ---")

    try:
        # 1. Download the file from Storage
        bucket_name = "Kogna"
        file_content_bytes = supabase.storage.from_(bucket_name).download(file_path_in_bucket)

        if not file_content_bytes:
            print(f"Warning: Failed to download {file_path_in_bucket} or file is empty.")
            return

        # 2. Extract Text / Decode and Chunk based on file type
        file_content_str = ""
        chunks = []

        # --- MODIFICATION: Handle PDF ---
        if file_path_in_bucket.lower().endswith(".pdf"):
            print(f"Extracting text from PDF: {file_path_in_bucket}")
            try:
                # Open PDF from bytes
                with fitz.open(stream=io.BytesIO(file_content_bytes)) as doc:
                    full_pdf_text = ""
                    for page in doc:
                        full_pdf_text += page.get_text() + "\n\n" # Add space between pages
                file_content_str = full_pdf_text
                # Use the standard text splitter for PDF content
                chunks = text_splitter.split_text(file_content_str)
                print(f"Successfully extracted text from {len(doc)} pages.")
            except Exception as pdf_e:
                print(f"Warning: Could not extract text from PDF {file_path_in_bucket}: {pdf_e}")
                return # Skip this file if extraction fails

        elif file_path_in_bucket.endswith(".json"):
             file_content_str = file_content_bytes.decode('utf-8')
             chunks = json_splitter.split_text(file_content_str)

        elif file_path_in_bucket.endswith(".txt") or file_path_in_bucket.endswith(".csv"):
             file_content_str = file_content_bytes.decode('utf-8')
             chunks = text_splitter.split_text(file_content_str)

        else:
            # Try decoding as text for any other unknown type, skip if it fails
            try:
                file_content_str = file_content_bytes.decode('utf-8')
                chunks = text_splitter.split_text(file_content_str)
                print(f"Attempting text embedding for unknown type: {file_path_in_bucket}")
            except UnicodeDecodeError:
                print(f"Skipping embedding for unsupported/binary file type: {file_path_in_bucket}")
                return
        # --- END MODIFICATION ---

        if not chunks:
            print(f"Warning: No text chunks generated for {file_path_in_bucket}.")
            return

        print(f"Generated {len(chunks)} chunks for {file_path_in_bucket}.")

        # 3. Embed the chunks in batches
        batch_size = 90
        chunk_embeddings = []

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            print(f"Embedding batch {int(i/batch_size) + 1}/{int(len(chunks)/batch_size) + 1}...")
            try:
                batch_embeddings = embeddings_model.embed_documents(batch_chunks)
                chunk_embeddings.extend(batch_embeddings)
                print(f"Batch embedded. Waiting 1 second...")
                time.sleep(1)

            except Exception as batch_e:
                print(f"Error on batch {int(i/batch_size) + 1}: {batch_e}")
                raise batch_e


        if not chunk_embeddings or len(chunk_embeddings) != len(chunks):
            print("Error: Embedding process failed or returned mismatched count.")
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

        # 5. Upsert to the database
        print(f"Deleting old chunks for {file_path_in_bucket}...")
        delete_response = supabase.table("document_chunks").delete().eq("file_path", file_path_in_bucket).execute()

        print(f"Inserting {len(documents_to_insert)} new chunks...")
        insert_response = supabase.table("document_chunks").insert(documents_to_insert).execute()

        print(f"✅ Successfully embedded and stored {len(documents_to_insert)} chunks for {file_path_in_bucket}.")

    except Exception as e:
        print(f"❌ Error during embedding for {file_path_in_bucket}: {e}")
        import traceback
        traceback.print_exc()