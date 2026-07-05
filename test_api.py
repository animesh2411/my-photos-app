import urllib.request
import json

print("=" * 70)
print("PhotoBridge API Test")
print("=" * 70)

# Test 1: Get config
print("\n1. GET /api/config")
response = urllib.request.urlopen('http://localhost:8000/api/config')
config = json.loads(response.read().decode())
print(f"   Status: ✓")
print(f"   Response: {json.dumps(config, indent=4)}")

# Test 2: Get media
print("\n2. GET /api/media")
response = urllib.request.urlopen('http://localhost:8000/api/media')
media = json.loads(response.read().decode())
print(f"   Status: ✓")
print(f"   Media count: {len(media)}")
if media:
    print(f"   First item: {json.dumps(media[0], indent=4)}")
    media_id = media[0]['id']
else:
    print("   No media found")
    media_id = None

# Test 3: Get thumbnail
if media_id:
    print(f"\n3. GET /api/thumb/{media_id}")
    try:
        url = f'http://localhost:8000/api/thumb/{media_id}?w=300'
        response = urllib.request.urlopen(url)
        data = response.read()
        print(f"   Status: ✓")
        print(f"   Thumbnail size: {len(data)} bytes")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
    except Exception as e:
        print(f"   Error: {e}")

# Test 4: Get full media
if media_id:
    print(f"\n4. GET /api/full/{media_id}")
    try:
        url = f'http://localhost:8000/api/full/{media_id}'
        response = urllib.request.urlopen(url)
        data = response.read()
        print(f"   Status: ✓")
        print(f"   File size: {len(data)} bytes")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        print(f"   Accept-Ranges: {response.headers.get('Accept-Ranges')}")
    except Exception as e:
        print(f"   Error: {e}")

print("\n" + "=" * 70)
print("All tests completed!")
print("=" * 70)

