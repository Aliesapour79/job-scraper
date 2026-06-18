
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

class SemanticMatcher:
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        """
        مقداردهی اولیه مدل Embedding
        
        Args:
            model_name: نام مدل از HuggingFace
                - paraphrase-multilingual-MiniLM-L12-v2 (پشتیبانی از فارسی)
                - distiluse-base-multilingual-cased-v2 (پشتیبانی از فارسی)
                - all-MiniLM-L6-v2 (فقط انگلیسی)
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            self.is_loaded = True
            print(f"✅ Semantic model loaded: {model_name}")
        except ImportError:
            print("❌ sentence-transformers not installed!")
            print("   Run: pip install sentence-transformers")
            self.is_loaded = False
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.is_loaded = False
    
    def encode_texts(self, texts, show_progress=False):
        """
        تبدیل متن به بردار (embedding)
        
        Args:
            texts: لیست متن‌ها یا یک متن
            show_progress: نمایش پیشرفت
        
        Returns:
            numpy array of embeddings
        """
        if not self.is_loaded:
            return None
        
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            embeddings = self.model.encode(
                texts, 
                convert_to_tensor=False,
                show_progress_bar=show_progress,
                normalize_embeddings=True  # برای محاسبه‌ی سریع‌تر cosine similarity
            )
            return embeddings
        except Exception as e:
            print(f"❌ Error encoding texts: {e}")
            return None
    
    def calculate_similarity(self, text1, text2):
        """
        محاسبه شباهت معنایی بین دو متن
        
        Returns:
            float: درصد شباهت (0-100)
        """
        if not self.is_loaded:
            return 0
        
        embeddings = self.encode_texts([text1, text2])
        if embeddings is None:
            return 0
        
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity * 100)
    
    def calculate_batch_similarity(self, job_texts, resume_text):
        """
        محاسبه شباهت یک رزومه با لیستی از آگهی‌ها
        
        Returns:
            list: لیست درصدهای شباهت
        """
        if not self.is_loaded or not job_texts:
            return [0] * len(job_texts) if job_texts else []
        
        # تبدیل رزومه به بردار
        resume_embedding = self.encode_texts([resume_text])
        if resume_embedding is None:
            return [0] * len(job_texts)
        
        # تبدیل همه آگهی‌ها به بردار (دسته‌جمعی برای سرعت بیشتر)
        job_embeddings = self.encode_texts(job_texts)
        if job_embeddings is None:
            return [0] * len(job_texts)
        
        # محاسبه شباهت همه با هم
        similarities = cosine_similarity(resume_embedding, job_embeddings)[0]
        return [float(sim * 100) for sim in similarities]
    
    def extract_keywords_from_embedding(self, text, top_n=20):
        """
        استخراج کلمات کلیدی مهم از متن با استفاده از Embedding
        (روش پیشرفته‌تر برای پیدا کردن کلمات مهم)
        """
        if not self.is_loaded:
            return []
        
        words = text.split()
        if len(words) < 2:
            return words
        
        try:
            # محاسبه embedding برای کل متن
            text_embedding = self.encode_texts([text])[0]
            
            # محاسبه embedding برای هر کلمه
            word_embeddings = self.encode_texts(words)
            
            # محاسبه شباهت هر کلمه با کل متن
            similarities = cosine_similarity([text_embedding], word_embeddings)[0]
            
            # مرتب‌سازی بر اساس اهمیت
            word_scores = list(zip(words, similarities))
            word_scores.sort(key=lambda x: x[1], reverse=True)
            
            return [word for word, score in word_scores[:top_n]]
        except:
            return []

# ==========================================
# تابع کمکی برای ترکیب با کد اصلی
# ==========================================

def combine_scores(keyword_score, tfidf_score, embedding_score):
    """
    ترکیب سه امتیاز با وزن‌های مختلف
    
    Args:
        keyword_score: امتیاز کلمه‌کلیدی (0-100)
        tfidf_score: امتیاز TF-IDF (0-100)
        embedding_score: امتیاز Embedding (0-100)
    
    Returns:
        int: امتیاز نهایی (0-100)
    """
    # وزن‌ها را می‌توانید تنظیم کنید
    weights = {
        'keyword': 0.30,    # 40%
        'tfidf': 0.30,      # 30%
        'embedding': 0.40   # 30%
    }
    
    final_score = (
        (keyword_score * weights['keyword']) +
        (tfidf_score * weights['tfidf']) +
        (embedding_score * weights['embedding'])
    )
    
    return int(min(100, final_score))

# ==========================================
# تست
# ==========================================
if __name__ == "__main__":
    print("🧪 Testing Semantic Matcher...")
    
    matcher = SemanticMatcher()
    
    if matcher.is_loaded:
        # تست ۱: شباهت جملات مشابه
        text1 = "برنامه‌نویس پایتون با تجربه هوش مصنوعی"
        text2 = "توسعه‌دهنده پایتون و یادگیری ماشین"
        
        similarity = matcher.calculate_similarity(text1, text2)
        print(f"\n📝 Test 1: Similar sentences")
        print(f"   Text 1: {text1}")
        print(f"   Text 2: {text2}")
        print(f"   Similarity: {similarity:.1f}%")
        
        # تست ۲: جملات غیرمشابه
        text3 = "حسابدار ارشد با تجربه مالی"
        similarity2 = matcher.calculate_similarity(text1, text3)
        print(f"\n📝 Test 2: Different sentences")
        print(f"   Text 1: {text1}")
        print(f"   Text 2: {text3}")
        print(f"   Similarity: {similarity2:.1f}%")
        
        print("\n✅ Semantic Matcher is ready!")
    else:
        print("\n❌ Please install: pip install sentence-transformers")