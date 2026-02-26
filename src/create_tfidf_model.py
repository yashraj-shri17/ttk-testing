"""
TF-IDF model creation module for Bhagavad Gita verses.

This module creates a TF-IDF based search model for keyword-based search,
particularly useful for Hindi/Hinglish queries.
"""
import json
import pickle
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from sklearn.feature_extraction.text import TfidfVectorizer

from src.config import settings
from src.logger import setup_logger
from src.exceptions import DataFileNotFoundError, EmbeddingGenerationError

logger = setup_logger(__name__, settings.LOG_LEVEL, settings.LOG_FILE)


# Stopwords for Hindi (basic list)
HINDI_STOPWORDS: Set[str] = {
    "me", "mein", "ko", "se", "ka", "ki", "ke", "hai", "hain", "aur", "toh", "hi", "bhi",
    "tha", "the", "thi", "kar", "karna", "wale", "wala", "wali", "ne", "par", "liye",
    "saath", "kya", "kyon", "kaise", "kab", "kahan", "kisi", "kuch", "sab", "sabse",
    "apna", "apni", "apne", "tum", "tumhara", "hum", "hamara", "main", "mera", "meri",
    "is", "us", "iska", "uska", "ye", "woh", "wo", "unka", "unki", "unke", "in", "un"
}


class TextPreprocessor:
    """Text preprocessing utilities for Hindi/English text."""
    
    @staticmethod
    def clean_text(text: str, stopwords: Optional[Set[str]] = None) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Input text to clean
            stopwords: Set of stopwords to remove
            
        Returns:
            Cleaned text
        """
        if stopwords is None:
            stopwords = HINDI_STOPWORDS
        
        # Keep alphanumeric characters and Hindi characters (Devanagari)
        text = re.sub(r'[^\w\s\u0900-\u097F]', ' ', text)
        
        # Tokenize and remove stopwords
        tokens = text.lower().split()
        cleaned_tokens = [word for word in tokens if word not in stopwords]
        
        return " ".join(cleaned_tokens)


class TFIDFModelBuilder:
    """Build and manage TF-IDF model for Gita verses."""
    
    def __init__(
        self,
        input_file: Optional[Path] = None,
        output_file: Optional[Path] = None
    ):
        """
        Initialize the TF-IDF model builder.
        
        Args:
            input_file: Path to input JSON file with Gita data
            output_file: Path to save TF-IDF model
        """
        self.input_file = input_file or settings.gita_emotions_path
        self.output_file = output_file or settings.tfidf_model_path
        self.preprocessor = TextPreprocessor()
        
    def load_data(self) -> Dict[str, Any]:
        """
        Load Gita data from JSON file.
        
        Returns:
            Dictionary containing Gita data
            
        Raises:
            DataFileNotFoundError: If input file doesn't exist
        """
        logger.info(f"Loading Gita data from {self.input_file}")
        
        if not self.input_file.exists():
            raise DataFileNotFoundError(
                f"Input file not found: {self.input_file}. "
                "Please ensure the data file exists."
            )
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Successfully loaded data from {self.input_file}")
            return data
        except json.JSONDecodeError as e:
            raise EmbeddingGenerationError(f"Invalid JSON in {self.input_file}: {e}")
        except Exception as e:
            raise EmbeddingGenerationError(f"Error loading data: {e}")
    
    def prepare_texts(
        self,
        data: Dict[str, Any],
        emotion_threshold: float = 0.4
    ) -> tuple[List[Dict], List[str]]:
        """
        Prepare texts from Gita data for TF-IDF vectorization.
        
        Args:
            data: Dictionary containing Gita chapters and verses
            emotion_threshold: Threshold for including emotion keywords
            
        Returns:
            Tuple of (shloka_list, texts_for_tfidf)
        """
        logger.info("Preparing texts for TF-IDF vectorization...")
        
        shloka_list = []
        texts_for_tfidf = []
        
        chapters = data.get('chapters', {})
        
        for ch_id, verses in chapters.items():
            for v_id, verse in verses.items():
                meaning = verse.get('meaning', '')
                
                # Add emotion keywords to boost semantic matching
                emotions = verse.get('emotions', {})
                top_emotions = [
                    emotion for emotion, score in emotions.items()
                    if score > emotion_threshold
                ]
                emotion_text = " ".join(top_emotions)
                
                # Combine meaning with emotion keywords
                full_text = f"{meaning} {emotion_text}"
                cleaned_text = self.preprocessor.clean_text(full_text)
                
                shloka_info = {
                    "id": f"{ch_id}.{v_id}",
                    "text": verse.get('text', ''),
                    "meaning": meaning,
                    "emotions": emotions
                }
                
                shloka_list.append(shloka_info)
                texts_for_tfidf.append(cleaned_text)
        
        logger.info(f"Prepared {len(texts_for_tfidf)} verses for vectorization")
        return shloka_list, texts_for_tfidf
    
    def create_vectorizer(
        self,
        texts: List[str],
        min_df: int = 1,
        ngram_range: tuple = (1, 2)
    ) -> tuple[TfidfVectorizer, Any]:
        """
        Create TF-IDF vectorizer and transform texts.
        
        Args:
            texts: List of texts to vectorize
            min_df: Minimum document frequency
            ngram_range: Range of n-grams to consider
            
        Returns:
            Tuple of (vectorizer, tfidf_matrix)
        """
        logger.info(f"Creating TF-IDF vectorizer with ngram_range={ngram_range}")
        
        try:
            vectorizer = TfidfVectorizer(
                min_df=min_df,
                ngram_range=ngram_range,
                max_features=10000  # Limit features for performance
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            logger.info(
                f"Vectorization complete. "
                f"Vocabulary size: {len(vectorizer.vocabulary_)}, "
                f"Matrix shape: {tfidf_matrix.shape}"
            )
            
            return vectorizer, tfidf_matrix
            
        except Exception as e:
            raise EmbeddingGenerationError(f"Failed to create vectorizer: {e}")
    
    def save_model(
        self,
        shlokas: List[Dict],
        vectorizer: TfidfVectorizer,
        tfidf_matrix: Any
    ) -> None:
        """
        Save TF-IDF model and metadata to file.
        
        Args:
            shlokas: List of shloka metadata
            vectorizer: Fitted TF-IDF vectorizer
            tfidf_matrix: TF-IDF matrix
        """
        logger.info(f"Saving TF-IDF model to {self.output_file}")
        
        try:
            # Ensure output directory exists
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.output_file, 'wb') as f:
                pickle.dump({
                    'shlokas': shlokas,
                    'vectorizer': vectorizer,
                    'matrix': tfidf_matrix
                }, f)
            
            logger.info(f"Successfully saved model to {self.output_file}")
        except Exception as e:
            raise EmbeddingGenerationError(f"Failed to save model: {e}")
    
    def build_model(self) -> None:
        """
        Main method to build and save TF-IDF model.
        
        This orchestrates the entire model building process.
        """
        try:
            # Load data
            data = self.load_data()
            
            # Prepare texts
            shloka_list, texts_for_tfidf = self.prepare_texts(data)
            
            # Create vectorizer
            vectorizer, tfidf_matrix = self.create_vectorizer(texts_for_tfidf)
            
            # Save model
            self.save_model(shloka_list, vectorizer, tfidf_matrix)
            
            logger.info("✓ TF-IDF model creation completed successfully!")
            logger.info("You can now use the TF-IDF search functionality.")
            
        except Exception as e:
            logger.error(f"Model building failed: {e}")
            raise


def main():
    """Main entry point for TF-IDF model building."""
    try:
        builder = TFIDFModelBuilder()
        builder.build_model()
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
