"""Generate FusionFlow logo assets"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_logo(size):
    """Create FusionFlow logo at specified size"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    blue = (70, 130, 230)  # #4682E6
    orange = (255, 140, 50)  # #FF8C32
    
    # Background circle
    margin = max(2, size // 10)
    if size >= 32:
        draw.ellipse([margin, margin, size-margin, size-margin], fill=blue)
    
    # Draw "FF" text
    try:
        font_size = max(int(size * 0.5), 12)
        # Try to use a bold font
        try:
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("Arial Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    text = "FF"
    
    # Get text size
    if hasattr(font, 'getbbox'):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        text_width, text_height = draw.textsize(text, font=font)
    
    # Center text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - max(2, size // 20)
    
    # Draw text with gradient effect (orange)
    draw.text((x, y), text, fill=orange, font=font)
    
    # Add temporal wave accent at bottom
    if size >= 48:
        wave_y = int(size * 0.75)
        wave_points = []
        for i in range(0, size, max(1, size // 20)):
            wave_points.append((i, wave_y))
        if len(wave_points) > 1:
            draw.line(wave_points, fill=(150, 100, 230), width=max(1, size // 32))
    
    return img

def main():
    """Generate all logo sizes"""
    output_dir = "logos"
    os.makedirs(output_dir, exist_ok=True)
    
    sizes = [16, 32, 48, 64, 128, 256, 512]
    
    for size in sizes:
        img = create_logo(size)
        img.save(f"{output_dir}/logo_{size}.png")
        print(f"Created logo_{size}.png")
    
    # Create ICO file with multiple sizes
    images = []
    for size in [16, 32, 48, 64, 128, 256]:
        images.append(create_logo(size))
    
    images[0].save(
        f"{output_dir}/fusionflow.ico",
        format='ICO',
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )
    print("Created fusionflow.ico")
    
    print("\nAll logos generated successfully!")

if __name__ == "__main__":
    main()
