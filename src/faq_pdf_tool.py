# src/faq_pdf_tool.py

import os
import torch
import pytesseract
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from PIL import Image
from llama_index.core import VectorStoreIndex, StorageContext, Document
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.mistralai import MistralAI
from llama_index.core.schema import NodeWithScore
from llama_index.core.prompts import PromptTemplate
from llama_index.core.response_synthesizers import ResponseMode
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
load_dotenv()

# Configuration
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"  # Larger model for better performance
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
INDEX_NAME = "faq-index-ocr"  # New index name to avoid conflicts
EMBEDDING_DIM = 1024  # Dimension for BAAI/bge-large-en-v1.5

# OCR Configuration
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path if needed
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

def initialize_pinecone():
    """Initialize Pinecone and return the index."""
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY environment variable not set")
    
    # Initialize Pinecone client
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Create index if it doesn't exist
    if INDEX_NAME not in [index.name for index in pc.list_indexes()]:
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=PINECONE_ENV
            )
        )
    
    return pc.Index(INDEX_NAME)

class OCRProcessor:
    """Handles OCR processing for PDFs and images."""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
        """Extract text from PDF with page numbers and bounding boxes."""
        try:
            doc = fitz.open(pdf_path)
            pages_data = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                pages_data.append({
                    "page_number": page_num + 1,
                    "text": text,
                    "source": os.path.basename(pdf_path),
                    "content_type": "pdf"
                })
            return pages_data
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
            return []

    @staticmethod
    def process_image(image_path: str) -> Optional[Dict]:
        """Extract text from an image using OCR."""
        try:
            text = pytesseract.image_to_string(Image.open(image_path))
            if text.strip():
                return {
                    "text": text,
                    "page_number": 1,
                    "source": os.path.basename(image_path),
                    "content_type": "image"
                }
            return None
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return None

def get_or_create_index():
    """Get or create the FAQ index with Pinecone storage and OCR support."""
    # Initialize embedding model with better parameters
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device} for embeddings")
    
    embed_model = HuggingFaceEmbedding(
        model_name=EMBEDDING_MODEL,
        device=device,
        embed_batch_size=32
    )
    
    # Initialize Pinecone
    pinecone_index = initialize_pinecone()
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # Check if index is empty
    if pinecone_index.describe_index_stats().total_vector_count > 0:
        print("Loading existing index from Pinecone")
        return VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embed_model
        )
    
    print("No existing index found. Creating new index with OCR support...")
    documents = []
    ocr_processor = OCRProcessor()
    
    # Process all files in the faqs directory
    faqs_dir = Path("src/faqs/")
    supported_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
    
    for file_path in faqs_dir.rglob('*'):
        if file_path.suffix.lower() in {'.pdf'}:
            # Process PDF with OCR
            pages_data = ocr_processor.extract_text_from_pdf(str(file_path))
            for page in pages_data:
                doc = Document(
                    text=page['text'],
                    metadata={
                        "source": page['source'],
                        "page_number": page['page_number'],
                        "content_type": "pdf"
                    }
                )
                documents.append(doc)
                
        elif file_path.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
            # Process images with OCR
            ocr_result = ocr_processor.process_image(str(file_path))
            if ocr_result:
                doc = Document(
                    text=ocr_result['text'],
                    metadata={
                        "source": ocr_result['source'],
                        "page_number": 1,
                        "content_type": "image"
                    }
                )
                documents.append(doc)
    
    if not documents:
        raise ValueError("No valid documents found in the faqs directory")
    
    print(f"Processed {len(documents)} documents with OCR support")
    
    # Create index with the processed documents
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model
    )
    
    print("Index created with OCR support and stored in Pinecone")
    return index

# Initialize components with Pinecone
try:
    faq_index = get_or_create_index()
except Exception as e:
    raise RuntimeError(f"Failed to initialize Pinecone: {str(e)}") from e

# Initialize LLM for querying
local_llm = MistralAI(
    model="mistral-large-latest",  # or any other Mistral model you prefer
    api_key=os.environ['MISTRAL_API_KEY'],
    temperature=0
)

# Define a custom text QA template that includes source information
TextQATemplate = PromptTemplate("""
Context information is below.
----------------------
{context_str}
----------------------
Given the context information and not prior knowledge, answer the question.
If the answer is not in the context, say you don't know. Don't make up an answer.
Include the source document name and page number in your response.

Question: {query_str}
Answer: """)

# Create query engine with source tracking
faq_query_engine = faq_index.as_query_engine(
    llm=local_llm,
    similarity_top_k=3,
    verbose=True,
    response_mode="compact",
    text_qa_template=TextQATemplate,
    streaming=False
)

def format_sources(sources: List[NodeWithScore]) -> str:
    """Format source information for display."""
    if not sources:
        return "\n\nNo source information available."
    
    formatted = ["\n\n📄 Source Information:", "-" * 40]
    for i, node in enumerate(sources, 1):
        metadata = node.node.metadata
        source = metadata.get('source', 'Unknown Document')
        page = metadata.get('page_number', 'N/A')
        score = f"{node.score:.2f}" if hasattr(node, 'score') else 'N/A'
        
        # Clean up the source filename for display
        source_name = Path(source).name if source != 'Unknown Document' else source
        
        formatted.extend([
            f"\n🔍 Source {i}:",
            f"   • Document: {source_name}",
            f"   • Page: {page}",
            f"   • Confidence: {score}",
            f"\n   📝 Snippet:\n   {node.node.text[:250].strip()}...",
            "-" * 40
        ])
    
    return "\n".join(formatted)

def query_faq_pdf(question: str) -> str:
    """
    Search the FAQ with OCR support and return the most relevant answer
    along with source information.
    
    Args:
        question: The user's question or query
        
    Returns:
        str: Formatted response with answer and source information
    """
    if not question or not question.strip():
        return "Please provide a valid question."
    
    try:
        print(f"\n🔍 Searching for: {question}")
        
        # Get response with source nodes
        response = faq_query_engine.query(question)
        
        # Get the response text
        response_text = str(response).strip()
        
        # Always include source information if available
        if hasattr(response, 'source_nodes') and response.source_nodes:
            source_info = format_sources(response.source_nodes)
            return f"{response_text}\n{source_info}"
        
        # If no source nodes but we have a response, return it with a note
        if response_text:
            return f"{response_text}\n\nℹ️ No specific source information available for this response."
            
        return "I couldn't find a relevant answer in the FAQ. Could you try rephrasing your question?"
    
    except Exception as e:
        error_msg = f"Error querying FAQ: {str(e)}"
        print(f"❌ {error_msg}")
        return (
            "I'm sorry, but I encountered an error while processing your request. "
            "Please try again or contact support if the issue persists.\n"
            f"Error details: {str(e)}"
        )