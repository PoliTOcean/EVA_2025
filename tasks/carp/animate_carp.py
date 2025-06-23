import os
from PIL import Image, ImageDraw, ImageFont, ImageTk
import tkinter as tk
from tkinter import messagebox, Label, Button
import subprocess 
import sys 

# --- Configuration ---
BASE_IMAGE_PATH = "basin.png"
OUTPUT_GIF_PATH = "carp_animation.gif"

START_YEAR = 2016
END_YEAR = 2025
FRAME_DURATION_MS = 1000  # Duration of each frame in milliseconds (1 second)

# River colors
RIVER_COLOR_CARP_PRESENT = "red"
RIVER_COLOR_CARP_ABSENT = "blue" # Color for river sections where carp are not present

# Text properties for displaying the year
TEXT_POSITION = (10, 10) 
TEXT_COLOR = "black"
FONT_SIZE = 60

# --- Data ---
# IMPORTANT: Define the coordinates for each river region.
REGIONS_COORDINATES = [
    # Region 1 
    [(226, 818), (223, 815), (218, 815), (216, 819), (213, 821), (209, 818), (206, 815), (204, 812), (204, 809), (204, 804), (203, 795), (201, 783), (201, 778), (204, 773), (201, 765), (201, 751), (204, 733), (206, 711), (206, 706), (200, 695), (199, 687), (203, 670), (208, 652), (210, 647), (214, 643), (217, 635), (219, 627), (222, 624), (228, 619), (235, 612)],
    # Region 2
    [(236, 612), (237, 608), (241, 603), (247, 599), (255, 599), (261, 596), (267, 591), (269, 586), (274, 585), (275, 580), (279, 576), (285, 569), (289, 560), (293, 551), (302, 546), (309, 536), (318, 529), (337, 519)],
    # Region 3
    [(340, 520), (343, 516), (349, 505), (358, 493), (359, 480), (367, 462), (373, 458), (373, 452), (378, 447), (379, 427), (395, 413), (395, 407), (391, 387), (394, 381), (405, 378), (432, 379)],
    # Region 4
    [(432, 377), (440, 377), (453, 377), (466, 373), (479, 377), (499, 381), (547, 365), (556, 356), (564, 346), (570, 335), (570, 322), (578, 310), (593, 300), (608, 287), (621, 275), (638, 268)],
    # Region 5
    [(613, 158), (613, 168), (609, 181), (608, 193), (612, 209), (620, 225), (630, 236), (634, 247), (636, 264), (640, 280), (648, 294), (659, 311), (667, 312), (674, 320), (690, 322), (714, 317), (733, 309), (754, 293), (766, 277), (778, 250)],
]

def get_font(font_size, bold=False):
    """Attempts to load a preferred font, falling back to common system fonts or a default."""
    font_name_templates = [
        "{name}bd.ttf", "{name}b.ttf", "{Name}Bold.ttf", "{Name}-Bold.ttf", # Bold variants
        "{name}.ttf", "{Name}.ttf" # Regular variants
    ]
    base_font_names = ["arial", "helvetica", "DejaVuSans", "LiberationSans-Regular"]

    tried_fonts = []
    if bold:
        for base_name in base_font_names:
            for template in font_name_templates:
                if "Bold" in template or "bd" in template or "b" in template: # Prioritize bold templates
                    font_name_attempt = template.format(name=base_name.lower(), Name=base_name.capitalize())
                    tried_fonts.append(font_name_attempt)
                    try:
                        return ImageFont.truetype(font_name_attempt, font_size)
                    except IOError:
                        continue
    
    for base_name in base_font_names:
        for template in font_name_templates:
            font_name_attempt = template.format(name=base_name.lower(), Name=base_name.capitalize())
            if bold and ("Bold" in template or "bd" in template or "b" in template) and font_name_attempt in tried_fonts:
                continue
            if not bold and ("Bold" in template or "bd" in template or "b" in template): 
                continue
            tried_fonts.append(font_name_attempt)
            try:
                return ImageFont.truetype(font_name_attempt, font_size)
            except IOError:
                continue
                
    print(f"Common fonts (including bold attempts if requested) not found. Using Pillow's default font. Text size/style might be affected.")
    try:
        return ImageFont.load_default(size=font_size) 
    except TypeError:
        return ImageFont.load_default()

# --- GIF Player Class (adapted from user's example) ---
class MyLabel(Label):
    def __init__(self, master, filename):
        im = Image.open(filename)
        seq =  []
        try:
            while 1:
                seq.append(im.copy())
                im.seek(len(seq)) # skip to next frame
        except EOFError:
            pass # we're done with sequence

        try:
            self.delay = im.info['duration']
        except KeyError:
            self.delay = 1000 # Default delay

        self.frames = []
        self.idx = 0
        
        # Re-open image to iterate frames cleanly for PhotoImage conversion
        # Using a new variable for clarity, im_reopened
        im_reopened = Image.open(filename) 
        for i in range(im_reopened.n_frames):
            im_reopened.seek(i)
            frame_rgba = im_reopened.convert('RGBA') 
            # Pass master to PhotoImage to associate it with the correct Tk window
            self.frames.append(ImageTk.PhotoImage(frame_rgba, master=master))

        if not self.frames:
            raise ValueError("Could not load any frames from GIF.")

        super().__init__(master, image=self.frames[0])

        self.cancel_id = None 
        self.play()

    def play(self):
        self.config(image=self.frames[self.idx])
        self.idx += 1
        if self.idx >= len(self.frames): # Use >= for safety
            self.idx = 0
        self.cancel_id = self.after(self.delay, self.play)

    def stop_animation(self):
        if self.cancel_id:
            self.after_cancel(self.cancel_id)
            self.cancel_id = None

def show_gif_in_window(gif_path):
    # Since CarpApp's root is destroyed, we create a new main Tk window.
    gif_viewer_root = tk.Tk() 
    gif_viewer_root.title("GIF Animation Preview")
    
    anim_player = None # Initialize to ensure it's defined in broader scope for on_close
    try:
        # Open the GIF using PIL
        gif_image = Image.open(gif_path)
        
        # Get the original GIF dimensions
        original_width, original_height = gif_image.size
        
        # Set a maximum width and height for the display window
        max_width = 800
        max_height = 600
        
        # Calculate the scaling factor to fit within the maximum dimensions
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        scale_factor = min(width_ratio, height_ratio)
        
        # Calculate the new dimensions
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Resize the GIF frames
        resized_frames = []
        for i in range(gif_image.n_frames):
            gif_image.seek(i)
            frame = gif_image.convert("RGBA").resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_frames.append(ImageTk.PhotoImage(frame, master=gif_viewer_root))
        
        class ScaledMyLabel(Label):
            def __init__(self, master, frames, delay):
                super().__init__(master, image=frames[0])
                self.frames = frames
                self.delay = delay
                self.idx = 0
                self.cancel_id = None
                self.play()

            def play(self):
                self.config(image=self.frames[self.idx])
                self.idx = (self.idx + 1) % len(self.frames)
                self.cancel_id = self.after(self.delay, self.play)

            def stop_animation(self):
                if self.cancel_id:
                    self.after_cancel(self.cancel_id)
                    self.cancel_id = None
        
        anim_player = ScaledMyLabel(gif_viewer_root, resized_frames, FRAME_DURATION_MS)
        anim_player.pack(padx=10, pady=10)

        def on_close():
            if anim_player: # Check if anim_player was successfully created
                anim_player.stop_animation()
            gif_viewer_root.destroy()

        Button(gif_viewer_root, text='Close Preview', command=on_close).pack(pady=10)
        gif_viewer_root.protocol("WM_DELETE_WINDOW", on_close) 
        
        # This mainloop is crucial for the GIF viewer window to operate correctly
        # after the main application's window has been destroyed.
        gif_viewer_root.mainloop()

    except Exception as e:
        # If an error occurs (e.g., MyLabel fails), destroy the window if it exists
        if gif_viewer_root.winfo_exists():
            gif_viewer_root.destroy()
        messagebox.showerror("GIF Player Error", f"Could not display GIF: {e}")
        print(f"Error displaying GIF: {e}")


def generate_animation_core(carp_presence_table, river_line_width_param, years_list):
    """
    Generates the carp animation GIF using data from the GUI.
    carp_presence_table is a list of lists of booleans: table[year_idx][region_idx]
    """
    if not os.path.exists(BASE_IMAGE_PATH):
        messagebox.showerror("File Error", f"Base image not found at {BASE_IMAGE_PATH}")
        return

    try:
        base_image = Image.open(BASE_IMAGE_PATH).convert("RGBA")
    except Exception as e:
        messagebox.showerror("File Error", f"Error opening base image: {e}")
        return

    frames = []
    font = get_font(FONT_SIZE, bold=True)

    print(f"\nGenerating frames for years {years_list[0]} to {years_list[-1]}...")
    print(f"Using line width: {river_line_width_param}")
    # print(f"Carp presence table: {carp_presence_table}") # Can be very verbose


    for y_idx, year_loop_val in enumerate(years_list):
        frame_image = base_image.copy()
        draw = ImageDraw.Draw(frame_image)

        for r_idx, region_path in enumerate(REGIONS_COORDINATES):
            if not region_path or len(region_path) < 2:
                continue

            # Use the direct state from the table for the current year and region
            carp_present = carp_presence_table[y_idx][r_idx]
            
            color = RIVER_COLOR_CARP_PRESENT if carp_present else RIVER_COLOR_CARP_ABSENT
            
            try:
                draw.line(region_path, fill=color, width=river_line_width_param, joint="curve")
            except TypeError: 
                 draw.line(region_path, fill=color, width=river_line_width_param)

        draw.text(TEXT_POSITION, str(year_loop_val), fill=TEXT_COLOR, font=font)
        frames.append(frame_image)
        # print(f"Generated frame for {year_loop_val}") # Reduce console output

    if not frames:
        messagebox.showinfo("Result", "No frames were generated.")
        return

    try:
        frames[0].save(
            OUTPUT_GIF_PATH,
            save_all=True,
            append_images=frames[1:],
            optimize=False, 
            duration=FRAME_DURATION_MS,
            loop=0 
        )
        print(f"Animation saved to {OUTPUT_GIF_PATH}")
        # Attempt to open the GIF in a new Tkinter window
        show_gif_in_window(OUTPUT_GIF_PATH)
        
    except Exception as e:
        messagebox.showerror("Save Error", f"Error saving GIF: {e}")

class CarpApp:
    def __init__(self, master):
        self.master = master
        master.title("Carp Animation Data Input")

        self.num_regions = len(REGIONS_COORDINATES)
        self.years = list(range(START_YEAR, END_YEAR + 1))
        self.check_vars = [] # List of lists: self.check_vars[year_idx][region_idx]

        # --- River Line Width Input ---
        controls_frame = tk.Frame(master)
        controls_frame.pack(pady=10)
        tk.Label(controls_frame, text="River Line Width:").pack(side=tk.LEFT, padx=5)
        self.line_width_var = tk.IntVar(value=5) 
        tk.Entry(controls_frame, textvariable=self.line_width_var, width=5).pack(side=tk.LEFT, padx=5)

        # --- Table Frame ---
        table_frame = tk.Frame(master)
        table_frame.pack(padx=10, pady=10)

        # --- Table Header (Regions) ---
        tk.Label(table_frame, text="Year").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        for r_idx in range(self.num_regions):
            tk.Label(table_frame, text=f"Region {r_idx + 1}").grid(row=0, column=r_idx + 1, padx=5, pady=2)

        # --- Table Rows (Years and Checkboxes) ---
        for y_idx, year in enumerate(self.years):
            tk.Label(table_frame, text=str(year)).grid(row=y_idx + 1, column=0, padx=5, pady=2, sticky="w")
            
            region_check_vars = []
            for r_idx in range(self.num_regions):
                var = tk.BooleanVar(value=False) # Default to N (unchecked)
                # Use a lambda that captures current y_idx and r_idx
                cb = tk.Checkbutton(table_frame, variable=var, 
                                   command=lambda y=y_idx, r=r_idx: self.on_check_change(y, r))
                cb.grid(row=y_idx + 1, column=r_idx + 1, padx=5, pady=0)
                region_check_vars.append(var)
            self.check_vars.append(region_check_vars)

        # --- Generate Button ---
        self.generate_button = tk.Button(master, text="Generate Animation & Save", command=self.process_and_generate)
        self.generate_button.pack(pady=10)

    def on_check_change(self, year_idx, region_idx):
        # If a box is checked, check all boxes below it in the same column
        if self.check_vars[year_idx][region_idx].get(): # If current checkbox is now True
            for y_below_idx in range(year_idx + 1, len(self.years)):
                self.check_vars[y_below_idx][region_idx].set(True)
        # If a box is unchecked, the user must manually uncheck subsequent years if desired.
        # This logic directly implements: "when i put to true a tickbox for a column i want all the below tick to became true"

    def process_and_generate(self):
        # Collect the exact state of all checkboxes
        carp_presence_table = []
        for y_idx in range(len(self.years)):
            year_region_presence = []
            for r_idx in range(self.num_regions):
                year_region_presence.append(self.check_vars[y_idx][r_idx].get())
            carp_presence_table.append(year_region_presence)
        
        river_line_width = self.line_width_var.get()
        if river_line_width <= 0:
            messagebox.showerror("Input Error", "River line width must be a positive number.")
            return

        # Destroy the main application window. This should terminate its mainloop.
        self.master.destroy() 
        
        # Now, generate the animation and show it in a new window, which will have its own mainloop.
        generate_animation_core(carp_presence_table, river_line_width, self.years)

if __name__ == "__main__":
    # This is the root for the main application (CarpApp)
    initial_root = tk.Tk() 
    app = CarpApp(initial_root)
    # This mainloop runs the CarpApp.
    # When initial_root.destroy() is called in CarpApp, this mainloop should end.
    initial_root.mainloop()
    # After the above mainloop finishes, script execution continues.
    # The show_gif_in_window function will then start its own mainloop if called.
if __name__ == "__main__":
    # Ensure Pillow is installed, REGIONS_COORDINATES is updated.
    root = tk.Tk()
    app = CarpApp(root)
    root.mainloop()
