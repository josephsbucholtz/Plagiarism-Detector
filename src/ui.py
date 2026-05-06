from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

import document
import library_manager
import utils


APP_WIDTH = 1280
APP_HEIGHT = 840
APP_BG = "#f3efe7"
PANEL_BG = "#fffaf2"
CARD_BORDER = "#d9d1c3"
TEXT_PRIMARY = "#1f2a2e"
TEXT_MUTED = "#5f6b6d"
ACCENT = "#0f766e"
ACCENT_SOFT = "#d7f0ea"
GOLD = "#d97706"
GOLD_SOFT = "#fff2d9"
ROSE = "#a16207"
ROSE_SOFT = "#f5ead3"
SLATE = "#1d4ed8"
SLATE_SOFT = "#e6eef8"


class PlagiarismDetectorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Plagiarism Detector")
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.minsize(760, 640)
        self.root.configure(bg=APP_BG)

        self.status_var = tk.StringVar(value="Plagiarism Detector is ready to scan documents.")
        self.library_summary_var = tk.StringVar(value="Preparing the reference library snapshot...")
        self.compare_file_1_var = tk.StringVar()
        self.compare_file_2_var = tk.StringVar()
        self.query_file_var = tk.StringVar()
        self.library_folder_var = tk.StringVar(value=str(library_manager.DEFAULT_LIBRARY_DIR))
        self.generate_highlight_var = tk.BooleanVar(value=True)
        self.metric_similarity_var = tk.StringVar(value="0.00%")
        self.metric_jaccard_var = tk.StringVar(value="0.00%")
        self.metric_common_var = tk.StringVar(value="0")
        self.metric_duplicate_var = tk.StringVar(value="No match")
        self.highlight_status_var = tk.StringVar(value="No plagiarism evidence report has been generated yet.")
        self.highlight_path_var = tk.StringVar(value="No plagiarism evidence report is selected.")
        self.result_queue: queue.Queue = queue.Queue()
        self.current_library_results = []
        self.current_pair_result: dict | None = None
        self.current_selection_result: dict | None = None
        self.action_buttons: list[ttk.Button] = []
        self.busy = False
        self.wrap_labels: list[tuple[tk.Widget, int]] = []
        self.summary_cards: list[tk.Frame] = []
        self.button_rows: list[tuple[tk.Widget, list[ttk.Button], int, int]] = []
        self.selector_rows: list[tuple[tk.Widget, ttk.Label, ttk.Entry, ttk.Button, int]] = []

        self._configure_styles()
        self._build_layout()
        self.root.bind("<Configure>", self.on_root_resize)
        self.refresh_library_summary()
        self.refresh_highlight_list()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", font=("Segoe UI", 10), foreground=TEXT_PRIMARY)
        style.configure("App.TFrame", background=APP_BG)
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure("App.TNotebook", background=APP_BG, borderwidth=0)
        style.configure("App.TNotebook.Tab", padding=(16, 10), font=("Segoe UI Semibold", 10))
        style.map("App.TNotebook.Tab", background=[("selected", PANEL_BG)], foreground=[("selected", ACCENT)])
        style.configure("Panel.TLabelframe", background=PANEL_BG, bordercolor=CARD_BORDER, relief="solid")
        style.configure("Panel.TLabelframe.Label", background=PANEL_BG, foreground=TEXT_PRIMARY, font=("Segoe UI Semibold", 11))
        style.configure("Panel.TLabel", background=PANEL_BG, foreground=TEXT_PRIMARY)
        style.configure("Muted.TLabel", background=PANEL_BG, foreground=TEXT_MUTED)
        style.configure("Accent.TButton", background=ACCENT, foreground="white", borderwidth=0, padding=(14, 11), font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton", background=[("active", "#115e59"), ("disabled", "#8dbab6")], foreground=[("disabled", "#e6f3f1")])
        style.configure("Secondary.TButton", background="#f6efe2", foreground=TEXT_PRIMARY, borderwidth=0, padding=(12, 11))
        style.map("Secondary.TButton", background=[("active", "#efe2c9"), ("disabled", "#f5eee4")])
        style.configure("Treeview", background="white", fieldbackground="white", rowheight=28, bordercolor=CARD_BORDER)
        style.configure("Treeview.Heading", background="#f3ead8", foreground=TEXT_PRIMARY, font=("Segoe UI Semibold", 10))
        style.map("Treeview", background=[("selected", ACCENT_SOFT)], foreground=[("selected", TEXT_PRIMARY)])
        style.configure("TCheckbutton", background=PANEL_BG, foreground=TEXT_PRIMARY)
        style.configure("TEntry", fieldbackground="white", bordercolor=CARD_BORDER, padding=6)
        style.configure("Status.TLabel", background="#ece4d6", foreground=TEXT_PRIMARY, padding=8)

    def _build_layout(self) -> None:
        self.container = ttk.Frame(self.root, style="App.TFrame", padding=16)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(2, weight=1)

        self._build_hero(self.container)
        self._build_summary_cards(self.container)

        self.content_pane = ttk.Panedwindow(self.container, orient=tk.HORIZONTAL)
        self.content_pane.grid(row=2, column=0, sticky="nsew", pady=(8, 0))

        self.left_panel = ttk.Frame(self.content_pane, style="Panel.TFrame", padding=12)
        self.right_panel = ttk.Frame(self.content_pane, style="Panel.TFrame", padding=12)
        self.left_panel.columnconfigure(0, weight=1)
        self.left_panel.rowconfigure(1, weight=1)
        self.right_panel.columnconfigure(0, weight=1)
        self.right_panel.rowconfigure(0, weight=1)
        self.content_pane.add(self.left_panel, weight=4)
        self.content_pane.add(self.right_panel, weight=3)

        self._build_controls_panel(self.left_panel)
        self._build_results_panel(self.left_panel)
        self._build_highlight_panel(self.right_panel)

        status_bar = ttk.Label(self.container, textvariable=self.status_var, style="Status.TLabel", anchor="w")
        status_bar.grid(row=3, column=0, sticky="ew", pady=(12, 0))

    def _build_hero(self, parent: ttk.Frame) -> None:
        hero = tk.Frame(parent, bg=ACCENT, bd=0, highlightthickness=0)
        hero.grid(row=0, column=0, sticky="ew")
        hero.grid_columnconfigure(0, weight=1)

        hero_inner = tk.Frame(hero, bg=ACCENT, padx=20, pady=18)
        hero_inner.grid(row=0, column=0, sticky="ew")
        hero_inner.grid_columnconfigure(0, weight=1)

        tk.Label(
            hero_inner,
            text="Plagiarism Detector Studio",
            bg=ACCENT,
            fg="white",
            font=("Georgia", 22, "bold"),
        ).grid(row=0, column=0, sticky="w")
        subtitle = tk.Label(
            hero_inner,
            text="Investigate suspicious overlap, compare submissions against a reference library, and generate evidence-ready highlight reports.",
            bg=ACCENT,
            fg="#d5f1ec",
            font=("Segoe UI", 11),
            justify="left",
        )
        subtitle.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.wrap_labels.append((subtitle, 40))

    def _build_summary_cards(self, parent: ttk.Frame) -> None:
        self.cards_container = tk.Frame(parent, bg=APP_BG, pady=12)
        self.cards_container.grid(row=1, column=0, sticky="ew")
        self.cards_container.grid_columnconfigure(0, weight=1)
        self.cards_container.grid_columnconfigure(1, weight=1)
        self.cards_container.grid_columnconfigure(2, weight=1)
        self.cards_container.grid_columnconfigure(3, weight=1)

        self.summary_label, library_card = self._create_metric_card(self.cards_container, "Reference Library", "Loading...", ACCENT_SOFT, ACCENT)
        self.similarity_label, similarity_card = self._create_metric_card(self.cards_container, "Fingerprint Match", "0.00%", GOLD_SOFT, GOLD)
        self.jaccard_label, jaccard_card = self._create_metric_card(self.cards_container, "Text Overlap", "0.00%", ROSE_SOFT, ROSE)
        self.highlight_label, highlight_card = self._create_metric_card(self.cards_container, "Evidence Reports", "0 files", SLATE_SOFT, SLATE)
        self.summary_cards = [library_card, similarity_card, jaccard_card, highlight_card]
        self._relayout_summary_cards(parent.winfo_width())

    def _create_metric_card(self, parent: tk.Frame, title: str, value: str, bg_color: str, accent_color: str) -> tuple[tk.Label, tk.Frame]:
        card = tk.Frame(parent, bg=bg_color, highlightbackground=CARD_BORDER, highlightthickness=1, padx=16, pady=14)
        card.grid_columnconfigure(0, weight=1)
        tk.Label(card, text=title, bg=bg_color, fg=TEXT_MUTED, font=("Segoe UI Semibold", 10)).grid(row=0, column=0, sticky="w")
        value_label = tk.Label(card, text=value, bg=bg_color, fg=accent_color, font=("Segoe UI", 18, "bold"))
        value_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        return value_label, card

    def _build_controls_panel(self, parent: ttk.Frame) -> None:
        notebook = ttk.Notebook(parent, style="App.TNotebook")
        notebook.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        compare_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=16)
        library_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=16)
        maintenance_tab = ttk.Frame(notebook, style="Panel.TFrame", padding=16)
        for tab in (compare_tab, library_tab, maintenance_tab):
            tab.columnconfigure(0, weight=1)
        notebook.add(compare_tab, text="Pairwise Scan")
        notebook.add(library_tab, text="Reference Library Scan")
        notebook.add(maintenance_tab, text="Reference Library Cache")

        self._build_compare_tab(compare_tab)
        self._build_library_tab(library_tab)
        self._build_maintenance_tab(maintenance_tab)

    def _build_compare_tab(self, parent: ttk.Frame) -> None:
        self._build_file_selector(parent, "Document A", self.compare_file_1_var, row=0)
        self._build_file_selector(parent, "Document B", self.compare_file_2_var, row=1)

        options_frame = ttk.Frame(parent, style="Panel.TFrame")
        options_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Checkbutton(
            options_frame,
            text="Create a plagiarism evidence report immediately after the scan",
            variable=self.generate_highlight_var,
        ).grid(row=0, column=0, sticky="w")

        button_row = ttk.Frame(parent, style="Panel.TFrame")
        button_row.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        compare_button = ttk.Button(button_row, text="Run Pairwise Plagiarism Scan", style="Accent.TButton", command=self.compare_selected_files)
        self._register_button_row(button_row, [compare_button], wide_columns=1, breakpoint=420)

    def _build_library_tab(self, parent: ttk.Frame) -> None:
        self._build_file_selector(parent, "Query Document", self.query_file_var, row=0)
        self._build_folder_selector(parent, "Reference Folder", self.library_folder_var, row=1)

        button_row = ttk.Frame(parent, style="Panel.TFrame")
        button_row.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        compare_button = ttk.Button(button_row, text="Scan Against Reference Library", style="Accent.TButton", command=self.compare_against_library)
        add_button = ttk.Button(button_row, text="Add Document To Reference Library", style="Secondary.TButton", command=self.add_query_file_to_library)
        self._register_button_row(button_row, [compare_button, add_button], wide_columns=2, breakpoint=620)

    def _build_maintenance_tab(self, parent: ttk.Frame) -> None:
        cache_text = ttk.Label(
            parent,
            text="Refresh or rebuild cached fingerprints for the selected reference library after changing its source documents.",
            style="Muted.TLabel",
            justify="left",
        )
        cache_text.grid(row=0, column=0, sticky="ew")
        self.wrap_labels.append((cache_text, 20))

        self._build_folder_selector(parent, "Reference Folder", self.library_folder_var, row=1)

        button_row = ttk.Frame(parent, style="Panel.TFrame")
        button_row.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        refresh_button = ttk.Button(button_row, text="Refresh Reference Snapshot", style="Secondary.TButton", command=self.refresh_library_summary)
        rebuild_button = ttk.Button(button_row, text="Rebuild Fingerprint Cache", style="Accent.TButton", command=self.rebuild_cache)
        self._register_button_row(button_row, [refresh_button, rebuild_button], wide_columns=2, breakpoint=620)

    def _build_results_panel(self, parent: ttk.Frame) -> None:
        results_frame = ttk.LabelFrame(parent, text="Plagiarism Analysis", style="Panel.TLabelframe", padding=12)
        results_frame.grid(row=1, column=0, sticky="nsew")
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(3, weight=1)

        self.badge_container = ttk.Frame(results_frame, style="Panel.TFrame")
        self.badge_container.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.badge_container.grid_columnconfigure(0, weight=1)
        self.badge_container.grid_columnconfigure(1, weight=1)
        self.badge_container.grid_columnconfigure(2, weight=1)
        self.badge_container.grid_columnconfigure(3, weight=1)

        self.result_badges = [
            self._create_result_badge(self.badge_container, "Fingerprint Match", self.metric_similarity_var, ACCENT_SOFT, ACCENT),
            self._create_result_badge(self.badge_container, "Text Overlap", self.metric_jaccard_var, GOLD_SOFT, GOLD),
            self._create_result_badge(self.badge_container, "Shared Evidence", self.metric_common_var, ROSE_SOFT, ROSE),
            self._create_result_badge(self.badge_container, "Verdict", self.metric_duplicate_var, SLATE_SOFT, SLATE),
        ]
        self._relayout_badges(parent.winfo_width())

        tree_frame = ttk.Frame(results_frame, style="Panel.TFrame")
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("file", "minhash", "jaccard", "common", "duplicate")
        self.matches_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        self.matches_tree.heading("file", text="Reference Document")
        self.matches_tree.heading("minhash", text="Fingerprint %")
        self.matches_tree.heading("jaccard", text="Overlap %")
        self.matches_tree.heading("common", text="Shared Evidence")
        self.matches_tree.heading("duplicate", text="Exact Match")
        self.matches_tree.column("file", width=260, minwidth=180, anchor="w", stretch=True)
        self.matches_tree.column("minhash", width=110, minwidth=90, anchor="center", stretch=True)
        self.matches_tree.column("jaccard", width=110, minwidth=90, anchor="center", stretch=True)
        self.matches_tree.column("common", width=120, minwidth=100, anchor="center", stretch=True)
        self.matches_tree.column("duplicate", width=95, minwidth=90, anchor="center", stretch=True)
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.matches_tree.yview)
        self.matches_tree.configure(yscrollcommand=tree_scroll.set)
        self.matches_tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.matches_tree.bind("<<TreeviewSelect>>", self.show_selected_match_details)

        button_row = ttk.Frame(results_frame, style="Panel.TFrame")
        button_row.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        clear_button = ttk.Button(button_row, text="Clear Plagiarism Findings", style="Secondary.TButton", command=self.clear_results_state)
        self._register_button_row(button_row, [clear_button], wide_columns=1, breakpoint=420)

        self.result_text = scrolledtext.ScrolledText(
            results_frame,
            height=18,
            wrap="word",
            font=("Consolas", 10),
            bg="#fffdf8",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            padx=12,
            pady=12,
        )
        self.result_text.grid(row=3, column=0, sticky="nsew", pady=(10, 0))

    def _create_result_badge(self, parent: ttk.Frame, title: str, variable: tk.StringVar, bg_color: str, fg_color: str) -> tk.Frame:
        badge = tk.Frame(parent, bg=bg_color, highlightbackground=CARD_BORDER, highlightthickness=1, padx=12, pady=10)
        badge.grid_columnconfigure(0, weight=1)
        tk.Label(badge, text=title, bg=bg_color, fg=TEXT_MUTED, font=("Segoe UI Semibold", 9)).grid(row=0, column=0, sticky="w")
        tk.Label(badge, textvariable=variable, bg=bg_color, fg=fg_color, font=("Segoe UI", 14, "bold")).grid(row=1, column=0, sticky="w", pady=(4, 0))
        return badge

    def _build_highlight_panel(self, parent: ttk.Frame) -> None:
        highlight_frame = ttk.LabelFrame(parent, text="Plagiarism Evidence Reports", style="Panel.TLabelframe", padding=12)
        highlight_frame.grid(row=0, column=0, sticky="nsew")
        highlight_frame.columnconfigure(0, weight=1)
        highlight_frame.rowconfigure(3, weight=1)

        highlight_text = ttk.Label(
            highlight_frame,
            text="Generate, review, or remove Word evidence reports that highlight suspicious overlap between documents.",
            style="Muted.TLabel",
            justify="left",
        )
        highlight_text.grid(row=0, column=0, sticky="ew")
        self.wrap_labels.append((highlight_text, 20))

        action_row = ttk.Frame(highlight_frame, style="Panel.TFrame")
        action_row.grid(row=1, column=0, sticky="ew", pady=(12, 10))
        generate_button = ttk.Button(action_row, text="Generate Evidence Report", style="Accent.TButton", command=self.generate_highlight_document)
        refresh_button = ttk.Button(action_row, text="Refresh Report List", style="Secondary.TButton", command=self.refresh_highlight_list)
        self._register_button_row(action_row, [generate_button, refresh_button], wide_columns=2, breakpoint=520)

        status_label = ttk.Label(highlight_frame, textvariable=self.highlight_status_var, style="Panel.TLabel", justify="left")
        status_label.grid(row=2, column=0, sticky="ew")
        self.wrap_labels.append((status_label, 20))

        list_frame = ttk.Frame(highlight_frame, style="Panel.TFrame")
        list_frame.grid(row=3, column=0, sticky="nsew", pady=(10, 8))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.highlight_listbox = tk.Listbox(
            list_frame,
            activestyle="none",
            bg="white",
            fg=TEXT_PRIMARY,
            highlightbackground=CARD_BORDER,
            selectbackground=ACCENT_SOFT,
            selectforeground=TEXT_PRIMARY,
            relief="flat",
            font=("Segoe UI", 10),
        )
        highlight_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.highlight_listbox.yview)
        self.highlight_listbox.configure(yscrollcommand=highlight_scroll.set)
        self.highlight_listbox.grid(row=0, column=0, sticky="nsew")
        highlight_scroll.grid(row=0, column=1, sticky="ns")
        self.highlight_listbox.bind("<<ListboxSelect>>", self.on_highlight_selected)

        path_label = ttk.Label(highlight_frame, textvariable=self.highlight_path_var, style="Muted.TLabel", justify="left")
        path_label.grid(row=4, column=0, sticky="ew")
        self.wrap_labels.append((path_label, 20))

        bottom_row = ttk.Frame(highlight_frame, style="Panel.TFrame")
        bottom_row.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        open_file_button = ttk.Button(bottom_row, text="Open Evidence Report", style="Accent.TButton", command=self.open_selected_highlight)
        delete_file_button = ttk.Button(bottom_row, text="Delete Evidence Report", style="Secondary.TButton", command=self.delete_selected_highlight)
        open_folder_button = ttk.Button(bottom_row, text="Open Report Folder", style="Secondary.TButton", command=self.open_highlight_folder)
        self._register_button_row(bottom_row, [open_file_button, delete_file_button, open_folder_button], wide_columns=3, breakpoint=640)

    def _build_file_selector(self, parent: ttk.Frame, label: str, variable: tk.StringVar, row: int) -> None:
        selector = ttk.Frame(parent, style="Panel.TFrame")
        selector.grid(row=row, column=0, sticky="ew", pady=6)
        label_widget = ttk.Label(selector, text=label, width=16, style="Panel.TLabel")
        entry_widget = ttk.Entry(selector, textvariable=variable)
        browse_button = ttk.Button(selector, text="Browse File", style="Secondary.TButton", command=lambda: self.browse_file(variable))
        self.action_buttons.append(browse_button)
        self.selector_rows.append((selector, label_widget, entry_widget, browse_button, 760))
        self._relayout_selector_row(selector, label_widget, entry_widget, browse_button, 760, self.root.winfo_width())

    def _build_folder_selector(self, parent: ttk.Frame, label: str, variable: tk.StringVar, row: int) -> None:
        selector = ttk.Frame(parent, style="Panel.TFrame")
        selector.grid(row=row, column=0, sticky="ew", pady=6)
        label_widget = ttk.Label(selector, text=label, width=16, style="Panel.TLabel")
        entry_widget = ttk.Entry(selector, textvariable=variable)
        browse_button = ttk.Button(selector, text="Browse Folder", style="Secondary.TButton", command=lambda: self.browse_folder(variable))
        self.action_buttons.append(browse_button)
        self.selector_rows.append((selector, label_widget, entry_widget, browse_button, 760))
        self._relayout_selector_row(selector, label_widget, entry_widget, browse_button, 760, self.root.winfo_width())

    def _register_button_row(self, frame: ttk.Frame, buttons: list[ttk.Button], wide_columns: int, breakpoint: int) -> None:
        self.button_rows.append((frame, buttons, wide_columns, breakpoint))
        for button in buttons:
            self.action_buttons.append(button)
        self._relayout_button_row(frame, buttons, wide_columns, breakpoint, self.root.winfo_width())

    def _relayout_selector_row(
        self,
        frame: ttk.Frame,
        label_widget: ttk.Label,
        entry_widget: ttk.Entry,
        browse_button: ttk.Button,
        breakpoint: int,
        width: int,
    ) -> None:
        label_widget.grid_forget()
        entry_widget.grid_forget()
        browse_button.grid_forget()

        for index in range(3):
            frame.columnconfigure(index, weight=0)

        if width >= breakpoint:
            frame.columnconfigure(1, weight=1)
            label_widget.grid(row=0, column=0, sticky="w", padx=(0, 8))
            entry_widget.grid(row=0, column=1, sticky="ew", padx=(0, 8))
            browse_button.grid(row=0, column=2, sticky="ew")
            return

        frame.columnconfigure(0, weight=1)
        label_widget.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        entry_widget.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        browse_button.grid(row=1, column=1, sticky="ew")

    def _relayout_button_row(self, frame: ttk.Frame, buttons: list[ttk.Button], wide_columns: int, breakpoint: int, width: int) -> None:
        for child in buttons:
            child.grid_forget()

        columns = wide_columns if width >= breakpoint else 1
        for index in range(max(wide_columns, len(buttons))):
            frame.columnconfigure(index, weight=0)
        for index in range(columns):
            frame.columnconfigure(index, weight=1)

        for index, button in enumerate(buttons):
            row = index // columns
            column = index % columns
            padx = (0, 8) if column < columns - 1 else 0
            pady = (0, 8) if columns == 1 and index < len(buttons) - 1 else 0
            button.grid(row=row, column=column, sticky="ew", padx=padx, pady=pady)

    def _relayout_summary_cards(self, width: int) -> None:
        columns = 4 if width >= 1150 else 2
        for index in range(4):
            self.cards_container.grid_columnconfigure(index, weight=0)
        for index in range(columns):
            self.cards_container.grid_columnconfigure(index, weight=1)

        for index, card in enumerate(self.summary_cards):
            card.grid_forget()
            row = index // columns
            column = index % columns
            card.grid(row=row, column=column, sticky="ew", padx=(0, 10 if column < columns - 1 else 0), pady=(0, 10 if row == 0 and columns == 2 else 0))

    def _relayout_badges(self, width: int) -> None:
        columns = 4 if width >= 1050 else 2
        for index in range(4):
            self.badge_container.grid_columnconfigure(index, weight=0)
        for index in range(columns):
            self.badge_container.grid_columnconfigure(index, weight=1)

        for index, badge in enumerate(self.result_badges):
            badge.grid_forget()
            row = index // columns
            column = index % columns
            badge.grid(row=row, column=column, sticky="ew", padx=(0, 8 if column < columns - 1 else 0), pady=(0, 8 if row == 0 and columns == 2 else 0))

    def _update_wrap_lengths(self) -> None:
        for label, padding in self.wrap_labels:
            width = max(label.winfo_width() - padding, 120)
            try:
                label.configure(wraplength=width)
            except tk.TclError:
                continue

    def on_root_resize(self, _event=None) -> None:
        width = self.root.winfo_width()
        self.content_pane.configure(orient=tk.HORIZONTAL if width >= 1180 else tk.VERTICAL)
        self._relayout_summary_cards(width)
        self._relayout_badges(width)
        for frame, buttons, wide_columns, breakpoint in self.button_rows:
            self._relayout_button_row(frame, buttons, wide_columns, breakpoint, width)
        for frame, label_widget, entry_widget, browse_button, breakpoint in self.selector_rows:
            self._relayout_selector_row(frame, label_widget, entry_widget, browse_button, breakpoint, width)
        self._update_wrap_lengths()

    def browse_file(self, variable: tk.StringVar) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Document For Plagiarism Analysis",
            initialdir=os.path.abspath("src"),
            filetypes=[("Text Files", "*.txt")],
        )
        if file_path:
            variable.set(file_path)

    def browse_folder(self, variable: tk.StringVar) -> None:
        initial_dir = variable.get().strip() or os.path.abspath("src")
        folder_path = filedialog.askdirectory(
            title="Select Reference Library Folder",
            initialdir=initial_dir,
            mustexist=False,
        )
        if folder_path:
            variable.set(folder_path)
            self.refresh_library_summary()

    def get_selected_library_dir(self) -> str:
        selected_folder = self.library_folder_var.get().strip()
        if not selected_folder:
            selected_folder = str(library_manager.DEFAULT_LIBRARY_DIR)
            self.library_folder_var.set(selected_folder)
        return selected_folder

    def set_busy(self, is_busy: bool, message: str | None = None) -> None:
        self.busy = is_busy
        button_state = "disabled" if is_busy else "normal"
        for button in self.action_buttons:
            button.configure(state=button_state)
        self.status_var.set(message or ("Plagiarism Detector is scanning evidence..." if is_busy else "Plagiarism Detector is ready to scan documents."))

    def run_background(self, task, on_success, start_message: str) -> None:
        if self.busy:
            return

        self.set_busy(True, start_message)

        def worker():
            try:
                result = task()
                self.result_queue.put(("success", result, on_success))
            except Exception as error:  # pragma: no cover
                self.result_queue.put(("error", error, None))

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(100, self._poll_queue)

    def _poll_queue(self) -> None:
        try:
            status, payload, callback = self.result_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_queue)
            return

        self.set_busy(False)
        if status == "error":
            messagebox.showerror("Plagiarism Detection Error", str(payload))
            self.status_var.set("Plagiarism Detector could not complete the requested analysis.")
            return

        callback(payload)

    def compare_selected_files(self) -> None:
        file_1 = self.compare_file_1_var.get().strip()
        file_2 = self.compare_file_2_var.get().strip()
        if not file_1 or not file_2:
            messagebox.showwarning("Missing Documents", "Choose both documents before running a pairwise plagiarism scan.")
            return

        self.run_background(
            lambda: utils.run_comparison(file_1, file_2, generate_highlight=self.generate_highlight_var.get()),
            self.on_pair_comparison_ready,
            "Plagiarism Detector is comparing the selected documents...",
        )

    def on_pair_comparison_ready(self, result: dict) -> None:
        if "error" in result:
            messagebox.showerror("Pairwise Scan Error", result["error"])
            self.status_var.set("The pairwise plagiarism scan could not be completed.")
            return

        self.clear_tree()
        self.current_library_results = []
        self.current_pair_result = result
        self.current_selection_result = result
        self.update_metric_cards(result)
        self.render_pair_result(result, heading="Pairwise plagiarism scan")

        if result.get("highlight_path"):
            self.highlight_status_var.set("A plagiarism evidence report was generated from the latest pairwise scan.")
            self.refresh_highlight_list(select_path=result["highlight_path"])

        self.status_var.set("The pairwise plagiarism scan is complete.")

    def compare_against_library(self) -> None:
        query_file = self.query_file_var.get().strip()
        if not query_file:
            messagebox.showwarning("Missing Document", "Choose a query document before scanning the reference library.")
            return

        self.run_background(
            lambda: utils.compare_with_library(query_file, self.get_selected_library_dir(), top_n=10),
            self.on_library_comparison_ready,
            "Plagiarism Detector is scanning the query document against the selected reference library...",
        )

    def on_library_comparison_ready(self, report: dict) -> None:
        if "error" in report:
            messagebox.showerror("Reference Library Scan Error", report["error"])
            self.status_var.set("The reference library plagiarism scan could not be completed.")
            return

        self.current_pair_result = None
        self.current_library_results = report["results"]
        self.current_selection_result = report["results"][0] if report["results"] else None
        self.populate_tree(report["results"])
        self.render_library_report(report)

        if self.current_selection_result is not None:
            self.update_metric_cards(self.current_selection_result)

        if report["duplicate_found"]:
            duplicate = report["duplicate_match"]
            messagebox.showinfo(
                "Exact Match Found",
                f"Plagiarism Detector found an exact reference match:\n{duplicate['file_name']}",
            )
            self.status_var.set("Plagiarism Detector found an exact match in the selected reference library.")
        else:
            self.status_var.set("The reference library plagiarism scan is complete.")

    def add_query_file_to_library(self) -> None:
        query_file = self.query_file_var.get().strip()
        if not query_file:
            messagebox.showwarning("Missing Document", "Choose a document before adding it to the reference library.")
            return

        self.run_background(
            lambda: utils.add_file_to_library(query_file, self.get_selected_library_dir()),
            self.on_add_to_library_ready,
            "Plagiarism Detector is checking the document before adding it to the reference library...",
        )

    def on_add_to_library_ready(self, result: dict) -> None:
        if "error" in result:
            messagebox.showerror("Reference Library Error", result["error"])
            self.status_var.set("The document could not be processed for the selected reference library.")
            return

        if result["duplicate_found"]:
            messagebox.showinfo(
                "Document Already Indexed",
                f"This document already exists in the reference library as:\n{result['existing_file']}\n{result['existing_path']}",
            )
            self.status_var.set("That document is already present in the selected reference library.")
        else:
            messagebox.showinfo(
                "Document Indexed",
                f"Plagiarism Detector added this document to the reference library:\n{result['stored_file']}\n{result['stored_path']}",
            )
            self.status_var.set("The document was added to the selected reference library.")

        self.refresh_library_summary()

    def refresh_library_summary(self) -> None:
        self.run_background(
            lambda: utils.get_library_summary(self.get_selected_library_dir()),
            self.on_library_summary_ready,
            "Plagiarism Detector is refreshing the selected reference library snapshot...",
        )

    def on_library_summary_ready(self, summary: dict) -> None:
        cache_status = "ready for plagiarism scans" if summary["cache_ready"] else "needs fingerprint cache rebuild"
        first_files = ", ".join(item["file_name"] for item in summary["documents"][:5])
        if len(summary["documents"]) > 5:
            first_files += ", ..."
        if not first_files:
            first_files = "No documents are currently indexed in this reference library."

        self.library_summary_var.set(
            f"Reference folder: {summary['library_dir']}\n"
            f"Indexed documents: {summary['document_count']}\n"
            f"Fingerprint cache: {cache_status}\n"
            f"Sample evidence sources: {first_files}"
        )
        self.summary_label.configure(text=f"{summary['document_count']} indexed docs")
        self.status_var.set("The reference library snapshot has been updated.")
        self._update_wrap_lengths()

    def rebuild_cache(self) -> None:
        self.run_background(
            lambda: utils.rebuild_library_cache(self.get_selected_library_dir(), force=True),
            self.on_cache_rebuilt,
            "Plagiarism Detector is rebuilding the fingerprint cache for the selected reference library...",
        )

    def on_cache_rebuilt(self, index: dict) -> None:
        messagebox.showinfo("Fingerprint Cache Rebuilt", f"Indexed {len(index['documents'])} reference documents for faster plagiarism scans.")
        self.refresh_library_summary()
        self.status_var.set("The reference library fingerprint cache has been rebuilt.")

    def clear_tree(self) -> None:
        for item_id in self.matches_tree.get_children():
            self.matches_tree.delete(item_id)

    def clear_results_state(self) -> None:
        self.clear_tree()
        self.current_library_results = []
        self.current_pair_result = None
        self.current_selection_result = None
        self.result_text.delete("1.0", tk.END)
        self.update_metric_cards(None)
        self.status_var.set("The current plagiarism findings have been cleared.")

    def populate_tree(self, results: list[dict]) -> None:
        self.clear_tree()
        for index, result in enumerate(results):
            self.matches_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    Path(result["file2"]).name,
                    f"{result['minhash_similarity'] * 100:.2f}",
                    f"{result['real_similarity'] * 100:.2f}",
                    result["common_shingles"],
                    "Yes" if result["identical_shingles"] else "No",
                ),
            )

    def update_metric_cards(self, result: dict | None) -> None:
        if result is None:
            self.metric_similarity_var.set("0.00%")
            self.metric_jaccard_var.set("0.00%")
            self.metric_common_var.set("0")
            self.metric_duplicate_var.set("No match")
            self.similarity_label.configure(text="0.00%")
            self.jaccard_label.configure(text="0.00%")
            return

        similarity_percent = f"{result['minhash_similarity'] * 100:.2f}%"
        jaccard_percent = f"{result['real_similarity'] * 100:.2f}%"
        duplicate_status = "Exact match" if result["identical_shingles"] else "Distinct source"
        self.metric_similarity_var.set(similarity_percent)
        self.metric_jaccard_var.set(jaccard_percent)
        self.metric_common_var.set(str(result["common_shingles"]))
        self.metric_duplicate_var.set(duplicate_status)
        self.similarity_label.configure(text=similarity_percent)
        self.jaccard_label.configure(text=jaccard_percent)

    def render_pair_result(self, result: dict, heading: str) -> None:
        lines = [
            heading,
            "=" * len(heading),
            f"Document A: {result['file1']}",
            f"Document B: {result['file2']}",
            "",
            f"Fingerprint match: {result['minhash_similarity']:.4f} ({result['minhash_similarity'] * 100:.2f}%)",
            f"Text overlap: {result['real_similarity']:.4f} ({result['real_similarity'] * 100:.2f}%)",
            f"Shared evidence units: {result['common_shingles']}",
            f"Evidence units in document A: {result['num_shingles_doc1']}",
            f"Evidence units in document B: {result['num_shingles_doc2']}",
            f"Combined evidence vocabulary: {result['vocab_size']}",
            f"Exact plagiarism fingerprint match: {'Yes' if result['identical_shingles'] else 'No'}",
        ]

        if result.get("highlight_path"):
            lines.append(f"Evidence report: {result['highlight_path']}")

        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "\n".join(lines))

    def render_library_report(self, report: dict) -> None:
        lines = [
            "Reference library plagiarism scan",
            "==================================",
            f"Query document: {report['query_file']}",
            f"Reference folder: {report['library_dir']}",
            f"Indexed reference documents: {report['library_size']}",
            f"Exact reference match: {'Yes' if report['duplicate_found'] else 'No'}",
            "",
            "Top evidence matches:",
        ]

        for index, result in enumerate(report["results"], start=1):
            lines.append(
                f"{index}. {Path(result['file2']).name} | "
                f"Fingerprint {result['minhash_similarity'] * 100:.2f}% | "
                f"Overlap {result['real_similarity'] * 100:.2f}% | "
                f"Shared evidence {result['common_shingles']}"
            )

        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "\n".join(lines))

    def show_selected_match_details(self, _event=None) -> None:
        selection = self.matches_tree.selection()
        if not selection:
            return

        selected_index = int(selection[0])
        if selected_index >= len(self.current_library_results):
            return

        result = self.current_library_results[selected_index]
        self.current_selection_result = result
        self.update_metric_cards(result)
        self.render_pair_result(result, heading="Selected reference match")
        self.status_var.set(f"Selected plagiarism evidence source: {Path(result['file2']).name}")

    def generate_highlight_document(self) -> None:
        source_result = self.current_pair_result or self.current_selection_result
        if source_result is None:
            messagebox.showwarning("No Scan Result", "Run a plagiarism scan first or select a reference match before generating an evidence report.")
            return

        self._generate_highlight_for_result(source_result, include_second_document=True)

    def _generate_highlight_for_result(self, result: dict, include_second_document: bool) -> None:
        self.run_background(
            lambda: document.create_highlight_documents(
                result["file1"],
                result["file2"],
                result["minhash_similarity"] * 100,
                include_second_document=include_second_document,
            ),
            self.on_highlight_generated,
            "Plagiarism Detector is generating a Word evidence report...",
        )

    def on_highlight_generated(self, output_paths: list[str]) -> None:
        if not output_paths:
            messagebox.showinfo("No Plagiarism Evidence", "No shared evidence units were found to highlight.")
            self.highlight_status_var.set("No plagiarism evidence report was created because the scan found no shared text patterns.")
            return

        self.highlight_status_var.set(f"Generated {len(output_paths)} plagiarism evidence report(s).")
        self.refresh_highlight_list(select_path=output_paths[0])
        self.status_var.set("The plagiarism evidence report is ready.")

    def refresh_highlight_list(self, select_path: str | None = None) -> None:
        library_manager.ensure_runtime_directories()
        highlight_files = sorted(library_manager.HIGHLIGHT_DIR.glob("*.docx"), key=lambda path: path.stat().st_mtime, reverse=True)

        self.highlight_listbox.delete(0, tk.END)
        for item in highlight_files:
            self.highlight_listbox.insert(tk.END, item.name)

        self.highlight_label.configure(text=f"{len(highlight_files)} reports")

        if not highlight_files:
            self.highlight_path_var.set("No plagiarism evidence reports were found yet.")
            return

        selected_index = 0
        if select_path is not None:
            target_name = Path(select_path).name
            for index, item in enumerate(highlight_files):
                if item.name == target_name:
                    selected_index = index
                    break

        self.highlight_listbox.selection_clear(0, tk.END)
        self.highlight_listbox.selection_set(selected_index)
        self.highlight_listbox.activate(selected_index)
        self.highlight_path_var.set(str(highlight_files[selected_index].resolve()))
        self._update_wrap_lengths()

    def on_highlight_selected(self, _event=None) -> None:
        selection = self.highlight_listbox.curselection()
        if not selection:
            return
        file_name = self.highlight_listbox.get(selection[0])
        self.highlight_path_var.set(str((library_manager.HIGHLIGHT_DIR / file_name).resolve()))
        self._update_wrap_lengths()

    def open_selected_highlight(self) -> None:
        selection = self.highlight_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Evidence Report Selected", "Choose a plagiarism evidence report first.")
            return

        file_name = self.highlight_listbox.get(selection[0])
        self._open_path(library_manager.HIGHLIGHT_DIR / file_name)

    def delete_selected_highlight(self) -> None:
        selection = self.highlight_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Evidence Report Selected", "Choose a plagiarism evidence report to delete first.")
            return

        file_name = self.highlight_listbox.get(selection[0])
        target_path = library_manager.HIGHLIGHT_DIR / file_name
        confirmed = messagebox.askyesno(
            "Delete Evidence Report",
            f"Delete this plagiarism evidence report?\n\n{target_path}",
        )
        if not confirmed:
            return

        try:
            target_path.unlink(missing_ok=False)
        except FileNotFoundError:
            messagebox.showerror("Missing Evidence Report", f"Cannot find:\n{target_path}")
            return
        except OSError as error:
            messagebox.showerror("Delete Failed", str(error))
            return

        self.highlight_status_var.set(f"Deleted plagiarism evidence report: {file_name}")
        self.status_var.set(f"Deleted plagiarism evidence report: {file_name}")
        self.refresh_highlight_list()

    def open_highlight_folder(self) -> None:
        self._open_path(library_manager.HIGHLIGHT_DIR)

    def _open_path(self, path: Path) -> None:
        resolved_path = path.resolve()
        if not resolved_path.exists():
            messagebox.showerror("Missing File", f"Cannot find:\n{resolved_path}")
            return

        try:
            os.startfile(str(resolved_path))  # type: ignore[attr-defined]
            self.status_var.set(f"Opened plagiarism evidence report: {resolved_path.name}")
        except AttributeError:
            messagebox.showinfo("Open Path", str(resolved_path))
        except OSError as error:
            messagebox.showerror("Open Failed", str(error))


def main() -> None:
    root = tk.Tk()
    PlagiarismDetectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
