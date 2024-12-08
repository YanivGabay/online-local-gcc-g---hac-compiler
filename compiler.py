#!/usr/bin/env python3

import subprocess
import shutil
import os
import sys
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box
from pathlib import Path

# Initialize Rich console
console = Console()

# Configuration Constants
DOCKER_IMAGE = 'yaniv242/hacenv'  # Replace with your actual Docker image name
WORKDIR_IN_CONTAINER = '/workspace'
EXECUTABLE_NAME = 'program'  # Default executable name

# Global variable to keep track of the current compilation context
current_context = {
    'source_dir': os.getcwd(),
    'source_file': None,
    'executable_path': None,
    'compiler': 'gcc'  # Default compiler
}

def check_docker_installed():
    """Check if Docker is installed."""
    if not shutil.which('docker'):
        console.print("[bold red]Error:[/bold red] Docker is not installed or not found in PATH.")
        sys.exit(1)

def check_docker_running():
    """Check if Docker daemon is running."""
    try:
        subprocess.run(['docker', 'info'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        console.print("[bold red]Error:[/bold red] Docker daemon is not running. Please start Docker Desktop.")
        sys.exit(1)

def pull_docker_image(image_name):
    """Pull the Docker image if not available locally."""
    try:
        subprocess.run(['docker', 'image', 'inspect', image_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        console.print(f"[green]Docker image '{image_name}' is already available locally.[/green]")
    except subprocess.CalledProcessError:
        console.print(f"[yellow]Docker image '{image_name}' not found locally. Pulling from Docker Hub...[/yellow]")
        try:
            pull_process = subprocess.Popen(['docker', 'pull', image_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            for line in pull_process.stdout:
                console.print(line.strip())
            pull_process.wait()
            if pull_process.returncode == 0:
                console.print(f"[green]Successfully pulled '{image_name}'.[/green]")
            else:
                console.print(f"[bold red]Error:[/bold red] Failed to pull Docker image '{image_name}'.")
                sys.exit(1)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] Failed to pull Docker image '{image_name}'. Exception: {e}")
            sys.exit(1)

def get_c_files(directory):
    """Retrieve all .c and .cpp files in the specified directory."""
    try:
        return [file for file in os.listdir(directory) if file.endswith('.c') or file.endswith('.cpp')]
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] Directory '{directory}' does not exist.")
        return []

def compile_program(source_file, compile_flags='', compiler='gcc'):
    """Compile the C/C++ program inside Docker."""
    absolute_path = os.path.abspath(source_file)
    source_dir = os.path.dirname(absolute_path)
    source_filename = os.path.basename(absolute_path)

    docker_image = DOCKER_IMAGE

    docker_cmd = [
        'docker', 'run', '--rm',
        '-v', f'{source_dir}:{WORKDIR_IN_CONTAINER}',
        '-w', WORKDIR_IN_CONTAINER,
        docker_image,
        compiler, compile_flags, '-o', EXECUTABLE_NAME, source_filename
    ]

    console.print(f"[blue]Compiling '{source_filename}' with flags '{compile_flags}' using {compiler}...[/blue]")
    try:
        result = subprocess.run(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to execute Docker command: {e}")
        sys.exit(1)

    # Update current context
    current_context['source_dir'] = source_dir
    current_context['source_file'] = source_file
    current_context['executable_path'] = os.path.join(source_dir, EXECUTABLE_NAME)
    current_context['compiler'] = compiler

    return result

def run_program(program_args, source_dir):
    """Run the compiled program inside Docker."""
    executable_path = f'{WORKDIR_IN_CONTAINER}/{EXECUTABLE_NAME}'

    # Prepare arguments
    args = [f'./{EXECUTABLE_NAME}'] + program_args

    docker_cmd = [
        'docker', 'run', '--rm',
        '-v', f'{source_dir}:{WORKDIR_IN_CONTAINER}',
        '-w', WORKDIR_IN_CONTAINER,
        DOCKER_IMAGE,
    ] + args

    console.print(f"[blue]Running the program with arguments: {' '.join(program_args)}[/blue]")
    try:
        result = subprocess.run(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to execute Docker command: {e}")
        sys.exit(1)

    return result

def run_valgrind(program_args, source_dir):
    """Run Valgrind on the compiled program inside Docker."""
    executable_path = f'{WORKDIR_IN_CONTAINER}/{EXECUTABLE_NAME}'

    docker_cmd = [
        'docker', 'run', '--rm',
        '-v', f'{source_dir}:{WORKDIR_IN_CONTAINER}',
        '-w', WORKDIR_IN_CONTAINER,
        DOCKER_IMAGE,
        'valgrind', '--leak-check=full', '--error-exitcode=1', f'./{EXECUTABLE_NAME}'
    ] + program_args

    console.print(f"[blue]Running Valgrind with arguments: {' '.join(program_args)}[/blue]")
    try:
        result = subprocess.run(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to execute Valgrind: {e}")
        sys.exit(1)

    return result

def display_compile_results(result):
    """Display compilation warnings and errors."""
    if result.stdout:
        console.print("[bold cyan]Compilation Standard Output:[/bold cyan]")
        console.print(result.stdout)
    if result.stderr:
        console.print("[bold yellow]Compilation Warnings/Errors:[/bold yellow]")
        console.print(result.stderr)
    if result.returncode != 0:
        console.print("[bold red]Compilation failed.[/bold red]")
    else:
        console.print("[bold green]Compilation succeeded.[/bold green]")

def display_run_results(result):
    """Display program output and errors."""
    if result.stdout:
        console.print("[bold green]Program Output:[/bold green]")
        console.print(result.stdout)
    if result.stderr:
        console.print("[bold red]Program Errors:[/bold red]")
        console.print(result.stderr)
    if result.returncode != 0:
        console.print(f"[bold red]Program exited with return code {result.returncode}.[/bold red]")
    else:
        console.print("[bold green]Program executed successfully.[/bold green]")

def display_valgrind_results(result):
    """Display Valgrind output."""
    if result.returncode == 0:
        console.print("[bold green]Valgrind: No memory leaks or errors detected.[/bold green]")
    else:
        console.print("[bold red]Valgrind: Memory leaks or errors detected![/bold red]")
        if result.stderr:
            console.print("[bold red]Valgrind Errors:[/bold red]")
            console.print(result.stderr)
        else:
            console.print("[bold red]Valgrind detected errors, but no error messages were captured.[/bold red]")

def select_source_file():
    """Allow the user to select a source file from the current directory."""
    c_files = get_c_files(current_context['source_dir'])
    if not c_files:
        console.print("[bold red]No C/C++ source files found in the current directory.[/bold red]")
        return None

    table = Table(show_header=True, header_style="bold magenta", box=box.MINIMAL_DOUBLE_HEAD)
    table.add_column("No.", style="dim", width=6)
    table.add_column("Filename", min_width=20)

    for idx, file in enumerate(c_files, 1):
        table.add_row(str(idx), file)

    console.print(table)

    choices = [str(i) for i in range(1, len(c_files)+1)]
    choice = Prompt.ask(f"Select a file to compile [1-{len(c_files)}]", choices=choices)

    selected_file = c_files[int(choice)-1]
    return os.path.join(current_context['source_dir'], selected_file)

def interactive_menu():
    """Display an interactive menu to the user."""
    while True:
        table = Table(title="C/C++ Compiler Menu", box=box.ROUNDED, show_header=False, header_style="bold magenta")
        table.add_column("Option", style="dim", width=6)
        table.add_column("Description", min_width=20)

        table.add_row("1", "List C/C++ source files")
        table.add_row("2", "Compile a C/C++ program")
        table.add_row("3", "Run the compiled program")
        table.add_row("4", "Run Valgrind on the program")
        table.add_row("5", "Change Source Directory")
        table.add_row("6", "Exit")

        console.print(table)

        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6"], default="6")

        if choice == "1":
            # List C/C++ source files from the current context
            c_files = get_c_files(current_context['source_dir'])
            console.print(f"[bold green]C/C++ Source Files in '{current_context['source_dir']}':[/bold green]")

            if not c_files:
                console.print("[bold red]No C/C++ source files found in the current directory.[/bold red]")
            else:
                table_files = Table(show_header=True, header_style="bold magenta", box=box.MINIMAL_DOUBLE_HEAD)
                table_files.add_column("No.", style="dim", width=6)
                table_files.add_column("Filename", min_width=20)

                for idx, file in enumerate(c_files, 1):
                    table_files.add_row(str(idx), file)

                console.print(table_files)

        elif choice == "2":
            # Compile a C/C++ program
            selected_file = select_source_file()
            if not selected_file:
                continue

            # Determine the compiler based on file extension
            if selected_file.endswith('.c'):
                compiler = 'gcc'
            elif selected_file.endswith('.cpp'):
                compiler = 'g++'
            else:
                console.print("[bold red]Error:[/bold red] Unsupported file extension.")
                continue

            # Optional: Get compilation flags
            compile_flags = Prompt.ask("Enter compilation flags (default: -Wall)", default="-Wall")

            # Compile the program
            compile_result = compile_program(selected_file, compile_flags, compiler)
            display_compile_results(compile_result)

        elif choice == "3":
            # Run the compiled program
            if not current_context['executable_path'] or not os.path.isfile(current_context['executable_path']):
                console.print("[bold red]Executable not found. Please compile a program first.[/bold red]")
                continue

            # Prompt for program arguments
            args_input = Prompt.ask("Enter arguments to pass to the program (separated by space)", default="")
            program_args = args_input.split() if args_input else []

            # Run the program
            run_result = run_program(program_args, current_context['source_dir'])
            display_run_results(run_result)

        elif choice == "4":
            # Run Valgrind on the program
            if not current_context['executable_path'] or not os.path.isfile(current_context['executable_path']):
                console.print("[bold red]Executable not found. Please compile a program first.[/bold red]")
                continue

            # Prompt for Valgrind arguments (e.g., program arguments)
            valgrind_args_input = Prompt.ask("Enter arguments to pass to Valgrind (separated by space)", default="")
            valgrind_args = valgrind_args_input.split() if valgrind_args_input else []

            # Run Valgrind
            valgrind_result = run_valgrind(valgrind_args, current_context['source_dir'])
            display_valgrind_results(valgrind_result)

        elif choice == "5":
            # Change Source Directory
            new_directory = Prompt.ask("Enter the new source directory path", default=os.getcwd())
            if not os.path.isdir(new_directory):
                console.print(f"[bold red]Error:[/bold red] '{new_directory}' is not a valid directory.")
                continue
            current_context['source_dir'] = os.path.abspath(new_directory)
            current_context['source_file'] = None
            current_context['executable_path'] = None
            console.print(f"[bold green]Source directory changed to '{new_directory}'.[/bold green]")

        elif choice == "6":
            # Exit the script
            console.print("[bold blue]Goodbye![/bold blue]")
            sys.exit(0)

        else:
            console.print("[bold red]Invalid option. Please choose a valid option.[/bold red]")

def main():
    # Check Docker installation and status
    check_docker_installed()
    check_docker_running()
    # Pull Docker image
    pull_docker_image(DOCKER_IMAGE)

    # Start interactive menu
    interactive_menu()

if __name__ == "__main__":
    main()
