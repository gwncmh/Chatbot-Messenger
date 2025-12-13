"""
Reflection Agent - Self-critique and improvement
"""

from typing import Dict, Any
import google.generativeai as genai


class ReflectionAgent:
    """Agent that reflects on and improves responses"""
    
    def __init__(self, model: genai.GenerativeModel):
        self.model = model
    
    def reflect_and_improve(self, original_query: str, original_response: str, 
                        agent_type: str, conversation_history: list = None) -> Dict[str, Any]:
        """
        Reflect on response quality with conversation context
        """
        
        reflection_prompt = f"""Bạn là chuyên gia đảm bảo chất lượng cho hệ thống học tiếng Anh.

    **Lịch sử hội thoại gần đây:**
    """
        
        # Add conversation history for context
        if conversation_history and len(conversation_history) > 0:
            for msg in conversation_history[-4:]:  # Last 2 exchanges
                role = "Học sinh" if msg["role"] == "user" else "Trợ lý"
                reflection_prompt += f"{role}: {msg['content'][:100]}...\n"
        else:
            reflection_prompt += "(Không có lịch sử)\n"
        
        reflection_prompt += f"""
    **Câu hỏi hiện tại:**
    {original_query}

    **Loại Agent:**
    {agent_type}

    **Câu trả lời của Agent:**
    {original_response}

    **Nhiệm vụ của bạn:**
    Đánh giá câu trả lời dựa trên:
    1. **Độ chính xác**: Có lỗi sự thật không?
    2. **Tính liên kết**: Có kết nối với câu hỏi trước không (nếu có)?
    3. **Độ đầy đủ**: Trả lời đủ câu hỏi chưa?
    4. **Tính rõ ràng**: Dễ hiểu không?
    5. **Tính hữu ích**: Thực tế cho người học không?

    **Format trả lời:**
    Confidence Score: [0.0-1.0]
    Needs Improvement: [Yes/No]
    Critique: [Nhận xét ngắn gọn nếu cần cải thiện]
    Improved Response: [Chỉ cung cấp nếu Needs Improvement là Yes]

    Hãy nghiêm khắc nhưng công bằng. Chỉ đề xuất cải thiện khi thực sự cần thiết.
    """
        
        try:
            reflection = self.model.generate_content(reflection_prompt)
            result = self._parse_reflection(reflection.text, original_response)
            return result
            
        except Exception as e:
            return {
                "needs_improvement": False,
                "critique": "",
                "improved_response": original_response,
                "confidence_score": 0.8,
                "error": str(e)
            }
    
    def _parse_reflection(self, reflection_text: str, original_response: str) -> Dict[str, Any]:
        """Parse reflection output"""
        
        # Extract confidence score
        confidence = 0.8  # Default
        if "Confidence Score:" in reflection_text:
            try:
                conf_line = [l for l in reflection_text.split('\n') if 'Confidence Score:' in l][0]
                confidence = float(conf_line.split(':')[1].strip())
            except:
                pass
        
        # Check if improvement needed
        needs_improvement = "Needs Improvement: Yes" in reflection_text or "Needs Improvement: yes" in reflection_text
        
        # Extract critique
        critique = ""
        if "Critique:" in reflection_text:
            try:
                critique_start = reflection_text.find("Critique:") + len("Critique:")
                critique_end = reflection_text.find("Improved Response:", critique_start)
                if critique_end == -1:
                    critique = reflection_text[critique_start:].strip()
                else:
                    critique = reflection_text[critique_start:critique_end].strip()
            except:
                pass
        
        # Extract improved response
        improved_response = original_response
        if needs_improvement and "Improved Response:" in reflection_text:
            try:
                improved_start = reflection_text.find("Improved Response:") + len("Improved Response:")
                improved_response = reflection_text[improved_start:].strip()
            except:
                pass
        
        return {
            "needs_improvement": needs_improvement,
            "critique": critique,
            "improved_response": improved_response,
            "confidence_score": confidence
        }