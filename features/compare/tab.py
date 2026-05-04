"""
Compare Tab – MAT file comparison UI for the Python Runner app.

Allows user to select a root folder, load base/new MAT files,
view a log, and compare the 'extended_data' field side-by-side.
"""
from __future__ import annotations
import csv
import os
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import Qt, Slot, QEvent, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFileDialog, QMessageBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QDialogButtonBox,
)

from .mat_loader import load_folder
from .diff_engine import (
    ComparisonReport, FieldDiff, MatchStatus, Tolerance, compare_extended_data,
)


_GREEN = QColor(200, 255, 200)
_RED = QColor(255, 200, 200)
_YELLOW = QColor(255, 255, 200)
_COLUMNS = ["Field", "Base Value", "New Value", "Match?", "Numeric Diff"]


class CompareTab(QWidget):
    """Main Compare tab widget – drop-in for QTabWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_is_dark = False

        self._root_folder: Optional[Path] = None
        self._base_data: dict[str, dict[str, Any]] = {}
        self._new_data: dict[str, dict[str, Any]] = {}
        self._reports: list[ComparisonReport] = []

        self._init_ui()

    # ─── UI Setup ───────────────────────────────────────────────────────

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # ── Folder selection ──
        folder_box = QGroupBox("Root Folder (contains newVerOutputDir / oldVerOutputDir)")
        folder_layout = QHBoxLayout(folder_box)
        self.lbl_folder = QLabel("No folder selected")
        self.btn_browse = QPushButton("Browse…")
        self.btn_browse.clicked.connect(self._on_browse)
        folder_layout.addWidget(self.lbl_folder, 1)
        folder_layout.addWidget(self.btn_browse)
        main_layout.addWidget(folder_box)

        # Enable drag-and-drop on the folder box
        folder_box.setAcceptDrops(True)
        folder_box.dragEnterEvent = self._folder_drag_enter
        folder_box.dropEvent = self._folder_drop

        # ── Action buttons ──
        btn_layout = QHBoxLayout()

        self.btn_load_base = QPushButton("Load Base Version")
        self.btn_load_base.setEnabled(False)
        self.btn_load_base.clicked.connect(self._on_load_base)
        btn_layout.addWidget(self.btn_load_base)

        self.btn_load_new = QPushButton("Load New Version")
        self.btn_load_new.setEnabled(False)
        self.btn_load_new.clicked.connect(self._on_load_new)
        btn_layout.addWidget(self.btn_load_new)

        self.btn_open_log = QPushButton("Open Log")
        self.btn_open_log.setEnabled(False)
        self.btn_open_log.clicked.connect(self._on_open_log)
        btn_layout.addWidget(self.btn_open_log)

        self.btn_compare = QPushButton("Compare Values")
        self.btn_compare.setEnabled(False)
        self.btn_compare.clicked.connect(self._on_compare)
        btn_layout.addWidget(self.btn_compare)

        main_layout.addLayout(btn_layout)

        # ── Status label ──
        self.lbl_status = QLabel("Drop a folder or click Browse to begin.")
        main_layout.addWidget(self.lbl_status)

        # ── Comparison table ──
        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.table, 1)

        # ── Export button ──
        self.btn_export = QPushButton("Export CSV")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._on_export)
        main_layout.addWidget(self.btn_export)

    # ─── Theme support (matches EXE Runner API) ─────────────────────────

    def set_theme_dark(self, is_dark: bool):
        self.theme_is_dark = is_dark

    # ─── Drag & Drop on folder box ──────────────────────────────────────

    def _folder_drag_enter(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _folder_drop(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile())
            if path.is_dir():
                self._set_folder(path)

    # ─── Slots ──────────────────────────────────────────────────────────

    @Slot()
    def _on_browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select root folder")
        if folder:
            self._set_folder(Path(folder))

    @Slot()
    def _on_load_base(self):
        subfolder = self._root_folder / "newVerOutputDir"
        if not subfolder.is_dir():
            QMessageBox.warning(self, "Not Found", f"Subfolder not found:\n{subfolder}")
            return
        try:
            self._base_data = load_folder(subfolder)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.lbl_status.setText(f"Base loaded: {len(self._base_data)} file(s) from newVerOutputDir")
        self._maybe_enable_compare()

    @Slot()
    def _on_load_new(self):
        subfolder = self._root_folder / "oldVerOutputDir"
        if not subfolder.is_dir():
            QMessageBox.warning(self, "Not Found", f"Subfolder not found:\n{subfolder}")
            return
        try:
            self._new_data = load_folder(subfolder)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        self.lbl_status.setText(f"New loaded: {len(self._new_data)} file(s) from oldVerOutputDir")
        self._maybe_enable_compare()

    @Slot()
    def _on_open_log(self):
        log_path = self._root_folder / "origLogInputPath"
        if not log_path.is_file():
            QMessageBox.warning(self, "Not Found", f"Log file not found:\n{log_path}")
            return
        text = log_path.read_text(encoding="utf-8", errors="replace")

        dlg = QDialog(self)
        dlg.setWindowTitle("Log — origLogInputPath")
        dlg.setMinimumSize(600, 400)
        layout = QVBoxLayout(dlg)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setPlainText(text)
        layout.addWidget(te)
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(dlg.close)
        layout.addWidget(btn_box)
        dlg.show()

    @Slot()
    def _on_compare(self):
        tolerance = Tolerance()
        all_files = sorted(set(self._base_data.keys()) | set(self._new_data.keys()))
        if not all_files:
            QMessageBox.information(self, "Nothing", "No files loaded.")
            return

        reports: list[ComparisonReport] = []
        for filename in all_files:
            base_dict = self._base_data.get(filename, {})
            new_dict = self._new_data.get(filename, {})
            report = compare_extended_data(base_dict, new_dict, tolerance, source_file=filename)
            reports.append(report)

        self._reports = reports
        self._populate_table(reports)

        total_mismatches = sum(1 for r in reports if r.has_mismatches)
        self.lbl_status.setText(
            f"Comparison done: {len(reports)} file(s), {total_mismatches} with mismatches."
        )

    @Slot()
    def _on_export(self):
        path_str, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV files (*.csv)")
        if not path_str:
            return
        with open(path_str, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Source File", *_COLUMNS])
            for report in self._reports:
                for diff in report.diffs:
                    writer.writerow([
                        report.source_file,
                        diff.field_path,
                        diff.base_value,
                        diff.new_value,
                        diff.status.name,
                        diff.numeric_diff,
                    ])
        self.lbl_status.setText(f"Exported to {path_str}")

    # ─── Helpers ────────────────────────────────────────────────────────

    def _set_folder(self, folder: Path):
        self._root_folder = folder
        self._base_data = {}
        self._new_data = {}
        self._reports = []
        self.table.setRowCount(0)
        self.btn_export.setEnabled(False)

        mat_count = sum(1 for _ in folder.rglob("*.mat"))
        self.lbl_folder.setText(f"{folder.name}  —  {mat_count} .mat file(s)")
        self.lbl_status.setText(f"Folder set: {folder}")

        self.btn_load_base.setEnabled(True)
        self.btn_load_new.setEnabled(True)
        self.btn_open_log.setEnabled(True)
        self.btn_compare.setEnabled(False)

    def _maybe_enable_compare(self):
        if self._base_data and self._new_data:
            self.btn_compare.setEnabled(True)

    def _populate_table(self, reports: list[ComparisonReport]):
        all_diffs: list[tuple[str, FieldDiff]] = []
        for report in reports:
            for diff in report.diffs:
                all_diffs.append((report.source_file, diff))

        self.table.setRowCount(len(all_diffs))
        for row, (source, diff) in enumerate(all_diffs):
            label = f"[{source}] {diff.field_path}" if source else diff.field_path
            items = [label, diff.base_value, diff.new_value, diff.status.name, diff.numeric_diff]
            bg = self._bg_for_status(diff.status)
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setBackground(bg)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)

        self.btn_export.setEnabled(len(all_diffs) > 0)

    @staticmethod
    def _bg_for_status(status: MatchStatus) -> QColor:
        if status == MatchStatus.MATCH:
            return _GREEN
        if status in (MatchStatus.MISSING_IN_BASE, MatchStatus.MISSING_IN_NEW):
            return _YELLOW
        return _RED
