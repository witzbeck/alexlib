#!/bin/bash

# Define the list of Python versions to manage
versions=("3.12" "3.11" "3.10")
# Define packages and their respective Docker tags
declare -A packages=(
    ["nb_base"]="ipykernel"
    ["nb_scipy"]="ipykernel scipy"
    ["alexlib_base"]="$HOME/repos/alexlib"
)

# Loop over each version
for version in "${versions[@]}"; do
    # Loop over each package configuration
    for key in "${!packages[@]}"; do
        # Create a requirements.txt file dynamically
        if [[ ${packages[$key]} == $HOME/repos/* ]]; then
            # Local package; assuming setup.py is available for editable installs
            echo "-e ${packages[$key]}" > requirements.txt
        else
            # Remote package from PyPI
            echo ${packages[$key]} > requirements.txt
        fi

        # Define the image tag
        image_tag="python_${version}_${key}"

        # Replace Python version in Dockerfile and build the image
        sed "s/\${PYTHON_VERSION}/${version}/" Dockerfile.template > Dockerfile
        docker build -t ${image_tag} .
        echo "Built Docker image ${image_tag}"

        # Clean up the temporary requirements file
        rm requirements.txt
    done
done
