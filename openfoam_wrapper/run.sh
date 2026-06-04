#!/bin/bash
# OpenFOAM GUI Wrapper - Launch Script

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if dependencies are installed
python3 -c "import PyQt6; import pyvista" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Dependencies not found. Installing..."
    pip install -r requirements.txt
fi

# Check if OpenFOAM is installed
which simpleFoam > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "WARNING: OpenFOAM not found in PATH"
    echo "Please ensure OpenFOAM is installed and source the bashrc file:"
    echo "  source /opt/openfoam*/etc/bashrc"
fi

# Launch the application
echo "Launching OpenFOAM GUI Wrapper..."
python3 main.py
