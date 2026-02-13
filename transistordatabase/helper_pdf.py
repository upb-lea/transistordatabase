"""PDF generation helper using PyQt5 WebEngine.

This module isolates the PyQt5 dependency so that helper_functions.py
can be imported headlessly without requiring PyQt5.
"""
from __future__ import annotations

import os
import sys
from typing import List


def html_to_pdf(html: List | str, name: List | str, path: List | str) -> None:
    """Convert HTML document(s) to PDF using Qt WebEngineWidgets.

    :param html: HTML string or list of HTML strings.
    :param name: File name(s) for display.
    :param path: Output path(s) for the PDF file(s).
    """
    try:
        from PyQt5 import QtWidgets, QtWebEngineWidgets
    except ImportError as exc:
        raise ImportError(
            "PyQt5 and PyQtWebEngine are required for PDF export. "
            "Install with: pip install PyQt5 PyQtWebEngine"
        ) from exc

    app = QtWidgets.QApplication(sys.argv)
    page = QtWebEngineWidgets.QWebEnginePage()
    path_item = str()
    name_item = str()
    html_item = str()

    def fetch_next():
        try:
            nonlocal html_item, name_item, path_item
            html_item, name_item, path_item = next(html_and_paths)
        except StopIteration:
            return False
        else:
            page.setHtml(html_item)
        return True

    def handle_print_finished(filepath, status):
        print(f"Export virtual datasheet {name_item} to {os.getcwd()}")
        print(f"Open Datasheet here: {os.getcwd()}")
        if not fetch_next():
            app.quit()

    def handle_load_finished(status):
        if status:
            nonlocal path_item
            page.printToPdf(path_item)
        else:
            print("Failed")
            app.quit()

    page.pdfPrintingFinished.connect(handle_print_finished)
    page.loadFinished.connect(handle_load_finished)
    if isinstance(html, list):
        html_and_paths = iter(zip(html, name, path, strict=True))
    else:
        html_and_paths = iter(zip([html], [name], [path], strict=True))
    fetch_next()
    app.exec_()
