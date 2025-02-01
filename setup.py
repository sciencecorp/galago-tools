import os
from setuptools import setup
import subprocess
from setuptools.command.build_py import build_py as _build_py
from os.path import join, dirname, realpath
import shutil 


class BuildProtobuf(_build_py):
   def run(self) -> None:
        proto_src = os.path.join(dirname(dirname(realpath(__file__))), "interfaces")
        grpc_interfaces_output_dir = os.path.abspath(join(os.path.dirname(__file__), "grpc_interfaces"))

        os.makedirs(grpc_interfaces_output_dir, exist_ok=True)

        grpc_proto_files = [
            os.path.join(proto_src, "tools/grpc_interfaces", proto_file)
            for proto_file in os.listdir(os.path.join(proto_src, "tools/grpc_interfaces"))
            if proto_file.endswith(".proto")
        ]

        root_proto_files = [
            os.path.join(proto_src, proto_file)
            for proto_file in os.listdir(proto_src)
            if proto_file.endswith(".proto")
        ]

        #Compile the files in the grpc_interfaces folder
        if grpc_proto_files:
            subprocess.run(
                [
                    "python", "-m", "grpc_tools.protoc",
                    "-I" + proto_src,
                    "--python_out=grpc_interfaces/",
                    "--pyi_out=grpc_interfaces/",
                    "--grpc_python_out=grpc_interfaces/",
                    *grpc_proto_files,
                ],
                check=True,
            )

        for file in os.listdir(os.path.join(grpc_interfaces_output_dir,"tools","grpc_interfaces")):
            if file.endswith(".py") or file.endswith(".pyi"):
                shutil.move(os.path.join(grpc_interfaces_output_dir,"tools","grpc_interfaces", file), os.path.join(grpc_interfaces_output_dir, file))
        

        # Compile the root-level .proto files
        if root_proto_files:
            subprocess.run(
                [
                    "python", "-m", "grpc_tools.protoc",
                    "-I" + proto_src,
                    "--python_out=grpc_interfaces/",
                    "--pyi_out=grpc_interfaces/", 
                    "--grpc_python_out=grpc_interfaces/",
                    *root_proto_files,
                ],
                check=True,
            )

        super().run()

def readme() -> str:
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        return open(readme_path).read()
    return ""

def read_requirements(filename:str) -> list[str]:
    requirements_path = os.path.join(os.path.dirname(__file__), filename)
    with open(requirements_path) as f:
        return [line.strip() for line in f
                if line.strip() and not line.startswith('#')]

def find_tool_packages() -> list[str]:
    """Find all packages and subpackages in the current directory"""
    packages = ['tools']
    for root, dirs, files in os.walk('.'):
        if '__init__.py' in files and root != '.':
            # Convert path to package name
            package_path = root.lstrip('./').replace('/', '.')
            print(package_path)
            if package_path:
                packages.append(f'tools.{package_path}')
    packages.append('tools.grpc_interfaces')
    return packages

find_tool_packages()
setup(
    name='galago_tools',
    version='0.9',
    packages=find_tool_packages(),
    package_dir={'tools': '.'},
    license='Apache',
    description='Open Source Lab Orchestration Software',
    long_description=readme(),
    install_requires=read_requirements('requirements.txt'),
    include_package_data=True,
    #package_data={'tools': ['*.dll', "site_logo.png", "favicon.ico"]},
    package_data={'tools': ['*.dll',"site_logo.png","favicon.ico",'grpc_interfaces/*.py']},
    url='https://github.com/sciencecorp/galago-core',
    author='Science Corporation',
    python_requires=">=3.9",
    author_email='',
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'galago-run=tools.cli:launch_all_servers',  
            'galago-stop=tools.cli:stop_all_servers',
            'galago-status=tools.cli:status_all_servers',
            'galago-restart=tools.cli:restart_all_servers',
            'galago-logs=tools.cli:logs_all_servers',
            'galago-run-server=tools.cli:launch_server',
            'galago-proto=tools.cli:generate_protobuf',
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