# src/faq_pdf_tool.py

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
import os

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

data_files = ["src/faqs/faq_data.pdf"]
documents = SimpleDirectoryReader(input_files=data_files).load_data()


faq_index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)


model="llama-3.3-70b-versatile"
local_llm = Groq(model=model, api_key=os.environ['GROQ_API_KEY'], temperature=0)


faq_query_engine = faq_index.as_query_engine(llm=local_llm)


def query_faq_pdf(question: str) -> str:
    """
    Search the FAQ PDF and return the most relevant answer using
    the local LLM and embedding.
    """
    response = faq_query_engine.query(question)
    return str(response)


