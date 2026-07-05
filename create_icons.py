from PIL import Image, ImageDraw

# Create 180x180 icon
img = Image.new('RGB', (180, 180), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
draw.rectangle([30, 30, 150, 150], outline=(255, 255, 255), width=3)
draw.ellipse([60, 60, 90, 90], fill=(255, 255, 255))
img.save('icons/icon-180.png')

# Create 512x512 icon
img = Image.new('RGB', (512, 512), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
draw.rectangle([80, 80, 432, 432], outline=(255, 255, 255), width=8)
draw.ellipse([160, 160, 250, 250], fill=(255, 255, 255))
img.save('icons/icon-512.png')

print('Icons created successfully')

