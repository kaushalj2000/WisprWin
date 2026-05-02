from PIL import Image, ImageDraw
import os

logo_path = r"C:\Users\jkaus\OneDrive\Pictures\Wisprtype\logo.png"
app_logo_path = r"C:\Users\jkaus\OneDrive\Pictures\Wisprtype\App_logo.png"
assets_dir = r"C:\Users\jkaus\OneDrive\Pictures\Wisprtype\wisprwin\assets"

os.makedirs(assets_dir, exist_ok=True)

def pad_to_square(img):
    max_dim = max(img.width, img.height)
    square_img = Image.new("RGBA", (max_dim, max_dim), (255, 255, 255, 0))
    offset = ((max_dim - img.width) // 2, (max_dim - img.height) // 2)
    square_img.paste(img, offset)
    return square_img

try:
    # 1. Desktop Icon (logo.png -> icon.ico)
    if os.path.exists(logo_path):
        app_img = Image.open(logo_path).convert("RGBA")
        app_square = pad_to_square(app_img)
        icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        app_square.save(os.path.join(assets_dir, "icon.ico"), format="ICO", sizes=icon_sizes)
        print("SUCCESS: Generated desktop icon.ico from logo.png")
    else:
        print(f"WARNING: {logo_path} not found.")

    # 2. Tray Icons and Sidebar UI (logo.png -> PNGs)
    if os.path.exists(logo_path):
        tray_img = Image.open(logo_path).convert("RGBA")
        tray_square = pad_to_square(tray_img)
        
        base_tray = tray_square.resize((64, 64), Image.Resampling.LANCZOS)
        base_tray.save(os.path.join(assets_dir, "icon_idle.png"))
        
        # Recording
        rec_img = base_tray.copy()
        draw = ImageDraw.Draw(rec_img)
        r = 10
        draw.ellipse((64 - 2*r, 0, 64, 2*r), fill="#EF4444", outline="#FFFFFF", width=2)
        rec_img.save(os.path.join(assets_dir, "icon_recording.png"))
        
        # Processing
        proc_img = base_tray.copy()
        draw = ImageDraw.Draw(proc_img)
        draw.ellipse((64 - 2*r, 0, 64, 2*r), fill="#F59E0B", outline="#FFFFFF", width=2)
        proc_img.save(os.path.join(assets_dir, "icon_processing.png"))
        print("SUCCESS: Generated tray PNGs from logo.png")
    else:
        print(f"WARNING: {logo_path} not found.")

except Exception as e:
    print(f"FAILED: {e}")
