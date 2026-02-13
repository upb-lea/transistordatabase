"""
PyQt5 implementation of frontend interfaces.

This module provides concrete implementations of the frontend interfaces using PyQt5.
"""
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
        QTextEdit, QDoubleSpinBox, QGroupBox,
        QScrollArea, QMessageBox, QProgressBar, QFileDialog, QInputDialog,
        QMainWindow, QStatusBar
    )
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    # Provide mock classes for testing without PyQt5
    
    class QWidget:
        """Mock QWidget for headless environments."""

    class QMainWindow:
        """Mock QMainWindow for headless environments."""

    class QVBoxLayout:
        """Mock QVBoxLayout for headless environments."""

    class FigureCanvas:
        """Mock FigureCanvas for headless environments."""

    class Figure:
        """Mock Figure for headless environments."""

from transistordatabase.frontend.interfaces import (
    IPlotWidget, ITransistorView, IMainWindow, IDialogFactory
)
from transistordatabase.core.models import Transistor, TransistorMetadata, ElectricalRatings, ThermalProperties


class MatplotlibPlotWidget(QWidget, IPlotWidget):
    """PyQt5 implementation of plot widget using matplotlib."""
    
    def __init__(self, parent=None):
        """Initialize matplotlib plot widget."""
        super().__init__(parent)
        
        if not PYQT5_AVAILABLE:
            raise ImportError("PyQt5 is required for MatplotlibPlotWidget")
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Configure matplotlib
        self.figure.tight_layout()
        
    def clear_plot(self) -> None:
        """Clear the current plot."""
        self.axes.clear()
        self.canvas.draw()
    
    def render_plot_data(self, plot_data: Dict[str, Any]) -> None:
        """Render plot data on the widget."""
        if "error" in plot_data:
            self.axes.text(0.5, 0.5, f"Error: {plot_data['error']}",
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.axes.transAxes, fontsize=12, color='red')
            self.canvas.draw()
            return
        
        curves = plot_data.get('curves', [])
        
        for curve in curves:
            x_data = curve.get('x_data', [])
            y_data = curve.get('y_data', [])
            label = curve.get('label', 'Unlabeled')
            
            if x_data and y_data:
                self.axes.plot(x_data, y_data, label=label, linewidth=2)
        
        # Set grid
        self.axes.grid(True, alpha=0.3)
        
        self.canvas.draw()
    
    def set_title(self, title: str) -> None:
        """Set plot title."""
        self.axes.set_title(title, fontsize=14, fontweight='bold')
        self.canvas.draw()
    
    def set_labels(self, xlabel: str, ylabel: str) -> None:
        """Set axis labels."""
        self.axes.set_xlabel(xlabel, fontsize=12)
        self.axes.set_ylabel(ylabel, fontsize=12)
        self.canvas.draw()
    
    def add_legend(self, show: bool = True) -> None:
        """Add or hide plot legend."""
        if show:
            self.axes.legend(fontsize=10, loc='best')
        else:
            legend = self.axes.get_legend()
            if legend:
                legend.remove()
        self.canvas.draw()
    
    def save_plot(self, filepath: Path, format: str = "png") -> bool:
        """Save plot to file."""
        try:
            self.figure.savefig(str(filepath), format=format, dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"Error saving plot: {e}")
            return False


class TransistorEditWidget(QWidget, ITransistorView):
    """PyQt5 implementation of transistor view/editor."""
    
    def __init__(self, parent=None):
        """Initialize transistor edit widget."""
        super().__init__(parent)
        
        if not PYQT5_AVAILABLE:
            raise ImportError("PyQt5 is required for TransistorEditWidget")
        
        self._current_transistor = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Create scroll area for large forms
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Metadata group
        self._create_metadata_group(scroll_layout)
        
        # Electrical ratings group
        self._create_electrical_group(scroll_layout)
        
        # Thermal properties group
        self._create_thermal_group(scroll_layout)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        self.setLayout(layout)
    
    def _create_metadata_group(self, layout):
        """Create metadata input group."""
        group = QGroupBox("Transistor Metadata")
        group_layout = QVBoxLayout()
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        group_layout.addLayout(name_layout)
        
        # Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["IGBT", "MOSFET", "SiC-MOSFET", "GaN-Transistor", "Diode"])
        type_layout.addWidget(self.type_combo)
        group_layout.addLayout(type_layout)
        
        # Author
        author_layout = QHBoxLayout()
        author_layout.addWidget(QLabel("Author:"))
        self.author_edit = QLineEdit()
        author_layout.addWidget(self.author_edit)
        group_layout.addLayout(author_layout)
        
        # Manufacturer
        manufacturer_layout = QHBoxLayout()
        manufacturer_layout.addWidget(QLabel("Manufacturer:"))
        self.manufacturer_edit = QLineEdit()
        manufacturer_layout.addWidget(self.manufacturer_edit)
        group_layout.addLayout(manufacturer_layout)
        
        # Housing type
        housing_layout = QHBoxLayout()
        housing_layout.addWidget(QLabel("Housing Type:"))
        self.housing_edit = QLineEdit()
        housing_layout.addWidget(self.housing_edit)
        group_layout.addLayout(housing_layout)
        
        # Comment
        comment_layout = QVBoxLayout()
        comment_layout.addWidget(QLabel("Comment:"))
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        comment_layout.addWidget(self.comment_edit)
        group_layout.addLayout(comment_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_electrical_group(self, layout):
        """Create electrical ratings input group."""
        group = QGroupBox("Electrical Ratings")
        group_layout = QVBoxLayout()
        
        # Maximum voltage
        v_max_layout = QHBoxLayout()
        v_max_layout.addWidget(QLabel("Max Voltage (V):"))
        self.v_max_spin = QDoubleSpinBox()
        self.v_max_spin.setRange(0, 10000)
        self.v_max_spin.setSuffix(" V")
        v_max_layout.addWidget(self.v_max_spin)
        group_layout.addLayout(v_max_layout)
        
        # Maximum current
        i_max_layout = QHBoxLayout()
        i_max_layout.addWidget(QLabel("Max Current (A):"))
        self.i_max_spin = QDoubleSpinBox()
        self.i_max_spin.setRange(0, 1000)
        self.i_max_spin.setSuffix(" A")
        i_max_layout.addWidget(self.i_max_spin)
        group_layout.addLayout(i_max_layout)
        
        # Continuous current
        i_cont_layout = QHBoxLayout()
        i_cont_layout.addWidget(QLabel("Continuous Current (A):"))
        self.i_cont_spin = QDoubleSpinBox()
        self.i_cont_spin.setRange(0, 1000)
        self.i_cont_spin.setSuffix(" A")
        i_cont_layout.addWidget(self.i_cont_spin)
        group_layout.addLayout(i_cont_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_thermal_group(self, layout):
        """Create thermal properties input group."""
        group = QGroupBox("Thermal Properties")
        group_layout = QVBoxLayout()
        
        # Maximum junction temperature
        t_j_max_layout = QHBoxLayout()
        t_j_max_layout.addWidget(QLabel("Max Junction Temp (°C):"))
        self.t_j_max_spin = QDoubleSpinBox()
        self.t_j_max_spin.setRange(-50, 300)
        self.t_j_max_spin.setSuffix(" °C")
        t_j_max_layout.addWidget(self.t_j_max_spin)
        group_layout.addLayout(t_j_max_layout)
        
        # Thermal resistance
        r_th_layout = QHBoxLayout()
        r_th_layout.addWidget(QLabel("Thermal Resistance (K/W):"))
        self.r_th_spin = QDoubleSpinBox()
        self.r_th_spin.setRange(0, 10)
        self.r_th_spin.setDecimals(3)
        self.r_th_spin.setSuffix(" K/W")
        r_th_layout.addWidget(self.r_th_spin)
        group_layout.addLayout(r_th_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def load_transistor(self, transistor: Transistor) -> None:
        """Load transistor data into the view."""
        self._current_transistor = transistor
        
        # Load metadata
        if transistor.metadata:
            self.name_edit.setText(transistor.metadata.name or "")
            self.type_combo.setCurrentText(transistor.metadata.type or "IGBT")
            self.author_edit.setText(transistor.metadata.author or "")
            self.manufacturer_edit.setText(transistor.metadata.manufacturer or "")
            self.housing_edit.setText(transistor.metadata.housing_type or "")
            self.comment_edit.setPlainText(transistor.metadata.comment or "")
        
        # Load electrical ratings
        if transistor.electrical:
            self.v_max_spin.setValue(transistor.electrical.v_abs_max or 0)
            self.i_max_spin.setValue(transistor.electrical.i_abs_max or 0)
            self.i_cont_spin.setValue(transistor.electrical.i_cont or 0)
        
        # Load thermal properties
        if transistor.thermal:
            self.t_j_max_spin.setValue(transistor.thermal.t_j_max or 150)
            self.r_th_spin.setValue(transistor.thermal.r_th_cs or 0)
    
    def get_transistor(self) -> Transistor:
        """Get transistor data from the view."""
        # Create metadata
        metadata = TransistorMetadata(
            name=self.name_edit.text() or "Unnamed",
            type=self.type_combo.currentText(),
            author=self.author_edit.text(),
            manufacturer=self.manufacturer_edit.text(),
            housing_type=self.housing_edit.text(),
            comment=self.comment_edit.toPlainText() or None
        )
        
        # Create electrical ratings
        electrical = ElectricalRatings(
            v_abs_max=self.v_max_spin.value(),
            i_abs_max=self.i_max_spin.value(),
            i_cont=self.i_cont_spin.value()
        )
        
        # Create thermal properties
        thermal = ThermalProperties(
            t_j_max=self.t_j_max_spin.value(),
            r_th_cs=self.r_th_spin.value()
        )
        
        # Create transistor
        transistor = Transistor(
            metadata=metadata,
            electrical=electrical,
            thermal=thermal
        )
        
        # Copy existing switch/diode data if available
        if self._current_transistor:
            transistor.switch = self._current_transistor.switch
            transistor.diode = self._current_transistor.diode
        
        return transistor
    
    def validate_input(self) -> Dict[str, List[str]]:
        """Validate user input."""
        errors = []
        warnings = []
        
        # Validate name
        if not self.name_edit.text().strip():
            errors.append("Transistor name is required")
        
        # Validate electrical ratings
        if self.v_max_spin.value() <= 0:
            warnings.append("Maximum voltage should be greater than 0")
        
        if self.i_max_spin.value() <= 0:
            warnings.append("Maximum current should be greater than 0")
        
        # Validate thermal properties
        if self.t_j_max_spin.value() <= 25:
            warnings.append("Maximum junction temperature seems low")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def clear_view(self) -> None:
        """Clear all fields in the view."""
        self.name_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.author_edit.clear()
        self.manufacturer_edit.clear()
        self.housing_edit.clear()
        self.comment_edit.clear()
        
        self.v_max_spin.setValue(0)
        self.i_max_spin.setValue(0)
        self.i_cont_spin.setValue(0)
        
        self.t_j_max_spin.setValue(150)
        self.r_th_spin.setValue(0)
        
        self._current_transistor = None
    
    def set_read_only(self, read_only: bool) -> None:
        """Set view to read-only mode."""
        self.name_edit.setReadOnly(read_only)
        self.type_combo.setEnabled(not read_only)
        self.author_edit.setReadOnly(read_only)
        self.manufacturer_edit.setReadOnly(read_only)
        self.housing_edit.setReadOnly(read_only)
        self.comment_edit.setReadOnly(read_only)
        
        self.v_max_spin.setReadOnly(read_only)
        self.i_max_spin.setReadOnly(read_only)
        self.i_cont_spin.setReadOnly(read_only)
        
        self.t_j_max_spin.setReadOnly(read_only)
        self.r_th_spin.setReadOnly(read_only)


class MainWindowImpl(QMainWindow, IMainWindow):
    """PyQt5 implementation of main window interface."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        if not PYQT5_AVAILABLE:
            raise ImportError("PyQt5 is required for MainWindowImpl")
        
        self._current_transistor = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.setWindowTitle("Transistor Database")
        self.resize(1200, 800)
    
    def show_message(self, message: str, message_type: str = "info") -> None:
        """Show message to user."""
        # Show in status bar
        self.status_bar.showMessage(message, 5000)  # 5 seconds
        
        # Show message box for errors and warnings
        if message_type in ["error", "warning"]:
            if message_type == "error":
                QMessageBox.critical(self, "Error", message)
            else:
                QMessageBox.warning(self, "Warning", message)
        elif message_type == "success":
            QMessageBox.information(self, "Success", message)
    
    def show_progress(self, message: str, progress: int = 0) -> None:
        """Show progress indicator."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(progress)
        self.status_bar.showMessage(message)
    
    def hide_progress(self) -> None:
        """Hide progress indicator."""
        self.progress_bar.setVisible(False)
        self.status_bar.clearMessage()
    
    def get_active_transistor(self) -> Optional[Transistor]:
        """Get currently active transistor."""
        return self._current_transistor
    
    def set_active_transistor(self, transistor: Transistor) -> None:
        """Set currently active transistor."""
        self._current_transistor = transistor
        self.setWindowTitle(f"Transistor Database - {transistor.name}")
    
    def refresh_transistor_list(self) -> None:
        """Refresh the list of available transistors."""
        # This would be implemented based on the specific UI design
        pass


class PyQt5DialogFactory(IDialogFactory):
    """PyQt5 implementation of dialog factory."""
    
    def __init__(self, parent=None):
        """Initialize dialog factory."""
        self.parent = parent
        
        if not PYQT5_AVAILABLE:
            raise ImportError("PyQt5 is required for PyQt5DialogFactory")
    
    def create_file_dialog(self, dialog_type: str, 
                          file_filter: str = "",
                          title: str = "") -> Optional[Path]:
        """Create file dialog."""
        if dialog_type == "open":
            filename, _ = QFileDialog.getOpenFileName(
                self.parent, title or "Open File", "", file_filter
            )
            return Path(filename) if filename else None
        
        elif dialog_type == "save":
            filename, _ = QFileDialog.getSaveFileName(
                self.parent, title or "Save File", "", file_filter
            )
            return Path(filename) if filename else None
        
        elif dialog_type == "open_multiple":
            filenames, _ = QFileDialog.getOpenFileNames(
                self.parent, title or "Open Files", "", file_filter
            )
            return [Path(f) for f in filenames] if filenames else None
        
        else:
            raise ValueError(f"Unknown dialog type: {dialog_type}")
    
    def create_input_dialog(self, title: str, 
                           label: str,
                           default_value: str = "") -> Optional[str]:
        """Create input dialog."""
        text, ok = QInputDialog.getText(
            self.parent, title, label, text=default_value
        )
        return text if ok else None
    
    def create_confirmation_dialog(self, title: str, 
                                 message: str) -> bool:
        """Create confirmation dialog."""
        reply = QMessageBox.question(
            self.parent, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes


# Factory function for creating PyQt5 implementations
def create_pyqt5_implementations(parent=None):
    """
    Create PyQt5 implementations of all interfaces.
    
    :param parent: Parent widget for Qt objects
    :return: Dictionary with all implementations
    """
    if not PYQT5_AVAILABLE:
        raise ImportError("PyQt5 is not available")
    
    return {
        'plot_widget': MatplotlibPlotWidget(parent),
        'transistor_view': TransistorEditWidget(parent),
        'main_window': MainWindowImpl(),
        'dialog_factory': PyQt5DialogFactory(parent)
    }
