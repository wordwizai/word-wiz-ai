"""
Temporary Audio Cache Utility

This module provides functionality to cache audio files at different stages
of the processing pipeline for debugging and analysis purposes.
"""

import io
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np
import soundfile as sf
import json
import dotenv


class TempAudioCache:
    """
    A utility class for caching audio files at different processing stages.
    
    This helps with debugging by allowing you to examine audio files at various
    points in the processing pipeline.
    """
    
    def __init__(self, base_dir: str = "./temp_audio"):
        """
        Initialize the audio cache.
        
        Args:
            base_dir (str): Base directory for storing cached audio files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different cache stages
        self.stages = {
            "original": self.base_dir / "original",
            "preprocessed": self.base_dir / "preprocessed", 
            "segments": self.base_dir / "segments",
            "feedback": self.base_dir / "feedback",
            "analysis": self.base_dir / "analysis"
        }

        dotenv.load_dotenv()  # Load environment variables from .env file
        
        for stage_dir in self.stages.values():
            stage_dir.mkdir(exist_ok=True)
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID for this audio processing session."""
        return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    def save_audio(
        self,
        audio_data: np.ndarray,
        stage: str,
        session_id: str,
        sample_rate: int = 16000,
        filename_suffix: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save audio data to the cache.
        
        Args:
            audio_data (np.ndarray): Audio array to save
            stage (str): Processing stage (original, preprocessed, segments, feedback, analysis)
            session_id (str): Session identifier
            sample_rate (int): Sample rate of the audio
            filename_suffix (str): Optional suffix for filename
            metadata (Dict): Optional metadata to save alongside audio
            
        Returns:
            str: Path to the saved audio file
        """
        if stage not in self.stages:
            raise ValueError(f"Invalid stage: {stage}. Valid stages: {list(self.stages.keys())}")
        if os.getenv("ENABLE_AUDIO_CACHE", "0") not in ("1", "true", "yes", "on"):
            print("Audio caching is not enabled via environment variable.")
            return ""
        
        # Generate filename
        timestamp = datetime.now().strftime('%H%M%S')
        suffix = f"_{filename_suffix}" if filename_suffix else ""
        filename = f"{session_id}_{timestamp}_{stage}{suffix}.wav"
        filepath = self.stages[stage] / filename
        
        # Save audio file
        sf.write(filepath, audio_data, sample_rate)
        
        # Save metadata if provided
        if metadata:
            metadata_path = filepath.with_suffix('.json')
            metadata_with_info = {
                "session_id": session_id,
                "stage": stage,
                "timestamp": datetime.now().isoformat(),
                "sample_rate": sample_rate,
                "audio_length": len(audio_data),
                "audio_duration_seconds": len(audio_data) / sample_rate,
                **metadata
            }
            with open(metadata_path, 'w') as f:
                json.dump(metadata_with_info, f, indent=2)
        
        print(f"Audio cached: {filepath}")
        return str(filepath)
    
    def save_audio_bytes(
        self,
        audio_bytes: bytes,
        stage: str,
        session_id: str,
        filename_suffix: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save audio bytes directly to cache (useful for uploaded files).
        
        Args:
            audio_bytes (bytes): Raw audio bytes
            stage (str): Processing stage
            session_id (str): Session identifier
            filename_suffix (str): Optional suffix for filename
            metadata (Dict): Optional metadata to save alongside audio
            
        Returns:
            str: Path to the saved audio file
        """
        if stage not in self.stages:
            raise ValueError(f"Invalid stage: {stage}. Valid stages: {list(self.stages.keys())}")
        if os.getenv("ENABLE_AUDIO_CACHE", "0") not in ("1", "true", "yes", "on"):
            print("Audio caching is not enabled via environment variable.")
            return ""
        
        # Generate filename
        timestamp = datetime.now().strftime('%H%M%S')
        suffix = f"_{filename_suffix}" if filename_suffix else ""
        filename = f"{session_id}_{timestamp}_{stage}{suffix}.wav"
        filepath = self.stages[stage] / filename
        
        # Save audio bytes
        with open(filepath, 'wb') as f:
            f.write(audio_bytes)
        
        # Save metadata if provided
        if metadata:
            metadata_path = filepath.with_suffix('.json')
            metadata_with_info = {
                "session_id": session_id,
                "stage": stage,
                "timestamp": datetime.now().isoformat(),
                "audio_size_bytes": len(audio_bytes),
                **metadata
            }
            with open(metadata_path, 'w') as f:
                json.dump(metadata_with_info, f, indent=2)
        
        print(f"Audio bytes cached: {filepath}")
        return str(filepath)
    
    def save_feedback_audio(
        self,
        audio_data: bytes,
        session_id: str,
        feedback_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save feedback audio with associated text.
        
        Args:
            audio_data (bytes): Audio bytes from TTS
            session_id (str): Session identifier
            feedback_text (str): The feedback text that was converted to audio
            metadata (Dict): Optional metadata
            
        Returns:
            str: Path to the saved audio file
        """
        if os.getenv("ENABLE_AUDIO_CACHE", "0") not in ("1", "true", "yes", "on"):
            print("Audio caching is not enabled via environment variable.")
            return ""
        feedback_metadata = {
            "feedback_text": feedback_text,
            "type": "tts_feedback",
            **(metadata or {})
        }
        
        return self.save_audio_bytes(
            audio_data, 
            "feedback", 
            session_id, 
            "tts_output",
            feedback_metadata
        )
    
    def get_session_files(self, session_id: str) -> Dict[str, list]:
        """
        Get all files for a specific session.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Dict[str, list]: Dictionary mapping stage names to lists of file paths
        """
        session_files = {}
        
        for stage, stage_dir in self.stages.items():
            files = []
            for filepath in stage_dir.glob(f"{session_id}_*.wav"):
                files.append(str(filepath))
            session_files[stage] = sorted(files)
        
        return session_files
    
    def cleanup_old_files(self, hours_old: int = 24):
        """
        Clean up files older than specified hours.
        
        Args:
            hours_old (int): Delete files older than this many hours
        """
        import time
        cutoff_time = time.time() - (hours_old * 3600)
        
        deleted_count = 0
        for stage_dir in self.stages.values():
            for filepath in stage_dir.iterdir():
                if filepath.stat().st_mtime < cutoff_time:
                    filepath.unlink()
                    deleted_count += 1
        
        print(f"Cleaned up {deleted_count} old cache files")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the current cache state.
        
        Returns:
            Dict: Cache statistics and information
        """
        info = {
            "base_dir": str(self.base_dir),
            "stages": {}
        }
        
        total_files = 0
        total_size = 0
        
        for stage, stage_dir in self.stages.items():
            files = list(stage_dir.glob("*.wav"))
            stage_size = sum(f.stat().st_size for f in files)
            
            info["stages"][stage] = {
                "file_count": len(files),
                "size_bytes": stage_size,
                "size_mb": round(stage_size / (1024 * 1024), 2)
            }
            
            total_files += len(files)
            total_size += stage_size
        
        info["total_files"] = total_files
        info["total_size_bytes"] = total_size
        info["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        
        return info


# Global cache instance
audio_cache = TempAudioCache()

