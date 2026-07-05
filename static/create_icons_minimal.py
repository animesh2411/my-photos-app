import base64

# Minimal 1x1 black PNG
minimal_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
minimal_png = base64.b64decode(minimal_png_b64)

with open('icons/icon-180.png', 'wb') as f:
    f.write(minimal_png)

with open('icons/icon-512.png', 'wb') as f:
    f.write(minimal_png)

print("Icons created")

