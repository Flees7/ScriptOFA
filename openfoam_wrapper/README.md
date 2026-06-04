# OpenFOAM GUI Wrapper

A PyQt6-based desktop application for OpenFOAM that abstracts the complexity of dictionary files. Designed for novice users to easily import STL geometries, assign boundary conditions visually, configure simulations, and run them automatically.

## Features

✅ **STL Import & Auto-Segmentation**: Load STL files and automatically split them into distinct clickable patches
✅ **Interactive 3D Visualization**: PyVista-powered 3D viewer with color-coded boundary types
✅ **Graphical Boundary Condition Assignment**: Click on patches to assign Inlet, Outlet, Wall, or Symmetry
✅ **Configurable Simulation Parameters**: Time controls, physical properties, turbulence settings
✅ **Automatic Case Generation**: Generates complete OpenFOAM case structure and dictionaries
✅ **Async Solver Execution**: Run simulations without blocking the GUI
✅ **Live Console Output**: Real-time feedback from the solver

## Installation

### Prerequisites
- **Linux** (Ubuntu 20.04+ / Fedora 35+) with OpenFOAM installed
- **Python 3.10+**
- **pip** or **conda** for dependency management

### Setup

1. **Clone or download this repository:**
   ```bash
   cd /path/to/ScriptOFA/openfoam_wrapper
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify OpenFOAM installation:**
   ```bash
   which simpleFoam  # Should return the path to simpleFoam executable
   ```

## Usage

### Running the Application

```bash
python3 main.py
```

### Step-by-Step Workflow

#### 1. **Create a New Case**
   - Click **"New Case"** button
   - Select a working directory where the OpenFOAM case will be created
   - A new directory structure (`0/`, `constant/`, `system/`) is initialized

#### 2. **Load STL Geometry**
   - Click **"Load STL File"** button
   - Select your `.stl` geometry file
   - The 3D viewer will display the mesh with auto-detected patches (shown in light gray)

#### 3. **Assign Boundary Conditions**
   - Click on patches in the 3D viewer to assign boundary types
   - A dialog will appear asking you to select:
     - **Blue (Inlet)**: Inlet boundary with fixed velocity
     - **Red (Outlet)**: Outlet boundary
     - **Gray (Wall)**: Wall boundary
     - **Green (Symmetry)**: Symmetry plane
   - Patches change color once assigned

#### 4. **Configure Simulation Parameters**
   - Left panel allows you to set:
     - **Solver**: `simpleFoam`, `icoFoam`, `pisoFoam`
     - **Time controls**: End time, time step (Δt), write interval
     - **Physical properties**: Kinematic viscosity (ν)
     - **Inlet conditions**: Velocity magnitude, turbulent kinetic energy (k), specific dissipation (ω)

#### 5. **Generate Case**
   - Click **"Generate Case"** button
   - The application will:
     - Create necessary directories
     - Generate all OpenFOAM dictionaries from templates
     - Substitute your parameters into the case files
   - Success message appears when complete

#### 6. **Run Solver**
   - Click **"Run Solver"** button
   - The selected solver runs asynchronously
   - Real-time output appears in the console widget at the bottom
   - GUI remains responsive during execution

## Project Structure

```
openfoam_wrapper/
├── main.py                   # Entry point
├── gui.py                    # PyQt6 GUI components
├── mesh_utils.py             # STL loading and mesh picking
├── foam_utils.py             # Dictionary generation and execution
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
└── templates/                # OpenFOAM dictionary templates
    ├── controlDict.template
    ├── fvSchemes.template
    ├── fvSolution.template
    ├── U.template
    ├── p.template
    ├── k.template
    ├── omega.template
    ├── nut.template
    ├── transportProperties.template
    └── turbulenceProperties.template
```

## Key Classes

### `MeshManager` (mesh_utils.py)
- Handles STL import and auto-segmentation
- Tracks patch assignments and colors
- Provides picking functionality

### `OpenFOAMCase` (foam_utils.py)
- Creates case structure
- Renders templates with user parameters
- Executes solvers asynchronously

### `OpenFOAMWrapperApp` (gui.py)
- Main PyQt6 application window
- Integrates mesh visualization and configuration panels
- Manages user interactions

### `SolverThread` (gui.py)
- QThread worker for non-blocking solver execution
- Emits signals for output and completion

## Configuration

### Modifying Templates
Templates are located in `templates/` directory. To customize OpenFOAM settings:

1. Edit the corresponding `.template` file
2. Use tags like `#SOLVER#`, `#END_TIME#`, etc.
3. These tags are replaced at runtime by values from the GUI

### Adding New Solvers
Edit `gui.py` in the `create_config_panel()` method:
```python
self.solver_combo.addItems(["simpleFoam", "icoFoam", "pisoFoam", "myNewSolver"])
```

## Troubleshooting

**Issue**: "ModuleNotFoundError: No module named 'pyvista'"
- **Solution**: Install dependencies: `pip install -r requirements.txt`

**Issue**: Solver fails silently
- **Solution**: Check console output for error messages. Verify case was generated correctly.

**Issue**: STL file doesn't load
- **Solution**: Ensure the STL file is valid. Try opening it in FreeCAD or Paraview first.

**Issue**: GUI is frozen during mesh loading
- **Solution**: Large STL files may take time. This is normal. Wait for the operation to complete.

## Dependencies

- **PyQt6**: GUI framework
- **pyvista**: 3D visualization (VTK wrapper)
- **pyvistaqt**: PyVista + PyQt6 integration
- **NumPy**: Numerical computations (indirect dependency)

See `requirements.txt` for full list and versions.

## Future Enhancements

- [ ] Mesh quality visualization
- [ ] Automatic mesh generation (blockMesh, snappyHexMesh integration)
- [ ] Post-processing visualization in-app
- [ ] Case templates library
- [ ] Parallel execution support
- [ ] Residual plotting during simulation

## License

Project for EPF internship preparation. Use freely for educational purposes.

## Support

For issues or questions, please refer to the OpenFOAM documentation:
- Official docs: https://www.openfoam.com/documentation
- Community: https://www.cfd-online.com/Forums/openfoam/
