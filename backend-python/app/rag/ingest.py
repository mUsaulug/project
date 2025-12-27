import chromadb
from chromadb.utils import embedding_functions
import os

def chunk_text(text: str, max_words: int = 120, overlap: int = 20) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks

def ingest_data():
    print("Initializing ChromaDB for ingestion...")
    db_path = os.path.join(os.getcwd(), "chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    
    # Delete existing to start fresh
    try:
        client.delete_collection("complaint_sops")
    except:
        pass

    collection = client.create_collection(
        name="complaint_sops",
        embedding_function=embedding_fn
    )

    # 1. Load Markdown Files from data/sops/
    documents = []
    sops_dir = os.path.join(os.getcwd(), "data", "sops")
    if not os.path.exists(sops_dir):
        print(f"Warning: {sops_dir} not found. Creating it.")
        os.makedirs(sops_dir, exist_ok=True)
        # Fallback dummy file to prevent empty error
        with open(os.path.join(sops_dir, "readme.md"), "w", encoding="utf-8") as f:
            f.write("# Welcome\nSystem initialized. Please add SOPs here.")

    for filename in os.listdir(sops_dir):
        if filename.endswith(".md"):
            file_path = os.path.join(sops_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            # Simple Category Heuristic based on filename
            category = "GENERAL"
            if "credit" in filename: category = "CARD_LIMIT_CREDIT"
            elif "transfer" in filename: category = "TRANSFER_DELAY"
            elif "security" in filename: category = "ACCESS_LOGIN_MOBILE"
            
            documents.append({
                "text": text,
                "category": category,
                "filename": filename
            })

    chunked_docs = []
    ids = []
    metadatas = []
    
    for doc in documents:
        doc_name = doc["filename"]
        # Split by headers to keep context or just simple chunking
        # For simplicity, using valid chunk_text function
        for chunk_index, chunk in enumerate(chunk_text(doc["text"])):
            chunk_id = f"{doc_name}_chunk_{chunk_index}"
            chunked_docs.append(chunk)
            ids.append(chunk_id)
            metadatas.append(
                {
                    "source": "Bank_SOP_v2",
                    "doc_name": doc_name,
                    "chunk_id": chunk_id,
                    "category": doc["category"],
                }
            )

    if not chunked_docs:
        print("No documents found to ingest!")
        return

    print(f"Adding {len(chunked_docs)} chunks from {len(documents)} files...")
    collection.add(
        documents=chunked_docs,
        ids=ids,
        metadatas=metadatas,
    )
    print("Ingestion complete. ChromaDB is ready.")

if __name__ == "__main__":
    ingest_data()
