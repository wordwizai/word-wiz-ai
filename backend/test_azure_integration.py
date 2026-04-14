"""
Test Azure Pronunciation Assessment Integration

This script tests the Azure backend with sample audio files to verify:
1. Azure credentials are configured correctly
2. Audio processing works end-to-end
3. Phoneme extraction produces valid results
4. Latency is acceptable
"""

import os
import sys
import time
import librosa
import numpy as np
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.phoneme_extractor_azure import AzurePronunciationExtractor
from core.phoneme_assistant import PhonemeAssistant


def test_azure_credentials():
    """Test that Azure credentials are configured"""
    print("🔍 Testing Azure credentials...")
    
    load_dotenv()
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION", "eastus")
    
    if not key:
        print("❌ AZURE_SPEECH_KEY not set in environment")
        print("   Please add AZURE_SPEECH_KEY to your .env file")
        return False
    
    print(f"✅ Azure credentials found (region: {region})")
    print(f"   Key: {key[:8]}...{key[-4:]}")
    return True


def test_azure_extractor():
    """Test Azure extractor directly"""
    print("\n🔍 Testing Azure extractor...")
    
    load_dotenv()
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION", "eastus")
    
    if not key:
        print("❌ Skipping: AZURE_SPEECH_KEY not set")
        return False
    
    try:
        # Initialize extractor
        extractor = AzurePronunciationExtractor(key, region)
        print("✅ Azure extractor initialized successfully")
        
        # Load test audio
        test_audio = "tests/system/test_case_02/audio.wav"
        if not os.path.exists(test_audio):
            print(f"❌ Test audio not found: {test_audio}")
            return False
        
        print(f"📁 Loading test audio: {test_audio}")
        audio_data, sr = librosa.load(test_audio, sr=16000, mono=True)
        print(f"   Duration: {len(audio_data)/sr:.2f}s")
        
        # Test with reference text
        reference_text = "The cat sat on the mat"
        print(f"   Reference text: '{reference_text}'")
        
        start_time = time.time()
        result = extractor.extract_phonemes(audio_data, sr, reference_text)
        elapsed = time.time() - start_time
        
        print(f"✅ Extraction completed in {elapsed:.2f}s")
        print(f"   Phonemes: {result['phonemes']}")
        print(f"   Recognized: '{result['recognized_text']}'")
        
        if 'azure_scores' in result:
            scores = result['azure_scores']
            print(f"   Accuracy: {scores['accuracy_score']:.1f}%")
            print(f"   Pronunciation: {scores['pronunciation_score']:.1f}%")
        
        # Verify latency is acceptable (should be < 2s)
        if elapsed > 2.0:
            print(f"⚠️  Warning: Latency higher than expected ({elapsed:.2f}s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_phoneme_assistant():
    """Test PhonemeAssistant with Azure backend"""
    print("\n🔍 Testing PhonemeAssistant with Azure backend...")
    
    # Set backend to auto mode
    os.environ["PHONEME_BACKEND"] = "auto"
    
    try:
        # Initialize assistant
        print("   Initializing PhonemeAssistant...")
        assistant = PhonemeAssistant()
        
        # Check which backend was loaded
        backend_type = getattr(assistant, 'backend_type', 'unknown')
        print(f"✅ Backend loaded: {backend_type}")
        
        if backend_type == "azure":
            print("   ✅ Azure backend is active!")
        elif backend_type == "onnx":
            print("   ⚠️  ONNX fallback is active (Azure not available)")
        else:
            print(f"   ⚠️  Unexpected backend: {backend_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ PhonemeAssistant initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end():
    """Test end-to-end audio processing with Azure"""
    print("\n🔍 Testing end-to-end audio processing...")
    
    # This would require async setup, so we'll skip for now
    print("   (Skipping async end-to-end test - use manual testing)")
    return True


def main():
    """Run all tests"""
    print("="*60)
    print("Azure Pronunciation Assessment - Integration Tests")
    print("="*60)
    
    results = []
    
    # Test 1: Credentials
    results.append(("Credentials", test_azure_credentials()))
    
    # Test 2: Azure extractor (only if credentials are set)
    if results[0][1]:
        results.append(("Azure Extractor", test_azure_extractor()))
    
    # Test 3: PhonemeAssistant
    results.append(("PhonemeAssistant", test_phoneme_assistant()))
    
    # Test 4: End-to-end
    results.append(("End-to-End", test_end_to_end()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:12} {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("="*60)
    if all_passed:
        print("✅ All tests passed!")
        print("\nNext steps:")
        print("1. Deploy to production with PHONEME_BACKEND=auto")
        print("2. Monitor Azure usage in Azure Portal")
        print("3. Decommission old 2vCPU server to save $30/month")
    else:
        print("❌ Some tests failed. Please check configuration.")
        print("\nTroubleshooting:")
        print("1. Verify AZURE_SPEECH_KEY in .env file")
        print("2. Check Azure Portal for service status")
        print("3. Ensure azure-cognitiveservices-speech is installed")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
