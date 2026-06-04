"""
OpenFOAM utilities: dictionary generation, template rendering, and subprocess execution.
Handles case creation, parameter substitution, and solver execution.
"""

import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Callable, Optional
import shutil


class OpenFOAMCase:
    """Manages OpenFOAM case creation and execution."""
    
    def __init__(self, case_dir: Path):
        """
        Initialize an OpenFOAM case manager.
        
        Args:
            case_dir: Root directory of the OpenFOAM case
        """
        self.case_dir = Path(case_dir)
        self.templates_dir = Path(__file__).parent / "templates"
        self.output_callback = None
    
    def create_case_structure(self) -> bool:
        """
        Create the basic OpenFOAM case directory structure (0/, constant/, system/).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create subdirectories
            subdirs = ["0", "constant", "system"]
            for subdir in subdirs:
                (self.case_dir / subdir).mkdir(parents=True, exist_ok=True)
            
            # Create polyMesh subdirectory
            (self.case_dir / "constant" / "polyMesh").mkdir(parents=True, exist_ok=True)
            
            return True
        except Exception as e:
            self._log(f"Error creating case structure: {e}")
            return False
    
    def generate_dictionaries(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> bool:
        """
        Generate OpenFOAM dictionaries from templates using configuration and patch info.
        
        Args:
            config: Configuration dictionary with solver, time, and physical parameters
            patch_info: Dictionary of patch names to boundary types
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate controlDict
            self._generate_control_dict(config)
            
            # Generate fvSchemes
            self._generate_fv_schemes(config)
            
            # Generate fvSolution
            self._generate_fv_solution(config)
            
            # Generate boundary condition files (U, p, k, etc.)
            self._generate_boundary_conditions(config, patch_info)
            
            # Generate transportProperties
            self._generate_transport_properties(config)
            
            return True
        except Exception as e:
            self._log(f"Error generating dictionaries: {e}")
            return False
    
    def _generate_control_dict(self, config: Dict[str, Any]) -> None:
        """Generate system/controlDict from template."""
        template_file = self.templates_dir / "controlDict.template"
        target_file = self.case_dir / "system" / "controlDict"
        
        with open(template_file, "r") as f:
            content = f.read()
        
        # Replace tags
        content = content.replace("#SOLVER#", config.get("solver", "simpleFoam"))
        content = content.replace("#END_TIME#", str(config.get("endTime", 3500)))
        content = content.replace("#DELTA_T#", str(config.get("deltaT", 1)))
        content = content.replace("#WRITE_INTERVAL#", str(config.get("writeInterval", 150)))
        
        with open(target_file, "w") as f:
            f.write(content)
        
        self._log(f"Generated: {target_file}")
    
    def _generate_fv_schemes(self, config: Dict[str, Any]) -> None:
        """Generate system/fvSchemes from template."""
        template_file = self.templates_dir / "fvSchemes.template"
        target_file = self.case_dir / "system" / "fvSchemes"
        
        with open(template_file, "r") as f:
            content = f.read()
        
        # Schemes are typically predefined; minimal substitution needed
        with open(target_file, "w") as f:
            f.write(content)
        
        self._log(f"Generated: {target_file}")
    
    def _generate_fv_solution(self, config: Dict[str, Any]) -> None:
        """Generate system/fvSolution from template."""
        template_file = self.templates_dir / "fvSolution.template"
        target_file = self.case_dir / "system" / "fvSolution"
        
        with open(template_file, "r") as f:
            content = f.read()
        
        # Replace solver-specific settings if needed
        with open(target_file, "w") as f:
            f.write(content)
        
        self._log(f"Generated: {target_file}")
    
    def _generate_boundary_conditions(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> None:
        """
        Generate 0/ boundary condition files (U, p, k, omega, nut).
        
        Args:
            config: Configuration dictionary
            patch_info: Dictionary of patch names to boundary types
        """
        # Generate U field
        self._generate_u_field(config, patch_info)
        
        # Generate p field
        self._generate_p_field(config, patch_info)
        
        # Generate k field (if turbulence is enabled)
        if config.get("turbulenceModel"):
            self._generate_k_field(config, patch_info)
            self._generate_omega_field(config, patch_info)
            self._generate_nut_field(config, patch_info)
    
    def _generate_u_field(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> None:
        """Generate 0/U boundary conditions."""
        template_file = self.templates_dir / "U.template"
        target_file = self.case_dir / "0" / "U"
        
        with open(template_file, "r") as f:
            content = f.read()
        
        # Build boundary field configuration
        boundary_config = self._build_boundary_config_u(config, patch_info)
        content = content.replace("#BOUNDARY_CONFIG_U#", boundary_config)
        
        with open(target_file, "w") as f:
            f.write(content)
        
        self._log(f"Generated: {target_file}")
    
    def _build_boundary_config_u(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> str:
        """Build boundary configuration for U field."""
        bc_lines = []
        
        for patch_name, bc_type in patch_info.items():
            if bc_type == "Inlet":
                # Inlet: fixed velocity
                u_inlet = config.get("u_inlet", [20, 0, 0])
                bc_lines.append(f"""
    {patch_name}
    {{
        type            fixedValue;
        value           uniform ({u_inlet[0]} {u_inlet[1]} {u_inlet[2]});
    }}""")
            elif bc_type == "Outlet":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            zeroGradient;
    }}""")
            elif bc_type == "Wall":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            slip;
    }}""")
            elif bc_type == "Symmetry":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            symmetryPlane;
    }}""")
        
        return "\n".join(bc_lines)
    
    def _generate_p_field(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> None:
        """Generate 0/p boundary conditions."""
        template_file = self.templates_dir / "p.template"
        target_file = self.case_dir / "0" / "p"
        
        with open(template_file, "r") as f:
            content = f.read()
        
        boundary_config = self._build_boundary_config_p(config, patch_info)
        content = content.replace("#BOUNDARY_CONFIG_P#", boundary_config)
        
        with open(target_file, "w") as f:
            f.write(content)
        
        self._log(f"Generated: {target_file}")
    
    def _build_boundary_config_p(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> str:
        """Build boundary configuration for p field."""
        bc_lines = []
        
        for patch_name, bc_type in patch_info.items():
            if bc_type == "Inlet":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            zeroGradient;
    }}""")
            elif bc_type == "Outlet":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            fixedValue;
        value           uniform 0;
    }}""")
            elif bc_type == "Wall":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            zeroGradient;
    }}""")
            elif bc_type == "Symmetry":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            symmetryPlane;
    }}""")
        
        return "\n".join(bc_lines)
    
    def _generate_k_field(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> None:
        """Generate 0/k boundary conditions (turbulent kinetic energy)."""
        template_file = self.templates_dir / "k.template"
        target_file = self.case_dir / "0" / "k"
        
        with open(template_file, "r") as f:
            content = f.read()
        
        boundary_config = self._build_boundary_config_k(config, patch_info)
        content = content.replace("#BOUNDARY_CONFIG_K#", boundary_config)
        
        with open(target_file, "w") as f:
            f.write(content)
        
        self._log(f"Generated: {target_file}")
    
    def _build_boundary_config_k(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> str:
        """Build boundary configuration for k field."""
        bc_lines = []
        k_inlet = config.get("k_inlet", 0.1)
        
        for patch_name, bc_type in patch_info.items():
            if bc_type == "Inlet":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            fixedValue;
        value           uniform {k_inlet};
    }}""")
            elif bc_type in ["Outlet", "Wall"]:
                bc_lines.append(f"""
    {patch_name}
    {{
        type            zeroGradient;
    }}""")
            elif bc_type == "Symmetry":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            symmetryPlane;
    }}""")
        
        return "\n".join(bc_lines)
    
    def _generate_omega_field(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> None:
        """Generate 0/omega boundary conditions (specific dissipation rate)."""
        template_file = self.templates_dir / "omega.template"
        target_file = self.case_dir / "0" / "omega"
        
        with open(template_file, "r") as f:
            content = f.read()
        
        boundary_config = self._build_boundary_config_omega(config, patch_info)
        content = content.replace("#BOUNDARY_CONFIG_OMEGA#", boundary_config)
        
        with open(target_file, "w") as f:
            f.write(content)
        
        self._log(f"Generated: {target_file}")
    
    def _build_boundary_config_omega(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> str:
        """Build boundary configuration for omega field."""
        bc_lines = []
        omega_inlet = config.get("omega_inlet", 100)
        
        for patch_name, bc_type in patch_info.items():
            if bc_type == "Inlet":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            fixedValue;
        value           uniform {omega_inlet};
    }}""")
            elif bc_type in ["Outlet", "Wall"]:
                bc_lines.append(f"""
    {patch_name}
    {{
        type            zeroGradient;
    }}""")
            elif bc_type == "Symmetry":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            symmetryPlane;
    }}""")
        
        return "\n".join(bc_lines)
    
    def _generate_nut_field(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> None:
        """Generate 0/nut boundary conditions (turbulent viscosity)."""
        template_file = self.templates_dir / "nut.template"
        target_file = self.case_dir / "0" / "nut"
        
        with open(template_file, "r") as f:
            content = f.read()
        
        boundary_config = self._build_boundary_config_nut(config, patch_info)
        content = content.replace("#BOUNDARY_CONFIG_NUT#", boundary_config)
        
        with open(target_file, "w") as f:
            f.write(content)
        
        self._log(f"Generated: {target_file}")
    
    def _build_boundary_config_nut(self, config: Dict[str, Any], patch_info: Dict[str, str]) -> str:
        """Build boundary configuration for nut field."""
        bc_lines = []
        
        for patch_name, bc_type in patch_info.items():
            if bc_type == "Inlet":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            calculated;
        value           uniform 0;
    }}""")
            elif bc_type in ["Outlet", "Wall"]:
                bc_lines.append(f"""
    {patch_name}
    {{
        type            zeroGradient;
    }}""")
            elif bc_type == "Symmetry":
                bc_lines.append(f"""
    {patch_name}
    {{
        type            symmetryPlane;
    }}""")
        
        return "\n".join(bc_lines)
    
    def _generate_transport_properties(self, config: Dict[str, Any]) -> None:
        """Generate constant/transportProperties."""
        template_file = self.templates_dir / "transportProperties.template"
        target_file = self.case_dir / "constant" / "transportProperties"
        
        with open(template_file, "r") as f:
            content = f.read()
        
        # Replace physical properties
        nu = config.get("nu", 1.5e-05)
        content = content.replace("#NU#", str(nu))
        
        with open(target_file, "w") as f:
            f.write(content)
        
        self._log(f"Generated: {target_file}")
    
    def run_solver_async(self, solver: str, output_callback: Optional[Callable] = None) -> None:
        """
        Execute the OpenFOAM solver asynchronously.
        
        Args:
            solver: Solver name (e.g., "simpleFoam")
            output_callback: Optional callback function for output messages
        """
        self.output_callback = output_callback
        
        # Start solver in a separate thread
        thread = threading.Thread(
            target=self._run_solver_thread,
            args=(solver,),
            daemon=True
        )
        thread.start()
    
    def _run_solver_thread(self, solver: str) -> None:
        """Execute solver in a thread."""
        try:
            self._log(f"Starting solver: {solver}")
            
            process = subprocess.Popen(
                [solver],
                cwd=str(self.case_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output line by line
            for line in iter(process.stdout.readline, ""):
                if line:
                    self._log(line.rstrip())
            
            process.wait()
            
            if process.returncode == 0:
                self._log("Solver completed successfully!")
            else:
                self._log(f"Solver exited with code: {process.returncode}")
        
        except Exception as e:
            self._log(f"Error running solver: {e}")
    
    def _log(self, message: str) -> None:
        """Log a message, optionally via callback."""
        print(message)
        if self.output_callback:
            self.output_callback(message)
