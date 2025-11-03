"""
Upload the ONNX-converted wav2vec2-TIMIT-IPA model to HuggingFace Hub.

Instructions:
1. Create a HuggingFace account if you don't have one: https://huggingface.co/join
2. Create a new model repository: https://huggingface.co/new
   - Name it something like: your-username/wav2vec2-timit-ipa-onnx
3. Get your write token: https://huggingface.co/settings/tokens
4. Run: huggingface-cli login
5. Run: python upload_model.py
"""

from huggingface_hub import HfApi, create_repo
import os

# Configuration
MODEL_NAME = "wav2vec2-timit-ipa-onnx"  # Change this to your repo name
USERNAME = "Bobcat9"  # Your HuggingFace username
REPO_ID = f"{USERNAME}/{MODEL_NAME}"
LOCAL_DIR = "./wav2vec2-timit-ipa-onnx"

def upload_model():
    print(f"🚀 Uploading model to {REPO_ID}...")
    
    # Create API instance
    api = HfApi()
    
    # Create the repository if it doesn't exist
    try:
        create_repo(REPO_ID, repo_type="model", exist_ok=True)
        print(f"✅ Repository {REPO_ID} created/verified")
    except Exception as e:
        print(f"⚠️ Error creating repository: {e}")
        print("Make sure you're logged in: huggingface-cli login")
        return
    
    # Upload all files
    try:
        api.upload_folder(
            folder_path=LOCAL_DIR,
            repo_id=REPO_ID,
            repo_type="model"
        )
        print(f"✅ Model uploaded successfully!")
        print(f"📍 View at: https://huggingface.co/{REPO_ID}")
        print(f"\n🎯 Update your code to use: {REPO_ID}")
    except Exception as e:
        print(f"❌ Error uploading: {e}")

if __name__ == "__main__":
    if not os.path.exists(LOCAL_DIR):
        print(f"❌ Directory {LOCAL_DIR} not found!")
        print("Make sure you ran the ONNX export first.")
    else:
        print(f"📂 Found model files in {LOCAL_DIR}")
        upload_model()
