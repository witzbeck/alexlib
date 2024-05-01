#!/bin/bash

# Define the list of Python versions to manage
versions=("3.12" "3.11" "3.10")
# Define packages and their respective virtual environments with the ability to handle local paths
declare -A packages=(
    ["nb_base"]="ipykernel"
    ["nb_scipy"]="ipykernel scipy"
    ["nb_scikit"]="ipykernel scikit-learn"
    ["nb_pandas"]="ipykernel pandas"
    ["nb_seaborn"]="ipykernel seaborn"
    ["nb_pillow"]="ipykernel pillow"
    ["nb_transformers"]="ipykernel transformers"
    ["alexlib_base"]="$HOME/repos/alexlib"  # Local package path
)

# Directory for virtual environments
venv_dir="$HOME/.venvs"
cd $venv_dir

# Ensure the directory exists
mkdir -p "$venv_dir"

# Loop over each version
for version in "${versions[@]}"; do
    # Activate pyenv version
    eval "$(pyenv init -)"
    pyenv local $version

    # Loop over each package configuration
    for key in "${!packages[@]}"; do
        # Define environment name
        env_name="${version}_${key}"
        # Create virtual environment
        pyenv virtualenv $version "$env_name"
        # Activate virtual environment
        pyenv activate "$env_name"
        # Check if the package path is local and adjust pip install command
        if [[ ${packages[$key]} == $HOME/repos/* ]]; then
            # Install from a local directory
            pip install -e "${packages[$key]}"
        else
            # Install from PyPI
            pip install ${packages[$key]}
        fi
        # Deactivate environment
        pyenv deactivate
        echo "${env_name}[${packages[$key]} installed]"
    done
done
