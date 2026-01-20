import sys
from io import StringIO

from PySide6.QtWidgets import QSplitter, QPlainTextEdit
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt
from gwaio.launcher.qtclasses.dock_base import BaseDockWidget


class DockShell(BaseDockWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_widgets()
        QShortcut(QKeySequence('Ctrl+B'), self, self.execute_command)

    def create_widgets(self):
        splitter = QSplitter()
        splitter.setOrientation(Qt.Vertical)
        self.text_box = QPlainTextEdit()
        self.text_box.setReadOnly(True)
        self.code_editor = QPlainTextEdit()
        self.code_editor.setMaximumHeight(50)
        
        splitter.addWidget(self.text_box)
        splitter.addWidget(self.code_editor)
        splitter.setSizes([1,0])
        self.setWidget(splitter)

    def execute_command(self):
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        code = self.code_editor.toPlainText()
        try:
            exec(code)
        except Exception as e:
            self.text_box.appendPlainText(str(e))
        finally:
            sys.stdout = old_stdout

        self.text_box.appendPlainText(redirected_output.getvalue())