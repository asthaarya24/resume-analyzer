import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("🔍 Checking available models for your API key...")

try:
    for m in client.models.list():
        # In the 2026 SDK, we check 'supported_generation_methods' 
        # but let's print the name to be sure.
        methods = getattr(m, 'supported_generation_methods', [])
        
        if 'generateContent' in methods:
            print(f"✅ {m.name}")
        else:
            # Fallback check for newer SDK versions
            print(f"❓ {m.name} (Methods: {methods})")

except Exception as e:
    print(f"❌ Error listing models: {e}")