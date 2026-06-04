"""
Mesh utilities for STL import, surface splitting, and PyVista visualization.
Handles auto-segmentation of STL files into distinct clickable patches.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import pyvista as pv
from pyvista import Plotter


class MeshManager:
    """Manages STL import, surface splitting, and patch tracking."""
    
    def __init__(self):
        """Initialize the mesh manager."""
        self.original_mesh = None
        self.separated_surfaces = None
        self.patch_assignments = {}  # {patch_name: boundary_type}
        self.patch_colors = {}  # {patch_name: color}
        self.patch_selection_callbacks = []
    
    def load_stl(self, file_path: Path) -> bool:
        """
        Load an STL file and automatically split it into surfaces.
        
        Args:
            file_path: Path to the STL file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load the raw STL mesh
            self.original_mesh = pv.read(str(file_path))
            
            # Extract surface and split based on connectivity
            # This identifies distinct patches automatically
            self.separated_surfaces = self.original_mesh.extract_surface().split_bodies()
            
            # Initialize patch tracking
            for i, patch in enumerate(self.separated_surfaces):
                patch_name = f"patch_{i}"
                self.patch_assignments[patch_name] = "unassigned"
                self.patch_colors[patch_name] = (0.5, 0.5, 0.5)  # Default gray
            
            return True
        except Exception as e:
            print(f"Error loading STL file: {e}")
            return False
    
    def get_patches(self) -> Dict[str, str]:
        """
        Get all detected patches and their current assignments.
        
        Returns:
            Dictionary mapping patch names to boundary types
        """
        return self.patch_assignments.copy()
    
    def assign_patch(self, patch_name: str, boundary_type: str) -> None:
        """
        Assign a boundary type to a patch.
        
        Args:
            patch_name: Name of the patch
            boundary_type: Type of boundary (Inlet, Outlet, Wall, Symmetry)
        """
        if patch_name in self.patch_assignments:
            self.patch_assignments[patch_name] = boundary_type
            # Update color based on boundary type
            self._update_patch_color(patch_name, boundary_type)
    
    def _update_patch_color(self, patch_name: str, boundary_type: str) -> None:
        """Update patch color based on boundary type."""
        color_map = {
            "Inlet": (0.0, 0.0, 1.0),      # Blue
            "Outlet": (1.0, 0.0, 0.0),     # Red
            "Wall": (0.5, 0.5, 0.5),       # Gray
            "Symmetry": (0.0, 1.0, 0.0),   # Green
            "unassigned": (0.8, 0.8, 0.8)  # Light gray
        }
        self.patch_colors[patch_name] = color_map.get(boundary_type, (0.5, 0.5, 0.5))
    
    def create_visualization(self, picker_callback=None):
        """
        Create an interactive PyVista visualization with picking support.
        
        Args:
            picker_callback: Callback function when a patch is clicked
            
        Returns:
            PyVista Plotter object ready to display
        """
        plotter = Plotter(lighting='three lights')
        
        if self.separated_surfaces is None:
            return plotter
        
        # Add each patch with its assigned color
        for i, patch in enumerate(self.separated_surfaces):
            patch_name = f"patch_{i}"
            color = self.patch_colors.get(patch_name, (0.5, 0.5, 0.5))
            
            # Add the patch to the visualization
            plotter.add_mesh(
                patch,
                color=color,
                name=patch_name,
                show_edges=True,
                opacity=0.9
            )
        
        # Enable picking with left-click
        if picker_callback:
            plotter.track_click_position(
                callback=self._handle_pick(picker_callback, plotter),
                side="left"
            )
        
        plotter.view_isometric()
        return plotter
    
    def _handle_pick(self, callback, plotter):
        """
        Create a click handler that identifies which patch was selected.
        
        Args:
            callback: User callback function(patch_name, coordinates)
            plotter: PyVista Plotter instance
            
        Returns:
            Handler function for click events
        """
        def pick_handler(click_pos):
            """Handle mesh picking."""
            if self.separated_surfaces is None:
                return
            
            # Find which patch was clicked by ray casting
            for i, patch in enumerate(self.separated_surfaces):
                selection = patch.pick(click_pos, tolerance=1e-6)
                if selection is not None and selection.n_cells > 0:
                    patch_name = f"patch_{i}"
                    callback(patch_name, click_pos)
                    break
        
        return pick_handler
    
    def get_mesh_bounds(self) -> Tuple[Tuple, Tuple]:
        """
        Get the bounding box of the mesh.
        
        Returns:
            Tuple of (min_coords, max_coords)
        """
        if self.original_mesh is None:
            return None
        
        bounds = self.original_mesh.bounds
        return (bounds[0:3], bounds[3:6])
    
    def export_patch_info(self) -> Dict[str, str]:
        """
        Export current patch assignments for foam_utils to use.
        
        Returns:
            Dictionary ready for OpenFOAM boundary condition generation
        """
        return {
            name: assignment 
            for name, assignment in self.patch_assignments.items()
            if assignment != "unassigned"
        }
