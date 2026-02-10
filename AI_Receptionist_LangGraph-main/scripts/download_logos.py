import requests
import os

def download_logo(url, filename):
    """Download logo from URL and save to static/images/"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        filepath = os.path.join('static', 'images', filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"✅ Downloaded: {filename} ({len(response.content)} bytes)")
        return True
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False

# Healthcare/Medical logos from free resources
# Using PNG logos with transparent backgrounds

logos_to_try = [
    {
        'url': 'https://cdn-icons-png.flaticon.com/512/2913/2913133.png',
        'filename': 'health_logo_1.png',
        'description': 'Medical cross with heart'
    },
    {
        'url': 'https://cdn-icons-png.flaticon.com/512/3209/3209265.png',
        'filename': 'health_logo_2.png',
        'description': 'Healthcare heartbeat logo'
    },
    {
        'url': 'https://cdn-icons-png.flaticon.com/512/2913/2913145.png',
        'filename': 'health_logo_3.png',
        'description': 'Medical stethoscope logo'
    },
    {
        'url': 'https://cdn-icons-png.flaticon.com/512/684/684262.png',
        'filename': 'health_logo_4.png',
        'description': 'Hospital building logo'
    },
    {
        'url': 'https://cdn-icons-png.flaticon.com/512/3774/3774299.png',
        'filename': 'health_logo_5.png',
        'description': 'AI Medical robot logo'
    }
]

print("🔄 Downloading healthcare logos from Flaticon...")
print("=" * 60)

success_count = 0
for logo in logos_to_try:
    print(f"\n📥 Downloading: {logo['description']}")
    if download_logo(logo['url'], logo['filename']):
        success_count += 1

print("\n" + "=" * 60)
print(f"✅ Download complete! {success_count}/{len(logos_to_try)} logos downloaded successfully")
print("\nYou can now choose which logo to use for your application.")
