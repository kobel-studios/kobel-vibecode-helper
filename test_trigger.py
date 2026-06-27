import time
from PIL import Image, ImageTk
import tkinter as tk
import os

# TEST CODE MARKER - This is test code that does nothing and won't interfere with other code
# Test script to display the Accept All button image repeatedly
# This simulates the button appearing in Windsurf for testing

IMAGE_PATH = "accept_all_button.png"

def main():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: {IMAGE_PATH} not found")
        return
    
    # Load the image
    img = Image.open(IMAGE_PATH)
    
    # Create a window to display the image
    root = tk.Tk()
    root.title("Test Trigger - Accept All Button")
    root.attributes("-topmost", True)
    
    # Position window on the left side of screen
    screen_width = root.winfo_screenwidth()
    x_position = 100
    y_position = 100
    root.geometry(f"+{x_position}+{y_position}")
    
    # Display the image
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=photo)
    label.pack()
    
    print("Displaying Accept All button for 5 seconds...")
    print("Vibe Code-Helper should click it automatically if running")
    
    # Keep window open for 5 seconds
    root.after(5000, root.destroy)
    
    root.mainloop()
    print("Test complete")

if __name__ == "__main__":
    main()
