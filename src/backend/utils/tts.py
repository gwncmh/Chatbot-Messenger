"""
Text-to-Speech Module
Converts text to speech for pronunciation practice
"""

from gtts import gTTS
import os
from pathlib import Path
import base64


class TextToSpeechEngine:
    """
    Text-to-Speech engine using gTTS (Google Text-to-Speech)
    Free and works offline after download
    """
    
    def __init__(self, output_dir: str = "../data/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def text_to_speech(self, text: str, lang: str = 'en', 
                       accent: str = 'com', slow: bool = False) -> str:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            lang: Language code ('en' for English)
            accent: Accent ('com' for American, 'co.uk' for British)
            slow: Speak slowly for learning
        
        Returns:
            Path to generated audio file
        """
        try:
            # Generate filename
            filename = f"tts_{hash(text) % 10000}.mp3"
            filepath = self.output_dir / filename
            
            # Generate speech
            tts = gTTS(text=text, lang=lang, tld=accent, slow=slow)
            tts.save(str(filepath))
            
            return str(filepath)
            
        except Exception as e:
            print(f"TTS Error: {e}")
            return None
    
    def text_to_speech_base64(self, text: str, slow: bool = False, max_duration_seconds: int = 30) -> str:
        """
        Convert text to speech and return base64 encoded audio
        
        Args:
            text: Text to convert
            slow: Speak slowly for learning
            max_duration_seconds: Maximum audio duration (default 30s)
        
        Returns:
            Base64 encoded audio string
        """
        try:
            # Estimate duration: ~2.5 words per second (normal), ~1.5 words/s (slow)
            words_per_second = 1.5 if slow else 2.5
            max_words = int(max_duration_seconds * words_per_second)
            
            # Truncate text to fit max duration
            words = text.split()
            if len(words) > max_words:
                text = ' '.join(words[:max_words]) + "..."
                print(f"⚠️ Text truncated to {max_words} words (~{max_duration_seconds}s)")
            
            # Generate TTS
            tts = gTTS(text=text, lang='en', slow=slow)
            
            # Save to BytesIO instead of file
            from io import BytesIO
            audio_bytes = BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            
            # Encode to base64
            audio_base64 = base64.b64encode(audio_bytes.read()).decode('utf-8')
            
            return audio_base64
        
        except Exception as e:
            print(f"TTS Error: {e}")
            return None
    
    def pronounce_word(self, word: str, slow: bool = True) -> str:
        """
        Generate pronunciation for a single word
        
        Args:
            word: Word to pronounce
            slow: Speak slowly
        
        Returns:
            Path to audio file
        """
        return self.text_to_speech(word, slow=slow)
    
    def pronounce_sentence(self, sentence: str, slow: bool = False) -> str:
        """
        Generate pronunciation for a sentence
        
        Args:
            sentence: Sentence to pronounce
            slow: Speak slowly
        
        Returns:
            Path to audio file
        """
        return self.text_to_speech(sentence, slow=slow)


# For Streamlit integration
def create_audio_player_html(audio_base64: str) -> str:
    """
    Create HTML audio player for Streamlit
    
    Args:
        audio_base64: Base64 encoded audio
    
    Returns:
        HTML string with audio player
    """
    html = f"""
    <audio controls autoplay>
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    """
    return html


# Example usage
if __name__ == "__main__":
    tts = TextToSpeechEngine()
    
    # Test word pronunciation
    audio_file = tts.pronounce_word("resilient", slow=True)
    print(f"Word audio: {audio_file}")
    
    # Test sentence
    audio_file = tts.pronounce_sentence("She is a resilient person who never gives up.")
    print(f"Sentence audio: {audio_file}")
    
    # Base64 for web
    audio_b64 = tts.text_to_speech_base64("Hello, how are you?")
    print(f"Base64 length: {len(audio_b64) if audio_b64 else 0}")