"""
Frontend interfaces for transistor database - Presentation Layer.

This module contains the interface contracts between the GUI and backend services.
All UI-related logic should implement these interfaces to ensure clean separation.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

# Import backend services from core
from transistordatabase.core.services import (
    IPlottingService, ICalculationService, IExportService,
    IComparisonService, IValidationService
)
from transistordatabase.core.models import Transistor


class IPlotWidget(ABC):
    """Interface for plot widgets in the frontend."""
    
    @abstractmethod
    def clear_plot(self) -> None:
        """Clear the current plot."""
        pass
    
    @abstractmethod
    def render_plot_data(self, plot_data: Dict[str, Any]) -> None:
        """
        Render plot data on the widget.
        
        :param plot_data: Plot data dictionary from backend plotting service
        """
        pass
    
    @abstractmethod
    def set_title(self, title: str) -> None:
        """Set plot title."""
        pass
    
    @abstractmethod
    def set_labels(self, xlabel: str, ylabel: str) -> None:
        """Set axis labels."""
        pass
    
    @abstractmethod
    def add_legend(self, show: bool = True) -> None:
        """Add or hide plot legend."""
        pass
    
    @abstractmethod
    def save_plot(self, filepath: Path, format: str = "png") -> bool:
        """
        Save plot to file.
        
        :param filepath: Path to save the plot
        :param format: File format ("png", "pdf", "svg", etc.)
        :return: True if successful, False otherwise
        """
        pass


class ITransistorView(ABC):
    """Interface for transistor view/editor widgets."""
    
    @abstractmethod
    def load_transistor(self, transistor: Transistor) -> None:
        """Load transistor data into the view."""
        pass
    
    @abstractmethod
    def get_transistor(self) -> Transistor:
        """Get transistor data from the view."""
        pass
    
    @abstractmethod
    def validate_input(self) -> Dict[str, List[str]]:
        """
        Validate user input.
        
        :return: Dictionary with validation results (errors, warnings)
        """
        pass
    
    @abstractmethod
    def clear_view(self) -> None:
        """Clear all fields in the view."""
        pass
    
    @abstractmethod
    def set_read_only(self, read_only: bool) -> None:
        """Set view to read-only mode."""
        pass


class IMainWindow(ABC):
    """Interface for the main application window."""
    
    @abstractmethod
    def show_message(self, message: str, message_type: str = "info") -> None:
        """
        Show message to user.
        
        :param message: Message text
        :param message_type: "info", "warning", "error", "success"
        """
        pass
    
    @abstractmethod
    def show_progress(self, message: str, progress: int = 0) -> None:
        """
        Show progress indicator.
        
        :param message: Progress message
        :param progress: Progress percentage (0-100)
        """
        pass
    
    @abstractmethod
    def hide_progress(self) -> None:
        """Hide progress indicator."""
        pass
    
    @abstractmethod
    def get_active_transistor(self) -> Optional[Transistor]:
        """Get currently active transistor."""
        pass
    
    @abstractmethod
    def set_active_transistor(self, transistor: Transistor) -> None:
        """Set currently active transistor."""
        pass
    
    @abstractmethod
    def refresh_transistor_list(self) -> None:
        """Refresh the list of available transistors."""
        pass


class IDialogFactory(ABC):
    """Interface for creating dialogs."""
    
    @abstractmethod
    def create_file_dialog(self, dialog_type: str, 
                          file_filter: str = "",
                          title: str = "") -> Optional[Path]:
        """
        Create file dialog.
        
        :param dialog_type: "open", "save", "open_multiple"
        :param file_filter: File filter string
        :param title: Dialog title
        :return: Selected file path or None
        """
        pass
    
    @abstractmethod
    def create_input_dialog(self, title: str, 
                           label: str,
                           default_value: str = "") -> Optional[str]:
        """
        Create input dialog.
        
        :param title: Dialog title
        :param label: Input label
        :param default_value: Default input value
        :return: User input or None if cancelled
        """
        pass
    
    @abstractmethod
    def create_confirmation_dialog(self, title: str, 
                                 message: str) -> bool:
        """
        Create confirmation dialog.
        
        :param title: Dialog title
        :param message: Confirmation message
        :return: True if confirmed, False otherwise
        """
        pass


# Frontend Controller Classes
class PlotController:
    """Controller for managing plot widgets and backend plotting service."""
    
    def __init__(self, plot_widget: IPlotWidget, plotting_service: IPlottingService):
        """
        Initialize plot controller.
        
        :param plot_widget: Plot widget implementation
        :param plotting_service: Backend plotting service
        """
        self.plot_widget = plot_widget
        self.plotting_service = plotting_service
        self._current_plot_type = None
        self._current_plot_data = None
    
    def plot_channel_characteristics(self, transistor: Transistor,
                                   component: str = "switch",
                                   **kwargs) -> bool:
        """
        Plot channel characteristics.
        
        :param transistor: Transistor object
        :param component: "switch" or "diode"
        :param kwargs: Additional plotting parameters
        :return: True if successful, False otherwise
        """
        try:
            # Get plot data from backend service
            plot_data = self.plotting_service.plot_channel_characteristics(
                transistor, component, **kwargs
            )
            
            if "error" in plot_data:
                return False
            
            # Clear and render plot
            self.plot_widget.clear_plot()
            self.plot_widget.render_plot_data(plot_data)
            
            # Set plot properties
            metadata = plot_data.get('metadata', {})
            self.plot_widget.set_title(metadata.get('title', ''))
            self.plot_widget.set_labels(
                metadata.get('xlabel', ''),
                metadata.get('ylabel', '')
            )
            self.plot_widget.add_legend()
            
            # Store current plot data
            self._current_plot_type = "channel"
            self._current_plot_data = plot_data
            
            return True
            
        except Exception as e:
            print(f"Error plotting channel characteristics: {e}")
            return False
    
    def plot_switching_losses(self, transistor: Transistor,
                            loss_type: str = "e_on",
                            plot_type: str = "i_e") -> bool:
        """
        Plot switching losses.
        
        :param transistor: Transistor object
        :param loss_type: "e_on", "e_off", or "e_rr"
        :param plot_type: "i_e", "r_e", or "t_e"
        :return: True if successful, False otherwise
        """
        try:
            # Get plot data from backend service
            plot_data = self.plotting_service.plot_switching_losses(
                transistor, loss_type, plot_type
            )
            
            if "error" in plot_data:
                return False
            
            # Clear and render plot
            self.plot_widget.clear_plot()
            self.plot_widget.render_plot_data(plot_data)
            
            # Set plot properties
            metadata = plot_data.get('metadata', {})
            self.plot_widget.set_title(metadata.get('title', ''))
            self.plot_widget.set_labels(
                metadata.get('xlabel', ''),
                metadata.get('ylabel', '')
            )
            self.plot_widget.add_legend()
            
            # Store current plot data
            self._current_plot_type = f"losses_{loss_type}_{plot_type}"
            self._current_plot_data = plot_data
            
            return True
            
        except Exception as e:
            print(f"Error plotting switching losses: {e}")
            return False
    
    def plot_safe_operating_area(self, transistor: Transistor) -> bool:
        """Plot safe operating area."""
        try:
            plot_data = self.plotting_service.plot_safe_operating_area(transistor)
            
            if "error" in plot_data:
                return False
            
            self.plot_widget.clear_plot()
            self.plot_widget.render_plot_data(plot_data)
            
            metadata = plot_data.get('metadata', {})
            self.plot_widget.set_title(metadata.get('title', ''))
            self.plot_widget.set_labels(
                metadata.get('xlabel', ''),
                metadata.get('ylabel', '')
            )
            self.plot_widget.add_legend()
            
            self._current_plot_type = "soa"
            self._current_plot_data = plot_data
            
            return True
            
        except Exception as e:
            print(f"Error plotting SOA: {e}")
            return False
    
    def plot_thermal_impedance(self, transistor: Transistor) -> bool:
        """Plot thermal impedance."""
        try:
            plot_data = self.plotting_service.plot_thermal_impedance(transistor)
            
            if "error" in plot_data:
                return False
            
            self.plot_widget.clear_plot()
            self.plot_widget.render_plot_data(plot_data)
            
            metadata = plot_data.get('metadata', {})
            self.plot_widget.set_title(metadata.get('title', ''))
            self.plot_widget.set_labels(
                metadata.get('xlabel', ''),
                metadata.get('ylabel', '')
            )
            self.plot_widget.add_legend()
            
            self._current_plot_type = "thermal"
            self._current_plot_data = plot_data
            
            return True
            
        except Exception as e:
            print(f"Error plotting thermal impedance: {e}")
            return False
    
    def plot_gate_charge(self, transistor: Transistor) -> bool:
        """Plot gate charge."""
        try:
            plot_data = self.plotting_service.plot_gate_charge(transistor)
            
            if "error" in plot_data:
                return False
            
            self.plot_widget.clear_plot()
            self.plot_widget.render_plot_data(plot_data)
            
            metadata = plot_data.get('metadata', {})
            self.plot_widget.set_title(metadata.get('title', ''))
            self.plot_widget.set_labels(
                metadata.get('xlabel', ''),
                metadata.get('ylabel', '')
            )
            self.plot_widget.add_legend()
            
            self._current_plot_type = "gate_charge"
            self._current_plot_data = plot_data
            
            return True
            
        except Exception as e:
            print(f"Error plotting gate charge: {e}")
            return False
    
    def save_current_plot(self, filepath: Path, format: str = "png") -> bool:
        """Save current plot to file."""
        return self.plot_widget.save_plot(filepath, format)
    
    def get_current_plot_data(self) -> Optional[Dict[str, Any]]:
        """Get current plot data for export or analysis."""
        return self._current_plot_data


class TransistorController:
    """Controller for managing transistor view and backend services."""
    
    def __init__(self, transistor_view: ITransistorView, 
                 calculation_service: ICalculationService,
                 validation_service: Optional[IValidationService] = None):
        """
        Initialize transistor controller.
        
        :param transistor_view: Transistor view implementation
        :param calculation_service: Backend calculation service
        :param validation_service: Optional validation service
        """
        self.transistor_view = transistor_view
        self.calculation_service = calculation_service
        self.validation_service = validation_service
        self._current_transistor = None
    
    def load_transistor(self, transistor: Transistor) -> bool:
        """Load transistor into view."""
        try:
            self.transistor_view.load_transistor(transistor)
            self._current_transistor = transistor
            return True
        except Exception as e:
            print(f"Error loading transistor: {e}")
            return False
    
    def save_transistor(self) -> Optional[Transistor]:
        """Save transistor from view."""
        try:
            # Validate input first
            validation_result = self.transistor_view.validate_input()
            if validation_result.get('errors'):
                print(f"Validation errors: {validation_result['errors']}")
                return None
            
            # Get transistor from view
            transistor = self.transistor_view.get_transistor()
            
            # Additional validation with service if available
            if self.validation_service:
                service_validation = self.validation_service.validate_transistor(transistor)
                if service_validation.get('errors'):
                    print(f"Service validation errors: {service_validation['errors']}")
                    return None
            
            self._current_transistor = transistor
            return transistor
            
        except Exception as e:
            print(f"Error saving transistor: {e}")
            return None
    
    def calculate_losses(self, operating_point: Dict[str, float]) -> Optional[Dict[str, float]]:
        """Calculate losses for current transistor."""
        if not self._current_transistor:
            return None
        
        try:
            return self.calculation_service.calculate_losses(
                self._current_transistor, operating_point
            )
        except Exception as e:
            print(f"Error calculating losses: {e}")
            return None
    
    def get_current_transistor(self) -> Optional[Transistor]:
        """Get current transistor."""
        return self._current_transistor


class ApplicationController:
    """Main application controller coordinating all components."""

    def handle_error(self, message: str) -> None:
        """Handle errors by displaying a message in the main window."""
        self.main_window.show_message(message, "error")
    
    def __init__(self, main_window: IMainWindow, dialog_factory: IDialogFactory):
        """
        Initialize application controller.
        
        :param main_window: Main window implementation
        :param dialog_factory: Dialog factory implementation
        """
        self.main_window = main_window
        self.dialog_factory = dialog_factory
        self.plot_controllers: Dict[str, PlotController] = {}
        self.transistor_controller: Optional[TransistorController] = None
        
        # Backend services
        from transistordatabase.backend.concrete_services import ConcreteServiceFactory
        self.plotting_service = ConcreteServiceFactory.create_plotting_service()
        self.calculation_service = ConcreteServiceFactory.create_calculation_service()
    
    def register_plot_controller(self, name: str, plot_controller: PlotController) -> None:
        """Register a plot controller."""
        self.plot_controllers[name] = plot_controller
    
    def register_transistor_controller(self, transistor_controller: TransistorController) -> None:
        """Register transistor controller."""
        self.transistor_controller = transistor_controller
    
    def load_transistor_from_file(self) -> bool:
        """Load transistor from file using dialog."""
        try:
            file_path = self.dialog_factory.create_file_dialog(
                "open", 
                "JSON files (*.json);;All files (*.*)",
                "Load Transistor"
            )
            
            if not file_path:
                return False
            
            # Load transistor using core loader
            from transistordatabase.core.models import JsonTransistorLoader
            loader = JsonTransistorLoader()
            transistor = loader.load_from_file(file_path)
            
            if transistor and self.transistor_controller:
                success = self.transistor_controller.load_transistor(transistor)
                if success:
                    self.main_window.set_active_transistor(transistor)
                    self.main_window.show_message(f"Transistor loaded: {transistor.name}", "success")
                    return True
            
            self.main_window.show_message("Failed to load transistor", "error")
            return False
            
        except Exception as e:
            self.main_window.show_message(f"Error loading transistor: {e}", "error")
            return False
    
    def save_transistor_to_file(self) -> bool:
        """Save current transistor to file using dialog."""
        try:
            if not self.transistor_controller:
                return False
            
            transistor = self.transistor_controller.save_transistor()
            if not transistor:
                return False
            
            file_path = self.dialog_factory.create_file_dialog(
                "save",
                "JSON files (*.json);;All files (*.*)",
                "Save Transistor"
            )
            
            if not file_path:
                return False
            
            # Save using core loader
            from transistordatabase.core.models import JsonTransistorLoader
            loader = JsonTransistorLoader()
            success = loader.save_to_file(transistor, file_path)
            
            if success:
                self.main_window.show_message(f"Transistor saved: {file_path.name}", "success")
                return True
            else:
                self.main_window.show_message("Failed to save transistor", "error")
                return False
                
        except Exception as e:
            self.main_window.show_message(f"Error saving transistor: {e}", "error")
            return False
    
    def plot_transistor_characteristic(self, plot_name: str, 
                                     characteristic_type: str,
                                     **kwargs) -> bool:
        """Plot transistor characteristic in specified plot widget."""
        if plot_name not in self.plot_controllers:
            self.main_window.show_message(f"Plot controller '{plot_name}' not found", "error")
            return False
        
        transistor = self.main_window.get_active_transistor()
        if not transistor:
            self.main_window.show_message("No active transistor", "warning")
            return False
        
        plot_controller = self.plot_controllers[plot_name]
        
        try:
            if characteristic_type == "channel":
                return plot_controller.plot_channel_characteristics(transistor, **kwargs)
            elif characteristic_type == "losses":
                return plot_controller.plot_switching_losses(transistor, **kwargs)
            elif characteristic_type == "soa":
                return plot_controller.plot_safe_operating_area(transistor)
            elif characteristic_type == "thermal":
                return plot_controller.plot_thermal_impedance(transistor)
            elif characteristic_type == "gate_charge":
                return plot_controller.plot_gate_charge(transistor)
            else:
                self.main_window.show_message(f"Unknown characteristic type: {characteristic_type}", "error")
                return False
                
        except Exception as e:
            self.main_window.show_message(f"Error plotting {characteristic_type}: {e}", "error")
            return False
