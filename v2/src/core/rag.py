# v2/src/core/rag.py
import os
import PyPDF2
import docx2txt
import re
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

class EnhancedDocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def setup_document_processing(self, collection_name: str = "documents"):
        """Initialize vector database for document processing"""
        try:
            # Setup ChromaDB
            chroma_client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create or get collection
            collection = chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            print("✅ Vector database setup complete")
            return collection
            
        except Exception as e:
            print(f"❌ Vector database setup failed: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF files"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text if text else "No extractable text found in PDF"
        except Exception as e:
            return f"Error extracting PDF text: {e}"
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            return docx2txt.process(docx_path)
        except Exception as e:
            return f"Error extracting DOCX text: {e}"
    
    def extract_text_from_txt(self, txt_path: str) -> str:
        """Extract text from TXT files"""
        try:
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            return f"Error extracting TXT text: {e}"
    
    def split_text(self, text: str) -> List[str]:
        """Simple text splitter without LangChain dependency"""
        # Split by paragraphs, sentences, or fixed length
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        
        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                # Split long paragraphs into smaller chunks
                words = paragraph.split()
                current_chunk = []
                current_length = 0
                
                for word in words:
                    if current_length + len(word) + 1 > self.chunk_size:
                        if current_chunk:
                            chunks.append(' '.join(current_chunk))
                            current_chunk = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else []
                            current_length = sum(len(w) + 1 for w in current_chunk)
                        current_chunk.append(word)
                        current_length += len(word) + 1
                    else:
                        current_chunk.append(word)
                        current_length += len(word) + 1
                
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
            else:
                chunks.append(paragraph)
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def process_single_document(self, file_path: str) -> Dict[str, Any]:
        """Process a single document and return chunks with metadata"""
        try:
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # Extract text based on file type
            if file_ext == '.pdf':
                content = self.extract_text_from_pdf(file_path)
            elif file_ext == '.docx':
                content = self.extract_text_from_docx(file_path)
            elif file_ext == '.txt':
                content = self.extract_text_from_txt(file_path)
            else:
                return {
                    'success': False,
                    'file_name': file_name,
                    'error': f'Unsupported file type: {file_ext}'
                }
            
            if content.startswith('Error'):
                return {
                    'success': False,
                    'file_name': file_name,
                    'error': content
                }
            
            # Split into chunks
            chunks = self.split_text(content)
            
            return {
                'success': True,
                'file_name': file_name,
                'file_path': file_path,
                'content': content,
                'chunks': chunks,
                'chunk_count': len(chunks),
                'file_type': file_ext
            }
            
        except Exception as e:
            return {
                'success': False,
                'file_name': os.path.basename(file_path),
                'error': f'Processing error: {e}'
            }
    
    def process_local_documents(self, collection, folder_path: str = "./documents", clear_existing: bool = False):
        """Process all documents in a folder and add to vector store"""
        try:
            if not os.path.exists(folder_path):
                print(f"❌ Documents folder not found: {folder_path}")
                return False
            
            if clear_existing:
                collection.delete(where={})
                print("🧹 Cleared existing documents")
            
            supported_extensions = {'.pdf', '.docx', '.txt'}
            processed_files = []
            failed_files = []
            total_chunks = 0
            
            print(f"📁 Processing documents from: {folder_path}")
            
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    file_ext = os.path.splitext(filename)[1].lower()
                    
                    if file_ext in supported_extensions:
                        result = self.process_single_document(file_path)
                        
                        if result['success']:
                            # Add chunks to vector store
                            chunks = result['chunks']
                            metadatas = [
                                {
                                    'file_name': result['file_name'],
                                    'file_path': result['file_path'],
                                    'file_type': result['file_type'],
                                    'chunk_index': i
                                } for i in range(len(chunks))
                            ]
                            
                            collection.add(
                                documents=chunks,
                                metadatas=metadatas,
                                ids=[f"{result['file_name']}_{i}" for i in range(len(chunks))]
                            )
                            
                            processed_files.append(result['file_name'])
                            total_chunks += len(chunks)
                            
                            print(f"✅ Loaded {file_ext.upper()}: {result['file_name']} ({len(chunks)} pages)")
                        else:
                            failed_files.append({
                                'file_name': result['file_name'],
                                'error': result['error']
                            })
                            print(f"❌ Failed to process: {result['file_name']} - {result['error']}")
            
            # Print processing summary
            self._print_processing_summary(processed_files, failed_files, total_chunks)
            
            return True
            
        except Exception as e:
            print(f"❌ Document processing failed: {e}")
            return False
    
    def _print_processing_summary(self, processed_files: List[str], failed_files: List[Dict], total_chunks: int):
        """Print a nice processing summary"""
        print("\n" + "="*50)
        print("📊 PROCESSING SUMMARY")
        print("="*50)
        print(f"📁 Total files found: {len(processed_files) + len(failed_files)}")
        print(f"✅ Successfully processed: {len(processed_files)}")
        print(f"❌ Failed files: {len(failed_files)}")
        print(f"📄 Total chunks created: {total_chunks}")
        
        if processed_files:
            print(f"\n📋 Processed files:")
            for file in processed_files:
                print(f"  • {file}")
        
        if failed_files:
            print(f"\n⚠️  Failed files:")
            for failed in failed_files:
                print(f"  • {failed['file_name']}: {failed['error']}")
        
        print("="*50)
    
    def search_local_documents(self, collection, query: str, max_results: int = 5, include_metadata: bool = True):
        """Search through processed documents"""
        try:
            results = collection.query(
                query_texts=[query],
                n_results=max_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                similarity_score = 1 - distance  # Convert distance to similarity score
                
                result = {
                    'content': doc,
                    'similarity_score': similarity_score,
                    'rank': i + 1
                }
                
                if include_metadata:
                    result.update({
                        'file_name': metadata.get('file_name', 'Unknown'),
                        'file_path': metadata.get('file_path', 'Unknown'),
                        'file_type': metadata.get('file_type', 'Unknown'),
                        'chunk_index': metadata.get('chunk_index', 0)
                    })
                
                formatted_results.append(result)
            
            print(f"🔍 Found {len(formatted_results)} relevant chunks (best similarity: {formatted_results[0]['similarity_score']:.3f})")
            return formatted_results
            
        except Exception as e:
            print(f"❌ Document search failed: {e}")
            return []
    
    def get_collection_stats(self, collection) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        try:
            # Get total document count
            count_result = collection.count()
            
            # Get some sample documents to analyze
            sample_results = collection.get(limit=100)
            
            total_chunks = count_result
            unique_files = set()
            file_types = {}
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    if 'file_name' in metadata:
                        unique_files.add(metadata['file_name'])
                    if 'file_type' in metadata:
                        file_type = metadata['file_type']
                        file_types[file_type] = file_types.get(file_type, 0) + 1
            
            return {
                'total_documents': total_chunks,
                'unique_files': len(unique_files),
                'file_types': file_types,
                'sample_files': list(unique_files)[:5]  # First 5 unique files
            }
            
        except Exception as e:
            print(f"❌ Failed to get collection stats: {e}")
            return {}
