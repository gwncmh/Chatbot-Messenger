"""
Security utilities for input validation
"""

import re
from typing import Tuple


class InputSanitizer:
    """Sanitize and validate user inputs"""
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r"ignore\s+previous",
        r"ignore\s+all",
        r"system:",
        r"assistant:",
        r"</s>",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"###\s+instruction",
        r"you\s+are\s+now",
        r"pretend\s+you\s+are",
        r"act\s+as\s+if",
        r"override\s+your",
        r"disregard\s+your",
    ]
    
    MAX_LENGTH = 1000  # Max input length
    
    @staticmethod
    def sanitize(user_input: str) -> Tuple[str, bool, str]:
        """
        Sanitize user input
        
        Returns:
            (sanitized_text, is_safe, warning_message)
        """
        
        if not user_input or not user_input.strip():
            return "", False, "Empty input"
        
        original_length = len(user_input)
        
        # 1. Check length
        if original_length > InputSanitizer.MAX_LENGTH:
            user_input = user_input[:InputSanitizer.MAX_LENGTH]
            warning = f"Input truncated from {original_length} to {InputSanitizer.MAX_LENGTH} chars"
        else:
            warning = None
        
        # 2. Check for dangerous patterns
        input_lower = user_input.lower()
        for pattern in InputSanitizer.DANGEROUS_PATTERNS:
            if re.search(pattern, input_lower):
                return "", False, f"⚠️ Suspicious pattern detected: '{pattern}'. Input blocked for security."
        
        # 3. Remove excessive whitespace
        user_input = re.sub(r'\s+', ' ', user_input).strip()
        
        # 4. Basic XSS prevention (for web display)
        dangerous_chars = ['<script>', '</script>', '<iframe>', 'javascript:']
        for char in dangerous_chars:
            if char in user_input.lower():
                return "", False, f"⚠️ Potentially malicious content detected. Input blocked."
        
        return user_input, True, warning
    
    @staticmethod
    def validate_image_upload(file_size_bytes: int, file_extension: str) -> Tuple[bool, str]:
        """
        Validate uploaded image
        
        Returns:
            (is_valid, error_message)
        """
        MAX_SIZE = 10 * 1024 * 1024  # 10MB
        ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'webp']
        
        if file_size_bytes > MAX_SIZE:
            return False, f"File too large: {file_size_bytes / 1024 / 1024:.1f}MB (max 10MB)"
        
        if file_extension.lower() not in ALLOWED_EXTENSIONS:
            return False, f"Invalid file type: {file_extension}"
        
        return True, None