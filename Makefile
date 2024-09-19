.PHONY: venv clean_venv install_requirements
# create venv with:
# make venv

# Define the virtual environment directory
VENV_DIR = venv

# Target to remove the existing virtual environment
clean_venv:
	rm -rf $(VENV_DIR)

# Target to create a new virtual environment and install requirements
venv: clean_venv
	python -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && pip install --upgrade pip
	$(MAKE) install_requirements

# Target to install dependencies from requirements.txt
install_requirements:
	. $(VENV_DIR)/bin/activate && pip install -r requirements.txt
