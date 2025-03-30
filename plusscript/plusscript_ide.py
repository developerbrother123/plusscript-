import tkinter as tk
from tkinter import scrolledtext, filedialog
import subprocess
import os
import sys
from plusscript import tokenize, run, variables, functions, classes, modules, types, BUILTINS  # Import interpreter components

class PlusScriptIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("PlusScript IDE with Terminal")
        self.root.geometry("1000x800")

        # Set icon (assuming plusscript.ico/png is in the directory)
        if sys.platform == "win32":
            self.root.iconbitmap("plusscript.ico")
        else:
            self.root.tk.call('wm', 'iconphoto', self.root._w, tk.PhotoImage(file="plusscript.png"))

        # Main frame
        self.main_frame = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame (Editor)
        self.left_frame = tk.Frame(self.main_frame)
        self.main_frame.add(self.left_frame, width=500)

        self.editor_label = tk.Label(self.left_frame, text="Code Editor")
        self.editor_label.pack(pady=5)

        self.editor = scrolledtext.ScrolledText(self.left_frame, wrap=tk.WORD, width=60, height=30)
        self.editor.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        # Buttons
        self.button_frame = tk.Frame(self.left_frame)
        self.button_frame.pack(pady=5)

        self.run_button = tk.Button(self.button_frame, text="Run", command=self.run_code)
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(self.button_frame, text="Save", command=self.save_file)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.open_button = tk.Button(self.button_frame, text="Open", command=self.open_file)
        self.open_button.pack(side=tk.LEFT, padx=5)

        # Right frame (Output and Terminal)
        self.right_frame = tk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        self.main_frame.add(self.right_frame)

        # Output panel
        self.output_frame = tk.Frame(self.right_frame)
        self.right_frame.add(self.output_frame, height=300)

        self.output_label = tk.Label(self.output_frame, text="Output")
        self.output_label.pack(pady=5)

        self.output = scrolledtext.ScrolledText(self.output_frame, wrap=tk.WORD, width=60, height=15)
        self.output.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        # Terminal panel
        self.terminal_frame = tk.Frame(self.right_frame)
        self.right_frame.add(self.terminal_frame)

        self.terminal_label = tk.Label(self.terminal_frame, text="Terminal (ps> )")
        self.terminal_label.pack(pady=5)

        self.terminal = scrolledtext.ScrolledText(self.terminal_frame, wrap=tk.WORD, width=60, height=15)
        self.terminal.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        self.terminal.insert(tk.END, "ps> ")
        self.terminal.config(state=tk.NORMAL)

        # Bind Enter key to terminal input
        self.terminal.bind("<Return>", self.process_terminal_input)

        # Terminal state
        self.terminal_code = ""
        self.local_vars = variables.copy()

        # Check for file argument
        if len(sys.argv) > 1 and sys.argv[1].endswith('.ps'):
            self.open_file_from_arg(sys.argv[1])

    def run_code(self):
        code = self.editor.get("1.0", tk.END).strip()
        if code:
            tokens = tokenize(code)
            self.output.delete("1.0", tk.END)
            try:
                # Redirect stdout to output panel
                original_stdout = sys.stdout
                sys.stdout = OutputRedirector(self.output)
                run(tokens)
                sys.stdout = original_stdout
            except Exception as e:
                self.output.insert(tk.END, f"Error: {e}\n")

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".ps", filetypes=[("PlusScript Files", "*.ps")])
        if file_path:
            with open(file_path, "w") as f:
                f.write(self.editor.get("1.0", tk.END))
            self.root.title(f"PlusScript IDE - {file_path}")

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PlusScript Files", "*.ps")])
        if file_path:
            self.open_file_from_arg(file_path)

    def open_file_from_arg(self, file_path):
        with open(file_path, "r") as f:
            self.editor.delete("1.0", tk.END)
            self.editor.insert(tk.END, f.read())
        self.root.title(f"PlusScript IDE - {file_path}")

    def process_terminal_input(self, event):
        # Get the last line (input after ps> )
        current_text = self.terminal.get("1.0", tk.END).strip()
        lines = current_text.split('\n')
        last_line = lines[-1].replace("ps> ", "").strip()

        if last_line:
            if last_line == "exit":
                self.terminal.insert(tk.END, "\nTerminal closed. Restart IDE to use again.\n")
                self.terminal.config(state=tk.DISABLED)
                return "break"
            elif last_line == "help":
                self.terminal.insert(tk.END, "\nCommands:\n  exit - Close terminal\n  help - Show this\n  Any PlusScript code - Execute\n")
            elif last_line == "clear":
                self.terminal.delete("1.0", tk.END)
                self.terminal.insert(tk.END, "ps> ")
            else:
                self.terminal_code += last_line + "\n"
                try:
                    if not last_line.strip() or last_line.strip().endswith(':') or self.terminal_code.count('+func') > self.terminal_code.count('+end'):
                        self.terminal.insert(tk.END, "\n... ")
                    else:
                        tokens = tokenize(self.terminal_code)
                        original_stdout = sys.stdout
                        sys.stdout = OutputRedirector(self.terminal)
                        run(tokens, self.local_vars)
                        sys.stdout = original_stdout
                        self.terminal_code = ""
                        self.terminal.insert(tk.END, "\nps> ")
                except Exception as e:
                    self.terminal.insert(tk.END, f"\nError: {e}\nps> ")
                    self.terminal_code = ""

        else:
            self.terminal.insert(tk.END, "\nps> ")

        # Prevent default Enter behavior (extra newline)
        return "break"

class OutputRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = PlusScriptIDE(root)
    root.mainloop()