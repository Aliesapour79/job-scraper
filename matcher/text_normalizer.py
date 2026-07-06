# matcher/text_normalizer.py
"""
نرمال‌سازی متن برای تطابق بهتر کلمات کلیدی
"""

import re
import unicodedata

class TextNormalizer:
    """نرمال‌ساز متن برای کلمات فارسی و انگلیسی"""
    
    @staticmethod
    def normalize_persian(text: str) -> str:
        """نرمال‌سازی حروف فارسی"""
        if not text:
            return text
        
        # جایگزینی حروف مشابه
        replacements = {
            'ی': ['ي', 'ى', 'ئ'],  # همه شکل‌های 'ی'
            'ک': ['ك'],           # 'ک' با 'ك'
            'گ': ['ګ'],           # 'گ' با 'ګ'
            'آ': ['ا'],           # 'آ' با 'ا'
            'ئ': ['ي', 'ى'],      # 'ئ' با 'ی'
            'ء': '',              # حذف 'ء'
        }
        
        for standard, variants in replacements.items():
            for variant in variants:
                text = text.replace(variant, standard)
        
        return text
    
    @staticmethod
    def normalize_english(text: str) -> str:
        """نرمال‌سازی حروف انگلیسی (lowercase و حذف کاراکترهای اضافی)"""
        if not text:
            return text
        
        # lowercase
        text = text.lower()
        
        # حذف کاراکترهای خاص (فقط حروف و اعداد و فاصله)
        text = re.sub(r'[^\w\s\-]', '', text)
        
        return text
    
    @staticmethod
    def normalize(text: str) -> str:
        """نرمال‌سازی کامل متن (فارسی و انگلیسی)"""
        if not text:
            return text
        
        # نرمال‌سازی فارسی
        text = TextNormalizer.normalize_persian(text)
        
        # نرمال‌سازی انگلیسی (برای کلمات انگلیسی)
        # تشخیص کلمات انگلیسی با regex ساده
        parts = re.split(r'([a-zA-Z]+)', text)
        normalized_parts = []
        
        for part in parts:
            if re.match(r'^[a-zA-Z]+$', part):
                normalized_parts.append(TextNormalizer.normalize_english(part))
            else:
                normalized_parts.append(part)
        
        return ''.join(normalized_parts)
    
    @staticmethod
    def keyword_match(text: str, keyword: str) -> bool:
        """بررسی تطابق با نرمال‌سازی"""
        if not text or not keyword:
            return False
        
        text_norm = TextNormalizer.normalize(text.lower())
        keyword_norm = TextNormalizer.normalize(keyword.lower())
        
        # تطابق کامل یا جزئی
        return keyword_norm in text_norm
    
    @staticmethod
    def count_matches(text: str, keywords: list) -> int:
        """تعداد تطابق‌ها با نرمال‌سازی"""
        if not text or not keywords:
            return 0
        
        text_norm = TextNormalizer.normalize(text.lower())
        matched = set()
        
        for keyword in keywords:
            keyword_norm = TextNormalizer.normalize(keyword.lower())
            
            # بررسی تطابق
            if keyword_norm in text_norm:
                matched.add(keyword_norm)
        
        return len(matched)