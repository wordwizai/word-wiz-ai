import numpy as np
import onnxruntime as ort
from transformers import Wav2Vec2Processor
import re
import time
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


class PhonemeExtractorONNX:
    """ONNX Runtime-based phoneme extractor for faster inference."""
    
    _model_cache = {}
    
    def __init__(self, 
                 model_name: str = "Bobcat9/wav2vec2-timit-ipa-onnx",
                 model_output_processing=default_model_output_processing,
                 optimization_config=None):
        """
        Initialize ONNX-based PhonemeExtractor.
        
        Args:
            model_name: HuggingFace model identifier with ONNX files
            model_output_processing: Function to process model output
            optimization_config: OptimizationConfig instance (uses global config if None)
        """
        if optimization_config is None:
            optimization_config = config
        
        self.config = optimization_config
        self.model_name = model_name
        self.model_output_processing = model_output_processing
        self._performance_logging = self.config.get('enable_performance_logging', False)
        
        # Initialize optimized audio preprocessor
        self.audio_preprocessor = OptimizedAudioPreprocessor(
            target_sr=16000, 
            enable_logging=self._performance_logging
        )
        
        # Check if model is already cached
        if (self.config.get('model_cache_enabled', True) and 
            model_name in self._model_cache):
            if self._performance_logging:
                print(f"Using cached ONNX model: {model_name}")
            cached = self._model_cache[model_name]
            self.processor = cached['processor']
            self.session = cached['session']
        else:
            if self._performance_logging:
                print(f"Loading ONNX model: {model_name}")
            start_time = time.time()
            
            try:
                # Load processor (for tokenization)
                self.processor = Wav2Vec2Processor.from_pretrained(model_name)
                
                # Load ONNX model
                from huggingface_hub import hf_hub_download
                onnx_path = hf_hub_download(repo_id=model_name, filename="model.onnx")
                
                # Create ONNX Runtime session with optimizations
                sess_options = ort.SessionOptions()
                sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                sess_options.intra_op_num_threads = 2  # Use both CPU cores
                sess_options.inter_op_num_threads = 2
                
                self.session = ort.InferenceSession(
                    onnx_path,
                    sess_options=sess_options,
                    providers=['CPUExecutionProvider']
                )
                
                # Cache the model if enabled
                if self.config.get('model_cache_enabled', True):
                    self._model_cache[model_name] = {
                        'processor': self.processor,
                        'session': self.session
                    }
                
                load_time = time.time() - start_time
                if self._performance_logging:
                    print(f"ONNX model loaded in {load_time:.2f}s")
                
                # Perform warmup runs
                self._warmup()
                
            except Exception as e:
                print(f"Failed to load ONNX model: {e}")
                raise
    
    def _warmup(self):
        """Perform warmup runs to optimize the model."""
        warmup_runs = self.config.get('warmup_runs', 1)
        if warmup_runs > 0 and self._performance_logging:
            print(f"Performing {warmup_runs} warmup run(s)...")
        
        # Generate dummy audio for warmup
        dummy_audio = np.random.randn(16000).astype(np.float32)  # 1 second
        
        for i in range(warmup_runs):
            try:
                self.extract_phoneme(dummy_audio)
            except Exception as e:
                if self._performance_logging:
                    print(f"Warmup run {i+1} failed: {e}")
                break
    
    def extract_phoneme(self, audio, sampling_rate=16000, use_optimized_preprocessing=True):
        """
        Extract phonemes from audio using ONNX Runtime.
        
        Args:
            audio: Audio data as numpy array
            sampling_rate: Sample rate of the audio (default: 16000)
            use_optimized_preprocessing: Whether to use optimized audio preprocessing
            
        Returns:
            Processed phoneme transcription
            
        Raises:
            ValueError: If audio is invalid
        """
        start_time = time.time() if self._performance_logging else None
        
        # Validate audio input
        if audio is None or len(audio) == 0:
            raise ValueError("❌ Audio is empty - cannot extract phonemes")
        
        audio_duration = len(audio) / sampling_rate
        
        if audio_duration < 0.3:
            raise ValueError(f"❌ Audio too short ({audio_duration:.2f}s) - need at least 0.3s")
        
        audio_rms = np.sqrt(np.mean(audio ** 2))
        if audio_rms < 0.001:
            raise ValueError(f"❌ Audio appears to be silent (RMS: {audio_rms:.6f})")
        
        if self._performance_logging:
            print(f"📊 Audio validation: duration={audio_duration:.2f}s, RMS={audio_rms:.4f}, samples={len(audio)}")
        
        # Optimize audio preprocessing if enabled
        if use_optimized_preprocessing:
            audio, sampling_rate = self.audio_preprocessor.preprocess_audio(
                audio, sampling_rate
            )
        
        # Tokenize the audio file
        processor_outputs = self.processor(audio, sampling_rate=sampling_rate, return_tensors="np")
        input_values = processor_outputs.input_values
        
        # Run ONNX inference
        onnx_inputs = {self.session.get_inputs()[0].name: input_values.astype(np.float32)}
        logits = self.session.run(None, onnx_inputs)[0]
        
        # Get predicted IDs
        predicted_ids = np.argmax(logits, axis=-1)
        
        # Decode the token sequences
        transcription = self.processor.batch_decode(predicted_ids)
        transcription = self.model_output_processing(transcription)
        
        if self._performance_logging and start_time:
            inference_time = time.time() - start_time
            print(f"ONNX phoneme extraction took {inference_time:.3f}s")
        
        return transcription
    
    def set_performance_logging(self, enabled: bool):
        """Enable or disable performance logging."""
        self._performance_logging = enabled
    
    def get_model_info(self) -> dict:
        """Get information about the current model configuration."""
        return {
            'model_name': self.model_name,
            'backend': 'ONNX Runtime',
            'model_cached': self.model_name in self._model_cache,
            'performance_logging': self._performance_logging,
        }
