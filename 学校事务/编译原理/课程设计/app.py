from pathlib import Path
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from compiler.cfg_dag import analyze_control_flow
from compiler.lexer import KEYWORDS, Lexer
from compiler.log_automata import analyze_log_with_regex, write_log_outputs
from compiler.parser import Parser
from compiler.pipeline import run_pipeline, write_outputs
from compiler.semantic import SemanticAnalyzer
from compiler.source_format import INDENT, format_source


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


RESULT_GROUPS = (
    (
        "编译流程",
        (
            ("tokens", "Tokens"),
            ("ast", "AST"),
            ("semantic_errors", "Semantic Errors"),
            ("quads", "Quadruples"),
            ("interpreter", "Interpreter"),
        ),
    ),
    ("符号与诊断", (("const", "Const Symbols"), ("var", "Var Symbols"), ("function", "Functions"))),
    (
        "后端输出",
        (
            ("optimized_quads", "Optimized Quads"),
            ("llvm_ir", "LLVM IR"),
            ("llvm_verify", "LLVM Verify"),
            ("target_code", "Target Code"),
            ("assembly", "Assembly"),
            ("optimized_target_code", "Optimized Target Code"),
        ),
    ),
    (
        "扩展任务",
        (
            ("log_extract", "Log Extract"),
            ("log_nfa", "NFA Graph"),
            ("log_dfa", "DFA Graph"),
            ("log_dfa_table", "DFA Table"),
            ("log_nfa_visual", "NFA Visual"),
            ("log_dfa_visual", "DFA Visual"),
            ("basic_blocks", "Basic Blocks"),
            ("cfg", "CFG"),
            ("dag", "DAG"),
            ("dag_optimized_quads", "DAG Optimized Quads"),
            ("cfg_visual", "CFG Visual"),
            ("dag_visual", "DAG Visual"),
        ),
    ),
)

WELCOME_TEXT = (
    "就绪。\n\n"
    "左侧输入或打开源代码后，点击“运行”查看编译结果。\n"
    "进行 4.1 日志任务时，粘贴日志、填写 Regex，然后点击“日志识别”。\n"
    "结果会在这里显示。\n"
)

LOG_PLACEHOLDERS = {
    "log_extract": "Paste log text on the left, enter a regex, then click 日志识别.\n\nExample regex:\n\\d{4}-\\d{2}-\\d{2}\n",
    "log_nfa": "Enter a regex and click 日志识别 to build the NFA graph.\n",
    "log_dfa": "Enter a regex and click 日志识别 to build the DFA graph.\n",
    "log_dfa_table": "Enter a regex and click 日志识别 to build the DFA transition table.\n",
    "log_nfa_visual": "Enter a regex and click 日志识别 to draw the NFA graph.\n",
    "log_dfa_visual": "Enter a regex and click 日志识别 to draw the DFA graph.\n",
}

COMMON_REGEX_PATTERNS = (
    ("日期 DATE", r"\d{4}-\d{2}-\d{2}"),
    ("时间 TIME", r"\d{2}:\d{2}:\d{2}"),
    ("IP 地址", r"(?:\d{1,3}\.){3}\d{1,3}"),
    ("日志级别", r"\b(?:INFO|WARN|ERROR|DEBUG|FATAL)\b"),
    ("状态码", r"status=\d{3}"),
    ("用户", r"user=[A-Za-z_][A-Za-z0-9_]*"),
    ("动作", r"action=[A-Za-z_][A-Za-z0-9_]*"),
)


class CompilerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.current_file: Path | None = None
        self.current_result = None
        self.result_cache: dict[str, str] = {}
        self.tree_items: dict[str, str] = {}
        self.summary_vars: dict[str, tk.StringVar] = {}
        self.regex_var = tk.StringVar(value=r"\d{4}-\d{2}-\d{2}")
        self.regex_preset_var = tk.StringVar(value="常用")
        self.highlight_job = None
        self.diagnostics_job = None
        self.editor_diagnostics = []
        self.error_lines: set[int] = set()
        self.log_graph_fragments: list[str] = []
        self.current_visual_key: str | None = None
        self.control_flow_analysis = None
        self.graph_zoom = 1.0
        self.graph_zoom_var = tk.StringVar(value="100%")

        self.root.title("Compiler Course Design")
        self.root.geometry("1160x740")
        self.root.minsize(980, 620)

        self._configure_style()

        self._build_toolbar()
        self._build_main_area()
        self._build_status_bar()
        self.clear_results()

        self.source_text.insert("1.0", SAMPLE_SOURCE)
        self.source_text.edit_modified(False)
        self.source_text.bind("<<Modified>>", self._on_source_modified)
        self.source_text.bind("<Return>", self._on_return)
        self.source_text.bind("}", self._on_closing_brace)
        self.source_text.bind("<Configure>", self._on_editor_view_changed)
        self.source_text.bind("<KeyRelease>", self._on_editor_view_changed)
        self.source_text.bind("<MouseWheel>", self._on_editor_view_changed)
        self._configure_source_highlight_tags()
        self._highlight_source()
        self._schedule_diagnostics()
        self.root.after_idle(self._draw_line_numbers)
        self._set_status("Ready")

    def _configure_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.root.configure(bg="#f4f6f8")
        style.configure(".", font=("Microsoft YaHei UI", 10), background="#f4f6f8")
        style.configure("Toolbar.TFrame", background="#111827")
        style.configure("ToolbarTitle.TLabel", background="#111827", foreground="#f9fafb", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("Toolbar.TButton", padding=(10, 4), font=("Microsoft YaHei UI", 9))
        style.configure("Subtle.TButton", padding=(8, 3), font=("Microsoft YaHei UI", 9))
        style.configure("Panel.TFrame", background="#ffffff", relief=tk.FLAT)
        style.configure("PanelTitle.TLabel", background="#ffffff", foreground="#111827", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Summary.TFrame", background="#ffffff")
        style.configure("SummaryValue.TLabel", background="#ffffff", foreground="#111827", font=("Microsoft YaHei UI", 12, "bold"))
        style.configure("SummaryLabel.TLabel", background="#ffffff", foreground="#6b7280", font=("Microsoft YaHei UI", 9))
        style.configure("Treeview", rowheight=24, font=("Microsoft YaHei UI", 9), background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Diagnostics.Treeview", rowheight=22, font=("Microsoft YaHei UI", 9))

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root, padding=(12, 7), style="Toolbar.TFrame")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(toolbar, text="编译原理课程设计", style="ToolbarTitle.TLabel").pack(side=tk.LEFT, padx=(0, 20))

        buttons = (
            ("打开", self.open_file),
            ("保存", self.save_file),
            ("运行", self.run),
            ("导出", self.export),
        )
        for label, command in buttons:
            ttk.Button(toolbar, text=label, command=command, style="Toolbar.TButton").pack(side=tk.LEFT, padx=(0, 6))

    def _build_main_area(self) -> None:
        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=12)

        source_frame = ttk.Frame(main, padding=10, style="Panel.TFrame")
        source_header = ttk.Frame(source_frame, style="Panel.TFrame")
        source_header.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        source_header.columnconfigure(0, weight=1)
        ttk.Label(source_header, text="Source", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(source_header, text="格式化", command=self.format_current_source, style="Subtle.TButton").grid(row=0, column=1, padx=(0, 6))
        ttk.Button(source_header, text="清空", command=self.clear, style="Subtle.TButton").grid(row=0, column=2)

        self.source_text = tk.Text(
            source_frame,
            wrap=tk.NONE,
            undo=True,
            font=("Consolas", 11),
            background="#fbfdff",
            foreground="#111827",
            insertbackground="#111827",
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.line_numbers = tk.Canvas(source_frame, width=48, background="#eef2f7", highlightthickness=0)
        source_y = ttk.Scrollbar(source_frame, orient=tk.VERTICAL, command=self._on_source_scrollbar)
        source_x = ttk.Scrollbar(source_frame, orient=tk.HORIZONTAL, command=self.source_text.xview)
        self.source_text.configure(yscrollcommand=lambda first, last: self._on_source_yscroll(source_y, first, last), xscrollcommand=source_x.set)

        self.line_numbers.grid(row=1, column=0, sticky="ns")
        self.source_text.grid(row=1, column=1, sticky="nsew")
        source_y.grid(row=1, column=2, sticky="ns")
        source_x.grid(row=2, column=1, sticky="ew")
        self._build_regex_panel(source_frame)
        self._build_diagnostics_panel(source_frame)
        source_frame.rowconfigure(1, weight=1)
        source_frame.columnconfigure(1, weight=1)

        result_frame = ttk.Frame(main, padding=10, style="Panel.TFrame")
        result_frame.rowconfigure(2, weight=1)
        result_frame.columnconfigure(1, weight=1)

        ttk.Label(result_frame, text="Results", style="PanelTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self._build_summary(result_frame)
        self._build_result_view(result_frame)

        main.add(source_frame, weight=1)
        main.add(result_frame, weight=1)

    def _build_regex_panel(self, parent: ttk.Frame) -> None:
        regex_frame = ttk.Frame(parent, style="Panel.TFrame")
        regex_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 4))
        regex_frame.columnconfigure(1, weight=1)
        ttk.Label(regex_frame, text="Regex", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(regex_frame, textvariable=self.regex_var).grid(row=0, column=1, sticky="ew")
        self.regex_preset = ttk.Combobox(
            regex_frame,
            textvariable=self.regex_preset_var,
            values=[name for name, _pattern in COMMON_REGEX_PATTERNS],
            state="readonly",
            width=10,
        )
        self.regex_preset.grid(row=0, column=2, sticky="ew", padx=(8, 0))
        self.regex_preset.bind("<<ComboboxSelected>>", self._on_regex_preset_selected)
        ttk.Button(regex_frame, text="日志识别", command=self.run_log_automata, style="Subtle.TButton").grid(row=0, column=3, padx=(8, 0))

    def _on_regex_preset_selected(self, event=None) -> None:
        selected = self.regex_preset_var.get()
        for name, pattern in COMMON_REGEX_PATTERNS:
            if name == selected:
                self.regex_var.set(pattern)
                self._set_status(f"Regex preset: {name}")
                break

    def _build_diagnostics_panel(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Diagnostics", style="PanelTitle.TLabel").grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 6))
        columns = ("line", "phase", "code", "message")
        self.diagnostics_tree = ttk.Treeview(parent, columns=columns, show="headings", height=5, style="Diagnostics.Treeview")
        self.diagnostics_tree.heading("line", text="Line")
        self.diagnostics_tree.heading("phase", text="Phase")
        self.diagnostics_tree.heading("code", text="Code")
        self.diagnostics_tree.heading("message", text="Message")
        self.diagnostics_tree.column("line", width=48, minwidth=40, stretch=False, anchor=tk.CENTER)
        self.diagnostics_tree.column("phase", width=72, minwidth=60, stretch=False)
        self.diagnostics_tree.column("code", width=64, minwidth=54, stretch=False)
        self.diagnostics_tree.column("message", width=360, minwidth=180, stretch=True)
        diagnostics_scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.diagnostics_tree.yview)
        self.diagnostics_tree.configure(yscrollcommand=diagnostics_scroll.set)
        self.diagnostics_tree.grid(row=5, column=0, columnspan=2, sticky="ew")
        diagnostics_scroll.grid(row=5, column=2, sticky="ns")
        self.diagnostics_tree.bind("<<TreeviewSelect>>", self._on_diagnostic_selected)

    def _build_summary(self, parent: ttk.Frame) -> None:
        summary = ttk.Frame(parent, style="Summary.TFrame")
        summary.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        summary.columnconfigure(4, weight=0)
        for index, (key, label) in enumerate(
            (("tokens", "Tokens"), ("diagnostics", "Diagnostics"), ("quads", "Quadruples"), ("return", "Return"))
        ):
            summary.columnconfigure(index, weight=1)
            card = ttk.Frame(summary, padding=(8, 5), style="Summary.TFrame")
            card.grid(row=0, column=index, sticky="ew", padx=(0, 8 if index < 3 else 0))
            value = tk.StringVar(value="-")
            self.summary_vars[key] = value
            ttk.Label(card, textvariable=value, style="SummaryValue.TLabel").pack(anchor=tk.W)
            ttk.Label(card, text=label, style="SummaryLabel.TLabel").pack(anchor=tk.W)
        ttk.Button(summary, text="复制汇编", command=self.copy_assembly, style="Subtle.TButton").grid(row=0, column=4, sticky="e")

    def _build_result_view(self, parent: ttk.Frame) -> None:
        nav_frame = ttk.Frame(parent, style="Panel.TFrame")
        nav_frame.grid(row=2, column=0, sticky="nsw", padx=(0, 10))

        self.result_tree = ttk.Treeview(nav_frame, show="tree", selectmode="browse", height=18)
        self.result_tree.column("#0", width=170, minwidth=140, stretch=False)
        tree_scroll = ttk.Scrollbar(nav_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=tree_scroll.set)
        self.result_tree.grid(row=0, column=0, sticky="ns")
        tree_scroll.grid(row=0, column=1, sticky="ns")

        for index, (group_title, items) in enumerate(RESULT_GROUPS):
            group_id = self.result_tree.insert("", tk.END, text=group_title, open=index < 2)
            for key, title in items:
                item_id = self.result_tree.insert(group_id, tk.END, text=title)
                self.tree_items[key] = item_id
        self.result_tree.bind("<<TreeviewSelect>>", self._on_result_selected)

        text_frame = ttk.Frame(parent, style="Panel.TFrame")
        text_frame.grid(row=2, column=1, sticky="nsew")
        text_frame.rowconfigure(1, weight=1)
        text_frame.columnconfigure(0, weight=1)

        self.graph_tools = ttk.Frame(text_frame, style="Panel.TFrame")
        self.graph_tools.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Button(self.graph_tools, text="缩小", command=lambda: self._zoom_graph(0.8)).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(self.graph_tools, text="重置", command=self._reset_graph_zoom).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(self.graph_tools, text="适应", command=self._fit_graph_zoom).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(self.graph_tools, text="放大", command=lambda: self._zoom_graph(1.25)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(self.graph_tools, textvariable=self.graph_zoom_var, style="SummaryLabel.TLabel").pack(side=tk.LEFT)
        self.graph_tools.grid_remove()

        self.output_text = tk.Text(
            text_frame,
            wrap=tk.NONE,
            state=tk.DISABLED,
            font=("Consolas", 10),
            background="#0f172a",
            foreground="#e5e7eb",
            insertbackground="#e5e7eb",
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.output_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_x = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.output_text.xview)
        self.output_text.configure(yscrollcommand=self.output_y.set, xscrollcommand=self.output_x.set)
        self.output_text.grid(row=1, column=0, sticky="nsew")
        self.graph_canvas = tk.Canvas(text_frame, background="#f8fafc", highlightthickness=0)
        self.graph_canvas.configure(yscrollcommand=self.output_y.set, xscrollcommand=self.output_x.set)
        self.graph_canvas.bind("<Configure>", self._redraw_current_graph)
        self.output_y.grid(row=1, column=1, sticky="ns")
        self.output_x.grid(row=2, column=0, sticky="ew")

    def _build_status_bar(self) -> None:
        self.status_var = tk.StringVar()
        status = ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W, padding=(12, 6))
        status.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_source_modified(self, event=None) -> None:
        if self.source_text.edit_modified():
            self.current_result = None
            self.clear_results()
            self._clear_summary()
            self.source_text.edit_modified(False)
            self._schedule_highlight()
            self._schedule_diagnostics()
            self._draw_line_numbers()

    def _on_return(self, event=None) -> str:
        line_start = self.source_text.index("insert linestart")
        line_end = self.source_text.index("insert lineend")
        line = self.source_text.get(line_start, line_end)
        indent = re.match(r"\s*", line).group(0)
        if line.rstrip().endswith("{"):
            indent += INDENT
        self.source_text.insert("insert", "\n" + indent)
        self.root.after_idle(self._draw_line_numbers)
        return "break"

    def _on_closing_brace(self, event=None) -> str | None:
        line_start = self.source_text.index("insert linestart")
        before_cursor = self.source_text.get(line_start, "insert")
        if before_cursor.strip():
            return None
        remove_count = min(len(before_cursor), len(INDENT))
        if remove_count:
            self.source_text.delete(f"insert-{remove_count}c", "insert")
        self.source_text.insert("insert", "}")
        self.root.after_idle(self._draw_line_numbers)
        return "break"

    def _on_editor_view_changed(self, event=None) -> None:
        self.root.after_idle(self._draw_line_numbers)

    def _on_source_scrollbar(self, *args) -> None:
        self.source_text.yview(*args)
        self._draw_line_numbers()

    def _on_source_yscroll(self, scrollbar: ttk.Scrollbar, first: str, last: str) -> None:
        scrollbar.set(first, last)
        self._draw_line_numbers()

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
        self._clear_summary()
        self._highlight_source()
        self._schedule_diagnostics()
        self._draw_line_numbers()
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
        self.control_flow_analysis = analyze_control_flow(result.quads) if result.quads else None
        self._fill_results(result)
        self._fill_summary(result)
        self._apply_diagnostics(result.diagnostics)
        self._select_result("interpreter")
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

    def copy_assembly(self) -> None:
        if self.current_result is None and not self.run():
            return
        assembly = self.result_cache.get("assembly", "")
        if not assembly.strip():
            messagebox.showwarning("No Assembly", "Please run the compiler before copying assembly.")
            self._set_status("No assembly to copy")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(assembly)
        self.root.update()
        self._select_result("assembly")
        self._set_status("Assembly copied to clipboard")

    def run_log_automata(self) -> None:
        pattern = self.regex_var.get().strip()
        if not pattern:
            messagebox.showwarning("Regex Required", "Please enter a regular expression first.")
            self._set_status("Regex required")
            return
        try:
            result = analyze_log_with_regex(self._source(), pattern)
            write_log_outputs(result, Path("outputs"))
        except re.error as exc:
            messagebox.showerror("Invalid Regex", str(exc))
            self._set_status("Invalid regex")
            return
        except Exception as exc:
            messagebox.showerror("Log Scan Failed", str(exc))
            self._set_status("Log scan failed")
            return

        self.result_cache["log_extract"] = result.format_matches()
        self.result_cache["log_nfa"] = result.nfa_text
        self.result_cache["log_dfa"] = result.dfa_text
        self.result_cache["log_dfa_table"] = result.dfa_table_text
        self.result_cache["log_nfa_visual"] = "NFA graph rendered on canvas."
        self.result_cache["log_dfa_visual"] = "DFA graph rendered on canvas."
        self.log_graph_fragments = list(result.regex_fragments or [])
        self._select_result("log_extract")
        self._set_status(f"Log scan complete: {len(result.matches)} matches")

    def format_current_source(self) -> None:
        cursor = self.source_text.index("insert")
        formatted = format_source(self._source())
        self.source_text.delete("1.0", tk.END)
        self.source_text.insert("1.0", formatted)
        target_cursor = cursor if self.source_text.compare(cursor, "<=", "end-1c") else "end-1c"
        self.source_text.mark_set("insert", target_cursor)
        self.source_text.edit_modified(False)
        self.current_result = None
        self.clear_results()
        self._clear_summary()
        self._highlight_source()
        self._schedule_diagnostics()
        self._draw_line_numbers()
        self._set_status("Source formatted")

    def clear(self) -> None:
        self.source_text.delete("1.0", tk.END)
        self.source_text.edit_modified(False)
        self.current_result = None
        self.clear_results()
        self._clear_summary()
        self._apply_diagnostics([])
        self._highlight_source()
        self._draw_line_numbers()
        self._set_status("Cleared")

    def clear_results(self) -> None:
        self.result_cache = dict(LOG_PLACEHOLDERS)
        self.log_graph_fragments = []
        self.current_visual_key = None
        self.control_flow_analysis = None
        self._show_text_output()
        self._set_text(self.output_text, WELCOME_TEXT)
        if hasattr(self, "graph_canvas"):
            self.graph_canvas.delete("all")

    def _fill_results(self, result) -> None:
        self.result_cache = {**LOG_PLACEHOLDERS, **dict(result.texts)}

    def _fill_summary(self, result) -> None:
        self.summary_vars["tokens"].set(str(len(result.tokens)))
        self.summary_vars["diagnostics"].set(str(len(result.diagnostics)))
        self.summary_vars["quads"].set(str(len(result.quads)))
        self.summary_vars["return"].set(self._extract_return_value(result.texts.get("interpreter", "")))

    def _clear_summary(self) -> None:
        for value in self.summary_vars.values():
            value.set("-")

    def _extract_return_value(self, interpreter_text: str) -> str:
        for line in interpreter_text.splitlines():
            if line.startswith("return_value:"):
                return line.split(":", 1)[1].strip()
        return "-"

    def _on_result_selected(self, event=None) -> None:
        selected = self.result_tree.selection()
        if not selected:
            return
        item_id = selected[0]
        for key, known_id in self.tree_items.items():
            if known_id == item_id:
                if key in {"log_nfa_visual", "log_dfa_visual", "cfg_visual", "dag_visual"}:
                    self._show_graph(key)
                    return
                self._show_text_output()
                self._set_text(self.output_text, self.result_cache.get(key, ""))
                return

    def _select_result(self, key: str) -> None:
        item_id = self.tree_items.get(key)
        if item_id is None:
            return
        self.result_tree.selection_set(item_id)
        self.result_tree.focus(item_id)
        self.result_tree.see(item_id)
        if key in {"log_nfa_visual", "log_dfa_visual", "cfg_visual", "dag_visual"}:
            self._show_graph(key)
        else:
            self._show_text_output()
            self._set_text(self.output_text, self.result_cache.get(key, ""))

    def _show_text_output(self) -> None:
        self.current_visual_key = None
        if hasattr(self, "graph_canvas"):
            self.graph_canvas.grid_remove()
        if hasattr(self, "graph_tools"):
            self.graph_tools.grid_remove()
        self.output_y.configure(command=self.output_text.yview)
        self.output_x.configure(command=self.output_text.xview)
        self.output_text.configure(yscrollcommand=self.output_y.set, xscrollcommand=self.output_x.set)
        self.output_text.grid(row=1, column=0, sticky="nsew")

    def _show_graph(self, key: str) -> None:
        self.current_visual_key = key
        self.output_text.grid_remove()
        self.graph_tools.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.output_y.configure(command=self.graph_canvas.yview)
        self.output_x.configure(command=self.graph_canvas.xview)
        self.graph_canvas.configure(yscrollcommand=self.output_y.set, xscrollcommand=self.output_x.set)
        self.graph_canvas.grid(row=1, column=0, sticky="nsew")
        self._draw_automata_graph(key)

    def _zoom_graph(self, factor: float) -> None:
        self.graph_zoom = min(2.5, max(0.5, self.graph_zoom * factor))
        self.graph_zoom_var.set(f"{round(self.graph_zoom * 100):.0f}%")
        if self.current_visual_key:
            self._draw_automata_graph(self.current_visual_key)

    def _reset_graph_zoom(self) -> None:
        self.graph_zoom = 1.0
        self.graph_zoom_var.set("100%")
        if self.current_visual_key:
            self._draw_automata_graph(self.current_visual_key)

    def _fit_graph_zoom(self) -> None:
        if self.current_visual_key in {"log_nfa_visual", "log_dfa_visual"}:
            item_count = len(self.log_graph_fragments)
            natural_width = 70 * 2 + 150 * item_count + 120
        elif self.current_visual_key == "cfg_visual" and self.control_flow_analysis is not None:
            item_count = len(self.control_flow_analysis.basic_blocks)
            columns = 2 if item_count > 3 else 1
            natural_width = 60 * 2 + columns * 190 + (columns - 1) * 84
        elif self.current_visual_key == "dag_visual" and self.control_flow_analysis is not None:
            dag = next((item for item in self.control_flow_analysis.dag_blocks if item.nodes), None)
            item_count = len(dag.nodes) if dag is not None else 0
            natural_width = 70 * 2 + max(1, item_count) * 120
        else:
            return

        if item_count <= 0:
            return
        available_width = max(self.graph_canvas.winfo_width(), 640)
        self.graph_zoom = min(2.5, max(0.5, available_width / natural_width))
        self.graph_zoom_var.set(f"{round(self.graph_zoom * 100):.0f}%")
        if self.current_visual_key:
            self._draw_automata_graph(self.current_visual_key)

    def _redraw_current_graph(self, event=None) -> None:
        if self.current_visual_key:
            self._draw_automata_graph(self.current_visual_key)

    def _draw_automata_graph(self, key: str) -> None:
        if key == "cfg_visual":
            self._draw_cfg_graph()
            return
        if key == "dag_visual":
            self._draw_dag_graph()
            return

        self.graph_canvas.delete("all")
        fragments = self._expanded_regex_fragments(self.log_graph_fragments)
        if not fragments:
            self.graph_canvas.configure(scrollregion=(0, 0, 640, 360))
            self.graph_canvas.create_text(
                24,
                24,
                anchor="nw",
                fill="#334155",
                font=("Microsoft YaHei UI", 11),
                text="Enter a regex and click 日志识别 first.",
            )
            return

        if key == "log_nfa_visual":
            self._draw_log_nfa_graph(fragments)
        else:
            self._draw_log_dfa_graph(fragments)

    def _draw_log_nfa_graph(self, fragments: list[str]) -> None:
        zoom = self.graph_zoom
        visible_width = max(self.graph_canvas.winfo_width(), 640)
        visible_height = max(self.graph_canvas.winfo_height(), 360)
        margin = int(70 * zoom)
        step = max(int(130 * zoom), int(165 * zoom))
        radius = max(14, int(24 * zoom))
        y = max(visible_height // 2, int(180 * zoom))
        graph_width = max(visible_width, margin * 2 + step * len(fragments) + int(120 * zoom))
        graph_height = max(visible_height, y + int(220 * zoom))
        self.graph_canvas.configure(scrollregion=(0, 0, graph_width, graph_height))

        self.graph_canvas.create_text(
            margin,
            int(28 * zoom),
            anchor="w",
            fill="#0f172a",
            font=("Microsoft YaHei UI", max(10, int(14 * zoom)), "bold"),
            text="NFA Visual - Thompson Style",
        )
        self.graph_canvas.create_text(
            margin,
            int(54 * zoom),
            anchor="w",
            fill="#64748b",
            font=("Consolas", max(8, int(10 * zoom))),
            text=f"Regex: {self.regex_var.get().strip()}",
        )

        positions = []
        for index in range(len(fragments) + 1):
            positions.append((margin + index * step, y))

        start_x, start_y = positions[0]
        start_gap = int(58 * zoom)
        self.graph_canvas.create_line(start_x - start_gap, start_y, start_x - radius, start_y, arrow=tk.LAST, fill="#334155", width=max(1, int(2 * zoom)))
        self.graph_canvas.create_text(start_x - start_gap - int(4 * zoom), start_y - int(18 * zoom), text="start", fill="#334155", font=("Consolas", max(8, int(9 * zoom))))

        for index, fragment in enumerate(fragments):
            x1, y1 = positions[index]
            x2, y2 = positions[index + 1]
            self.graph_canvas.create_line(x1 + radius, y1, x2 - radius, y2, arrow=tk.LAST, fill="#334155", width=max(1, int(2 * zoom)))
            self._draw_nfa_operator_hint(index, fragment, positions, radius, zoom)
            self._draw_edge_label((x1 + x2) / 2, y1 - int(58 * zoom), self._short_label(fragment), zoom)

        for index, (x, node_y) in enumerate(positions):
            state = f"q{index}"
            fill = "#dcfce7" if index == len(positions) - 1 else "#e0f2fe"
            outline = "#16a34a" if index == len(positions) - 1 else "#0284c7"
            self._draw_state(x, node_y, radius, state, fill, outline, index == len(positions) - 1, zoom)

    def _draw_log_dfa_graph(self, fragments: list[str]) -> None:
        zoom = self.graph_zoom
        visible_width = max(self.graph_canvas.winfo_width(), 640)
        visible_height = max(self.graph_canvas.winfo_height(), 360)
        margin = int(80 * zoom)
        col_step = int(190 * zoom)
        row_step = int(155 * zoom)
        radius = max(18, int(30 * zoom))
        columns = max(1, min(4, len(fragments) + 1))
        rows = (len(fragments) + columns) // columns
        graph_width = max(visible_width, margin * 2 + columns * col_step)
        graph_height = max(visible_height, int(150 * zoom) + rows * row_step + int(150 * zoom))
        self.graph_canvas.configure(scrollregion=(0, 0, graph_width, graph_height))

        self.graph_canvas.create_text(
            margin,
            int(28 * zoom),
            anchor="w",
            fill="#0f172a",
            font=("Microsoft YaHei UI", max(10, int(14 * zoom)), "bold"),
            text="DFA Visual - Subset Construction",
        )
        self.graph_canvas.create_text(
            margin,
            int(54 * zoom),
            anchor="w",
            fill="#64748b",
            font=("Consolas", max(8, int(10 * zoom))),
            text=f"Regex: {self.regex_var.get().strip()}",
        )

        positions = []
        for index in range(len(fragments) + 1):
            row = index // columns
            col = index % columns
            if row % 2 == 1:
                col = columns - 1 - col
            positions.append((margin + col * col_step, int(160 * zoom) + row * row_step))

        for index, (x, y) in enumerate(positions):
            fill = "#dcfce7" if index == len(positions) - 1 else "#fef3c7"
            outline = "#16a34a" if index == len(positions) - 1 else "#d97706"
            self._draw_state(x, y, radius, f"D{index}", fill, outline, index == len(positions) - 1, zoom)
            self._draw_state_caption(x, y + radius + int(24 * zoom), f"{{q{index}}}", zoom)

        start_x, start_y = positions[0]
        self.graph_canvas.create_line(start_x - int(62 * zoom), start_y, start_x - radius, start_y, arrow=tk.LAST, fill="#334155", width=max(1, int(2 * zoom)))
        self.graph_canvas.create_text(start_x - int(70 * zoom), start_y - int(20 * zoom), text="start", fill="#334155", font=("Consolas", max(8, int(9 * zoom))))

        for index, fragment in enumerate(fragments):
            x1, y1 = positions[index]
            x2, y2 = positions[index + 1]
            self._draw_directed_edge(x1, y1, x2, y2, radius, zoom)
            label_x, label_y = self._edge_label_position(x1, y1, x2, y2, int(38 * zoom))
            self._draw_edge_label(label_x, label_y, self._short_label(fragment), zoom)
            if any(mark in fragment for mark in ("*", "+")):
                self._draw_self_loop(x2, y2, radius, self._short_label(fragment), zoom)

    def _draw_state(self, x: int, y: int, radius: int, label: str, fill: str, outline: str, accepting: bool, zoom: float) -> None:
        width = max(1, int(2 * zoom))
        self.graph_canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline=outline, width=width)
        if accepting:
            inset = max(4, int(6 * zoom))
            self.graph_canvas.create_oval(x - radius + inset, y - radius + inset, x + radius - inset, y + radius - inset, outline=outline, width=width)
        self.graph_canvas.create_text(x, y, text=label, fill="#0f172a", font=("Consolas", max(8, int(10 * zoom)), "bold"), justify=tk.CENTER)

    def _draw_directed_edge(self, x1: int, y1: int, x2: int, y2: int, radius: int, zoom: float) -> None:
        dx = x2 - x1
        dy = y2 - y1
        distance = max((dx * dx + dy * dy) ** 0.5, 1)
        sx = x1 + radius * dx / distance
        sy = y1 + radius * dy / distance
        ex = x2 - radius * dx / distance
        ey = y2 - radius * dy / distance
        self.graph_canvas.create_line(sx, sy, ex, ey, arrow=tk.LAST, fill="#334155", width=max(1, int(2 * zoom)))

    def _draw_edge_label(self, x: float, y: float, label: str, zoom: float) -> None:
        half_width = max(34, int((len(label) * 4 + 18) * zoom))
        half_height = max(10, int(12 * zoom))
        self.graph_canvas.create_rectangle(x - half_width, y - half_height, x + half_width, y + half_height, fill="#f8fafc", outline="#cbd5e1")
        self.graph_canvas.create_text(x, y, text=label, fill="#7c2d12", font=("Consolas", max(8, int(9 * zoom))))

    def _draw_state_caption(self, x: float, y: float, label: str, zoom: float) -> None:
        half_width = max(30, int((len(label) * 4 + 16) * zoom))
        half_height = max(9, int(10 * zoom))
        self.graph_canvas.create_rectangle(x - half_width, y - half_height, x + half_width, y + half_height, fill="#fff7ed", outline="#fed7aa")
        self.graph_canvas.create_text(x, y, text=label, fill="#9a3412", font=("Consolas", max(8, int(8 * zoom))))

    def _edge_label_position(self, x1: int, y1: int, x2: int, y2: int, offset: int) -> tuple[float, float]:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        dx = x2 - x1
        dy = y2 - y1
        distance = max((dx * dx + dy * dy) ** 0.5, 1)
        normal_x = -dy / distance
        normal_y = dx / distance
        if normal_y > 0:
            normal_x = -normal_x
            normal_y = -normal_y
        return mid_x + normal_x * offset, mid_y + normal_y * offset

    def _draw_nfa_operator_hint(self, index: int, fragment: str, positions: list[tuple[int, int]], radius: int, zoom: float) -> None:
        x1, y1 = positions[index]
        x2, y2 = positions[index + 1]
        if "|" in fragment or "?:" in fragment:
            top = y1 - int(126 * zoom)
            self.graph_canvas.create_line(x1, y1 - radius, x1 + int(38 * zoom), top, x2 - int(38 * zoom), top, x2, y2 - radius, smooth=True, arrow=tk.LAST, fill="#64748b", dash=(4, 3), width=max(1, int(1.5 * zoom)))
            self._draw_edge_label((x1 + x2) / 2, top - int(24 * zoom), "ε branch", zoom)
        if "*" in fragment or "+" in fragment:
            self._draw_self_loop(x2, y2, radius, "ε / repeat", zoom)
        if "?" in fragment and "?:" not in fragment:
            bottom = y1 + int(92 * zoom)
            self.graph_canvas.create_line(x1, y1 + radius, x1 + int(38 * zoom), bottom, x2 - int(38 * zoom), bottom, x2, y2 + radius, smooth=True, arrow=tk.LAST, fill="#64748b", dash=(4, 3), width=max(1, int(1.5 * zoom)))
            self._draw_edge_label((x1 + x2) / 2, bottom + int(24 * zoom), "ε skip", zoom)

    def _draw_self_loop(self, x: int, y: int, radius: int, label: str, zoom: float) -> None:
        loop_r = int(28 * zoom)
        self.graph_canvas.create_arc(x - loop_r, y - radius - loop_r, x + loop_r, y - radius + loop_r, start=20, extent=300, style=tk.ARC, outline="#64748b", width=max(1, int(2 * zoom)))
        self.graph_canvas.create_line(x + int(18 * zoom), y - radius - int(7 * zoom), x + int(8 * zoom), y - radius + int(2 * zoom), arrow=tk.LAST, fill="#64748b", width=max(1, int(2 * zoom)))
        self.graph_canvas.create_text(x, y - radius - int(56 * zoom), text=label, fill="#475569", font=("Consolas", max(8, int(8 * zoom))))

    def _short_label(self, text: str) -> str:
        return text if len(text) <= 18 else text[:15] + "..."

    def _expanded_regex_fragments(self, fragments: list[str]) -> list[str]:
        expanded: list[str] = []
        for fragment in fragments:
            expanded.extend(self._expand_regex_fragment(fragment))
        return expanded or ["ε"]

    def _expand_regex_fragment(self, fragment: str) -> list[str]:
        count_match = re.fullmatch(r"(.+)\{(\d+)\}", fragment)
        range_match = re.fullmatch(r"(.+)\{(\d+),(\d+)\}", fragment)
        if count_match:
            atom = self._display_regex_atom(count_match.group(1))
            return [atom for _ in range(int(count_match.group(2)))]
        if range_match:
            atom = self._display_regex_atom(range_match.group(1))
            lower = int(range_match.group(2))
            upper = int(range_match.group(3))
            items = [atom for _ in range(lower)]
            for _index in range(max(0, upper - lower)):
                items.append(f"{atom}?")
            return items
        return [self._display_regex_atom(fragment)]

    def _display_regex_atom(self, atom: str) -> str:
        replacements = {
            r"\d": "digit",
            r"\w": "word",
            r"\s": "space",
            r"\.": ".",
            r"\-": "-",
            r"\:": ":",
            r"\b": "word-boundary",
        }
        if atom in replacements:
            return replacements[atom]
        if atom.startswith("[") and atom.endswith("]"):
            return atom
        if atom.startswith("(?:") and atom.endswith(")"):
            return atom[3:-1]
        if atom.startswith("(") and atom.endswith(")"):
            return atom[1:-1]
        return atom

    def _draw_cfg_graph(self) -> None:
        self.graph_canvas.delete("all")
        analysis = self.control_flow_analysis
        if analysis is None or not analysis.basic_blocks:
            self.graph_canvas.configure(scrollregion=(0, 0, 640, 360))
            self.graph_canvas.create_text(
                24,
                24,
                anchor="nw",
                fill="#334155",
                font=("Microsoft YaHei UI", 11),
                text="Click 运行 first to generate quadruples and build the CFG.",
            )
            return

        zoom = self.graph_zoom
        blocks = analysis.basic_blocks
        node_width = int(240 * zoom)
        x_gap = int(100 * zoom)
        y_gap = int(90 * zoom)
        margin = int(60 * zoom)
        columns = 2 if len(blocks) > 3 else 1
        heights = {block.name: max(int(92 * zoom), int((3 + len(block.quads)) * 18 * zoom)) for block in blocks}
        positions = {}
        row_heights: dict[int, int] = {}
        for index, block in enumerate(blocks):
            row = index // columns
            row_heights[row] = max(row_heights.get(row, 0), heights[block.name])
        row_tops: dict[int, int] = {}
        current_y = margin + int(56 * zoom)
        for row in range(max(row_heights, default=-1) + 1):
            row_tops[row] = current_y
            current_y += row_heights[row] + y_gap
        for index, block in enumerate(blocks):
            row = index // columns
            col = index % columns
            positions[block.name] = (margin + col * (node_width + x_gap), row_tops[row])

        visible_width = max(self.graph_canvas.winfo_width(), 640)
        visible_height = max(self.graph_canvas.winfo_height(), 360)
        graph_width = max(visible_width, margin * 2 + columns * node_width + (columns - 1) * x_gap)
        graph_height = max(visible_height, current_y + margin)
        self.graph_canvas.configure(scrollregion=(0, 0, graph_width, graph_height))
        self.graph_canvas.create_text(margin, int(28 * zoom), anchor="w", fill="#0f172a", font=("Microsoft YaHei UI", max(10, int(14 * zoom)), "bold"), text="Control Flow Graph")

        for source, targets in analysis.cfg.successors.items():
            x1, y1 = positions[source]
            for target in targets:
                x2, y2 = positions[target]
                source_height = heights[source]
                self.graph_canvas.create_line(
                    x1 + node_width / 2,
                    y1 + source_height,
                    x2 + node_width / 2,
                    y2,
                    arrow=tk.LAST,
                    fill="#475569",
                    width=max(1, int(2 * zoom)),
                    smooth=True,
                )

        for block in blocks:
            x, y = positions[block.name]
            node_height = heights[block.name]
            self.graph_canvas.create_rectangle(x, y, x + node_width, y + node_height, fill="#eff6ff", outline="#2563eb", width=max(1, int(2 * zoom)))
            self.graph_canvas.create_text(x + int(12 * zoom), y + int(12 * zoom), anchor="nw", fill="#0f172a", font=("Consolas", max(8, int(11 * zoom)), "bold"), text=f"{block.name} [{block.start}..{block.end}]")
            reason = "; ".join(block.leader_reasons) or "-"
            self.graph_canvas.create_text(x + int(12 * zoom), y + int(34 * zoom), anchor="nw", fill="#64748b", font=("Consolas", max(8, int(8 * zoom))), text=f"leader: {reason}", width=node_width - int(24 * zoom))
            quad_lines = [f"{block.start + offset}: {self._format_quad_short(quad)}" for offset, quad in enumerate(block.quads)]
            self.graph_canvas.create_text(x + int(12 * zoom), y + int(58 * zoom), anchor="nw", fill="#334155", font=("Consolas", max(8, int(8 * zoom))), text="\n".join(quad_lines), width=node_width - int(24 * zoom))

    def _draw_dag_graph(self) -> None:
        self.graph_canvas.delete("all")
        analysis = self.control_flow_analysis
        dag_blocks = [item for item in (analysis.dag_blocks if analysis is not None else []) if item.nodes]
        if not dag_blocks:
            self.graph_canvas.configure(scrollregion=(0, 0, 640, 360))
            self.graph_canvas.create_text(
                24,
                24,
                anchor="nw",
                fill="#334155",
                font=("Microsoft YaHei UI", 11),
                text="Click 运行 first. DAG visual needs a basic block with expressions.",
            )
            return

        zoom = self.graph_zoom
        node_radius = max(20, int(28 * zoom))
        x_gap = int(120 * zoom)
        y_gap = int(100 * zoom)
        margin = int(70 * zoom)
        visible_width = max(self.graph_canvas.winfo_width(), 640)
        visible_height = max(self.graph_canvas.winfo_height(), 360)
        all_positions = {}
        block_offsets = {}
        current_y = margin + int(60 * zoom)
        graph_width = visible_width
        for dag in dag_blocks:
            levels = self._dag_levels(dag.nodes)
            max_nodes = max((len(nodes) for nodes in levels.values()), default=1)
            block_height = (max(levels.keys(), default=0) + 1) * y_gap + int(90 * zoom)
            block_offsets[dag.block] = current_y
            for level, nodes in levels.items():
                for index, node_id in enumerate(nodes):
                    all_positions[(dag.block, node_id)] = (margin + index * x_gap, current_y + level * y_gap + int(50 * zoom))
            graph_width = max(graph_width, margin * 2 + max_nodes * x_gap)
            current_y += block_height + int(52 * zoom)
        graph_height = max(visible_height, current_y + margin)
        self.graph_canvas.configure(scrollregion=(0, 0, graph_width, graph_height))
        self.graph_canvas.create_text(margin, int(28 * zoom), anchor="w", fill="#0f172a", font=("Microsoft YaHei UI", max(10, int(14 * zoom)), "bold"), text="DAG Visual - all basic blocks")

        for dag in dag_blocks:
            top_y = block_offsets[dag.block]
            self.graph_canvas.create_text(margin, top_y - int(26 * zoom), anchor="w", fill="#0f172a", font=("Consolas", max(9, int(11 * zoom)), "bold"), text=f"{dag.block}")
            node_by_id = {node.id: node for node in dag.nodes}
            for node in dag.nodes:
                x1, y1 = all_positions[(dag.block, node.id)]
                for child_id in node.children:
                    key = (dag.block, child_id)
                    if key not in all_positions:
                        continue
                    x2, y2 = all_positions[key]
                    self.graph_canvas.create_line(x1, y1 + node_radius, x2, y2 - node_radius, arrow=tk.LAST, fill="#64748b", width=max(1, int(2 * zoom)))

            for node_id, node in node_by_id.items():
                x, y = all_positions[(dag.block, node_id)]
                common = len(node.names) > 1
                fill = "#fee2e2" if common and node.children else ("#fef3c7" if node.children else "#dcfce7")
                outline = "#dc2626" if common and node.children else ("#d97706" if node.children else "#16a34a")
                self.graph_canvas.create_rectangle(x - int(42 * zoom), y - node_radius, x + int(42 * zoom), y + node_radius, fill=fill, outline=outline, width=max(1, int(2 * zoom)))
                label = f"{node.label}\n{','.join(node.names[:4])}" if node.names else node.label
                self.graph_canvas.create_text(x, y, fill="#0f172a", font=("Consolas", max(8, int(9 * zoom)), "bold"), text=label, justify=tk.CENTER)

    def _dag_levels(self, nodes) -> dict[int, list[str]]:
        level_by_id = {}
        node_by_id = {node.id: node for node in nodes}

        def level(node_id: str) -> int:
            if node_id in level_by_id:
                return level_by_id[node_id]
            node = node_by_id[node_id]
            if not node.children:
                level_by_id[node_id] = 0
            else:
                level_by_id[node_id] = 1 + max(level(child_id) for child_id in node.children if child_id in node_by_id)
            return level_by_id[node_id]

        for node in nodes:
            level(node.id)

        grouped: dict[int, list[str]] = {}
        max_level = max(level_by_id.values(), default=0)
        for node_id, item_level in level_by_id.items():
            grouped.setdefault(max_level - item_level, []).append(node_id)
        return grouped

    def _format_quad_short(self, quad) -> str:
        op, arg1, arg2, result = quad
        return f"({op},{arg1},{arg2},{result})"

    def _source(self) -> str:
        return self.source_text.get("1.0", "end-1c")

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.configure(state=tk.DISABLED)

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def _configure_source_highlight_tags(self) -> None:
        self.source_text.tag_configure("error_line", background="#fee2e2")
        self.source_text.tag_configure("keyword", foreground="#2563eb", font=("Consolas", 11, "bold"))
        self.source_text.tag_configure("function", foreground="#7c3aed")
        self.source_text.tag_configure("number", foreground="#b45309")
        self.source_text.tag_configure("literal", foreground="#047857")
        self.source_text.tag_configure("comment", foreground="#6b7280")

    def _schedule_highlight(self) -> None:
        if self.highlight_job is not None:
            self.root.after_cancel(self.highlight_job)
        self.highlight_job = self.root.after(160, self._highlight_source)

    def _highlight_source(self) -> None:
        self.highlight_job = None
        source = self._source()
        for tag in ("keyword", "function", "number", "literal", "comment"):
            self.source_text.tag_remove(tag, "1.0", tk.END)

        self._highlight_pattern(r"//[^\n]*|/\*.*?\*/", "comment", source, flags=re.DOTALL)
        self._highlight_pattern(r"'(?:\\.|[^'\\])'|\"(?:\\.|[^\"\\])*\"", "literal", source)
        self._highlight_pattern(r"\b\d+(?:\.\d+)?\b", "number", source)
        self._highlight_pattern(r"\b(" + "|".join(re.escape(word) for word in KEYWORDS) + r")\b", "keyword", source)
        self._highlight_functions(source)
        self.source_text.tag_raise("comment")
        self.source_text.tag_raise("literal")

    def _highlight_pattern(self, pattern: str, tag: str, source: str, flags: int = 0) -> None:
        for match in re.finditer(pattern, source, flags):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.source_text.tag_add(tag, start, end)

    def _highlight_functions(self, source: str) -> None:
        for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()", source):
            name = match.group(1)
            if name in KEYWORDS:
                continue
            start = f"1.0+{match.start(1)}c"
            end = f"1.0+{match.end(1)}c"
            self.source_text.tag_add("function", start, end)

    def _schedule_diagnostics(self) -> None:
        if self.diagnostics_job is not None:
            self.root.after_cancel(self.diagnostics_job)
        self.diagnostics_job = self.root.after(500, self._refresh_diagnostics)

    def _refresh_diagnostics(self) -> None:
        self.diagnostics_job = None
        try:
            diagnostics = self._collect_editor_diagnostics()
        except Exception as exc:
            self._set_status(f"Diagnostics failed: {exc}")
            return
        self._apply_diagnostics(diagnostics)

    def _collect_editor_diagnostics(self):
        tokens, lexer_diagnostics = Lexer().tokenize(self._source())
        diagnostics = list(lexer_diagnostics)
        if not tokens:
            return diagnostics

        ast, parser_diagnostics = Parser(tokens).parse()
        diagnostics.extend(parser_diagnostics)
        if ast is not None:
            analyzer = SemanticAnalyzer().analyze_program(ast)
            diagnostics.extend(analyzer.diagnostics)
        return diagnostics

    def _apply_diagnostics(self, diagnostics) -> None:
        self.editor_diagnostics = list(diagnostics)
        self.error_lines = {diagnostic.line for diagnostic in self.editor_diagnostics if diagnostic.line and diagnostic.line > 0}
        self.source_text.tag_remove("error_line", "1.0", tk.END)
        for line in self.error_lines:
            self.source_text.tag_add("error_line", f"{line}.0", f"{line}.end+1c")
        self.source_text.tag_lower("error_line")
        self._fill_diagnostics_tree()
        self._draw_line_numbers()

    def _fill_diagnostics_tree(self) -> None:
        for item in self.diagnostics_tree.get_children():
            self.diagnostics_tree.delete(item)
        if not self.editor_diagnostics:
            self.diagnostics_tree.insert("", tk.END, values=("-", "ok", "-", "No diagnostics"))
            return
        for diagnostic in self.editor_diagnostics:
            self.diagnostics_tree.insert(
                "",
                tk.END,
                values=(diagnostic.line, diagnostic.phase, diagnostic.code, diagnostic.message),
            )

    def _on_diagnostic_selected(self, event=None) -> None:
        selected = self.diagnostics_tree.selection()
        if not selected:
            return
        values = self.diagnostics_tree.item(selected[0], "values")
        if not values or values[0] == "-":
            return
        line = int(values[0])
        self.source_text.mark_set("insert", f"{line}.0")
        self.source_text.see(f"{line}.0")
        self.source_text.focus_set()
        self._draw_line_numbers()

    def _draw_line_numbers(self) -> None:
        if not hasattr(self, "line_numbers"):
            return
        self.line_numbers.delete("all")
        index = self.source_text.index("@0,0")
        while True:
            dline = self.source_text.dlineinfo(index)
            if dline is None:
                break
            y = dline[1]
            line = int(str(index).split(".", 1)[0])
            fill = "#dc2626" if line in self.error_lines else "#64748b"
            weight = "bold" if line in self.error_lines else "normal"
            self.line_numbers.create_text(38, y, anchor="ne", text=str(line), fill=fill, font=("Consolas", 10, weight))
            index = self.source_text.index(f"{index}+1line")


def main() -> None:
    root = tk.Tk()
    app = CompilerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
