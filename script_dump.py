# script_dumper.py
import os
from pathlib import Path

def dump_project_scripts():
    """
    Scans the project directory, combines all relevant source code files into
    a single 'script_dump.txt' file, excluding virtual environments, cache
    folders, and itself.
    """
    project_root = Path(__file__).parent
    output_filename = "script_dump.txt"
    script_name = Path(__file__).name

    # Define what to include and what to explicitly exclude
    include_extensions = ['.py', '.txt', '.gitignore']
    exclude_dirs = ['.venv', '__pycache__', '.git', '.vscode', 'saves']
    exclude_files = [script_name, output_filename, 'script_dump.txt']

    print(f"Starting script dump for project at: {project_root}")
    print(f"Output will be saved to: {output_filename}\n")

    all_code = []

    for root, dirs, files in os.walk(project_root):
        # Prevent os.walk from entering excluded folders
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # Process files in a consistent order
        for filename in sorted(files):
            if filename in exclude_files:
                continue

            file_path = Path(root) / filename
            if file_path.suffix in include_extensions:
                # Use a consistent, clean path format
                relative_path = file_path.relative_to(project_root).as_posix()
                print(f"  -> Dumping file: {relative_path}")
                
                # --- THIS IS THE CORRECTED LINE ---
                header = f"FILE: {relative_path}\n"
                all_code.append(header)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        all_code.append(f.read())
                        all_code.append("\n\n") # Ensure two newlines after each file for spacing
                except Exception as e:
                    all_code.append(f"*** ERROR READING FILE: {e} ***\n\n")

    try:
        with open(project_root / output_filename, 'w', encoding='utf-8') as f:
            f.write("".join(all_code))
        print(f"\nSUCCESS: All scripts have been dumped into '{output_filename}'")
    except Exception as e:
        print(f"\nERROR: Could not write to output file. {e}")


if __name__ == "__main__":
    dump_project_scripts()