"""
Advanced RAG System - Compatible with existing data structure
Loads from: data/vocab/, data/grammar/, data/exercise/
"""

import os
import json
import glob
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import PyPDF2


class AdvancedRAG:
    """
    RAG System that loads from existing data/ folder structure
    
    Supports:
    - data/vocab/oxford-3000-es.json (and other JSON vocab files)
    - data/grammar/*.json (CoEdIT grammar)
    - data/grammar/*.pdf (PDF files like Grammar in Use)
    - data/exercise/*.json (trivia exercises)
    """
    
    def __init__(self, data_dir: str = "../data"):
        """Initialize RAG system with data directory"""
        self.data_dir = Path(data_dir)
        
        # Use PersistentClient
        persist_dir = Path("./chroma_db")
        persist_dir.mkdir(exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        
        # Try to get existing collection
        try:
            self.collection = self.client.get_collection(name="english_learning")
            print("✅ Using existing ChromaDB collection")
            self._skip_loading = True
            
            # NEW: Load cached stats from file
            stats_file = persist_dir / "stats.json"
            if stats_file.exists():
                import json
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self._cached_stats = json.load(f)
                print(f"✓ Loaded stats from cache: {self._cached_stats['total']} documents")
            else:
                print("⚠️ No stats cache found - will calculate on first query")
                self._cached_stats = None
                
        except:
            print("📦 Creating new ChromaDB collection...")
            self.collection = self.client.create_collection(
                name="english_learning",
                metadata={"description": "English learning content"}
            )
            self._skip_loading = False
            self._cached_stats = None
    
    def load_all_data(self) -> Dict[str, int]:
        """Load all data from existing structure"""
        
        # Return cached stats if available
        if hasattr(self, '_skip_loading') and self._skip_loading:
            if self._cached_stats:
                print(f"✓ Using cached statistics")
                return self._cached_stats
            else:
                # Collection exists but no stats cache - calculate once
                print("📊 Calculating statistics from collection metadata...")
                count = self.collection.count()
                
                # Calculate breakdown (only once, then cached)
                try:
                    all_metadata = self.collection.get(limit=count)['metadatas']
                    
                    vocab_count = sum(1 for m in all_metadata if m.get('source') == 'vocabulary')
                    grammar_count = sum(1 for m in all_metadata if m.get('source') == 'grammar')
                    exercise_count = sum(1 for m in all_metadata if m.get('source') == 'exercise')
                    
                    stats = {
                        "total": count,
                        "vocabulary": vocab_count,
                        "grammar": grammar_count,
                        "exercises": exercise_count
                    }
                    
                    # Save to cache for next time
                    self._save_stats_cache(stats)
                    
                    return stats
                    
                except Exception as e:
                    print(f"⚠️ Error calculating stats: {e}")
                    return {
                        "total": count,
                        "vocabulary": 0,
                        "grammar": 0,
                        "exercises": 0
                    }
        
        # First time loading - process all data
        stats = {
            "vocabulary": 0,
            "grammar": 0,
            "exercises": 0,
            "total": 0
        }
        
        print("📚 Loading data from existing structure...")
        
        # Load vocabulary (JSON files)
        vocab_dir = self.data_dir / "vocab"
        if vocab_dir.exists():
            stats["vocabulary"] = self._load_vocabulary(vocab_dir)
        
        # Load grammar (JSON + PDF files)
        grammar_dir = self.data_dir / "grammar"
        if grammar_dir.exists():
            stats["grammar"] = self._load_grammar_pdfs(grammar_dir)
        
        # Load exercises (JSON)
        exercise_dir = self.data_dir / "exercise"
        if exercise_dir.exists():
            stats["exercises"] = self._load_exercises(exercise_dir)
        
        stats["total"] = sum(stats.values())
        
        print(f"\n✅ Loaded {stats['total']} documents:")
        print(f"   - Vocabulary: {stats['vocabulary']}")
        print(f"   - Grammar: {stats['grammar']}")
        print(f"   - Exercises: {stats['exercises']}")
        
        # Save stats to cache
        self._save_stats_cache(stats)
        
        return stats


    def _save_stats_cache(self, stats: Dict[str, int]):
        """Save statistics to cache file"""
        try:
            import json
            stats_file = Path("./chroma_db/stats.json")
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            print("💾 Statistics cached to disk")
        except Exception as e:
            print(f"⚠️ Failed to cache stats: {e}")
    
    def _load_vocabulary(self, vocab_dir: Path) -> int:
        """Load vocabulary JSON files"""
        count = 0
        
        for json_file in glob.glob(str(vocab_dir / "*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different JSON structures
                if isinstance(data, list):
                    vocab_list = data
                elif isinstance(data, dict) and "words" in data:
                    vocab_list = data["words"]
                else:
                    vocab_list = [data]
                
                for idx, item in enumerate(vocab_list):
                    # Flexible structure handling
                    word = item.get("word", item.get("headword", "unknown"))
                    
                    # Build searchable text
                    text_parts = [f"Word: {word}"]
                    
                    if "class" in item:
                        text_parts.append(f"Part of Speech: {item['class']}")
                    
                    if "level" in item:
                        text_parts.append(f"Level: {item['level']}")
                    
                    # Definitions
                    if "definitions" in item:
                        for defn in item.get("definitions", [])[:3]:  # Max 3
                            if isinstance(defn, dict):
                                text_parts.append(f"Definition: {defn.get('definition', '')}")
                            else:
                                text_parts.append(f"Definition: {defn}")
                    
                    # Spanish translation if available
                    if "spanish" in item:
                        text_parts.append(f"Spanish: {item['spanish']}")
                    
                    text = "\n".join(text_parts)
                    
                    # Add to collection
                    doc_id = f"vocab_{word.lower()}_{idx}"
                    
                    self.collection.add(
                        documents=[text],
                        ids=[doc_id],
                        metadatas=[{
                            "source": "vocabulary",
                            "word": word,
                            "level": item.get("level", "unknown"),
                            "file": os.path.basename(json_file)
                        }]
                    )
                    
                    count += 1
                
                print(f"   ✓ Loaded {len(vocab_list)} words from {os.path.basename(json_file)}")
                
            except Exception as e:
                print(f"   ✗ Error loading {json_file}: {e}")
        
        return count
    
    def _load_grammar_pdfs(self, grammar_dir: Path) -> int:
        """Load grammar from PDFs AND JSON files"""
        count = 0
        
        # 1. Load JSON files (CoEdIT)
        for json_file in glob.glob(str(grammar_dir / "*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle list of grammar examples
                if isinstance(data, list):
                    grammar_items = data
                else:
                    grammar_items = [data]
                
                for idx, item in enumerate(grammar_items):
                    # Build searchable text
                    text_parts = []
                    
                    # CoEdIT format
                    if "incorrect" in item and "correct" in item:
                        text_parts.append(f"Incorrect: {item['incorrect']}")
                        text_parts.append(f"Correct: {item['correct']}")
                        if "task" in item:
                            text_parts.append(f"Task: {item['task']}")
                        if "explanation" in item:
                            text_parts.append(f"Explanation: {item['explanation']}")
                    
                    if not text_parts:
                        continue
                    
                    text = "\n".join(text_parts)
                    doc_id = f"grammar_json_{idx}_{hash(text) % 10000}"
                    
                    self.collection.add(
                        documents=[text],
                        ids=[doc_id],
                        metadatas=[{
                            "source": "grammar",
                            "type": "correction",
                            "file": os.path.basename(json_file)
                        }]
                    )
                    count += 1
                
                print(f"   ✓ Loaded {len(grammar_items)} examples from {os.path.basename(json_file)}")
            
            except Exception as e:
                print(f"   ✗ Error loading {json_file}: {e}")
        
        # 2. Load PDFs (backward compatibility)
        for pdf_file in glob.glob(str(grammar_dir / "*.pdf")):
            try:
                print(f"   Loading PDF: {os.path.basename(pdf_file)}...")
                
                with open(pdf_file, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    max_pages = min(50, len(pdf_reader.pages))
                    
                    for page_num in range(max_pages):
                        try:
                            page = pdf_reader.pages[page_num]
                            text = page.extract_text()
                            
                            if len(text.strip()) < 100:
                                continue
                            
                            chunks = self._chunk_text(text, chunk_size=500)
                            
                            for chunk_idx, chunk in enumerate(chunks):
                                if len(chunk.strip()) < 50:
                                    continue
                                
                                doc_id = f"grammar_pdf_p{page_num}_c{chunk_idx}"
                                
                                self.collection.add(
                                    documents=[chunk],
                                    ids=[doc_id],
                                    metadatas=[{
                                        "source": "grammar",
                                        "type": "pdf",
                                        "page": page_num + 1,
                                        "file": os.path.basename(pdf_file)
                                    }]
                                )
                                
                                count += 1
                        
                        except Exception as e:
                            continue
                
                print(f"   ✓ Loaded chunks from PDF")
                
            except Exception as e:
                print(f"   ✗ Error loading PDF {pdf_file}: {e}")
        
        return count
    
    def _load_exercises(self, exercise_dir: Path) -> int:
        """Load exercise JSON files - UPDATED to support Trivia format"""
        count = 0
        
        for json_file in glob.glob(str(exercise_dir / "*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different structures
                if isinstance(data, list):
                    exercises = data
                elif isinstance(data, dict):
                    exercises = []
                    for key, value in data.items():
                        if isinstance(value, list):
                            exercises.extend(value)
                        elif isinstance(value, dict):
                            exercises.append(value)
                
                for idx, exercise in enumerate(exercises):
                    # Build searchable text
                    text_parts = []
                    
                    # NEW: Handle trivia format
                    if "question" in exercise and "correct_answer" in exercise:
                        text_parts.append(f"Question: {exercise['question']}")
                        text_parts.append(f"Answer: {exercise['correct_answer']}")
                        
                        if "incorrect_answers" in exercise:
                            all_options = [exercise['correct_answer']] + exercise['incorrect_answers']
                            text_parts.append(f"Options: {', '.join(all_options)}")
                        
                        if "category" in exercise:
                            text_parts.append(f"Category: {exercise['category']}")
                    
                    # OLD: Handle original format (compatibility)
                    elif "sentence" in exercise:
                        text_parts.append(f"Sentence: {exercise['sentence']}")
                    
                    if "topic" in exercise:
                        text_parts.append(f"Topic: {exercise['topic']}")
                    
                    if "explanation" in exercise:
                        text_parts.append(f"Explanation: {exercise['explanation']}")
                    
                    if not text_parts:
                        continue
                    
                    text = "\n".join(text_parts)
                    
                    doc_id = f"exercise_{idx}_{hash(text) % 10000}"
                    
                    self.collection.add(
                        documents=[text],
                        ids=[doc_id],
                        metadatas=[{
                            "source": "exercise",
                            "topic": exercise.get("topic", exercise.get("category", "general")),
                            "type": exercise.get("type", "multiple_choice"),
                            "file": os.path.basename(json_file)
                        }]
                    )
                    
                    count += 1
                
                print(f"   ✓ Loaded {len(exercises)} exercises from {os.path.basename(json_file)}")
                
            except Exception as e:
                print(f"   ✗ Error loading {json_file}: {e}")
        
        return count
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            
            if current_length >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def search(self, query: str, n_results: int = 5,
               filter_source: str = None) -> Dict[str, Any]:
        """Search knowledge base"""
        try:
            where_filter = {"source": filter_source} if filter_source else None
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            if not results['documents'] or not results['documents'][0]:
                return {"success": False, "results": []}
            
            formatted = []
            for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                formatted.append({
                    "document": doc,
                    "metadata": meta,
                    "score": 1 - dist
                })
            
            return {"success": True, "results": formatted}
            
        except Exception as e:
            return {"success": False, "error": str(e), "results": []}
    
    def search_with_reranking(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """Search with keyword reranking"""
        
        # Initial retrieval (2x results)
        initial = self.search(query, n_results=n_results * 2)
        
        if not initial["success"] or not initial["results"]:
            return initial
        
        # Rerank
        query_keywords = set(query.lower().split())
        
        for result in initial["results"]:
            doc_lower = result["document"].lower()
            keyword_matches = sum(1 for kw in query_keywords if kw in doc_lower)
            result["keyword_matches"] = keyword_matches
            result["combined_score"] = result["score"] + (keyword_matches * 0.1)
        
        # Sort and return top-k
        initial["results"].sort(key=lambda x: x["combined_score"], reverse=True)
        
        return {
            "success": True,
            "results": initial["results"][:n_results],
            "reranking_applied": True
        }