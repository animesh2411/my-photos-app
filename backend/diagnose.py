#!/usr/bin/env python
import urllib.request
import json

print("\n=== PHOTOBRIDGE DIAGNOSTICS ===\n")

# Test 1: Frontend loads
try:
    resp = urllib.request.urlopen('http://localhost:8000/')
    html = resp.read().decode()
    print("✓ Frontend loads (HTML size: {} bytes)".format(len(html)))
    if 'id="app"' in html:
        print("✓ App div found in HTML")
    else:
        print("✗ App div NOT found in HTML")
    if 'app.js' in html:
        print("✓ app.js script tag present")
    else:
        print("✗ app.js NOT in HTML")
except Exception as e:
    print("✗ Frontend load failed: {}".format(e))

# Test 2: API config
try:
    resp = urllib.request.urlopen('http://localhost:8000/api/config')
    config = json.loads(resp.read().decode())
    print("\n✓ API /config responds: {}".format(config))
except Exception as e:
    print("\n✗ API /config failed: {}".format(e))

# Test 3: API media
try:
    resp = urllib.request.urlopen('http://localhost:8000/api/media')
    media = json.loads(resp.read().decode())
    print("✓ API /media responds: {} items".format(len(media)))
except Exception as e:
    print("✗ API /media failed: {}".format(e))

# Test 4: Try POST config (this might fail if path is wrong)
try:
    import json as json_module
    data = json_module.dumps({"photos_dir": "C:\\Users\\anime\\Pictures"}).encode()
    req = urllib.request.Request('http://localhost:8000/api/config', data=data, headers={'Content-Type': 'application/json'}, method='POST')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    print("\n✓ POST /config success: {}".format(result))
except urllib.error.HTTPError as e:
    error_data = e.read().decode()
    print("\n✗ POST /config HTTP error {}: {}".format(e.code, error_data))
except Exception as e:
    print("\n✗ POST /config failed: {}".format(e))

print("\n=== END DIAGNOSTICS ===\n")

