"""
PyQt6 GUI for OpenFOAM wrapper.
Manages UI layout, widget interactions, and integration of mesh/foam utilities.
"""

import os
import warnings
from pathlib import Path
from typing import Optional, Dict
import threading
import logging

# Suppress VTK warnings early
os.environ['VTK_SUPPRESS_WARNINGS'] = '1'
warnings.filterwarnings('ignore', category=DeprecationWarning)

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton,
    QFileDialog, QMessageBox, QTextEdit, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pyvistaqt import QtInteractor

from mesh_utils import MeshManager
from foam_utils import OpenFOAMCase

logger = logging.getLogger(__name__)


class SolverThread(QThread):
    """Worker thread for running OpenFOAM solver asynchronously."""
    
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    
    def __init__(self, case: OpenFOAMCase, solver: str):
        super().__init__()
        self.case = case
        self.solver = solver
    
    def run(self):
        """Execute solver in thread."""
        try:
            self.case.output_callback = self.output_signal.emit
            # Call _run_solver_thread directly instead of run_solver_async to avoid nested threading
            self.case._run_solver_thread(self.solver)
            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))


class BoundaryConditionDialog(QDialog):
    """Dialog for assigning boundary conditions to a patch."""
    
    def __init__(self, patch_name: str, parent=None):
        super().__init__(parent)
        self.patch_name = patch_name
        self.selected_bc = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle(f"Assign Boundary Condition - {self.patch_name}")
        self.setGeometry(100, 100, 400, 200)
        
        layout = QFormLayout()
        
        # Boundary type selection
        label = QLabel(f"Select boundary condition for '{self.patch_name}':")
        layout.addRow(label)
        
        bc_combo = QComboBox()
        bc_options = ["Inlet", "Outlet", "Wall", "Symmetry"]
        bc_combo.addItems(bc_options)
        layout.addRow("Boundary Type:", bc_combo)
        
        # Store the combo box
        self.bc_combo = bc_combo
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        self.setLayout(layout)
    
    def get_selected_bc(self) -> Optional[str]:
        """Get the selected boundary condition."""
        if self.exec() == QDialog.DialogCode.Accepted:
            return self.bc_combo.currentText()
        return None


class OpenFOAMWrapperApp(QMainWindow):
    """Main application window for OpenFOAM GUI wrapper."""
    
    # Signal for thread-safe logging
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing OpenFOAMWrapperApp")
        self.setWindowTitle("OpenFOAM GUI Wrapper")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize managers
        self.mesh_manager = MeshManager()
        self.loaded_meshes = []  # List to hold multiple loaded mesh managers
        self.patch_to_mesh = {}  # Maps global patch names to mesh managers and local patch indices
        self.case = None
        self.case_dir = None
        self.solver_thread = None
        
        # Initialize UI
        self.init_ui()
        
        # Connect log signal to slot
        self.log_signal.connect(self._append_log)
        logger.info("OpenFOAMWrapperApp initialized")
    
    def init_ui(self):
        """Initialize the main UI layout."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout: left panel (config) + right panel (3D view)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel: Configuration
        left_panel = self.create_config_panel()
        
        # Right panel: 3D visualization
        right_panel = self.create_visualization_panel()
        
        # Add panels with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
    
    def create_config_panel(self) -> QWidget:
        """Create the left configuration panel."""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Case Management Group
        case_group = QGroupBox("Case Management")
        case_layout = QVBoxLayout()
        
        # New case button
        new_case_btn = QPushButton("New Case")
        new_case_btn.clicked.connect(self.new_case)
        case_layout.addWidget(new_case_btn)
        
        # Case directory display
        self.case_dir_label = QLineEdit()
        self.case_dir_label.setReadOnly(True)
        case_layout.addWidget(QLabel("Case Directory:"))
        case_layout.addWidget(self.case_dir_label)
        
        case_group.setLayout(case_layout)
        layout.addWidget(case_group)
        
        # STL Import Group
        stl_group = QGroupBox("Mesh Import")
        stl_layout = QVBoxLayout()
        
        load_stl_btn = QPushButton("Load STL File")
        load_stl_btn.clicked.connect(self.load_stl)
        stl_layout.addWidget(load_stl_btn)
        
        # Patches info
        self.patches_label = QLabel("No patches loaded")
        stl_layout.addWidget(QLabel("Detected Patches:"))
        stl_layout.addWidget(self.patches_label)
        
        stl_group.setLayout(stl_layout)
        layout.addWidget(stl_group)
        
        # Domain Configuration Group
        domain_group = QGroupBox("Domain Configuration")
        domain_layout = QFormLayout()
        
        # Domain center coordinates
        self.domain_center_x_spin = QDoubleSpinBox()
        self.domain_center_x_spin.setValue(0)
        self.domain_center_x_spin.setMinimum(-1e6)
        self.domain_center_x_spin.setMaximum(1e6)
        domain_layout.addRow("Center X (m):", self.domain_center_x_spin)
        
        self.domain_center_y_spin = QDoubleSpinBox()
        self.domain_center_y_spin.setValue(0)
        self.domain_center_y_spin.setMinimum(-1e6)
        self.domain_center_y_spin.setMaximum(1e6)
        domain_layout.addRow("Center Y (m):", self.domain_center_y_spin)
        
        self.domain_center_z_spin = QDoubleSpinBox()
        self.domain_center_z_spin.setValue(0)
        self.domain_center_z_spin.setMinimum(-1e6)
        self.domain_center_z_spin.setMaximum(1e6)
        domain_layout.addRow("Center Z (m):", self.domain_center_z_spin)
        
        # Domain dimensions
        self.domain_x_spin = QDoubleSpinBox()
        self.domain_x_spin.setValue(10)
        self.domain_x_spin.setMaximum(1e6)
        domain_layout.addRow("Domain X (m):", self.domain_x_spin)
        
        self.domain_y_spin = QDoubleSpinBox()
        self.domain_y_spin.setValue(10)
        self.domain_y_spin.setMaximum(1e6)
        domain_layout.addRow("Domain Y (m):", self.domain_y_spin)
        
        self.domain_z_spin = QDoubleSpinBox()
        self.domain_z_spin.setValue(10)
        self.domain_z_spin.setMaximum(1e6)
        domain_layout.addRow("Domain Z (m):", self.domain_z_spin)
        
        # Auto button
        auto_btn = QPushButton("Auto")
        auto_btn.clicked.connect(self.auto_domain)
        domain_layout.addRow("", auto_btn)
        
        # Update button
        update_btn = QPushButton("Update Visualization")
        update_btn.clicked.connect(self.visualize_mesh)
        domain_layout.addRow("", update_btn)
        
        domain_group.setLayout(domain_layout)
        layout.addWidget(domain_group)
        
        # Simulation Configuration Group
        sim_group = QGroupBox("Simulation Parameters")
        sim_layout = QFormLayout()
        
        # Solver selection
        self.solver_combo = QComboBox()
        self.solver_combo.addItems(["simpleFoam", "icoFoam", "pisoFoam"])
        sim_layout.addRow("Solver:", self.solver_combo)
        
        # Time parameters
        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setValue(3500)
        self.end_time_spin.setMaximum(1e6)
        sim_layout.addRow("End Time:", self.end_time_spin)
        
        self.delta_t_spin = QDoubleSpinBox()
        self.delta_t_spin.setValue(1)
        self.delta_t_spin.setSingleStep(0.1)
        sim_layout.addRow("Time Step (Δt):", self.delta_t_spin)
        
        self.write_interval_spin = QSpinBox()
        self.write_interval_spin.setValue(150)
        sim_layout.addRow("Write Interval:", self.write_interval_spin)
        
        # Physical parameters
        self.nu_spin = QDoubleSpinBox()
        self.nu_spin.setValue(1.5e-05)
        self.nu_spin.setDecimals(8)
        self.nu_spin.setSingleStep(1e-06)
        sim_layout.addRow("Kinematic Viscosity (ν):", self.nu_spin)
        
        # Inlet velocity
        self.u_inlet_spin = QDoubleSpinBox()
        self.u_inlet_spin.setValue(20)
        sim_layout.addRow("Inlet Velocity (m/s):", self.u_inlet_spin)
        
        # Turbulence parameters
        self.k_inlet_spin = QDoubleSpinBox()
        self.k_inlet_spin.setValue(0.1)
        self.k_inlet_spin.setDecimals(6)
        sim_layout.addRow("Turbulent KE (k):", self.k_inlet_spin)
        
        self.omega_inlet_spin = QDoubleSpinBox()
        self.omega_inlet_spin.setValue(100)
        sim_layout.addRow("Specific Dissipation (ω):", self.omega_inlet_spin)
        
        sim_group.setLayout(sim_layout)
        layout.addWidget(sim_group)
        
        # Control Buttons Group
        control_group = QGroupBox("Actions")
        control_layout = QVBoxLayout()
        
        generate_btn = QPushButton("Generate Case")
        generate_btn.clicked.connect(self.generate_case)
        control_layout.addWidget(generate_btn)
        
        run_btn = QPushButton("Run Solver")
        run_btn.clicked.connect(self.run_solver)
        self.run_btn = run_btn
        control_layout.addWidget(run_btn)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Console output
        console_group = QGroupBox("Console Output")
        console_layout = QVBoxLayout()
        
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setMaximumHeight(150)
        console_layout.addWidget(self.console_text)
        
        console_group.setLayout(console_layout)
        layout.addWidget(console_group)
        
        # Add stretch at bottom
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def create_visualization_panel(self) -> QWidget:
        """Create the right 3D visualization panel."""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("Use mouse to rotate, scroll to zoom")
        layout.addWidget(info_label)
        
        # PyVista visualizer
        self.plotter = QtInteractor(panel)
        layout.addWidget(self.plotter.interactor)
        
        # Add axes to show orientation (wrapped in try-catch)
        try:
            self.plotter.add_axes(viewport=(0.0, 0.0, 0.2, 0.2))
        except Exception as e:
            logger.warning(f"Could not add axes: {e}")
        
        panel.setLayout(layout)
        return panel
    
    def new_case(self):
        """Create a new OpenFOAM case."""
        logger.info("new_case called")
        # Select case directory
        case_dir = QFileDialog.getExistingDirectory(
            self, "Select Case Directory", str(Path.home())
        )
        
        if not case_dir:
            logger.info("new_case cancelled by user")
            return
        
        case_dir = Path(case_dir)
        logger.info(f"Creating new case at: {case_dir}")
        self.case_dir = case_dir
        self.case_dir_label.setText(str(case_dir))
        
        # Create case manager
        self.case = OpenFOAMCase(case_dir)
        
        # Create basic structure
        if self.case.create_case_structure():
            logger.info(f"Case created successfully at: {case_dir}")
            self.log_output(f"Case created at: {case_dir}")
        else:
            logger.error("Failed to create case structure")
            QMessageBox.critical(self, "Error", "Failed to create case structure")
    
    def load_stl(self):
        """Load an STL file."""
        logger.info("load_stl called")
        if not self.case_dir:
            logger.warning("load_stl: case_dir not set")
            QMessageBox.warning(self, "Warning", "Please create a case first")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open STL File", "", "STL Files (*.stl)"
        )
        
        if not file_path:
            logger.info("load_stl cancelled by user")
            return
        
        logger.info(f"Loading STL file: {file_path}")
        # Create new mesh manager for this STL
        mesh_mgr = MeshManager()
        
        # Load mesh
        if mesh_mgr.load_stl(Path(file_path)):
            logger.info(f"STL loaded successfully: {file_path}")
            self.log_output(f"STL loaded: {file_path}")
            
            # Add to loaded meshes list
            self.loaded_meshes.append(mesh_mgr)
            
            # Update patches display
            total_patches = sum(len(m.get_patches()) for m in self.loaded_meshes)
            logger.debug(f"Total patches across all meshes: {total_patches}")
            self.patches_label.setText(f"{total_patches} patches detected across {len(self.loaded_meshes)} STL(s)")
            
            # Visualize
            self.visualize_mesh()
        else:
            logger.error(f"Failed to load STL file: {file_path}")
            QMessageBox.critical(self, "Error", "Failed to load STL file")
    
    def visualize_mesh(self):
        """Visualize the mesh in PyVista."""
        try:
            # Check if any mesh is loaded
            if not self.loaded_meshes:
                return
            
            # Remove all previous actors from the plotter
            try:
                for actor in list(self.plotter.actors.values()):
                    self.plotter.remove_actor(actor)
            except:
                pass
            
            # Clear patch mapping
            self.patch_to_mesh = {}
            
            # Add domain box
            domain_box = self.mesh_manager.create_domain_box(
                self.domain_x_spin.value(),
                self.domain_y_spin.value(),
                self.domain_z_spin.value(),
                self.domain_center_x_spin.value(),
                self.domain_center_y_spin.value(),
                self.domain_center_z_spin.value()
            )
            self.plotter.add_mesh(
                domain_box,
                color=(0.2, 0.8, 0.2),
                name="domain",
                show_edges=True,
                opacity=0.3
            )
            
            # Add patches from all loaded meshes
            patch_counter = 0
            for mesh_idx, mesh_mgr in enumerate(self.loaded_meshes):
                if mesh_mgr.separated_surfaces:
                    for i, patch in enumerate(mesh_mgr.separated_surfaces):
                        patch_name = f"patch_{patch_counter}"
                        # Map global patch name to mesh manager and local patch index
                        self.patch_to_mesh[patch_name] = (mesh_mgr, f"patch_{i}")
                        
                        color = mesh_mgr.patch_colors.get(f"patch_{i}", (0.5, 0.5, 0.5))
                        
                        self.plotter.add_mesh(
                            patch,
                            color=color,
                            name=patch_name,
                            show_edges=True,
                            opacity=0.9
                        )
                        patch_counter += 1
            
            self.plotter.view_isometric()
            self.plotter.reset_camera()
            self.plotter.render()
        except Exception as e:
            logger.error(f"Error in visualize_mesh: {e}")
            print(f"Visualization error: {e}")
    
    def on_patch_picked(self, patch_name: str, coordinates):
        """Handle patch selection."""
        # Get the mesh manager and local patch name for this global patch name
        if patch_name not in self.patch_to_mesh:
            return
        
        mesh_mgr, local_patch_name = self.patch_to_mesh[patch_name]
        
        # Show BC assignment dialog
        dialog = BoundaryConditionDialog(patch_name, self)
        selected_bc = dialog.get_selected_bc()
        
        if selected_bc:
            # Assign BC to the correct mesh manager
            mesh_mgr.assign_patch(local_patch_name, selected_bc)
            self.log_output(f"Assigned {patch_name} -> {selected_bc}")
            
            # Update visualization
            self.visualize_mesh()
    
    def auto_domain(self):
        """Auto calculate domain dimensions."""
        pass
    
    def generate_case(self):
        """Generate OpenFOAM dictionaries."""
        logger.info("generate_case called")
        if not self.case:
            logger.warning("generate_case: case not initialized")
            QMessageBox.warning(self, "Warning", "Please create a case first")
            return
        
        logger.info("Collecting configuration from GUI")
        # Get current configuration
        config = {
            "solver": self.solver_combo.currentText(),
            "endTime": self.end_time_spin.value(),
            "deltaT": self.delta_t_spin.value(),
            "writeInterval": self.write_interval_spin.value(),
            "nu": self.nu_spin.value(),
            "u_inlet": [self.u_inlet_spin.value(), 0, 0],
            "k_inlet": self.k_inlet_spin.value(),
            "omega_inlet": self.omega_inlet_spin.value(),
            "turbulenceModel": "kOmegaSST"
        }
        logger.debug(f"Configuration: {config}")
        
        # Get patch assignments from all loaded meshes
        patch_info = {}
        for mesh_mgr in self.loaded_meshes:
            patch_info.update(mesh_mgr.export_patch_info())
        logger.debug(f"Patch info: {patch_info}")
        
        if not patch_info:
            logger.warning("generate_case: no patch assignments")
            QMessageBox.warning(self, "Warning", "Please assign boundary conditions to all patches")
            return
        
        logger.info("Generating case dictionaries")
        # Generate dictionaries
        if self.case.generate_dictionaries(config, patch_info):
            logger.info("Case dictionaries generated successfully")
            self.log_output("Case dictionaries generated successfully!")
            QMessageBox.information(self, "Success", "Case generated successfully!")
        else:
            logger.error("Failed to generate case dictionaries")
            QMessageBox.critical(self, "Error", "Failed to generate case dictionaries")
    
    def run_solver(self):
        """Run the OpenFOAM solver."""
        logger.info("run_solver called")
        if not self.case:
            logger.warning("run_solver: case not initialized")
            QMessageBox.warning(self, "Warning", "Please create and generate a case first")
            return
        
        logger.info("Starting CFD simulation pipeline")
        # Disable run button during execution
        self.run_btn.setEnabled(False)
        
        # Start solver in thread
        solver = self.solver_combo.currentText()
        logger.debug(f"Selected solver: {solver}")
        self.solver_thread = SolverThread(self.case, solver)
        self.solver_thread.output_signal.connect(self.log_output)
        self.solver_thread.finished_signal.connect(self.on_solver_finished)
        self.solver_thread.error_signal.connect(self.on_solver_error)
        self.solver_thread.start()
    
    def on_solver_finished(self):
        """Handle solver completion."""
        self.run_btn.setEnabled(True)
        self.log_output("Solver execution completed!")
    
    def on_solver_error(self, error_msg: str):
        """Handle solver error."""
        self.run_btn.setEnabled(True)
        self.log_output(f"ERROR: {error_msg}")
        QMessageBox.critical(self, "Solver Error", error_msg)
    
    def log_output(self, message: str):
        """Add message to console output (thread-safe via signal)."""
        self.log_signal.emit(message)
    
    def _append_log(self, message: str):
        """Actually append log message to console (runs on GUI thread)."""
        self.console_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.console_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
