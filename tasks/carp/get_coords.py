import tkinter as tk
from PIL import Image, ImageTk
import os

IMAGE_PATH = "/Users/simone/Downloads/carp/basin.png"
current_region_points = []

def on_image_click(event):
    """Records the click coordinates and draws a small circle."""
    x, y = event.x, event.y
    current_region_points.append((x, y))
    # Draw a small visual marker (optional)
    canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="red", outline="red")
    print(f"Clicked: ({x}, {y}). Points for current region: {current_region_points}")

def on_enter_key(event):
    """Prints the current list of points and clears it for the next region."""
    global current_region_points
    if current_region_points:
        print("\n--- Region Coordinates ---")
        print(f"{current_region_points},")
        print("--- End Region ---\n")
        current_region_points = []
        # Optionally, clear visual markers if you want a fresh canvas look per region
        # For simplicity, markers stay, but you could redraw the image or track markers.
    else:
        print("No points collected for this region.")
    print("Ready for next region. Click points or press ESC to exit.")


def on_escape_key(event):
    """Prints any remaining points and closes the application."""
    global current_region_points
    if current_region_points:
        print("\n--- Final Region Coordinates (before exit) ---")
        print(f"{current_region_points},")
        print("--- End Region ---\n")
    print("Exiting coordinate picker.")
    root.destroy()

if not os.path.exists(IMAGE_PATH):
    print(f"Error: Image not found at {IMAGE_PATH}")
    exit()

root = tk.Tk()
root.title("Coordinate Picker - Click points, Enter for new region, Esc to exit")

try:
    pil_image = Image.open(IMAGE_PATH)
    tk_image = ImageTk.PhotoImage(pil_image)
except Exception as e:
    print(f"Error opening or processing image: {e}")
    exit()

canvas = tk.Canvas(root, width=pil_image.width, height=pil_image.height)
canvas.pack()
canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)

canvas.bind("<Button-1>", on_image_click)  # Bind left mouse click
root.bind("<Return>", on_enter_key)       # Bind Enter key
root.bind("<Escape>", on_escape_key)     # Bind Escape key

print(f"Image '{os.path.basename(IMAGE_PATH)}' loaded.")
print("Instructions:")
print("1. Click on the image to select points for a river region.")
print("2. Press ENTER to print the coordinates for the current region and start a new one.")
print("3. Press ESC to print any unprinted coordinates and exit.")
print("\nThe printed coordinates will be in a list format, ready to be copied.")

root.mainloop()
