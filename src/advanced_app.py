"""
Advanced English Tutor Chatbot
Features: Multi-Agent, Real RAG, TTS, Progress Tracking
"""

import streamlit as st
import google.generativeai as genai
import os
from datetime import datetime
from pathlib import Path  

# Import backend modules
from backend.rag.advanced_rag import AdvancedRAG
from backend.agents.multi_agent import AgentRouter, AgentType
from backend.models.user_progress import ConversationHistory, UserProgressTracker
from backend.utils.tts import TextToSpeechEngine, create_audio_player_html
from backend.utils.security import InputSanitizer
from backend.agents.reflection_agent import ReflectionAgent


# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="English Tutor AI",
    page_icon="📚",
    layout="wide"
)


# ==================== INITIALIZE SYSTEMS ====================
@st.cache_resource
def initialize_rag():
    """Initialize RAG system (runs once)"""
    rag_system = AdvancedRAG(data_dir="../data")
    stats = rag_system.load_all_data()
    return rag_system, stats


def initialize_gemini():
    """Initialize Gemini model"""
    api_key = "AIzaSyC0G7aHcFEO212EFQLMk1bN6MlnxeIUYtU"
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model


@st.cache_resource
def initialize_agent_router(_model):
    """Initialize agent router"""
    return AgentRouter(_model)


@st.cache_resource
def initialize_tts():
    """Initialize TTS engine"""
    return TextToSpeechEngine(output_dir="../data/audio")

@st.cache_resource
def initialize_reflection_agent(_model):
    """Initialize reflection agent"""
    return ReflectionAgent(_model)


# Initialize all systems
rag_system, rag_stats = initialize_rag()
model = initialize_gemini()
agent_router = initialize_agent_router(model)
tts_engine = initialize_tts()
reflection_agent = initialize_reflection_agent(model) 


# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = "default_user"

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = ConversationHistory(
        st.session_state.user_id,
        storage_dir="../data/user_data"
    )

if "progress_tracker" not in st.session_state:
    st.session_state.progress_tracker = UserProgressTracker(
        st.session_state.user_id,
        storage_dir="../data/user_data"
    )

if "tts_enabled" not in st.session_state:
    st.session_state.tts_enabled = False

# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("⚙️ Settings")
    
    # TTS Toggle
    st.session_state.tts_enabled = st.checkbox(
        "🔊 Đọc chữ",
        value=st.session_state.tts_enabled
    )

    if st.session_state.tts_enabled:
        st.caption("📝 **Cách dùng:** `đọc: text` hoặc `read: text`")
    
    st.divider()

    # NEW: Reflection Toggle (LƯU VÀO SESSION STATE)
    if "use_reflection" not in st.session_state:
        st.session_state.use_reflection = False
    
    st.session_state.use_reflection = st.checkbox(
        "🤔 Tự đánh giá câu trả lời",
        value=st.session_state.use_reflection,
        help="Agent will self-critique and improve responses (slower but better)"
    )
    
    st.divider()
    
    # Progress Summary
    st.subheader("📊 Your Progress")
    progress_summary = st.session_state.progress_tracker.get_summary()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Số câu đã hỏi", progress_summary["statistics"]["total_queries"])
        st.metric("Từ vựng đã học", progress_summary["vocabulary_count"])
    with col2:
        st.metric("Ngữ pháp đã học", progress_summary["grammar_topics_count"])
        st.metric("Bài tập đã học", progress_summary["statistics"]["exercises_completed"])
    
    # Average score
    avg_score = progress_summary["average_exercise_score"]
    if avg_score > 0:
        st.metric("Avg Exercise Score", f"{avg_score:.1%}")
    
    st.divider()
    
    # Recommendations
    if st.button("💡 Đề xuất"):
        recommendations = st.session_state.progress_tracker.get_recommendations()
        
        st.subheader("📚 Đã đề xuất")
        
        if recommendations["vocabulary_to_review"]:
            st.write("**Words to Review:**")
            st.write(", ".join(recommendations["vocabulary_to_review"][:5]))
        
        if recommendations["grammar_topics_to_practice"]:
            st.write("**Grammar Topics to Practice:**")
            for topic in recommendations["grammar_topics_to_practice"][:3]:
                st.write(f"- {topic}")
    
    # st.divider()
    
    # # RAG Stats
    # st.subheader("📖 Kiến thức")
    # if rag_stats:
    #     st.write(f"**Tài liệu:** {rag_stats.get('total', 0)}")
    #     st.write(f"- Từ vựng: {rag_stats.get('vocabulary', 0)}")
    #     st.write(f"- Ngữ pháp: {rag_stats.get('grammar', 0)}")
    #     st.write(f"- Bài tập: {rag_stats.get('exercises', 0)}")
    
    # st.divider()
    
    # Clear conversation
    if st.button("🗑️ Xóa lịch sử chat"):
        st.session_state.conversation_history.save_session()
        st.session_state.conversation_history.clear_session()
        st.session_state.messages = []
        st.rerun()
        
    # Force reload database
    if st.button("🔄 Tải lại cơ sở dữ liệu", help="Delete and reload all data (takes ~60 min)"):
        import shutil
        
        # Delete persistent ChromaDB
        chroma_dir = Path("chroma_db")
        if chroma_dir.exists():
            shutil.rmtree(chroma_dir)
            st.success("✅ Database deleted!")
            st.info("🔄 Restart app to reload: streamlit run advanced_app.py")
            st.warning("⏱️ First load will take ~60 minutes to process 15K documents")
        else:
            st.warning("No database found to delete")
        
    # About
    st.divider()
    st.caption("Version 2.0")
    st.caption("🤖 Powered by: Google Gemini 1.5 Flash, ChromaDB, gTTS")


# ==================== MAIN CHAT INTERFACE ====================
st.title("📚 English Tutor AI")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show TTS if available
        if message["role"] == "assistant" and "audio_base64" in message and message["audio_base64"]:
            audio_html = create_audio_player_html(message["audio_base64"])
            st.markdown(audio_html, unsafe_allow_html=True)


# ==================== CHAT INPUT ====================
# ==================== IMAGE UPLOAD (VISION) ====================
st.subheader("📷 Tải ảnh lên phân tích")

uploaded_image = st.file_uploader(
    "Tải ảnh chữ lên phân tích",
    type=['png', 'jpg', 'jpeg', 'webp'],
    help="Tải ảnh chụp màn hình, ảnh chụp, hoặc ảnh tài liệu",
    label_visibility="collapsed"
)

if uploaded_image is not None:
    # NEW: Validate image
    file_size = len(uploaded_image.getvalue())
    file_ext = uploaded_image.name.split('.')[-1]
    
    is_valid, error_msg = InputSanitizer.validate_image_upload(file_size, file_ext)
    
    if not is_valid:
        st.error(f"❌ {error_msg}")
        st.stop()

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
    
    with col2:
        if st.button("🔍 Analyze Image", type="primary"):
            with st.spinner("Analyzing image with Gemini Vision..."):
                try:
                    from PIL import Image
                    import io
                    
                    # Load image
                    image_bytes = uploaded_image.getvalue()
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Create vision prompt
                    vision_prompt = """
                    Phân tích ảnh này theo các bước sau:

                    **BƯỚC 1: PHÁT HIỆN NGÔN NGỮ**
                    - Xác định văn bản trong ảnh là Tiếng Anh hay Tiếng Việt

                    **BƯỚC 2: TRÍCH XUẤT VĂN BẢN**
                    - Viết ra CHÍNH XÁC toàn bộ văn bản thấy trong ảnh (giữ nguyên ngôn ngữ gốc)

                    **BƯỚC 3: PHÂN TÍCH NGỮ PHÁP (CHỈ NẾU LÀ TIẾNG ANH)**
                    Nếu văn bản là Tiếng Anh:
                    - Kiểm tra lỗi ngữ pháp
                    - Giải thích ngữ pháp bằng TIẾNG VIỆT
                    - Đưa ra sửa lỗi (nếu có)

                    **BƯỚC 4: DỊCH THUẬT**
                    - Nếu văn bản gốc là Tiếng Anh → Dịch sang Tiếng Việt
                    - Nếu văn bản gốc là Tiếng Việt → Dịch sang Tiếng Anh

                    **ĐỊNH DẠNG TRẢ LỜI:**

                    📝 **Văn bản gốc:**
                    [Viết chính xác văn bản trong ảnh]

                    🔍 **Phân tích ngữ pháp:** (chỉ nếu là Tiếng Anh)
                    [Giải thích bằng Tiếng Việt]

                    ✅ **Sửa lỗi:** (nếu có)
                    [Câu đúng]

                    🌐 **Bản dịch:**
                    - Nếu gốc là Tiếng Anh → [Dịch sang Tiếng Việt]
                    - Nếu gốc là Tiếng Việt → [Dịch sang Tiếng Anh]

                    💡 **Ghi chú học tập:**
                    [Lưu ý quan trọng về ngữ pháp/từ vựng - bằng Tiếng Việt]
                    """
                    
                    # Call Gemini Vision
                    response = model.generate_content([vision_prompt, image])
                    
                    # Display result
                    st.success("✅ Analysis Complete!")
                    st.markdown(response.text)
                    
                    # Save to conversation
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"[Image uploaded for analysis]"
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.text,
                        "agent": "Vision Analysis"
                    })
                    
                    # Track progress
                    st.session_state.progress_tracker.increment_query_count()
                    
                except Exception as e:
                    st.error(f"❌ Error analyzing image: {e}")

st.divider()

if prompt := st.chat_input("Ask me anything about English..."):
    
    # NEW: Sanitize input
    sanitized_prompt, is_safe, warning = InputSanitizer.sanitize(prompt)
    
    if not is_safe:
        # Show security warning
        st.error(warning)
        st.warning("🛡️ Your input was blocked for security reasons. Please rephrase your question.")
        st.stop()
    
    if warning:
        # Show truncation warning
        st.warning(warning)
    
    # Use sanitized prompt
    prompt = sanitized_prompt

    # NEW: Check if user wants TTS
    tts_requested = False
    tts_text = None
    
    # Detect TTS command: "đọc: text" or "read: text"
    if prompt.lower().startswith(("đọc:", "read:")):
        tts_requested = True
        # Extract text after "đọc:" or "read:"
        tts_text = prompt.split(":", 1)[1].strip()
        
        # Generate TTS immediately
        with st.spinner("🔊 Generating audio..."):
            audio_base64 = tts_engine.text_to_speech_base64(
                tts_text, 
                slow=False, 
                max_duration_seconds=30
            )
            
            if audio_base64:
                st.success(f"✅ Audio generated (max 30s)")
                audio_html = create_audio_player_html(audio_base64)
                st.markdown(audio_html, unsafe_allow_html=True)
                
                # Show what will be read
                st.info(f"📝 Reading: {tts_text[:100]}...")
            else:
                st.error("❌ Failed to generate audio")
        
        # Don't process as regular chat
        st.stop()
    
    # Regular chat processing (existing code)
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process query
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Step 1: RAG Search
            rag_results = rag_system.search_with_reranking(prompt, n_results=3)
            
            # Step 2: Agent Processing
            context = {
                "rag_results": rag_results.get("results", []),
                "conversation_history": st.session_state.messages[-6:]
            }
            
            agent_response = agent_router.process_query(prompt, context=context)
            
            # Step 3: Format response
            if agent_response["success"]:
                response_text = agent_response["response"]
                agent_name = agent_response["routed_to"].replace("_", " ").title()
                
                # Show agent info
                st.caption(f"🤖 **Agent:** {agent_name}")
                
                # NEW: Apply reflection if enabled
                if st.session_state.use_reflection:
                    with st.spinner("🤔 Reflecting on response quality..."):
                        try:
                            reflection_result = reflection_agent.reflect_and_improve(
                                original_query=prompt,
                                original_response=response_text,
                                agent_type=agent_name,
                                conversation_history=st.session_state.messages  # ← NEW
                            )
                            
                            confidence = reflection_result.get("confidence_score", 0.8)
                            
                            if reflection_result.get("needs_improvement"):
                                st.warning(f"🔍 **Self-Critique:** {reflection_result.get('critique', 'N/A')}")
                                st.info("✨ **Improved Response Below:**")
                                response_text = reflection_result.get("improved_response", response_text)
                            else:
                                st.success(f"✅ **Quality Check Passed** - Confidence: {confidence:.0%}")
                                
                        except Exception as e:
                            st.warning(f"⚠️ Reflection failed: {e}")
                # Show response (original or improved)
                st.markdown(response_text)
                
                # Show sources if RAG found results
                if rag_results["success"] and rag_results["results"]:
                    with st.expander("📚 Sources", expanded=False):
                        for idx, result in enumerate(rag_results["results"][:3], 1):
                            st.write(f"**{idx}. {result['metadata']['source'].title()}**")
                            st.write(f"File: {result['metadata'].get('file', 'N/A')}")
                            st.write(f"Score: {result['combined_score']:.3f}")
                            st.caption(result["document"][:200] + "...")
                            st.divider()
                
                # REMOVED: Auto TTS generation
                # Now only generate TTS when user explicitly requests
                
                # Save to session (no audio)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "agent": agent_name,
                    "audio_base64": None  # No auto audio
                })
                
            else:
                error_msg = f"Sorry, I encountered an error: {agent_response.get('error', 'Unknown error')}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
# ==================== UPDATE PROGRESS TRACKING ====================
    # Track this interaction
    st.session_state.progress_tracker.increment_query_count()
    
    # Add to conversation history
    st.session_state.conversation_history.add_message(
        role="user",
        content=prompt
    )
    
    if agent_response["success"]:
        st.session_state.conversation_history.add_message(
            role="assistant",
            content=response_text,
            metadata={
                "agent_type": agent_response["routed_to"],
                "rag_used": rag_results["success"],
                "reflection_used": st.session_state.use_reflection
            }
        )
        
        # Track vocabulary if vocabulary agent was used
        if agent_response["routed_to"] == "vocabulary_expert":
            # Extract words from query
            words = [w.strip().lower() for w in prompt.split() 
                    if len(w) > 3 and w.isalpha()]
            for word in words[:3]:  # Track first 3 words
                st.session_state.progress_tracker.add_vocabulary(
                    word=word,
                    metadata={"learned_from": "query"}
                )
        
        # Track grammar topics if grammar agent was used
        if agent_response["routed_to"] == "grammar_expert":
            # Simple topic extraction
            grammar_topics = ["present perfect", "past simple", "conditionals", 
                            "passive voice", "future tense", "articles"]
            for topic in grammar_topics:
                if topic in prompt.lower():
                    st.session_state.progress_tracker.add_grammar_topic(
                        topic=topic,
                        mastery_level=0.6
                    )
                    break


# ==================== EXAMPLE QUERIES ====================
if len(st.session_state.messages) == 0:
    st.subheader("💡 Ví dụ đề xuất:")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📖 Nghĩa của từ 'resilient' là gì?"):
            st.session_state.user_query = "Nghĩa của từ 'resilient' là gì?"
            st.rerun()

    with col2:
        if st.button("📝 Giải thích thì hiện tại hoàn thành"):
            st.session_state.user_query = "Giải thích thì hiện tại hoàn thành?"
            st.rerun()

    with col3:
        if st.button("✍️ Tạo bài tập Tiếng Anh"):
            st.session_state.user_query = "Tạo 3 bài tập ngẫu nhiên"
            st.rerun()

    with col4:
        if st.button("🔊 TTS Demo"):
            st.session_state.user_query = "đọc: The quick brown fox jumps over the lazy dog"
            st.rerun()

# Handle button clicks
if "user_query" in st.session_state:
    query = st.session_state.user_query
    del st.session_state.user_query
    
    # NEW: Check if TTS command
    if query.lower().startswith(("đọc:", "read:")):
        # Handle TTS command
        tts_text = query.split(":", 1)[1].strip()
        
        # Add to messages
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Generate TTS
        with st.spinner("🔊 Generating audio..."):
            audio_base64 = tts_engine.text_to_speech_base64(
                tts_text, slow=False, max_duration_seconds=30
            )
            
            if audio_base64:
                # Create response message with audio
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"✅ Audio generated (max 30s)\n\n📝 Reading: {tts_text}",
                    "audio_base64": audio_base64
                })
        
        st.rerun()  # Refresh to show in chat
        
    else:
        # Regular query processing (existing code)
        st.session_state.messages.append({"role": "user", "content": query})
        
        # RAG Search
        rag_results = rag_system.search_with_reranking(query, n_results=3)
        
        # Agent Processing
        context = {
            "rag_results": rag_results.get("results", []),
            "conversation_history": st.session_state.messages[-6:]
        }
        agent_response = agent_router.process_query(query, context=context)
    
    if agent_response["success"]:
        response_text = agent_response["response"]
        agent_name = agent_response["routed_to"].replace("_", " ").title()
        
        # Generate TTS if enabled
        audio_base64 = None
        if st.session_state.tts_enabled:
            tts_text = response_text[:300]
            audio_base64 = tts_engine.text_to_speech_base64(tts_text, slow=False)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "agent": agent_name,
            "audio_base64": audio_base64
        })
        
        # Update tracking
        st.session_state.progress_tracker.increment_query_count()
        st.session_state.conversation_history.add_message(
            role="user",
            content=query
        )
        st.session_state.conversation_history.add_message(
            role="assistant",
            content=response_text,
            metadata={"agent_type": agent_response["routed_to"]}
        )
    
    st.rerun()
