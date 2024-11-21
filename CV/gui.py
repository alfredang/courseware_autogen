import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import subprocess
import sys

def run_processing(input_file):
    try:
        status_label.config(text="Processing...")
        
        # Define paths
        downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
        output_json = os.path.join(downloads_folder, 'output_TSC.json')
        output_docx = os.path.join(downloads_folder, 'updated_validation_form')

        # Paths to your template files
        word_template_1 = 'CP_validation_template_bernard.docx'  # Adjust if necessary
        word_template_2 = 'CP_validation_template_dwight.docx'
        word_template_3 = 'CP_validation_template_ferris.docx'

        # Step 1: Run main.py with dynamic paths
        subprocess.run([
            sys.executable, 'main.py',
            input_file,             # Input DOCX file
            output_json,            # Output JSON file from document_parser.py
            word_template_1,        # First Word template for json_docu_replace.py
            word_template_2,        # Second Word template for json_docu_replace.py
            word_template_3,        # Third Word template for json_docu_replace.py
            output_docx             # Base name for final output DOCX files
        ], check=True)
        
        status_label.config(text="Processing complete.")
        messagebox.showinfo("Success", f"Files processed and saved to {downloads_folder}")
    except subprocess.CalledProcessError as e:
        status_label.config(text="Error during processing.")
        messagebox.showerror("Error", f"An error occurred: {e}")
    except Exception as e:
        status_label.config(text="Error during processing.")
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
def start_processing():
    if not selected_file.get():
        messagebox.showwarning("No file selected", "Please select a file to process.")
        return
    threading.Thread(target=run_processing, args=(selected_file.get(),), daemon=True).start()

def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
    if file_path:
        selected_file.set(file_path)
        status_label.config(text=f"Selected file: {os.path.basename(file_path)}")

# Initialize the main window
root = tk.Tk()
root.title("File Processor")

selected_file = tk.StringVar()

# Create and place widgets
upload_button = tk.Button(root, text="Upload File", command=upload_file)
upload_button.pack(pady=10)

process_button = tk.Button(root, text="Process File", command=start_processing)
process_button.pack(pady=10)

status_label = tk.Label(root, text="No file selected")
status_label.pack(pady=10)

# Start the GUI event loop
root.mainloop()
