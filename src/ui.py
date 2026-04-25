import os
import tkinter as tk
from tkinter import filedialog, messagebox
import utils


def browse_file(entry_widget):
    file_path = filedialog.askopenfilename(
        title="Select Text File",
        initialdir=os.path.abspath("src/data"),
        filetypes=[("Text Files", "*.txt")]
    )
    if file_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)


def compare_documents():
    file1 = entry_file1.get()
    file2 = entry_file2.get()

    if not file1 or not file2:
        messagebox.showwarning("Warning", "Please select both files.")
        return

    result = utils.run_comparison(file1, file2)

    if "error" in result:
        messagebox.showerror("Error", result["error"])
        return

    result_text.delete("1.0", tk.END)
    result_text.insert(tk.END, f"Document 1: {result['file1']}\n")
    result_text.insert(tk.END, f"Document 2: {result['file2']}\n\n")
    result_text.insert(tk.END, "--- RESULT ---\n")
    result_text.insert(
        tk.END,
        f"MinHash similarity estimate: {result['minhash_similarity']:.4f} ({result['minhash_similarity'] * 100:.2f}%)\n"
    )
    result_text.insert(
        tk.END,
        f"Jaccard similarity (whole document): {result['real_similarity']:.4f} ({result['real_similarity'] * 100:.2f}%)\n\n"
    )
    result_text.insert(tk.END, "--- EXTRA INFO ---\n")
    result_text.insert(tk.END, f"Number of shingles in doc1: {result['num_shingles_doc1']}\n")
    result_text.insert(tk.END, f"Number of shingles in doc2: {result['num_shingles_doc2']}\n")
    result_text.insert(tk.END, f"Number of common shingles: {result['common_shingles']}\n")
    result_text.insert(tk.END, f"Vocabulary size: {result['vocab_size']}\n")


# ================= UI =================
root = tk.Tk()
root.title("Plagiarism Detector")
root.geometry("800x500")

label_title = tk.Label(root, text="Plagiarism Detector", font=("Arial", 16, "bold"))
label_title.pack(pady=10)

frame1 = tk.Frame(root)
frame1.pack(pady=5, fill="x", padx=10)

label1 = tk.Label(frame1, text="File 1:", width=10, anchor="w")
label1.pack(side="left")

entry_file1 = tk.Entry(frame1, width=70)
entry_file1.pack(side="left", padx=5)

button_browse1 = tk.Button(frame1, text="Browse", command=lambda: browse_file(entry_file1))
button_browse1.pack(side="left")

frame2 = tk.Frame(root)
frame2.pack(pady=5, fill="x", padx=10)

label2 = tk.Label(frame2, text="File 2:", width=10, anchor="w")
label2.pack(side="left")

entry_file2 = tk.Entry(frame2, width=70)
entry_file2.pack(side="left", padx=5)

button_browse2 = tk.Button(frame2, text="Browse", command=lambda: browse_file(entry_file2))
button_browse2.pack(side="left")

button_compare = tk.Button(root, text="Compare", font=("Arial", 12, "bold"), command=compare_documents)
button_compare.pack(pady=15)

result_text = tk.Text(root, height=18, width=95)
result_text.pack(padx=10, pady=10)

root.mainloop()