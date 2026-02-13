"""
Test suite for frontend/backend separation architecture.

Tests the clean interfaces between presentation and business logic layers.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch
from typing import List

from transistordatabase.core.models import Transistor, TransistorMetadata, ElectricalRatings, ThermalProperties
from transistordatabase.core.services import (
    IPlottingService, ICalculationService, IExportService,
    IComparisonService, IValidationService,
)
from transistordatabase.backend.concrete_services import (
    ConcreteServiceFactory as ServiceFactory,
    ExportService, ComparisonService, ValidationService,
)
from transistordatabase.frontend.interfaces import (
    IPlotWidget, ITransistorView, IMainWindow, IDialogFactory,
    PlotController, TransistorController, ApplicationController
)


def get_master_data_path() -> Path:
    """Get path to master data directory."""
    return Path(os.path.dirname(__file__)) / "master_data"


@pytest.fixture
def sample_transistor():
    """Create a sample transistor for testing."""
    metadata = TransistorMetadata(
        name="Test_IGBT_1200V_100A",
        type="IGBT",
        manufacturer="TestCorp",
        housing_type="TO-247",
        author="test_author",
        comment="Test transistor for unit tests"
    )
    
    electrical = ElectricalRatings(
        v_abs_max=1200.0,
        i_abs_max=100.0,
        i_cont=80.0,
        t_j_max=175.0
    )

    thermal = ThermalProperties(
        r_th_cs=0.5,
        housing_area=1.0,
        cooling_area=1.0
    )

    return Transistor(
        metadata=metadata,
        electrical=electrical,
        thermal=thermal
    )


@pytest.fixture
def sample_transistors(sample_transistor):
    """Create multiple sample transistors for testing."""
    transistors = [sample_transistor]
    
    # Create second transistor with different specs
    metadata2 = TransistorMetadata(
        name="Test_MOSFET_650V_50A",
        type="MOSFET",
        manufacturer="TestCorp",
        housing_type="TO-220",
        author="test_author"
    )

    electrical2 = ElectricalRatings(
        v_abs_max=650.0,
        i_abs_max=50.0,
        i_cont=40.0,
        t_j_max=150.0
    )

    thermal2 = ThermalProperties(
        r_th_cs=1.0,
        housing_area=1.0,
        cooling_area=1.0
    )

    transistor2 = Transistor(
        metadata=metadata2,
        electrical=electrical2,
        thermal=thermal2
    )

    transistors.append(transistor2)
    return transistors


class TestBackendServices:
    """Test backend service implementations."""
    
    def test_export_service_json(self, sample_transistor, tmp_path):
        """Test JSON export functionality."""
        export_service = ExportService()
        json_file = tmp_path / "test_transistor.json"
        
        result = export_service.export_to_json(sample_transistor, json_file)
        
        assert result is True
        assert json_file.exists()
        
        # Verify JSON content
        import json
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        assert data['metadata']['name'] == "Test_IGBT_1200V_100A"
        assert data['electrical']['v_abs_max'] == 1200.0
    
    def test_export_service_csv(self, sample_transistors, tmp_path):
        """Test CSV export functionality."""
        export_service = ExportService()
        csv_file = tmp_path / "test_transistors.csv"
        
        result = export_service.export_to_csv(sample_transistors, csv_file)
        
        assert result is True
        assert csv_file.exists()
        
        # Verify CSV content
        import csv
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['name'] == "Test_IGBT_1200V_100A"
        assert rows[1]['name'] == "Test_MOSFET_650V_50A"
    
    def test_export_service_spice(self, sample_transistor, tmp_path):
        """Test SPICE export functionality."""
        export_service = ExportService()
        spice_file = tmp_path / "test_transistor.cir"
        
        result = export_service.export_to_spice(sample_transistor, spice_file)
        
        assert result is True
        assert spice_file.exists()
        
        # Verify SPICE content
        content = spice_file.read_text()
        assert "Test_IGBT_1200V_100A" in content
        assert "BV=1200" in content
    
    def test_comparison_service(self, sample_transistors):
        """Test transistor comparison functionality."""
        comparison_service = ComparisonService()
        
        result = comparison_service.compare_transistors(sample_transistors)
        
        assert 'transistor_count' in result
        assert result['transistor_count'] == 2
        assert 'electrical_comparison' in result

        # Check electrical comparison
        elec = result['electrical_comparison']
        assert elec['voltage_max']['max'] == 1200.0
        assert elec['voltage_max']['min'] == 650.0
        assert elec['current_max']['max'] == 100.0
        assert elec['current_max']['min'] == 50.0
    
    def test_comparison_service_similar_transistors(self, sample_transistors):
        """Test finding similar transistors."""
        comparison_service = ComparisonService()

        # Create a similar transistor with all required fields
        similar_metadata = TransistorMetadata(
            name="Similar_IGBT_1200V_95A",
            type="IGBT",
            manufacturer="OtherCorp",
            housing_type="TO-247",
            author="test_author"
        )
        similar_electrical = ElectricalRatings(
            v_abs_max=1200.0,
            i_abs_max=95.0,
            i_cont=75.0,
            t_j_max=170.0
        )
        similar_thermal = ThermalProperties(
            r_th_cs=0.5,
            housing_area=1.0,
            cooling_area=1.0
        )
        similar_transistor = Transistor(
            metadata=similar_metadata,
            electrical=similar_electrical,
            thermal=similar_thermal
        )

        candidates = sample_transistors + [similar_transistor]
        target = sample_transistors[0]  # The IGBT

        similar = comparison_service.find_similar_transistors(
            target, candidates, tolerance=0.1
        )

        assert len(similar) == 1
        assert similar[0].metadata.name == "Similar_IGBT_1200V_95A"
    
    def test_validation_service(self, sample_transistor):
        """Test transistor validation."""
        validation_service = ValidationService()
        result = validation_service.validate_transistor(sample_transistor)
        assert 'warnings' in result
        assert len(result['errors']) == 0  # Should be valid
    
    def test_validation_service_invalid_data(self):
        """Test validation with invalid data."""
        validation_service = ValidationService()

        # Create transistor with invalid data
        invalid_metadata = TransistorMetadata(
            name="",  # Empty name (error)
            type="IGBT",
            manufacturer="",
            housing_type="",
            author=""
        )

        invalid_electrical = ElectricalRatings(
            v_abs_max=-100.0,  # Negative voltage (error)
            i_abs_max=0.0,     # Zero current (error)
            i_cont=150.0,      # Continuous > maximum (error)
            t_j_max=-50.0      # Invalid temperature (error)
        )

        invalid_thermal = ThermalProperties(
            r_th_cs=0.0,
            housing_area=0.0,
            cooling_area=0.0
        )

        invalid_transistor = Transistor(
            metadata=invalid_metadata,
            electrical=invalid_electrical,
            thermal=invalid_thermal
        )

        result = validation_service.validate_transistor(invalid_transistor)

        assert len(result['errors']) > 0
        assert any("name is required" in error for error in result['errors'])
        assert any("voltage must be positive" in error for error in result['errors'])
    
    def test_validation_completeness_check(self, sample_transistor):
        """Test data completeness checking."""
        validation_service = ValidationService()
        
        completeness = validation_service.check_data_completeness(sample_transistor)
        
        assert 'overall' in completeness
        assert completeness['metadata'] > 80  # Should be mostly complete
        assert completeness['electrical'] == 100  # All required fields present
        assert 'overall' in completeness


class TestFrontendInterfaces:
    """Test frontend interface contracts."""
    
    def test_plot_controller_interface(self):
        """Test plot controller interface compliance."""
        # Mock the plotting service
        mock_plotting_service = Mock(spec=IPlottingService)
        mock_plotting_service.plot_channel_characteristics.return_value = {
            'curves': [{'x_data': [1, 2, 3], 'y_data': [4, 5, 6], 'label': 'Test'}]
        }

        # Mock the plot widget
        mock_plot_widget = Mock(spec=IPlotWidget)

        # Create controller

        controller = PlotController(mock_plot_widget, mock_plotting_service)

        # Test plotting
        transistor = Mock()
        controller.plot_channel_characteristics(transistor, temperature=25)

        # Verify service was called
        mock_plotting_service.plot_channel_characteristics.assert_called_once()

        # Verify widget was updated
        mock_plot_widget.render_plot_data.assert_called_once()
        mock_plot_widget.set_title.assert_called_once()
        mock_plot_widget.set_labels.assert_called_once()
    
    def test_transistor_controller_interface(self, sample_transistor):
        """Test transistor controller interface compliance."""
        # Mock the validation service
        mock_validation_service = Mock(spec=IValidationService)
        mock_validation_service.validate_transistor.return_value = {
            'errors': [],
            'warnings': []
        }

        # Mock the transistor view
        mock_transistor_view = Mock(spec=ITransistorView)
        mock_transistor_view.get_transistor.return_value = sample_transistor
        mock_transistor_view.validate_input.return_value = {'errors': [], 'warnings': []}

        # Mock calculation service
        mock_calculation_service = Mock(spec=ICalculationService)

        # Create controller
        controller = TransistorController(mock_transistor_view, mock_calculation_service, mock_validation_service)

        # Test loading transistor
        controller.load_transistor(sample_transistor)
        mock_transistor_view.load_transistor.assert_called_once_with(sample_transistor)

        # Test validation (via save_transistor)
        result = controller.save_transistor()
        assert result is not None
        mock_validation_service.validate_transistor.assert_called_once()
    
    def test_application_controller_interface(self):
        """Test application controller interface compliance."""
        # Mock all required services
        # Mock the main window and dialog factory
        mock_main_window = Mock(spec=IMainWindow)
        mock_dialog_factory = Mock(spec=IDialogFactory)

        # Create controller
        controller = ApplicationController(mock_main_window, mock_dialog_factory)

        # Test error handling (simulate error display)
        controller.handle_error("Test error")
        mock_main_window.show_message.assert_called_with("Test error", "error")


class TestServiceFactory:
    """Test service factory functionality."""
    
    def test_concrete_service_factory(self):
        """Test concrete service factory creates all services."""
        services = {
            'plotting': ServiceFactory.create_plotting_service(),
            'calculation': ServiceFactory.create_calculation_service(),
            'export': ServiceFactory.create_export_service(),
            'comparison': ServiceFactory.create_comparison_service(),
            'validation': ServiceFactory.create_validation_service(),
        }

        assert 'plotting' in services
        assert 'calculation' in services
        assert 'export' in services
        assert 'comparison' in services
        assert 'validation' in services

        # Verify service types
        assert isinstance(services['export'], ExportService)
        assert isinstance(services['comparison'], ComparisonService)
        assert isinstance(services['validation'], ValidationService)
    
    def test_individual_service_creation(self):
        """Test individual service creation."""
        export_service = ServiceFactory.create_export_service()
        assert isinstance(export_service, IExportService)

        comparison_service = ServiceFactory.create_comparison_service()
        assert isinstance(comparison_service, IComparisonService)

        validation_service = ServiceFactory.create_validation_service()
        assert isinstance(validation_service, IValidationService)


class TestArchitecturalSeparation:
    """Test the architectural separation between frontend and backend."""
    
    def test_backend_independence(self):
        """Test that backend services don't depend on frontend."""
        # Backend services should work without any frontend components
        export_service = ExportService()
        comparison_service = ComparisonService()
        validation_service = ValidationService()
        
        # These should be instantiable without frontend
        assert export_service is not None
        assert comparison_service is not None
        assert validation_service is not None
    
    def test_frontend_backend_communication(self, sample_transistor):
        """Test communication between frontend and backend through interfaces."""
        # Create backend services
        validation_service = ValidationService()
        mock_calculation_service = Mock(spec=ICalculationService)

        # Create frontend controller
        # Mock frontend view
        mock_view = Mock(spec=ITransistorView)
        mock_view.get_transistor.return_value = sample_transistor
        mock_view.validate_input.return_value = {'errors': [], 'warnings': []}

        # Create controller with correct signature
        controller = TransistorController(mock_view, mock_calculation_service, validation_service)

        # Test the communication (simulate save, which triggers validation)
        result = controller.save_transistor()
        assert result is not None
    
    def test_interface_compliance(self):
        """Test that concrete implementations comply with interfaces."""
        # Check export service
        export_service = ExportService()
        assert isinstance(export_service, IExportService)
        
        # Check comparison service
        comparison_service = ComparisonService()
        assert isinstance(comparison_service, IComparisonService)
        
        # Check validation service
        validation_service = ValidationService()
        assert isinstance(validation_service, IValidationService)
        
        # Verify all required methods exist
        assert hasattr(export_service, 'export_to_json')
        assert hasattr(export_service, 'export_to_csv')
        assert hasattr(export_service, 'export_to_spice')
        
        assert hasattr(comparison_service, 'compare_transistors')
        assert hasattr(comparison_service, 'find_similar_transistors')
        
        assert hasattr(validation_service, 'validate_transistor')
        assert hasattr(validation_service, 'check_data_completeness')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
