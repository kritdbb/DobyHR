"""
Split a 3x3 grid image into 9 individual badge images.
Saves them to backend/uploads/badges/ directory.
"""
from PIL import Image
import os

# Input image path - the user's attached image
INPUT_IMAGE = "badge_grid.png"

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "backend", "uploads", "badges")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Badge names for each position (row by row, left to right)
BADGE_NAMES = [
    "dragon_slayer",      # Top-left: warrior vs dragon
    "forest_king",        # Top-center: green wizard/king
    "hydra_hunter",       # Top-right: warrior vs hydra
    "angel_warrior",      # Middle-left: angel with sword
    "forest_witch",       # Middle-center: forest sorceress
    "demon_knight",       # Middle-right: demon armor knight
    "frost_berserker",    # Bottom-left: ice warrior vs yeti
    "cosmic_mage",        # Bottom-center: purple magic caster
    "dark_rider",         # Bottom-right: dark horseback knight
]

def split_image(input_path, output_dir, names):
    img = Image.open(input_path)
    width, height = img.size
    
    cell_w = width // 3
    cell_h = height // 3
    
    print(f"Image size: {width}x{height}")
    print(f"Each badge: {cell_w}x{cell_h}")
    print(f"Output dir: {output_dir}")
    print()
    
    for row in range(3):
        for col in range(3):
            idx = row * 3 + col
            name = names[idx]
            
            left = col * cell_w
            top = row * cell_h
            right = left + cell_w
            bottom = top + cell_h
            
            badge_img = img.crop((left, top, right, bottom))
            
            output_path = os.path.join(output_dir, f"{name}.png")
            badge_img.save(output_path, "PNG")
            print(f"  [{idx+1}/9] Saved: {name}.png ({cell_w}x{cell_h})")
    
    print(f"\n✅ All 9 badges saved to {output_dir}")

if __name__ == "__main__":
    if not os.path.exists(INPUT_IMAGE):
        print(f"❌ Input image not found: {INPUT_IMAGE}")
        print("Please save the grid image as 'badge_grid.png' in the project root.")
    else:
        split_image(INPUT_IMAGE, OUTPUT_DIR, BADGE_NAMES)
