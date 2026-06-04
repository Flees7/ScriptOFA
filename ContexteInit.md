# Context & Specifications: OpenFOAM GUI Wrapper

## 1. Role & Objective
You are an expert Python developer and CFD engineer. Your task is to build a desktop application (GUI wrapper) for OpenFOAM under Linux. The goal of this application is to abstract the complexity of OpenFOAM dictionary files for novice users. The app must allow users to import a `.stl` geometry, visually assign boundary conditions (Inlet, Outlet, Wall, Symmetry) by clicking on the 3D model, configure simulation parameters, and run the simulation automatically.

---

## 2. Tech Stack & Dependencies
- **OS Target:** Linux (Ubuntu/Fedora compatible with OpenFOAM installed)
- **Language:** Python 3.10+
- **GUI Framework:** PyQt6 or PySide6
- **3D Engine & Mesh Interaction:** `pyvista` (VTK-based) integrated via `pyvistaqt` for native PyQt embedding
- **Process Management:** Native `subprocess` module with threading OR `QProcess` (asynchronous execution to avoid GUI freezing)
- **File System:** `pathlib` for robust cross-platform path handling
- **Mesher:** `cfMesh` (preferred for STL tolerance) or `blockMesh`/`snappyHexMesh`

---

## 3. Project Architecture
The project must follow a modular structure:

```text
openfoam_wrapper/
│
├── main.py                 # Application entry point, initializes GUI
├── gui.py                  # UI layout, widgets, dialogs, and window management
├── mesh_utils.py           # STL importing, automatic splitting, and PyVista picking logic
├── foam_utils.py           # Template rendering, dict generation, and subprocess execution
│
└── templates/              # Base OpenFOAM dictionary templates
    ├── controlDict.template
    ├── U.template
    └── ...
```

---

## 4. Detailed Core Workflow & Implementation Details

### Step 1: Case Initialization & STL Import
- User creates a "New Case" and selects a working directory. The app copies a clean OpenFOAM case structure (`0/`, `constant/`, `system/`).
- **STL Processing Logic (`mesh_utils.py`):**
  When the user loads a `.stl`, the script must segment it into distinct clickable patches. 
  *Reference Code for Auto-Splitting (using Feature Angles):*
  ```python
  import pyvista as pv
  
  # Load raw STL
  mesh = pv.read("domain.stl")
  
  # Split surfaces based on sharp edges (e.g., 45 degrees)
  separated_surfaces = mesh.extract_surface().split_bodies()
  
  # separated_surfaces is now a MultiBlock dataset containing individual patches
  ```

### Step 2: 3D Visualization & Graphical Mesh Picking
- The GUI must have a PyVista canvas on the right and a configuration panel on the left.
- Render each detected STL patch from the `separated_surfaces` with a distinct default color.
- **Interaction Logic (Picking):**
  Use PyVista's click tracking to identify which patch the user clicked.
  *Reference Code for Picking:*
  ```python
  def on_click(mesh_selected):
      # Trigger GUI popup to ask: "Define as: Inlet, Outlet, Wall, Symmetry?"
      pass
      
  plotter.track_click_position(callback=on_click, side="left")
  ```
- **Patch Assignment:**
  When assigned, update the patch color:
  - **Blue:** Inlet (Ask user for Velocity components U_x, U_y, U_z)
  - **Red:** Outlet
  - **Gray:** Wall
  - **Green:** Symmetry

### Step 3: Global Configuration Panel
Provide a clean UI form for global simulation variables:
- **Solver Choice:** Dropdown (`icoFoam`, `simpleFoam`, `pisoFoam`).
- **Time Controls:** `startTime` (0), `endTime` (float), `deltaT` (float).
- **Physical Properties:** Kinematic viscosity `nu` (float).

### Step 4: OpenFOAM Dictionary Generation (Template System)
- **Strict Rule:** Do not use complex regex on active OpenFOAM dicts. Use `.template` files with tags.
- The script reads the templates, replaces tags, and writes to the target directory.
  
  *Example of Template Processing (`foam_utils.py`):*
  ```python
  template_path = "templates/controlDict.template"
  target_path = "system/controlDict"
  
  with open(template_path, "r") as file:
      content = file.read()
      
  # Replace tags with GUI variables
  content = content.replace("#SOLVER#", selected_solver)
  content = content.replace("#END_TIME#", str(end_time))
  
  with open(target_path, "w") as file:
      file.write(content)
  ```

  *Example of `U.template` structure expected:*
  ```text
  dimensions      [0 1 -1 0 0 0 0];
  internalField   uniform (0 0 0);
  boundaryField
  {
      #BOUNDARY_CONFIG_U#
  }
  ```
  *(The agent must dynamically build the `#BOUNDARY_CONFIG_U#` string based on all patches assigned by the user in Step 2).*

### Step 5: Mesh Generation & Solver Execution
- Provide a "Run Simulation" button.
- **Execution Logic (`foam_utils.py`):**
  Run commands asynchronously and redirect stdout to a GUI console widget.
  *Reference Code for Subprocess:*
  ```python
  import subprocess
  
  try:
      # Example: run mesher then solver
      subprocess.run(["cartesianMesh"], check=True, cwd=target_case_dir)
      subprocess.run([selected_solver], check=True, cwd=target_case_dir)
  except subprocess.CalledProcessError as e:
      # Emit signal to GUI to show error dialog
      print(f"Error: {e}")
  ```

---

## 5. Coding Constraints & Guardrails
- **No Blocking Calls:** The GUI must remain responsive. Use `QThread` and Signals/Slots for the subprocess execution.
- **Error Handling:** Wrap STL parsing, PyVista picking, and OS execution in `try/except` blocks. Show user-friendly `QMessageBox` errors.
- **Paths:** Always use `pathlib.Path` for file manipulation.