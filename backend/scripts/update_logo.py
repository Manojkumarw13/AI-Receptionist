import requests
import os

def download_file(url, filename):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Save to current images folder
        filepath = os.path.join('static', 'images', 'current', filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
            
        print(f"✅ Downloaded new logo: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        return False

# High quality AI Medical/Receptionist Logo
# Source: Flaticon (Medical Chatbot/AI)
logo_url = "https://cdn-icons-png.flaticon.com/512/4712/4712035.png"  # A nice medical bot icon
filename = "logo.png"

print("⬇️  Downloading suitable AI Receptionist logo...")
if download_file(logo_url, filename):
    print("✨ Successfully updated project logo!")
else:
    print("⚠️  Failed to download. Using fallback...")
