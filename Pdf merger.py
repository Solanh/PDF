from PyPDF2 import PdfReader, PdfWriter
import tkinter as tk
from tkinter import filedialog
import os
import ctypes
from pdf2image import convert_from_path
from PIL import Image, ImageTk


ctypes.windll.shcore.SetProcessDpiAwareness(1)

class FileUploader:
    def __init__(self, root):
        self.root = root
        self.files = {}  # Stores uploaded files
        self.setup_ui()
        self.pdf_previews = {}
        self.uploaded_files = []
        self.page_order = []
        self.pages_img = {}
        self.pages_pdf = {}
        self.new_order = []
        
    
    def setup_ui(self):
        
        self.root.columnconfigure(0, weight=1)  # Left side (controls)
        self.root.columnconfigure(1, weight=2)  # Right side (preview)
        self.root.rowconfigure(0, weight=1)

        # === Left Frame: Controls & Status ===
        left_frame = tk.Frame(self.root)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        left_frame.columnconfigure(0, weight=1)
        # Let the listbox expand to fill available vertical space.
        left_frame.rowconfigure(4, weight=1)

        # Introduction Label
        self.introduction = tk.Label(
            left_frame,
            text="Welcome to the PDF Merger.\nPlease upload the files you would like to merge.",
            justify="center",
            font=("Helvetica", 12)
        )
        self.introduction.grid(row=0, column=0, sticky="n", pady=(0, 10))

        # Upload Button
        self.btn_upload = tk.Button(left_frame, text="Upload Files", command=self.upload_file, width=15)
        self.btn_upload.grid(row=1, column=0, sticky="n", pady=(0, 10))

        # Reset Button
        self.btn_reset = tk.Button(left_frame, text="Reset", command=self.reset, width=10)
        self.btn_reset.grid(row=2, column=0, sticky="n", pady=(0, 10))

        # Status Label
        self.lbl_status = tk.Label(left_frame, text="No files uploaded", anchor="w", font=("Helvetica", 10))
        self.lbl_status.grid(row=3, column=0, sticky="n", pady=(0, 10))

        # Status Listbox
        self.lbl_status_list = tk.Listbox(left_frame)
        self.lbl_status_list.grid(row=3, column=0, padx=20, pady=120, sticky="ew")
        
        self.btn_next = tk.Button(left_frame, text="Next", command=self.main_ui, width=10)
        self.btn_next.grid(row=4, column=0, sticky="n", pady=(0, 10), padx=20,)
        

        # === Right Frame: Preview Canvas ===
        right_frame = tk.Frame(self.root, bg="lightgray")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        right_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)

        # Preview Canvas
        self.preview_canvas = tk.Canvas(right_frame, bg="lightgray", width=200, height=500)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")

        # Vertical Scrollbar for the Canvas
        scrollbar = tk.Scrollbar(right_frame, orient="vertical", command=self.preview_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.preview_canvas.configure(yscrollcommand=scrollbar.set)

        # Frame inside the Canvas to hold preview images (or other content)
        self.preview_box = tk.Frame(self.preview_canvas, bg="white")
        self.preview_window = self.preview_canvas.create_window((0, 0), window=self.preview_box, anchor="nw")

        # Update the canvas scroll region when the inner frame changes
        self.preview_box.bind("<Configure>", self.update_scroll_region)

        # --- Mouse wheel scrolling bindings ---
        self.preview_canvas.bind("<Enter>", self._bound_to_mousewheel)
        self.preview_canvas.bind("<Leave>", self._unbound_to_mousewheel)
    
    
        
    def main_ui(self):
        self.lbl_status_list.destroy()
        self.btn_next.destroy()
        self.introduction.destroy()
        self.btn_upload.destroy()
        self.btn_reset.destroy()
        self.lbl_status.destroy()
        
        left_frame = tk.Frame(self.root)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        left_frame.columnconfigure(0, weight=1)
        # Let the listbox expand to fill available vertical space.
        left_frame.rowconfigure(6, weight=1)
        
        self.lbl_status = tk.Label(left_frame, text="Please select the order \n of the files you would like to merge", font=("Helvetica", 12))
        self.lbl_status.grid(row=0, column=0, sticky="n", pady=(0, 20))
        
        self.instructions = tk.Label(left_frame, text="Your input should be in the form of 1,2,3,...,10,11,12 \n with each number correlating to a page \n and the order indicating the order of pages", font=("Helvetica", 10))
        self.instructions.grid(row=1, column=0, sticky="n", pady=(0, 20))
        
        self.input_order = tk.Entry(left_frame, width=50)
        self.input_order.grid(row=2, column=0, sticky="n", pady=(0, 20))
        
        self.name_instructions = tk.Label(left_frame, text="Please enter the name of the file you would like to save", font=("Helvetica", 10))
        self.name_instructions.grid(row=3, column=0, sticky="n", pady=(0, 20))
        
        self.input_name = tk.Entry(left_frame, width=50)
        self.input_name.grid(row=4, column=0, sticky="n", pady=(0, 20))
        
        submit_button = tk.Button(left_frame, text="Submit", command=self.process_input, width=10)
        submit_button.grid(row=5, column=0, padx=20, pady=10)
        
        self.btn_preview = tk.Button(left_frame, text="Preview", command=self.preview_pdf, width=10)
        self.btn_preview.grid(row=6, column=0, sticky="n", pady=(0, 10))
        
        self.btn_back = tk.Button(left_frame, text="Back", command=self.setup_ui, width=10)
        self.btn_back.grid(row=7, column=0, sticky="n", pady=(0, 10))
        
        self.btn_merge = tk.Button(left_frame, text="Merge", command=self.merge_files, width=10)
        self.btn_merge.grid(row=8, column=0, sticky="n", pady=(0, 10))
        
           
    def process_input(self):
        self.new_order = list(self.input_order.get())
        self.new_order = [int(i) for i in self.new_order if i != ","]
        user_input_name = self.input_name.get()
        print("User input:", self.new_order, user_input_name)
        print(type(self.new_order))
        print(type(user_input_name))
        # Now you can store or use the user_input variable as needed
        
    def merge_files(self):
        None
        
    def preview_pdf(self):
        self.process_input()  
        self.clear_preview()
        for i in self.new_order:
            img = self.pages_img[i]
            img_tk = ImageTk.PhotoImage(img)
            self.pdf_previews[f"{i}"] = img_tk
            lbl_preview = tk.Label(self.preview_box, image=img_tk)
            lbl_preview.pack(side="top", padx=10, pady=10)
            self.preview_box.update_idletasks()
            self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
        
                
             
    def process_uploads(self):
        self.pages_img = {}
        self.pages_pdf = {}
        counter = 1
        counter_pdf = 1
        for filename, filepath in self.files.items():
            if filepath.endswith(".pdf"):
                read = PdfReader(filepath)
                
                for page in read.pages:
                    self.pages_pdf[counter_pdf] = page
                    counter_pdf += 1
                
                images = convert_from_path(filepath, dpi=100)
                for img in images:
                    img.thumbnail((400, 500))  # Resize for preview
                    img_tk = ImageTk.PhotoImage(img)
                    # Store image reference to prevent garbage collection
                    self.pdf_previews[f"{filename} {counter}"] = img_tk
                    self.pages_img[counter] = img
                    counter += 1

            elif filepath.endswith((".png", ".jpg", ".jpeg", ".gif")):
                
                 # Open and convert the image
                image = Image.open(filepath)

                # Ensure the image is in RGB mode
                if image.mode in ("RGBA", "P"):  # Convert if needed
                    image = image.convert("RGB")

                # Save the image as a PDF
                temp_pdf_path = f"temp_{counter}.pdf"
                image.save(temp_pdf_path, "PDF", resolution=100.0)
                
                # Open the newly created PDF and store its first page.
                with open(temp_pdf_path, "rb") as f:
                    pdf_reader = PdfReader(f)
                    # Assuming the saved PDF contains one page:
                    page = pdf_reader.pages[0]
                    self.pages_pdf[counter_pdf] = page
                counter_pdf += 1
                
                img = Image.open(filepath)
                img.thumbnail((400, 500))
                img_tk = ImageTk.PhotoImage(img)

                # Store image reference to prevent garbage collection
                self.pdf_previews[f"{filename} {counter}"] = img_tk


                self.pages_img[counter] = img
                counter += 1



    def clear_preview(self):
        # Remove all widgets (images) from the preview_box frame
        for widget in self.preview_box.winfo_children():
            widget.destroy()
        # Optionally, if you are keeping references to the images,
        # clear that dictionary as well:
        self.pdf_previews.clear()


    def get_pages(self, pdf):
        read = PdfReader(pdf)
        counter = 1
        for page in read.pages:
            self.pages[counter] = page
            counter += 1

            

        
    new_order = [1,2,3,4,18,5,6,7,8,9,10,11,12,13,14,15,16,17]


    def rearrange_pages(pages, new_order):
        writer = PdfWriter()

        for i in new_order:
            writer.add_page(pages[i])
            
        with open(f"combined.pdf", "wb") as f:
            writer.write(f)

        
    
    
    def upload_file(self):
        self.files = {}  # Reset files each time
        file_paths = filedialog.askopenfilenames(
            title="Select files to upload",
            filetypes=[("All Files", "*.*"), 
                    ("Images", "*.png;*.jpg;*.jpeg;*.gif"), 
                    ("PDF Files", "*.pdf")]
        )
        for filepath in file_paths:
            filename = os.path.basename(filepath)
            self.files[filename] = filepath  # Store file paths
        
        # Process the uploaded files to populate pages_img and pdf_previews.
        self.process_uploads()
        
        # Now generate the preview display.
        
        self.populate_previews_sequentially()
        
        self.lbl_status.destroy()
        
        for i in list(self.files.keys()):
            self.lbl_status_list.insert("end", i)
            self.lbl_status_list.grid(row=3, column=0, padx=20, pady=120, sticky="ew")

        
    
    def reset(self):
        self.files = {}
        self.uploaded_files = []
        self.pdf_previews = {}
        self.preview_box.destroy()
        self.preview_canvas.destroy()
        self.lbl_status_list.destroy()
        self.setup_ui()
        
        
            
    def generate_preview(self, filename, filepath):
        """
        Updated generate_preview: Display the preview images that have already
        been created by process_uploads().
        """
        try:
            # Iterate over all the keys (or you could filter by filename)
            for key in self.pages_img:
                # Retrieve the PIL image from pages_img and convert it to a PhotoImage
                img = self.pages_img[key]
                img_tk = ImageTk.PhotoImage(img)
                
                # Create a label with the image
                lbl_preview = tk.Label(self.preview_box, image=img_tk)
                lbl_preview.image = img_tk  # Keep a reference to prevent garbage collection
                lbl_preview.pack(side="top", padx=10, pady=10)
            
            # Update the scroll region
                self.preview_box.update_idletasks()  
                self.root.update()
                 
            
            self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
        
        except Exception as e:
            print(f"Error generating preview for {filename}: {e}")

    def populate_previews_sequentially(self, keys=None, index=0, delay=100):
        """
        Display preview images one by one with a delay.
        :param keys: Sorted list of keys from pages_img.
        :param index: Current index in the list.
        :param delay: Delay in milliseconds between adding images.
        """
        if keys is None:
            keys = sorted(self.pages_img.keys())
        if index < len(keys):
            key = keys[index]
            img = self.pages_img[key]
            img_tk = ImageTk.PhotoImage(img)
            lbl_preview = tk.Label(self.preview_box, image=img_tk)
            lbl_preview.image = img_tk  # Keep reference to avoid garbage collection
            lbl_preview.pack(side="top", padx=10, pady=10)
            self.preview_box.update_idletasks()
            self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
            # Schedule the next image after the specified delay
            self.root.after(delay, lambda: self.populate_previews_sequentially(keys, index + 1, delay))
        else:
            print("Finished displaying previews.")

      
        
    def update_scroll_region(self, event):
        """ Updates the scrolling region of the canvas when new content is added. """
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))   
    
    
    def _bound_to_mousewheel(self, event):
        """Bind mouse wheel events to the canvas when the cursor enters."""
        self.preview_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        # For Linux systems you may also want to bind Button-4 and Button-5:
        self.preview_canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.preview_canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        """Unbind mouse wheel events from the canvas when the cursor leaves."""
        self.preview_canvas.unbind_all("<MouseWheel>")
        self.preview_canvas.unbind_all("<Button-4>")
        self.preview_canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        """
        Scroll the canvas. On Windows and macOS, event.delta is used.
        On Linux, event.num is used to determine scroll direction.
        """
        # For Windows and macOS
        if event.delta:
            # Divide delta by 120 (typical on Windows) and invert sign to match scrolling direction
            self.preview_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        # For Linux systems (event.num 4 is scroll up, 5 is scroll down)
        elif event.num == 4:
            self.preview_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
             self.preview_canvas.yview_scroll(1, "units")
             
             
             
def center_window(root, width=800, height=600):
    # Get screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate x and y coordinates for the window to be centered
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    # Set window size and position
    root.geometry(f"{width}x{height}+{x}+{y}")

root = tk.Tk()
root.title("PDF Merger")

uploader = FileUploader(root)

# Call function to center the window
center_window(root, 1000, 800)

root.resizable(True, True)
root.mainloop()




pdfs = ["First 3.pdf", "Audience Title Page.pdf", "Moodboard Title.pdf", "Individual Project Mood Board.pdf", "Wireframes Title.pdf", "Individual Project Wireframes.pdf", "Last 2.pdf"]