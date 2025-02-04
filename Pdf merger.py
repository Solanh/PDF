from PyPDF2 import PdfReader, PdfWriter
import tkinter as tk
from tkinter import filedialog
import os
import ctypes
from pdf2image import convert_from_path
from PIL import Image, ImageTk
import subprocess as sp
import sys


try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except AttributeError:
    pass  # Ignore errors on non-Windows systems


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
        self.preview_canvas = tk.Canvas(right_frame, bg="lightgray", width=325)
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
        
        self.input_order = tk.Text(left_frame, width=40, height=3, wrap="word")
        self.input_order.grid(row=2, column=0, sticky="n", pady=(0, 20))
        
        
        self.page_order = list(self.pages_pdf.keys())  # Ensure page order includes all uploaded files


        self.input_order.insert("1.0", ",".join(map(str, self.page_order)))  
 
        
        self.num_index_display = tk.Label(left_frame, text=f"You should have {len(self.page_order)} indices", font=("Helvetica", 10))
        self.num_index_display.grid(row=3, column=0, sticky="n", pady=(0, 20))
        
        self.name_instructions = tk.Label(left_frame, text="Please enter the name of the file you would like to save", font=("Helvetica", 10))
        self.name_instructions.grid(row=4, column=0, sticky="n", pady=(0, 20))
        
        self.input_name = tk.Entry(left_frame, width=50)
        self.input_name.grid(row=5, column=0, sticky="n", pady=(0, 20))
        
        
        
        
        self.status_message = tk.Label(left_frame, text="", fg="red", font=("Helvetica", 10))
        self.status_message.grid(row=6, column=0, sticky="n", pady=(0, 10))
        
        self.btn_preview = tk.Button(left_frame, text="Preview", command=lambda: self.preview_pdf(0), width=10)
        self.btn_preview.grid(row=7, column=0, sticky="n", pady=(0, 10))

        
        self.reset_button = tk.Button(left_frame, text="Reset", command=self.reset_main, width=10)
        self.reset_button.grid(row=8, column=0, sticky="n", pady=(0, 10))
        
        self.btn_back = tk.Button(left_frame, text="Back", command=self.setup_ui, width=10)
        self.btn_back.grid(row=9, column=0, sticky="n", pady=(0, 10))
        
        self.btn_merge = tk.Button(left_frame, text="Merge", command=self.merge_files, width=10)
        self.btn_merge.grid(row=10, column=0, sticky="n", pady=(0, 10))
    
    
    def reset_main(self):
        
        self.preview_pdf(1)
        
    def update_status_message(self, message, color="red"):
        """Updates the status message label with the given message and color."""
        self.status_message.config(text=message, fg=color)
   
           
    def process_input(self):
        try:
            # Get input from the Text widget
            raw_input = self.input_order.get("1.0", "end-1c").strip()  # Extracts all input text and removes trailing newlines/spaces

            if not raw_input:
                raise ValueError("No page order provided.")

            # Convert input into a list of integers
            self.new_order = [int(x.strip()) for x in raw_input.split(",") if x.strip().isdigit()]

            # Check if the provided indices are within a valid range
            total_pages = len(self.pages_pdf)

            if not self.new_order:
                raise ValueError("Invalid input. Please enter numbers separated by commas.")

            if any(i < 1 or i > total_pages for i in self.new_order):
                raise ValueError(f"Invalid page numbers detected. Please enter numbers between 1 and {total_pages}.")

            if len(self.new_order) != total_pages:
                raise ValueError(f"Incorrect number of indices. You provided {len(self.new_order)}, but {total_pages} pages exist.")

            self.update_status_message("Order input is valid.", color="green")

        except ValueError as e:
            self.update_status_message(str(e), color="red")
            self.new_order = []  # Reset to avoid processing invalid input




    def ending_screen(self):
        self.lbl_status_list.destroy()
        self.btn_next.destroy()
        self.introduction.destroy()
        self.btn_upload.destroy()
        self.btn_reset.destroy()
        self.lbl_status.destroy()
        self.lbl_status_list.destroy()
        self.instructions.destroy()
        self.input_order.destroy()
        self.name_instructions.destroy()
        self.input_name.destroy()
        self.num_index_display.destroy()
        self.status_message.destroy()
        self.btn_preview.destroy()
        self.reset_button.destroy()
        self.btn_back.destroy()
        self.btn_merge.destroy()
        
        self.end_frame = tk.Frame(self.root)
        self.end_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.end_frame.columnconfigure(0, weight=1)
        # Let the listbox expand to fill available vertical space.
        self.end_frame.rowconfigure(6, weight=1)
        
        self.end_message = tk.Label(self.end_frame, text="Thank you for using the PDF Merger", font=("Helvetica", 12))
        self.end_message.grid(row=0, column=0, sticky="n", pady=(0, 20))
        
        self.end_message2 = tk.Label(self.end_frame, text="Please click the button below to close the application", font=("Helvetica", 12))
        self.end_message2.grid(row=1, column=0, sticky="n", pady=(0, 20))
        
        self.close_button = tk.Button(self.end_frame, text="Close", command=self.close, width=10)
        self.close_button.grid(row=2, column=0, sticky="n", pady=(0, 10))    


    def merge_files(self):
        self.process_input()

        if not self.new_order:
            self.update_status_message("Error: Invalid page order. Please check your input and try again.", color="red")
            return

        writer = PdfWriter()

        try:
            for i in self.new_order:
                if i in self.pages_pdf:
                    pdf_path = self.pages_pdf[i]
                    with open(pdf_path, "rb") as f:
                        pdf_reader = PdfReader(f)
                        writer.add_page(pdf_reader.pages[0])  # Properly re-opens the file

                else:
                    self.update_status_message(f"Warning: Page {i} not found in pages_pdf.", color="orange")

            output_filename = self.input_name.get().strip()
            if not output_filename:
                self.update_status_message("Error: No filename provided.", color="red")
                return
            
            if not output_filename.endswith(".pdf"):
                output_filename += ".pdf"

            abs_path = os.path.abspath(output_filename)

            with open(abs_path, "wb") as f:
                writer.write(f)

            self.update_status_message(f"PDF successfully saved as {abs_path}", color="green")

            # Open the merged PDF in the default viewer
            if sys.platform.startswith("win"):  # Windows
                os.startfile(abs_path)
            elif sys.platform.startswith("linux"):  # Linux
                sp.run(["xdg-open", abs_path])
            elif sys.platform.startswith("darwin"):  # macOS
                sp.run(["open", abs_path])
            # Cleanup temp files
            for temp_file in self.uploaded_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            self.uploaded_files = []  # Clear the list

                
            self.ending_screen()

        except Exception as e:
            self.update_status_message(f"Error while merging PDFs: {e}", color="red")



            
    def preview_pdf(self, counter):
        
        self.process_input()
        if not self.new_order:
            
            self.update_status_message("Error: Invalid page order. Please check your input.", color="red")
            return
        
        
        self.clear_preview()
        try:
            if counter == 0:
                for i in self.new_order:
                    if i not in self.pages_img:
                        self.update_status_message(f"Warning: Page {i} preview not found.")
                        continue

                    img = self.pages_img[i]
                    img_tk = ImageTk.PhotoImage(img)
                    self.pdf_previews[f"{i}"] = img_tk

                    # Add index label
                    num_label = tk.Label(self.preview_box, text=f"Page {i}", font=("Arial", 10, "bold"))
                    num_label.pack(side="top", pady=2)

                    lbl_preview = tk.Label(self.preview_box, image=img_tk)
                    lbl_preview.pack(side="top", padx=10, pady=10)

                    self.preview_box.update_idletasks()
                    self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

            elif counter == 1:
                for i in range(1, len(self.new_order) + 1):
                    if i not in self.pages_img:
                        print(f"Warning: Page {i} preview not found.")
                        continue

                    img = self.pages_img[i]
                    img_tk = ImageTk.PhotoImage(img)
                    self.pdf_previews[f"{i}"] = img_tk

                    # Add index label
                    num_label = tk.Label(self.preview_box, text=f"Page {i}", font=("Arial", 10, "bold"))
                    num_label.pack(side="top", pady=2)

                    lbl_preview = tk.Label(self.preview_box, image=img_tk)
                    lbl_preview.pack(side="top", padx=10, pady=5)

                    self.preview_box.update_idletasks()
                    self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

        except Exception as e:
            print(f"Error while generating preview: {e}")


    def process_uploads(self):
        if not hasattr(self, 'pages_img'):
            self.pages_img = {}
        if not hasattr(self, 'pages_pdf'):
            self.pages_pdf = {}

        counter = len(self.page_order) + 1  # Maintain numbering across uploads
        counter_pdf = len(self.pages_pdf) + 1  # Maintain numbering across PDFs

        self.page_order = sorted(set(self.page_order) | set(self.pages_img.keys()) | set(self.pages_pdf.keys()))

        
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
                    self.page_order.append(counter)
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
                self.pages_pdf[counter_pdf] = temp_pdf_path  # Store the path instead of closing
                self.uploaded_files.append(temp_pdf_path)  # Keep track of temp files

                counter_pdf += 1
                
                img = Image.open(filepath)
                img.thumbnail((400, 500))
                img_tk = ImageTk.PhotoImage(img)

                # Store image reference to prevent garbage collection
                self.pdf_previews[f"{filename} {counter}"] = img_tk

                self.page_order.append(counter)
                self.pages_img[counter] = img
                counter += 1

    def close(self):
        self.root.destroy()

    def clear_preview(self):
        # Remove all widgets (images) from the preview_box frame
        for widget in self.preview_box.winfo_children():
            widget.destroy()
        # Optionally, if you are keeping references to the images,
        # clear that dictionary as well:
        self.pdf_previews.clear()
        self.preview_canvas.update_idletasks()


    def get_pages(self, pdf):
        read = PdfReader(pdf)
        counter = 1
        for page in read.pages:
            self.pages[counter] = page
            counter += 1


    
    
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
        
        self.clear_preview()  # Clears old previews
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
        
        
            

    def populate_previews_sequentially(self, keys=None, index=0, delay=100):
        """
        Display preview images one by one with a delay, ensuring page numbers are visible above each slide.
        """
        if keys is None:
            keys = sorted(self.pages_img.keys())
        if index < len(keys):
            key = keys[index]
            img = self.pages_img[key]
            img_tk = ImageTk.PhotoImage(img)
            
            # Add a label for the index above the preview image
            lbl_index = tk.Label(self.preview_box, text=f"Page {key}", font=("Arial", 10, "bold"))
            lbl_index.pack(side="top", pady=2)

            lbl_preview = tk.Label(self.preview_box, image=img_tk)
            lbl_preview.image = img_tk  # Keep reference to avoid garbage collection
            lbl_preview.pack(side="top", padx=10, pady=10)

            self.preview_box.update_idletasks()
            self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

            # Schedule the next image after the specified delay
            self.root.after(delay, lambda: self.populate_previews_sequentially(keys, index + 1, delay))


      
        
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


