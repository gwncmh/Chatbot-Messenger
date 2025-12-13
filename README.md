# 📚 English Tutor AI

🎓 Project in: Topics in Computer Science INT3121 2 (VNU-UET)
Description: Multi-Agent AI system for English learning with RAG

## Team
1. Chung Thị Mai Anh 23021460
2. Nguyễn Công Mạnh Hùng 23021567
3. Phạm Công Khanh 23021596

## ✨ Features

- 🤖 **Multi-Agent Architecture**: 4 specialized agents (Grammar, Vocabulary, Conversation, Exercise)
- 📖 **RAG System**: 14,935+ documents (Oxford 3000, CoEdIT Grammar, Trivia Exercises)
- 🔊 **Text-to-Speech**: gTTS integration for pronunciation practice
- 📊 **Progress Tracking**: Persistent user progress and recommendations
- 🤔 **Self-Reflection**: Quality assurance with reflection pattern
- 📷 **Vision Support**: Image OCR for grammar checking
- 🔒 **Input Sanitization**: Security against prompt injection

## 🛠️ Tech Stack

- **LLM**: Google Gemini 2.5 Flash
- **Vector DB**: ChromaDB with semantic search
- **Framework**: Streamlit
- **TTS**: gTTS
- **Data Processing**: Python, Pandas, PyPDF2

**Concepts Demonstrated:**
- Foundation Models (Gemini)
- Multi-Agent Systems
- RAG (Retrieval-Augmented Generation)
- Reflection Pattern
- Vision-Language Models
- Input Sanitization

## Công nghệ sử dụng

- **LLM:** Google Gemini 2.5
- **Vector DB:** ChromaDB
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- **Framework:** Streamlit
- **External APIs:** Free Dictionary API

## Patterns đã áp dụng

1. **Routing Pattern** - Phân loại ý định người dùng
2. **Tool Use Pattern** - Sử dụng các công cụ phù hợp
3. **RAG Pattern** - Truy xuất kiến thức từ vector database
4. **Chain-of-Thought** - Suy luận từng bước
5. **Reflection Pattern** - Tự đánh giá trước khi trả lời

## 📊 Dataset Statistics

- **Total Documents**: 14,935
- **Vocabulary**: 3,785 words (Oxford 3000)
- **Grammar**: 10,000 examples (CoEdIT)
- **Exercises**: 1,150 questions (Trivia)

## 🙏 Acknowledgments

- Google Gemini API
- Grammarly CoEdIT Dataset
- Oxford 3000 Word List
- OpenTriviaDB

## System Architecture
```
User Input
    ↓
[Intent Classification] ← LLM Call 1
    ↓
[Tool Selection] ← Logic-based (no LLM)
    ├─→ Dictionary API
    ├─→ Grammar Checker
    ├─→ Example Generator
    └─→ RAG (ChromaDB)
    ↓
[Final Response Generation] ← LLM Call 2
    ↓
User Output
```

#### Video demo: https://drive.google.com/drive/folders/14p1-BSAr1ICtSvxSrUntvU80vdQOJmbR?lfhs=2

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/gwncmh/Chatbot-Messenger.git
cd Chatbot-Messenger
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download datasets:
```bash
cd src/scripts
python download_all_datasets.py
```

5. Run the app:
```bash
cd ../
streamlit run advanced_app.py
-------------------------------