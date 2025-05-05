import os
from setuptools import setup
import subprocess
from setuptools.command.build_py import build_py as _build_py
import shutil 
import sys 

base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Use "Console" if you want a console window


class BuildProtobuf(_build_py):
    def run(self) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Root directory
        proto_src = os.path.join(base_dir, "interfaces")
        grpc_interfaces_output_dir = os.path.join(base_dir, "tools", "grpc_interfaces")  

        # Create output directory
        os.makedirs(grpc_interfaces_output_dir, exist_ok=True)

        # Check if proto source directory exists
        if not os.path.exists(proto_src):
            print(f"Warning: Proto source directory {proto_src} not found. Skipping proto compilation.")
            super().run()
            return

        grpc_proto_dir = os.path.join(proto_src, "tools", "grpc_interfaces")
        grpc_proto_files = []
        
        # Only process grpc_proto_files if the directory exists
        if os.path.exists(grpc_proto_dir):
            grpc_proto_files = [
                os.path.join(grpc_proto_dir, proto_file)
                for proto_file in os.listdir(grpc_proto_dir)
                if proto_file.endswith(".proto")
            ]
        else:
            print(f"Warning: Proto directory {grpc_proto_dir} not found. Skipping grpc proto compilation.")

        # Get root proto files if they exist
        root_proto_files = []
        if os.path.exists(proto_src):
            root_proto_files = [
                os.path.join(proto_src, proto_file)
                for proto_file in os.listdir(proto_src)
                if proto_file.endswith(".proto")
            ]

        # Process grpc proto files if they exist
        if grpc_proto_files:
            try:
                subprocess.run(
                    [
                        "python", "-m", "grpc_tools.protoc",
                        f"-I{proto_src}",
                        f"--python_out={grpc_interfaces_output_dir}/",
                        f"--pyi_out={grpc_interfaces_output_dir}/",
                        f"--grpc_python_out={grpc_interfaces_output_dir}/",
                        *grpc_proto_files,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to compile grpc proto files: {e}")

        # Move generated files if they exist
        grpc_generated_path = os.path.join(grpc_interfaces_output_dir, "tools", "grpc_interfaces")
        if os.path.exists(grpc_generated_path):
            for file in os.listdir(grpc_generated_path):
                if file.endswith(".py") or file.endswith(".pyi"):
                    try:
                        shutil.move(
                            os.path.join(grpc_generated_path, file),
                            os.path.join(grpc_interfaces_output_dir, file),
                        )
                    except (shutil.Error, OSError) as e:
                        print(f"Warning: Failed to move file {file}: {e}")

        # Process root proto files if they exist
        if root_proto_files:
            try:
                subprocess.run(
                    [
                        "python", "-m", "grpc_tools.protoc",
                        f"-I{proto_src}",
                        f"--python_out={grpc_interfaces_output_dir}/",
                        f"--pyi_out={grpc_interfaces_output_dir}/",
                        f"--grpc_python_out={grpc_interfaces_output_dir}/",
                        *root_proto_files,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to compile root proto files: {e}")

        # Create __init__.py in grpc_interfaces directory if it doesn't exist
        init_py_path = os.path.join(grpc_interfaces_output_dir, "__init__.py")
        if not os.path.exists(init_py_path):
            with open(init_py_path, 'w') as f:
                f.write("# Auto-generated __init__.py for grpc_interfaces\n")

        super().run()

def readme() -> str:
    """
    Use PYPI.md for PyPI documentation if it exists,
    otherwise fall back to README.md
    """
    pypi_path = os.path.join(os.path.dirname(__file__), "PYPI.md")
    if os.path.exists(pypi_path):
        return open(pypi_path).read()
    
    # Fallback to README.md
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        return open(readme_path).read()
    return ""

def read_requirements(filename:str) -> list[str]:
    requirements_path = os.path.join(os.path.dirname(__file__), filename)
    print(requirements_path)
    with open(requirements_path) as f:
        return [line.strip() for line in f
                if line.strip() and not line.startswith('#')]

def find_tool_packages() -> list[str]:
    """Find all packages and subpackages in the current directory"""
    packages = []
    for root, dirs, files in os.walk('tools'):  # Only look inside `tools/`
        if '__init__.py' in files:
            package_path = root.replace('/', '.')
            print(f"Detected package: {package_path}")
            packages.append(package_path)

    # Ensure grpc_interfaces is included if it exists
    if os.path.exists("tools/grpc_interfaces") and "__init__.py" in os.listdir("tools/grpc_interfaces"):
        packages.append("tools.grpc_interfaces")

    return packages

setup(
    name='galago-tools',
    version='0.9',
    packages=find_tool_packages(),
    package_dir={'': '.'},
    license='Apache',
    description='Open Source Lab Automation GRPC Library',
    long_description=readme(),
    install_requires=read_requirements('requirements.txt'),
    include_package_data=True,
    package_data={'tools': ["site_logo.png",
                            'vcode/deps/*.dll',
                            'plateloc/deps/*.dll',
                            'vspin/deps/*.dll',
                            'hig_centrifuge/deps/*.dll',
                            'bravo/deps/*.dll',
                            'minihub/deps/*.dll',
                            "favicon.ico",
                            'grpc_interfaces/*.py']},
    url='https://github.com/sciencecorp/galago-tools',
    author='Science Corporation',
    python_requires=">=3.9",
    author_email='',
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'galago-tools=tools.cli:main', 
            'galago-tools-serve=tools.cli:serve',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License", 
        "Operating System :: OS Independent",
    ],
    cmdclass={
        'build_py': BuildProtobuf
    },
)