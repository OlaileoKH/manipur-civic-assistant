import math
import chromadb
from ddgs import DDGS

# Initialize persistent local ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_store")
rag_collection = chroma_client.get_or_create_collection(name="enterprise_vault")

if rag_collection.count() == 0:
    rag_collection.add(
        documents=[
            "To apply for an OBC, Domicile, Income, or Permanent Resident Certificate in Manipur, citizens can use the official e-Seba Manipur portal at https://esebamanipur.mn.gov.in/",
            "For electricity supply complaints, power cuts, or billing issues across districts, contact Manipur State Power Distribution Company Limited (MSPDCL) via mspdcl.in",
            "State welfare services and central schemes under one umbrella can be referenced through the Manipur Unified Service portal at uspmanipur.mn.gov.in",
            "First Aadhaar Seva Kendra in Imphal was launched at Waheng Leikai for local Aadhaar updates and processing."
        ],
        ids=["Civic-01", "Civic-02", "Civic-03", "Civic-04"]
    )


def query_local_rag_vault(query: str) -> str:
    """Performs semantic vector search across Manipur public data records."""
    try:
        results = rag_collection.query(query_texts=[query], n_results=2)
        matches = results.get("documents", [[]])
        if not matches or not matches:
            return "No matching local service records found."
        return "Local Manipur Service Info:\n" + "\n".join([f"- {doc}" for doc in matches])
    except Exception as e:
        return f"Database error: {e}"

def ingest_uploaded_document(file_content: str, filename: str) -> str:
    """Chunks text from an uploaded file and writes it straight to ChromaDB."""
    try:
        chunks = [c.strip() for c in file_content.split("\n") if c.strip()]
        if not chunks:
            chunks = [file_content.strip()]
            
        base_id = filename.replace(".", "_")
        ids = [f"{base_id}_chunk_{i}" for i in range(len(chunks))]
        
        rag_collection.upsert(
            documents=chunks,
            ids=ids,
            metadatas=[{"source": filename} for _ in chunks]
        )
        return f"Successfully ingested {len(chunks)} block(s) from '{filename}' into [ChromaDB](https://pypi.org)!"
    except Exception as e:
        return f"Ingestion error: {e}"


def search_web_internet(query: str) -> str:
    """Search live internet for current updates or announcements in Manipur."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"Manipur {query}", max_results=3))
        if not results:
            return "No recent public results found."
        return "\n".join([f"Web Info ({r.get('title')}): {r.get('body')}" for r in results])
    except Exception as e:
        return f"Network error: {e}"
        
# Keep execute_math_operation and super_tool_registry as before...


def execute_math_operation(operation: str, a, b = 0.0) -> str:
    """Precise calculator for arithmetic operations with safe input validation."""
    try:
        # Safely convert inputs if they accidentally receive strings like dates
        if isinstance(a, str):
            a = float(a)
        if isinstance(b, str):
            b = float(b)
            
        if operation == "add": return str(a + b)
        elif operation == "subtract": return str(a - b)
        elif operation == "multiply": return str(a * b)
        elif operation == "divide":
            return "Error: Division by zero." if b == 0 else str(a / b)
        elif operation == "power": return str(math.pow(a, b))
        elif operation == "sqrt":
            return "Error: Negative radicand." if a < 0 else str(math.sqrt(a))
        return f"Unknown operation: {operation}"
    except ValueError:
        return f"Error: Received a non-numeric value ('{a}' or '{b}') for a mathematical operation."
    except Exception as e:
        return f"Math error: {e}"


super_tool_registry = [
    {
        "type": "function",
        "function": {
            "name": "query_local_rag_vault",
            "description": "Use ONLY for private company documents, internal files, personal configuration notes, or local secrets uploaded by the user.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search keywords for private files"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web_internet",
            "description": "Use for public knowledge, current events, live news, public figures, and political officeholders (such as active Chief Ministers or government leaders).",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "The precise public search query"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_math_operation",
            "description": "Perform explicit arithmetic calculations (add, subtract, multiply, divide, power, sqrt) on numerical inputs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide", "power", "sqrt"]},
                    "a": {"type": "number"},
                    "b": {"type": "number", "default": 0.0}
                },
                "required": ["operation", "a"]
            }
        }
    }
]
