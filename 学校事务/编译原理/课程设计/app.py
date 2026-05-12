from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from compiler.pipeline import run_pipeline, write_outputs


SAMPLE_SOURCE = """const int limit = 3;

int add(int a, int b) {
    int c = a + b;
    return c;
}

int main() {
    int i = 0;
    int total = 0;
    while (i < limit) {
        total = add(total, i);
        i = i + 1;
    }
    return total;
}
"""


TAB_DEFINITIONS = (
    ("tokens", "Tokens"),
    ("ast", "AST"),
    ("semantic_errors", "Semantic Errors"),
    ("const", "Const Symbols"),
    ("var", "Var Symbols"),
    ("function", "Functions"),
    ("quads", "Quadruples"),
)


class CompilerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.current_file: Path | None = None
        self.current_result = None
        self.result_texts: dict[str, tk.Text] = {}

        self.root.title("Compiler Pipeline GUI")
        self.root.geometry("1100x720")

        self._build_toolbar()
        self._build_main_area()
        self._build_status_bar()

        self.source_text.insert("1.0", SAMPLE_SOURCE)
        self.source_text.edit_modified(False)
        self.source_text.bind("<<Modified>>", self._on_source_modified)
        self._set_status("Ready")

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root, padding=(8, 8, 8, 4))
        toolbar.pack(side=tk.TOP, fill=tk.X)

        buttons = (
            ("Open", self.open_file),
            ("Save", self.save_file),
            ("Run", self.run),
            ("Export", self.export),
            ("Clear", self.clear),
        )
        for label, command in buttons:
            ttk.Button(toolbar, text=label, command=command).pack(side=tk.LEFT, padx=(0, 6))

    def _build_main_area(self) -> None:
        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        source_frame = ttk.Frame(main)
        self.source_text = tk.Text(source_frame, wrap=tk.NONE, undo=True, font=("Consolas", 11))
        source_y = ttk.Scrollbar(source_frame, orient=tk.VERTICAL, command=self.source_text.yview)
        source_x = ttk.Scrollbar(source_frame, orient=tk.HORIZONTAL, command=self.source_text.xview)
        self.source_text.configure(yscrollcommand=source_y.set, xscrollcommand=source_x.set)

        self.source_text.grid(row=0, column=0, sticky="nsew")
        source_y.grid(row=0, column=1, sticky="ns")
        source_x.grid(row=1, column=0, sticky="ew")
        source_frame.rowconfigure(0, weight=1)
        source_frame.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(main)
        for key, title in TAB_DEFINITIONS:
            tab = ttk.Frame(self.notebook)
            text = tk.Text(tab, wrap=tk.NONE, state=tk.DISABLED, font=("Consolas", 10))
            y_scroll = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=text.yview)
            x_scroll = ttk.Scrollbar(tab, orient=tk.HORIZONTAL, command=text.xview)
            text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

            text.grid(row=0, column=0, sticky="nsew")
            y_scroll.grid(row=0, column=1, sticky="ns")
            x_scroll.grid(row=1, column=0, sticky="ew")
            tab.rowconfigure(0, weight=1)
            tab.columnconfigure(0, weight=1)

            self.notebook.add(tab, text=title)
            self.result_texts[key] = text

        main.add(source_frame, weight=1)
        main.add(self.notebook, weight=1)

    def _build_status_bar(self) -> None:
        self.status_var = tk.StringVar()
        status = ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W, padding=(8, 4))
        status.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_source_modified(self, event=None) -> None:
        if self.source_text.edit_modified():
            self.current_result = None
            self.source_text.edit_modified(False)

    def open_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="Open Source File",
            filetypes=(("C-like source", "*.c *.h *.txt"), ("All files", "*.*")),
        )
        if not filename:
            return

        path = Path(filename)
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Open Failed", str(exc))
            self._set_status("Open failed")
            return

        self.source_text.delete("1.0", tk.END)
        self.source_text.insert("1.0", source)
        self.source_text.edit_modified(False)
        self.current_file = path
        self.current_result = None
        self.clear_results()
        self._set_status(f"Opened {path}")

    def save_file(self) -> bool:
        if self.current_file is None:
            filename = filedialog.asksaveasfilename(
                title="Save Source File",
                defaultextension=".c",
                filetypes=(("C-like source", "*.c"), ("Text files", "*.txt"), ("All files", "*.*")),
            )
            if not filename:
                return False
            self.current_file = Path(filename)

        try:
            self.current_file.write_text(self._source(), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save Failed", str(exc))
            self._set_status("Save failed")
            return False

        self._set_status(f"Saved {self.current_file}")
        return True

    def run(self) -> bool:
        try:
            result = run_pipeline(self._source())
            write_outputs(result, Path("outputs"))
        except Exception as exc:
            messagebox.showerror("Run Failed", str(exc))
            self._set_status("Run failed")
            return False

        self.current_result = result
        self._fill_results(result)
        self._set_status(
            f"Run complete: {len(result.tokens)} tokens, "
            f"{len(result.diagnostics)} diagnostics, {len(result.quads)} quadruples"
        )
        return True

    def export(self) -> None:
        if self.current_result is None and not self.run():
            return

        try:
            write_outputs(self.current_result, Path("outputs"))
        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc))
            self._set_status("Export failed")
            return

        messagebox.showinfo("Export Complete", "Outputs written to outputs/")
        self._set_status("Exported outputs/")

    def clear(self) -> None:
        self.source_text.delete("1.0", tk.END)
        self.source_text.edit_modified(False)
        self.current_result = None
        self.clear_results()
        self._set_status("Cleared")

    def clear_results(self) -> None:
        for text in self.result_texts.values():
            self._set_text(text, "")

    def _fill_results(self, result) -> None:
        for key, _title in TAB_DEFINITIONS:
            self._set_text(self.result_texts[key], result.texts[key])

    def _source(self) -> str:
        return self.source_text.get("1.0", "end-1c")

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.configure(state=tk.DISABLED)

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)


def main() -> None:
    root = tk.Tk()
    app = CompilerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
