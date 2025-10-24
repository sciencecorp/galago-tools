import os
from setuptools import setup
import subprocess
from setuptools.command.build_py import build_py as _build_py
import shutil 
import sys 


# Version is now defined in tools/version.py and imported here.
# Scripts that need to extract the version should use:
# grep -oP "__version__ = ['\"]([^'\"]+)" tools/version.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools.version import __version__


base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Use "Console" if you want a console window 


class BuildProtobuf(_build_py):
    def run(self) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Root directory
        proto_src = os.path.join(base_dir, "interfaces")
        grpc_interfaces_output_dir = os.path.join(base_dir, "tools", "grpc_interfaces")  

        os.makedirs(grpc_interfaces_output_dir, exist_ok=True)

        grpc_proto_dir = os.path.join(proto_src, "tools", "grpc_interfaces")
        if not os.path.exists(grpc_proto_dir):
            raise FileNotFoundError(f"Expected proto directory {grpc_proto_dir} not found!")

        grpc_proto_files = [
            os.path.join(grpc_proto_dir, proto_file)
            for proto_file in os.listdir(grpc_proto_dir)
            if proto_file.endswith(".proto")
        ]

        root_proto_files = [
            os.path.join(proto_src, proto_file)
            for proto_file in os.listdir(proto_src)
            if proto_file.endswith(".proto")
        ]

        if grpc_proto_files:
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

        grpc_generated_path = os.path.join(grpc_interfaces_output_dir, "tools", "grpc_interfaces")
        if os.path.exists(grpc_generated_path):
            for file in os.listdir(grpc_generated_path):
                if file.endswith(".py") or file.endswith(".pyi"):
                    shutil.move(
                        os.path.join(grpc_generated_path, file),
                        os.path.join(grpc_interfaces_output_dir, file),
                    )

        if root_proto_files:
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
    version=__version__, # latest version
    packages=find_tool_packages(),
    package_dir={'': '.'},
    license='Apache-2.0',  # Standard SPDX identifier
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
                            'grpc_interfaces/*.py'],
                            # Add static web assets to the root package
                                '': [
                                'index.html',
                                'tool_images/*'
                                ]
                            },
    url='https://github.com/sciencecorp/galago-tools',
    author='Science Corporation',
    python_requires=">=3.9",
    author_email='',
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'galago-tools=tools.cli:main',
            'galago=tools.cli:main',
            'galago-serve=tools.cli:serve',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",  # Standard classifier for Apache
    ],
    cmdclass={
        'build_py': BuildProtobuf
    },
)