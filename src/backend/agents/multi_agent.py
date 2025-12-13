"""
Multi-Agent System for English Tutoring
Compatible with existing Chatbot-Messenger project
"""

from typing import Dict, Any
from enum import Enum


class AgentType(Enum):
    """Agent types"""
    GRAMMAR_EXPERT = "grammar_expert"
    VOCABULARY_EXPERT = "vocabulary_expert"
    CONVERSATION_PARTNER = "conversation_partner"
    EXERCISE_GENERATOR = "exercise_generator"


class BaseAgent:
    """Base agent class"""
    
    def __init__(self, agent_type: AgentType, model):
        self.agent_type = agent_type
        self.model = model
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        raise NotImplementedError
    
    def _build_prompt_with_history(self, query: str, context: Dict[str, Any]) -> str:
        """Build prompt including conversation history"""
        prompt = f"{self.system_prompt}\n\n"
        
        # Add conversation history if available
        if context and "conversation_history" in context:
            history = context["conversation_history"]
            if len(history) > 0:
                prompt += "📜 **Lịch sử hội thoại gần đây:**\n"
                for msg in history[-6:]:  # Last 3 exchanges (6 messages)
                    role = "Học sinh" if msg["role"] == "user" else "Trợ lý"
                    prompt += f"{role}: {msg['content'][:150]}...\n"
                prompt += "\n"
        
        prompt += f"🎯 **Câu hỏi hiện tại:** \"{query}\"\n\n"
        
        return prompt
    
    def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        raise NotImplementedError


class GrammarExpertAgent(BaseAgent):
    """Grammar specialist"""
    
    def __init__(self, model):
        super().__init__(AgentType.GRAMMAR_EXPERT, model)
    
    def _get_system_prompt(self) -> str:
        return """Bạn là giáo viên ngữ pháp tiếng Anh chuyên nghiệp với 20+ năm kinh nghiệm.

Chuyên môn:
- Giải thích quy tắc ngữ pháp rõ ràng, súc tích
- Đưa ra ví dụ cho mỗi quy tắc
- Giải thích lỗi phổ biến
- Sử dụng tiếng Việt khi giải thích khái niệm phức tạp

Phong cách giảng dạy:
- Bắt đầu với công thức/quy tắc cơ bản
- 3-5 ví dụ rõ ràng
- Giải thích lỗi thường gặp
- Tips để nhớ quy tắc

Cấu trúc:
1. Formula/Rule → Examples → Common Mistakes → Tips
2. Dùng bullet points và format rõ ràng
3. Khuyến khích và kiên nhẫn"""
    
    def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        # Build prompt with history
        prompt = self._build_prompt_with_history(query, context)
        
        # Add RAG results if available
        if context and "rag_results" in context and len(context["rag_results"]) > 0:
            prompt += "📚 **Kiến thức ngữ pháp liên quan:**\n"
            for r in context["rag_results"][:2]:
                prompt += f"- {r['document'][:200]}...\n"
            prompt += "\n"
        
        prompt += """✍️ **Nhiệm vụ của bạn:**
    Dựa vào lịch sử hội thoại (nếu có), hãy trả lời câu hỏi hiện tại một cách mạch lạc.
    Nếu câu hỏi liên quan đến câu trước, hãy kết nối với ngữ cảnh đã thảo luận.

    Hãy đưa ra giải thích có cấu trúc rõ ràng:"""
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "success": True,
                "agent": self.agent_type.value,
                "response": response.text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class VocabularyExpertAgent(BaseAgent):
    """Vocabulary specialist"""
    
    def __init__(self, model):
        super().__init__(AgentType.VOCABULARY_EXPERT, model)
    
    def _get_system_prompt(self) -> str:
        return """Bạn là giáo viên từ vựng tiếng Anh chuyên gia.

Chuyên môn:
- Giải thích nghĩa từ đơn giản
- Đưa context và ví dụ sử dụng
- Dạy collocations (từ đi cùng nhau)
- Giải thích word families
- Chia sẻ tricks ghi nhớ

Cấu trúc giải thích:
1. Định nghĩa đơn giản
2. 3-4 ví dụ trong ngữ cảnh khác nhau
3. Collocations phổ biến
4. Synonyms/Antonyms
5. Word family (verb, noun, adj, adv)
6. Memory trick"""
    
    def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = self._build_prompt_with_history(query, context)
        
        if context and "rag_results" in context and len(context["rag_results"]) > 0:
            prompt += "📖 **Thông tin từ điển:**\n"
            for r in context["rag_results"][:2]:
                prompt += f"- {r['document'][:200]}...\n"
            prompt += "\n"
        
        prompt += """✍️ **Nhiệm vụ của bạn:**
    Dựa vào lịch sử hội thoại, trả lời câu hỏi về từ vựng một cách toàn diện.
    Nếu câu hỏi liên quan đến từ đã học trước đó, hãy kết nối với kiến thức đã thảo luận.

    Hãy đưa ra bài học từ vựng chi tiết:"""
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "success": True,
                "agent": self.agent_type.value,
                "response": response.text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class ConversationPartnerAgent(BaseAgent):
    """Conversation partner"""
    
    def __init__(self, model):
        super().__init__(AgentType.CONVERSATION_PARTNER, model)
        self.history = []
    
    def _get_system_prompt(self) -> str:
        return """Bạn là người bạn luyện tiếng Anh thân thiện, kiên nhẫn.

Vai trò:
- Tham gia hội thoại tự nhiên
- Sửa lỗi nhẹ nhàng (không quá khắt khe)
- Đặt câu hỏi tiếp theo để duy trì cuộc trò chuyện
- Đưa ra cách diễn đạt thay thế
- Khuyến khích học sinh nói nhiều hơn

Phong cách:
- Tự nhiên, thân thiện
- Hỗ trợ và khuyến khích
- Kiên nhẫn với lỗi

Khi học sinh mắc lỗi:
1. Phản hồi tự nhiên trước
2. Chỉ ra lỗi nhẹ nhàng
3. Đưa ra dạng đúng
4. Giải thích ngắn gọn
5. Tiếp tục cuộc trò chuyện"""
    
    def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        self.history.append({"role": "user", "message": query})
        
        prompt = f"""{self.system_prompt}

Lịch sử hội thoại:
"""
        for msg in self.history[-6:]:
            prompt += f"{msg['role'].title()}: {msg['message']}\n"
        
        prompt += "\nHãy phản hồi tự nhiên và hữu ích:"
        
        try:
            response = self.model.generate_content(prompt)
            self.history.append({"role": "assistant", "message": response.text})
            
            return {
                "success": True,
                "agent": self.agent_type.value,
                "response": response.text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class ExerciseGeneratorAgent(BaseAgent):
    """Exercise generator"""
    
    def __init__(self, model):
        super().__init__(AgentType.EXERCISE_GENERATOR, model)
    
    def _get_system_prompt(self) -> str:
        return """Bạn là chuyên gia tạo bài tập tiếng Anh hiệu quả.

Chuyên môn:
- Thiết kế bài tập phù hợp với trình độ
- Tạo bài tập cho các điểm ngữ pháp cụ thể
- Nhiều loại bài tập (MCQ, Fill-in-blanks, Error correction)
- Hướng dẫn rõ ràng
- Có đáp án và giải thích

Format bài tập:
[Loại bài tập]
Hướng dẫn: ...
Câu hỏi:
1. ...
2. ...
Đáp án:
1. ... (Giải thích: ...)"""
    
    def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        prompt = self._build_prompt_with_history(query, context)
        
        if context and "rag_results" in context and len(context["rag_results"]) > 0:
            prompt += "📝 **Tham khảo bài tập mẫu:**\n"
            for r in context["rag_results"][:2]:
                prompt += f"- {r['document'][:200]}...\n"
            prompt += "\n"
        
        prompt += """✍️ **Nhiệm vụ của bạn:**
    Dựa vào lịch sử hội thoại (chủ đề đã học), tạo bài tập phù hợp.

    Hãy tạo 3-5 bài tập bao gồm:
    1. Hướng dẫn rõ ràng
    2. Câu hỏi
    3. Đáp án kèm giải thích"""
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "success": True,
                "agent": self.agent_type.value,
                "response": response.text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class AgentRouter:
    """Routes queries to appropriate agent"""
    
    def __init__(self, model):
        self.model = model
        self.agents = {
            AgentType.GRAMMAR_EXPERT: GrammarExpertAgent(model),
            AgentType.VOCABULARY_EXPERT: VocabularyExpertAgent(model),
            AgentType.CONVERSATION_PARTNER: ConversationPartnerAgent(model),
            AgentType.EXERCISE_GENERATOR: ExerciseGeneratorAgent(model)
        }
    
    def route(self, query: str) -> AgentType:
        """Determine which agent to use"""
        query_lower = query.lower()
        
        # Grammar keywords
        grammar_kw = ['thì', 'tense', 'grammar', 'conditional', 'passive', 
                      'ngữ pháp', 'câu điều kiện', 'giải thích', 'explain']
        
        # Vocabulary keywords
        vocab_kw = ['nghĩa', 'mean', 'meaning', 'what is', 'what does',
                    'từ', 'word', 'vocabulary', 'synonym']
        
        # Exercise keywords
        exercise_kw = ['bài tập', 'exercise', 'practice', 'quiz', 'test',
                       'generate', 'tạo', 'làm']
        
        # Conversation keywords
        conv_kw = ['chat', 'talk', 'conversation', 'trò chuyện', 'nói chuyện']
        
        if any(kw in query_lower for kw in exercise_kw):
            return AgentType.EXERCISE_GENERATOR
        
        if any(kw in query_lower for kw in vocab_kw):
            return AgentType.VOCABULARY_EXPERT
        
        if any(kw in query_lower for kw in grammar_kw):
            return AgentType.GRAMMAR_EXPERT
        
        if any(kw in query_lower for kw in conv_kw):
            return AgentType.CONVERSATION_PARTNER
        
        return AgentType.GRAMMAR_EXPERT
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route and process query"""
        agent_type = self.route(query)
        agent = self.agents[agent_type]
        
        result = agent.process(query, context)
        result["routed_to"] = agent_type.value
        
        return result
    
    def get_agent(self, agent_type: AgentType):
        """Get specific agent"""
        return self.agents.get(agent_type)