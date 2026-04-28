import requests
import os

def download_image(url, filename):
    """Download image from URL and save to static/images/"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        filepath = os.path.join('static', 'images', filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"✅ Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False

# Unsplash API (no key needed for basic usage via source.unsplash.com)
# High-quality healthcare/medical images

images_to_download = [
    {
        'url': 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1920&q=80',
        'filename': 'doctor_consultation.jpg',
        'description': 'Doctor consultation'
    },
    {
        'url': 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1920&q=80',
        'filename': 'hospital_interior.jpg',
        'description': 'Modern hospital interior'
    },
    {
        'url': 'https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=1920&q=80',
        'filename': 'medical_technology.jpg',
        'description': 'Medical technology background'
    },
    {
        'url': 'https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=1920&q=80',
        'filename': 'healthcare_team.jpg',
        'description': 'Healthcare team'
    },
    {
        'url': 'https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=1920&q=80',
        'filename': 'medical_background.jpg',
        'description': 'Medical abstract background'
    }
]

print("🔄 Downloading healthcare images from Unsplash...")
print("=" * 50)

for img in images_to_download:
    print(f"\n📥 Downloading: {img['description']}")
    download_image(img['url'], img['filename'])

print("\n" + "=" * 50)
print("✅ Download complete!")
