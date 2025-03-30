import sys
import os
from plusscript import main as terminal_main  # Import terminal functionality
from plusscript_ide import PlusScriptIDE  # Import IDE functionality
import tkinter as tk

def launch_ide(file_path=None):
    root = tk.Tk()
    app = PlusScriptIDE(root)
    if file_path and file_path.endswith('.ps'):
        app.open_file_from_arg(file_path)
    root.mainloop()

def launch_terminal(file_path=None):
    if file_path:
        sys.argv = [sys.argv[0], file_path]  # Simulate command-line arg
    terminal_main()

def print_help():
    print("PlusScript - The Hyper-Language")
    print("Usage:")
    print("  plusscript_main --ide [file.ps]    Launch the IDE (default if no args)")
    print("  plusscript_main --term [file.ps]   Launch the terminal")
    print("  plusscript_main <file.ps>          Run a .ps file in terminal")
    print("  plusscript_main --help             Show this help")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--ide":
            launch_ide(sys.argv[2] if len(sys.argv) > 2 else None)
        elif sys.argv[1] == "--term":
            launch_terminal(sys.argv[2] if len(sys.argv) > 2 else None)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print_help()
        elif sys.argv[1].endswith('.ps'):
            launch_terminal(sys.argv[1])
        else:
            print("Unknown argument. Use --help for usage.")
            sys.exit(1)
    else:
        launch_ide()  # Default to IDE if no args