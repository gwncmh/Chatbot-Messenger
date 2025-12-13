"""
Conversation History & User Progress Tracking System
Stores conversations and tracks learning progress
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions


class ConversationHistory:
    """
    Manages conversation history storage and retrieval
    Uses ChromaDB for semantic search over past conversations
    """
    
    def __init__(self, user_id: str, storage_dir: str = "../data/user_data"):
        self.user_id = user_id
        self.storage_dir = Path(storage_dir) / user_id
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # ChromaDB for semantic conversation search
        self.client = chromadb.Client()
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name=f"conversations_{user_id}",
            embedding_function=self.embedding_function
        )
        
        # Current session messages
        self.current_session = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add message to current session
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (agent_type, tools_used, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.current_session.append(message)
        
        # Add to ChromaDB for semantic search
        doc_id = f"{self.session_id}_{len(self.current_session)}"
        
        self.collection.add(
            documents=[content],
            ids=[doc_id],
            metadatas=[{
                "session_id": self.session_id,
                "role": role,
                "timestamp": message["timestamp"],
                **message["metadata"]
            }]
        )
    
    def get_current_session(self) -> List[Dict[str, Any]]:
        """Get all messages in current session"""
        return self.current_session
    
    def get_recent_context(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get last n messages for context"""
        return self.current_session[-n:] if len(self.current_session) > n else self.current_session
    
    def search_past_conversations(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search past conversations semantically
        
        Args:
            query: Search query
            n_results: Number of results
        
        Returns:
            List of relevant past messages
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            # Format results
            formatted = []
            for doc, metadata, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                formatted.append({
                    "content": doc,
                    "metadata": metadata,
                    "relevance": 1 - distance,
                    "timestamp": metadata.get("timestamp", "N/A")
                })
            
            return formatted
            
        except Exception as e:
            print(f"Error searching conversations: {e}")
            return []
    
    def save_session(self):
        """Save current session to JSON file"""
        if not self.current_session:
            return
        
        filename = self.storage_dir / f"session_{self.session_id}.json"
        
        session_data = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": self.current_session,
            "message_count": len(self.current_session),
            "started_at": self.current_session[0]["timestamp"] if self.current_session else None,
            "ended_at": datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        print(f"Session saved: {filename}")
    
    def clear_session(self):
        """Clear current session (start new conversation)"""
        self.save_session()
        self.current_session = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")


class UserProgressTracker:
    """
    Tracks user's learning progress
    """
    
    def __init__(self, user_id: str, storage_dir: str = "../data/user_data"):
        self.user_id = user_id
        self.storage_dir = Path(storage_dir) / user_id
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.progress_file = self.storage_dir / "progress.json"
        
        # Load existing progress or initialize
        self.progress = self._load_progress()
    
    def _load_progress(self) -> Dict[str, Any]:
        """Load progress from file"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self._initialize_progress()
    
    def _initialize_progress(self) -> Dict[str, Any]:
        """Initialize new progress structure"""
        return {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            
            "statistics": {
                "total_queries": 0,
                "total_sessions": 0,
                "vocabulary_learned": 0,
                "grammar_topics_covered": 0,
                "exercises_completed": 0
            },
            
            "vocabulary": {
                "learned_words": [],
                "words_in_progress": [],
                "words_to_review": []
            },
            
            "grammar": {
                "topics_studied": [],
                "topics_in_progress": [],
                "weak_areas": []
            },
            
            "mistakes": {
                "common_mistakes": [],
                "error_patterns": []
            },
            
            "exercises": {
                "completed": [],
                "scores_by_topic": {}
            }
        }
    
    def save_progress(self):
        """Save progress to file"""
        self.progress["last_updated"] = datetime.now().isoformat()
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)
    
    def increment_query_count(self):
        """Increment total queries"""
        self.progress["statistics"]["total_queries"] += 1
        self.save_progress()
    
    def add_vocabulary(self, word: str, metadata: Dict[str, Any] = None):
        """Add word to learned vocabulary"""
        existing = next((w for w in self.progress["vocabulary"]["learned_words"] 
                        if w["word"].lower() == word.lower()), None)
        
        if existing:
            existing["times_reviewed"] += 1
            existing["last_reviewed"] = datetime.now().isoformat()
        else:
            self.progress["vocabulary"]["learned_words"].append({
                "word": word,
                "learned_at": datetime.now().isoformat(),
                "times_reviewed": 1,
                "metadata": metadata or {}
            })
            self.progress["statistics"]["vocabulary_learned"] += 1
        
        self.save_progress()
    
    def add_grammar_topic(self, topic: str, mastery_level: float = 0.6):
        """Add or update a grammar topic with progressive mastery"""
        
        # Tìm topic đã tồn tại trong list
        existing = next((t for t in self.progress["grammar"]["topics_studied"]
                        if t["topic"].lower() == topic.lower()), None)
        
        if existing:
            # Topic đã học rồi → Tăng mastery lên 10%
            current_mastery = existing["mastery_level"]
            new_mastery = min(current_mastery + 0.1, 1.0)  # Max 100%
            
            existing["mastery_level"] = new_mastery
            existing["last_studied"] = datetime.now().isoformat()
            existing["times_studied"] += 1
            
            print(f"📈 Updated '{topic}': {current_mastery:.0%} → {new_mastery:.0%}")
        else:
            # Topic mới → Thêm vào list với mastery mặc định
            self.progress["grammar"]["topics_studied"].append({
                "topic": topic,
                "studied_at": datetime.now().isoformat(),
                "last_studied": datetime.now().isoformat(),
                "mastery_level": mastery_level,
                "times_studied": 1
            })
            self.progress["statistics"]["grammar_topics_covered"] += 1
            
            print(f"✨ New topic '{topic}': {mastery_level:.0%}")
        
        self.save_progress()
    
    def record_mistake(self, mistake_type: str, example: str):
        """Record a common mistake"""
        existing = next((m for m in self.progress["mistakes"]["common_mistakes"]
                        if m["mistake_type"] == mistake_type), None)
        
        if existing:
            existing["count"] += 1
            existing["examples"].append({
                "example": example,
                "timestamp": datetime.now().isoformat()
            })
            existing["examples"] = existing["examples"][-5:]
        else:
            self.progress["mistakes"]["common_mistakes"].append({
                "mistake_type": mistake_type,
                "count": 1,
                "examples": [{
                    "example": example,
                    "timestamp": datetime.now().isoformat()
                }]
            })
        
        self.save_progress()
    
    def record_exercise_completion(self, exercise_id: str, topic: str, score: float):
        """Record completed exercise"""
        self.progress["exercises"]["completed"].append({
            "exercise_id": exercise_id,
            "topic": topic,
            "completed_at": datetime.now().isoformat(),
            "score": score
        })
        
        if topic not in self.progress["exercises"]["scores_by_topic"]:
            self.progress["exercises"]["scores_by_topic"][topic] = []
        
        self.progress["exercises"]["scores_by_topic"][topic].append(score)
        self.progress["exercises"]["scores_by_topic"][topic] = \
            self.progress["exercises"]["scores_by_topic"][topic][-10:]
        
        self.progress["statistics"]["exercises_completed"] += 1
        
        self.save_progress()
    
    def get_weak_topics(self, threshold: float = 0.6) -> List[str]:
        """Get topics where user scored below threshold"""
        weak_topics = []
        
        for topic, scores in self.progress["exercises"]["scores_by_topic"].items():
            avg_score = sum(scores) / len(scores)
            if avg_score < threshold:
                weak_topics.append({
                    "topic": topic,
                    "avg_score": avg_score,
                    "attempts": len(scores)
                })
        
        return sorted(weak_topics, key=lambda x: x["avg_score"])
    
    def get_recommendations(self) -> Dict[str, Any]:
        """Get personalized learning recommendations"""
        recommendations = {
            "vocabulary_to_review": [],
            "grammar_topics_to_practice": [],
            "suggested_exercises": []
        }
        
        # Words to review (not reviewed in 7+ days)
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        for word_data in self.progress["vocabulary"]["learned_words"]:
            if word_data.get("last_reviewed", word_data["learned_at"]) < week_ago:
                recommendations["vocabulary_to_review"].append(word_data["word"])
        
        # Weak grammar topics
        weak_topics = self.get_weak_topics(threshold=0.7)
        recommendations["grammar_topics_to_practice"] = [t["topic"] for t in weak_topics[:3]]
        
        # Topics with low mastery
        for topic_data in self.progress["grammar"]["topics_studied"]:
            if topic_data["mastery_level"] < 0.7:
                recommendations["grammar_topics_to_practice"].append(topic_data["topic"])
        
        return recommendations
    
    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary for display"""
        return {
            "statistics": self.progress["statistics"],
            "vocabulary_count": len(self.progress["vocabulary"]["learned_words"]),
            "grammar_topics_count": len(self.progress["grammar"]["topics_studied"]),
            "average_exercise_score": self._calculate_average_exercise_score(),
            "common_mistakes": self.progress["mistakes"]["common_mistakes"][:5],
            "weak_topics": self.get_weak_topics(threshold=0.7)[:3]
        }
    
    def _calculate_average_exercise_score(self) -> float:
        """Calculate average score across all exercises"""
        all_scores = []
        for scores in self.progress["exercises"]["scores_by_topic"].values():
            all_scores.extend(scores)
        
        return sum(all_scores) / len(all_scores) if all_scores else 0.0