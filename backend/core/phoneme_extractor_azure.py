"""
Azure Pronunciation Assessment API Integration
Provides phoneme-level pronunciation feedback using Microsoft Azure Speech Services
"""

import azure.cognitiveservices.speech as speechsdk
import json
import numpy as np
import io
from typing import List, Dict, Any, Optional
from pydub import AudioSegment
import logging
import time

logger = logging.getLogger(__name__)


class AzurePronunciationExtractor:
    """
    Phoneme extractor using Azure Pronunciation Assessment API
    """
    
    def __init__(self, subscription_key: str, region: str = "eastus"):
        """
        Initialize Azure pronunciation extractor
        
        Args:
            subscription_key: Azure Speech Services subscription key
            region: Azure region (e.g., 'eastus', 'westus', 'westeurope')
        """
        self.subscription_key = subscription_key
        self.region = region
        
        # Configure speech service
        self.speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key,
            region=region
        )
        
        # Set language (can be made configurable)
        self.speech_config.speech_recognition_language = "en-US"
        
        logger.info(f"Initialized Azure Pronunciation Extractor (region: {region})")
    
    def extract_phoneme(self, audio, sampling_rate=16000, reference_text=None):
        """
        Extract phonemes from audio (interface compatible with other extractors)
        
        Args:
            audio: Audio data as numpy array
            sampling_rate: Sample rate of the audio
            reference_text: Optional reference text for pronunciation assessment
            
        Returns:
            List of lists of phonemes (one list per word)
        """
        result = self.extract_phonemes(audio, sampling_rate, reference_text)
        return result['phonemes']
    
    def extract_words(self, audio, sampling_rate=16000):
        """
        Extract words from audio (interface compatible with word extractors)
        
        Args:
            audio: Audio data as numpy array
            sampling_rate: Sample rate of the audio
            
        Returns:
            List of recognized words
        """
        result = self.extract_phonemes(audio, sampling_rate, reference_text=None)
        
        # Extract just the words from the recognized text
        recognized_text = result.get('recognized_text', '')
        words = recognized_text.lower().strip().split()
        
        return words
    
    def extract_words_and_phonemes(self, audio, sampling_rate=16000, reference_text=None):
        """
        Extract both words and phonemes in a single call (Azure-optimized)
        
        This method leverages Azure's built-in word recognition and phoneme alignment,
        avoiding the need for separate word extraction and phoneme-to-word alignment.
        
        Args:
            audio: Audio data as numpy array
            sampling_rate: Sample rate of the audio
            reference_text: Optional reference text for pronunciation assessment
            
        Returns:
            Dict containing:
                - words: List of recognized words
                - phonemes: List of lists of phonemes (aligned to words)
                - words_details: Detailed word-level information (if reference_text provided)
                - azure_scores: Overall pronunciation scores (if reference_text provided)
        """
        result = self.extract_phonemes(audio, sampling_rate, reference_text)
        
        # Extract words from recognized text
        recognized_text = result.get('recognized_text', '')
        words = recognized_text.lower().strip().split()
        
        return {
            'words': words,
            'phonemes': result['phonemes'],
            'recognized_text': recognized_text,
            'words_details': result.get('words', []),
            'azure_scores': result.get('azure_scores', {}),
            'backend': 'azure'
        }
    
    def extract_phonemes(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        reference_text: str = None
    ) -> Dict[str, Any]:
        """
        Extract phonemes and pronunciation scores using Azure
        
        Args:
            audio_data: Audio as numpy array
            sample_rate: Sample rate (should be 16000)
            reference_text: Expected sentence/text (optional, but recommended)
        
        Returns:
            Dict with phonemes, accuracy scores, and detailed results
        """
        start_time = time.time()
        
        try:
            # Convert numpy array to WAV bytes
            audio_bytes = self._numpy_to_wav_bytes(audio_data, sample_rate)
            
            # Create audio config
            stream = speechsdk.audio.PushAudioInputStream()
            stream.write(audio_bytes)
            stream.close()
            
            audio_config = speechsdk.audio.AudioConfig(stream=stream)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # If reference text provided, use pronunciation assessment
            if reference_text:
                # Create pronunciation assessment config
                pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                    reference_text=reference_text,
                    grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                    granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
                    enable_miscue=True  # Detect insertions/omissions
                )
                
                # Apply pronunciation assessment config
                pronunciation_config.apply_to(speech_recognizer)
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            # Check result
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                elapsed = time.time() - start_time
                logger.info(f"Azure pronunciation assessment completed in {elapsed:.2f}s")
                return self._parse_azure_result(result, has_reference=reference_text is not None)
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("Azure: No speech recognized")
                raise Exception("No speech could be recognized")
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Azure recognition canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation.error_details}")
                raise Exception(f"Recognition canceled: {cancellation.error_details}")
            else:
                raise Exception(f"Unexpected result reason: {result.reason}")
                
        except Exception as e:
            logger.error(f"Azure pronunciation extraction failed: {str(e)}")
            raise
    
    def _numpy_to_wav_bytes(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> bytes:
        """
        Convert numpy array to WAV bytes for Azure
        
        Args:
            audio_data: Audio as numpy array (float32, -1.0 to 1.0)
            sample_rate: Sample rate
        
        Returns:
            WAV file bytes
        """
        # Ensure audio is in correct format
        if audio_data.dtype != np.int16:
            # Convert float32 [-1.0, 1.0] to int16 [-32768, 32767]
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create audio segment
        audio_segment = AudioSegment(
            audio_data.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,  # 16-bit
            channels=1  # Mono
        )
        
        # Export to WAV bytes
        buffer = io.BytesIO()
        audio_segment.export(buffer, format="wav")
        return buffer.getvalue()
    
    def _parse_azure_result(self, result, has_reference=False) -> Dict[str, Any]:
        """
        Parse Azure pronunciation result into our standard format
        
        Args:
            result: Azure SpeechRecognitionResult
            has_reference: Whether reference text was provided for assessment
        
        Returns:
            Dict with phonemes and scores in our format
        """
        # Parse JSON result
        result_json = json.loads(result.json)
        
        if 'NBest' not in result_json or len(result_json['NBest']) == 0:
            raise Exception("No recognition results from Azure")
        
        best_result = result_json['NBest'][0]
        
        # Get pronunciation assessment if available
        pronunciation = best_result.get('PronunciationAssessment', {}) if has_reference else {}
        words_data = best_result.get('Words', [])
        
        # Extract phonemes by word (our standard format)
        phonemes_by_word = []
        words_details = []
        
        for word_item in words_data:
            # Extract phonemes for this word
            word_phonemes = []
            phonemes_with_scores = []
            
            # Get phonemes if available
            for phoneme_item in word_item.get('Phonemes', []):
                phoneme = phoneme_item.get('Phoneme', '')
                if not phoneme:
                    continue
                    
                accuracy = 100.0  # Default if no assessment
                if has_reference:
                    accuracy = phoneme_item.get('PronunciationAssessment', {}).get('AccuracyScore', 100.0)
                
                word_phonemes.append(phoneme)
                phonemes_with_scores.append({
                    'phoneme': phoneme,
                    'accuracy_score': accuracy
                })
            
            # If no phonemes available (no reference text mode), we need to generate them
            # from the recognized word using grapheme-to-phoneme
            if not word_phonemes and 'Word' in word_item:
                from .grapheme_to_phoneme import grapheme_to_phoneme
                word_text = word_item['Word']
                # g2p returns list of (word, phonemes) tuples
                g2p_result = grapheme_to_phoneme(word_text)
                if g2p_result and len(g2p_result) > 0:
                    word_phonemes = g2p_result[0][1]  # Get phonemes from first word
                    phonemes_with_scores = [{'phoneme': p, 'accuracy_score': 100.0} for p in word_phonemes]
            
            if word_phonemes:  # Only add if we have phonemes
                phonemes_by_word.append(word_phonemes)
                
                # Store word-level details
                word_assessment = word_item.get('PronunciationAssessment', {}) if has_reference else {}
                words_details.append({
                    'word': word_item.get('Word', ''),
                    'accuracy_score': word_assessment.get('AccuracyScore', 100.0),
                    'error_type': word_assessment.get('ErrorType', 'None'),
                    'phonemes': phonemes_with_scores
                })
        
        # Return in format compatible with our system
        result_dict = {
            # Standard phoneme output (compatible with current system)
            'phonemes': phonemes_by_word,
            
            # Recognized text (for validation)
            'recognized_text': result.text,
            
            # Backend identifier
            'backend': 'azure'
        }
        
        # Add Azure-specific scores only if we had reference text
        if has_reference and pronunciation:
            result_dict['azure_scores'] = {
                'accuracy_score': pronunciation.get('AccuracyScore', 0.0),
                'fluency_score': pronunciation.get('FluencyScore', 0.0),
                'completeness_score': pronunciation.get('CompletenessScore', 0.0),
                'pronunciation_score': pronunciation.get('PronScore', 0.0)
            }
            result_dict['words'] = words_details
        
        return result_dict
    
    def get_model_info(self) -> dict:
        """Get information about the Azure backend"""
        return {
            'backend': 'azure',
            'region': self.region,
            'language': 'en-US',
            'granularity': 'phoneme'
        }


# Helper function for testing
def test_azure_extraction():
    """Test Azure pronunciation extraction"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get credentials
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION", "eastus")
    
    if not key:
        print("ERROR: AZURE_SPEECH_KEY not set in environment")
        return
    
    # Initialize extractor
    extractor = AzurePronunciationExtractor(key, region)
    
    # Test with sample audio
    test_audio_file = "backend/tests/extraction/sample_audio/the_cat.wav"
    reference_text = "The cat sat on the mat"
    
    if os.path.exists(test_audio_file):
        import librosa
        audio_data, sr = librosa.load(test_audio_file, sr=16000, mono=True)
        
        result = extractor.extract_phonemes(audio_data, sr, reference_text)
        
        print("✅ Azure Extraction Success!")
        print(f"Phonemes: {result['phonemes']}")
        print(f"Accuracy: {result['azure_scores']['accuracy_score']:.1f}")
        print(f"Pronunciation Score: {result['azure_scores']['pronunciation_score']:.1f}")
    else:
        print(f"Test audio file not found: {test_audio_file}")


if __name__ == "__main__":
    test_azure_extraction()
