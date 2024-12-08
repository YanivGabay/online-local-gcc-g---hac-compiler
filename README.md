# Online Local GCC/G++ HAC Compiler

This project is designed for students at Hadassah Academic College who need to work in a CentOS 8 (or Rocky Linux) environment using GCC 8.5.0-22. Often, students face difficulties or discomfort when connecting to the college servers remotely. This project provides a solution by allowing students to compile and test their code in an environment identical to the college's setup, locally on their own machines.

## Features

- **Docker-based Environment**: Uses Docker to create an exact replica of the college's environment.
- **Rich Terminal Script**: Utilizes the Rich library to provide an interactive terminal experience.
- **Compilation and Testing**: Compile your programs and run Valgrind to check for memory leaks.
- **Ease of Use**: Download an executable file to avoid dependency installations, or clone the repository and run the Python script directly.

## Requirements

- **Docker Desktop**: Ensure Docker Desktop is installed on your Windows machine.
- **If running the script locally**:
  - **Python 3.6+**: Ensure Python 3.6 or higher is installed on your machine.
  - **Venv**: Install the `venv` module by running `python -m venv venv` in the project directory.
  - **Instal -r requirements.txt**: Install the required dependencies by running `pip install -r requirements.txt`.

  
## Usage

1. **Download the Executable**: If you prefer not to install dependencies, download the provided executable file.
2. **Clone the Repository**: Alternatively, clone the repository and run the Python script yourself.

This project aims to streamline the coding and testing process for students, providing a seamless and efficient way to ensure their code works correctly in the required environment.
