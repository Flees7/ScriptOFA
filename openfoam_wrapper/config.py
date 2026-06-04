"""
Configuration file for OpenFOAM GUI Wrapper.
Stores application settings and defaults.
"""

# Application Settings
APP_NAME = "OpenFOAM GUI Wrapper"
APP_VERSION = "1.0.0"

# Default Simulation Parameters
DEFAULT_CONFIG = {
    "solver": "simpleFoam",
    "endTime": 3500,
    "deltaT": 1,
    "writeInterval": 150,
    "nu": 1.5e-05,  # Kinematic viscosity (m²/s) for air at ~25°C
    "u_inlet": [20, 0, 0],  # m/s
    "k_inlet": 0.1,  # m²/s²
    "omega_inlet": 100,  # 1/s
    "turbulenceModel": "kOmegaSST"
}

# UI Colors for Boundary Types
BOUNDARY_COLORS = {
    "Inlet": (0.0, 0.0, 1.0),      # Blue
    "Outlet": (1.0, 0.0, 0.0),     # Red
    "Wall": (0.5, 0.5, 0.5),       # Gray
    "Symmetry": (0.0, 1.0, 0.0),   # Green
    "unassigned": (0.8, 0.8, 0.8)  # Light gray
}

# Available Solvers
SOLVERS = [
    "simpleFoam",   # Steady-state incompressible
    "icoFoam",      # Transient incompressible
    "pisoFoam",     # Transient incompressible (pressure-implicit, split-operator)
]

# Mesh Settings
MESH_FEATURE_ANGLE = 45  # Degrees - threshold for auto-splitting surfaces
STL_TOLERANCE = 1e-6

# Solver Execution Settings
SOLVER_TIMEOUT = None  # None = no timeout
CAPTURE_SOLVER_OUTPUT = True

# Logging
ENABLE_LOGGING = True
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
