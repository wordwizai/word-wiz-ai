import torch
import librosa
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import re
import time
import os
import gc
from typing import Optional
from .optimization_config import config
from .audio_optimization import OptimizedAudioPreprocessor


def default_model_output_processing(transcription):
    # Filter out our transcription
    filtered_transcription = transcription[0]

    # split by words
    filtered_transcription = re.split(r" ", filtered_transcription)

    filtered_transcription = [list(word.replace("ˈ","")) for word in filtered_transcription if word != ""]
    return filtered_transcription

class PhonemeExtractor:
    # Class-level cache for models to enable singleton-like behavior
    _model_cache = {}
    
    def __init__(self, 
                 model_name: str = "speech31/wav2vec2-large-TIMIT-IPA", 
                 model_output_processing=default_model_output_processing,
                 use_quantization: bool = None,
                 use_fast_model: bool = None,
                 optimization_config=None):
        """
        Initialize PhonemeExtractor with optimization options.
        
        Args:
            model_name: HuggingFace model identifier
            model_output_processing: Function to process model output
            use_quantization: Whether to apply dynamic quantization for faster inference
            use_fast_model: Use smaller, faster model for low-resource environments
            optimization_config: OptimizationConfig instance (uses global config if None)
        """
        # Use global config if not provided
        if optimization_config is None:
            optimization_config = config
        
        self.config = optimization_config
        
        # Override defaults with config values
        if use_quantization is None:
            use_quantization = self.config.get('use_quantization', True)
        if use_fast_model is None:
            use_fast_model = self.config.get('use_fast_models', True)
            
        # Use faster model if requested
        if use_fast_model:
            model_name = "facebook/wav2vec2-base-960h"  # Smaller, faster model
            
        self.model_name = model_name
        self.use_quantization = use_quantization
        self.model_output_processing = model_output_processing
        self._performance_logging = self.config.get('enable_performance_logging', False)
        
        # Initialize optimized audio preprocessor
        self.audio_preprocessor = OptimizedAudioPreprocessor(
            target_sr=16000, 
            enable_logging=self._performance_logging
        )
        
        # Check if model is already cached
        cache_key = f"{model_name}_{use_quantization}_{self.config.get('use_compilation', True)}"
        
        if (self.config.get('model_cache_enabled', True) and 
            cache_key in self._model_cache):
            if self._performance_logging:
                print(f"Using cached model: {model_name}")
            cached = self._model_cache[cache_key]
            self.processor = cached['processor']
            self.model = cached['model']
            self.blank_token_id = cached['blank_token_id']
        else:
            if self._performance_logging:
                print(f"Loading model: {model_name}")
            start_time = time.time()
            
            try:
                # Load the processor and model
                self.processor = Wav2Vec2Processor.from_pretrained(self.model_name)
                self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name)
                
                # Apply optimizations
                self._optimize_model()
                
                #Removing it for a second
                #self.blank_token_id = self.processor.tokenizer.pad_token_id
                
                # Cache the model components if caching is enabled
                # if self.config.get('model_cache_enabled', True):
                #     self._model_cache[cache_key] = {
                #         'processor': self.processor,
                #         'model': self.model,
                #         'blank_token_id': self.blank_token_id
                #     }
                
                load_time = time.time() - start_time
                if self._performance_logging:
                    print(f"Model loaded and optimized in {load_time:.2f}s")
                
                # Perform warmup runs if configured
                self._warmup()
                
                # Clear unnecessary cache if configured
                if self.config.get('clear_cache_after_init', False):
                    gc.collect()
                    
            except Exception as e:
                if self.config.get('fallback_on_error', True):
                    print(f"Model loading failed ({e}), falling back to basic configuration")
                    # Fallback to basic configuration
                    self.use_quantization = False
                    self.processor = Wav2Vec2Processor.from_pretrained(self.model_name)
                    self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name)
                    self.model.eval()
                    self.blank_token_id = self.processor.tokenizer.pad_token_id
                else:
                    raise
    
    def _optimize_model(self):
        """Apply various optimizations to the model."""
        # Set model to evaluation mode
        print("Evaluating model...")
        self.model.eval()
        
        # Apply dynamic quantization if requested
        if self.use_quantization:
            try:
                if self._performance_logging:
                    print("Applying dynamic quantization...")
                self.model = torch.quantization.quantize_dynamic(
                    self.model, 
                    {torch.nn.Linear}, 
                    dtype=torch.qint8
                )
                if self._performance_logging:
                    print("Dynamic quantization applied successfully")
            except Exception as e:
                if self._performance_logging:
                    print(f"Quantization failed, continuing without: {e}")
        
        # Try to compile the model for faster inference
        if self.config.get('use_compilation', True):
            try:
                if hasattr(torch, 'compile'):
                    if self._performance_logging:
                        print("Compiling model with torch.compile...")
                    compilation_mode = self.config.get('compilation_mode', 'reduce-overhead')
                    self.model = torch.compile(self.model, mode=compilation_mode)
                    if self._performance_logging:
                        print("Model compilation successful")
            except Exception as e:
                if self._performance_logging:
                    print(f"Model compilation failed, continuing without: {e}")
    
    def _warmup(self):
        """Perform warmup runs to optimize the model."""
        warmup_runs = self.config.get('warmup_runs', 1)
        if warmup_runs > 0 and self._performance_logging:
            print(f"Performing {warmup_runs} warmup run(s)...")
            
        # Generate dummy audio for warmup
        dummy_audio = torch.randn(16000).numpy()  # 1 second of dummy audio
        
        for i in range(warmup_runs):
            try:
                with torch.no_grad():
                    self.extract_phoneme(dummy_audio)
            except Exception as e:
                if self._performance_logging:
                    print(f"Warmup run {i+1} failed: {e}")
                break
    
    @classmethod
    def get_fast_instance(cls, model_output_processing=default_model_output_processing):
        """Factory method to create a fast, optimized instance for low-resource environments."""
        return cls(
            model_name="facebook/wav2vec2-base-960h",
            model_output_processing=model_output_processing,
            use_quantization=True,
            use_fast_model=True
        )

    def extract_phoneme(self, audio, sampling_rate=16000, use_optimized_preprocessing=True):
        """
        Extract phonemes from audio with optimized inference.
        
        Args:
            audio: Audio data as numpy array
            sampling_rate: Sample rate of the audio (default: 16000)
            use_optimized_preprocessing: Whether to use optimized audio preprocessing
            
        Returns:
            Processed phoneme transcription
        """
        start_time = time.time() if self._performance_logging else None
        
        # Optimize audio preprocessing if enabled
        if use_optimized_preprocessing:
            audio, sampling_rate = self.audio_preprocessor.preprocess_audio(
                audio, sampling_rate
            )
        
        # Tokenize the audio file
        processor_outputs = self.processor(audio, sampling_rate=sampling_rate, return_tensors="pt")
        input_values = processor_outputs.input_values
        
        # Use torch.no_grad() and optimize for inference
        with torch.no_grad():
            # Additional optimization: use torch.inference_mode if available
            if hasattr(torch, 'inference_mode'):
                with torch.inference_mode():
                    outputs = self.model(input_values)
            else:
                outputs = self.model(input_values)

        logits = outputs.logits

        # Optimized argmax computation
        predicted_ids = torch.argmax(logits, dim=-1)

        # Decode the token sequences
        transcription = self.processor.batch_decode(predicted_ids)
        transcription = self.model_output_processing(transcription)

        if self._performance_logging and start_time:
            inference_time = time.time() - start_time
            print(f"Phoneme extraction took {inference_time:.3f}s")

        return transcription
    
    def set_performance_logging(self, enabled: bool):
        """Enable or disable performance logging."""
        self._performance_logging = enabled
    
    def get_model_info(self) -> dict:
        """Get information about the current model configuration."""
        return {
            'model_name': self.model_name,
            'use_quantization': self.use_quantization,
            'model_cached': f"{self.model_name}_{self.use_quantization}" in self._model_cache,
            'performance_logging': self._performance_logging,
            'config_summary': self.config.summary() if hasattr(self, 'config') else 'No config'
        }

if __name__ == '__main__':
    from grapheme_to_phoneme import grapheme_to_phoneme
    from audio_recording import record_and_process_pronunciation

    # Load the audio file
    audio, sampling_rate = librosa.load("audio_samples/test.wav", sr=16000)
    # Create the phoneme extractor
    extractor = PhonemeExtractor()

    # Extract the phonemes
    phonemes = extractor.extract_phoneme(audio, sampling_rate)
    ground_truth_phonemes = grapheme_to_phoneme("zero three five one")
    # phonemes, ground_truth_phonemes = record_and_process_pronunciation("the quick brown fox jumped over the lazy dog", extractor)

    print(phonemes)
    print(ground_truth_phonemes)
