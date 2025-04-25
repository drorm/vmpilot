from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import CodeSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores import ChromaVectorStore

# === Configuration ===
SOURCE_DIR = "../src"  # Change to your source directory
VECTOR_STORE_DIR = "./index_store"  # Directory to persist the vector store
EMBEDDING_MODEL = "text-embedding-3-small"  # Or use a local model if desired

# === Load and Split Code ===
print("Loading documents from", SOURCE_DIR)
documents = SimpleDirectoryReader(SOURCE_DIR).load_data()

print("Splitting code using Tree-sitter-based CodeSplitter")
code_splitter = CodeSplitter(language="python")
nodes = code_splitter.get_nodes_from_documents(documents)

# === Create Embeddings and Store Index ===
print("Creating vector store index with OpenAI embedding")
embedding_model = OpenAIEmbedding(model=EMBEDDING_MODEL)

vector_store = ChromaVectorStore()
vector_store.add(nodes, embedding_model=embedding_model)

print("Persisting vector store to", VECTOR_STORE_DIR)
vector_store.persist(VECTOR_STORE_DIR)

print("Indexing complete. Ready for retrieval!")
