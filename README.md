# Galago Tools

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/)
[![GitHub Issues](https://img.shields.io/github/issues/sciencecorp/galago-tools)](https://github.com/sciencecorp/galago-tools/issues)

**Open Source Lab Automation gRPC Library**

Galago Tools is a comprehensive Python library for lab automation that provides standardized gRPC interfaces for a wide variety of laboratory instruments. Each tool runs as a gRPC server, enabling consistent command execution across different devices and platforms.

## 🚀 Features

- **Standardized Interface**: Uniform gRPC API across all supported instruments
- **Extensive Device Support**: 20+ instrument types including pipetting systems, centrifuges, readers, and more
- **32-bit Compatibility**: Special support for legacy Windows instruments requiring 32-bit Python
- **Production Ready**: Used in real laboratory environments


## 📦 Installation

### Option 1: Fork the Repository (For Contributors)


## 📋 Requirements

- **Python**: 3.9
- **Operating System**: Windows, macOS, Linux

If you plan to contribute or customize Galago Tools, start by forking the repository:

1. **Fork on GitHub**: Click the "Fork" button at the top right of the [repository page](https://github.com/sciencecorp/galago-tools), or use this direct link:
   
   **[Fork Galago Tools →](https://github.com/sciencecorp/galago-tools/fork)**

2. **Clone your fork** (replace `your-username` with your GitHub username):
```bash
   git clone https://github.com/your-username/galago-tools.git
   cd galago-tools
```

3. **Add upstream remote** (to keep your fork updated):
```bash
   git remote add upstream https://github.com/sciencecorp/galago-tools.git
```

4. **Install in dev mode and dev deps** 
```bash 
   pip install -e .
   pip install -r requirements-dev.txt
```

5. **Build proto files**
```bash 
bin/make proto
```

5. **Launch Galago Tools Manager** (The server used by [Galago Core](https://github.com/sciencecorp/galago-core))
```bash 
   galago 
```

## Option 2: Install via pip  directly. 

```bash
#Install latest distribution
pip install galago-tools

#Launch tools manager
galago 
```

## Option3: Windows Installer 

We also provide a Windows Installer that does all this for you. [Download Here](https://galago.bio/assets/installer/Galago%20Installer_x86.exe). A launch icon will automatically be created in the desktop. 


## 32-bit Windows Environment

Many legacy lab instruments require 32-bit Python on Windows. If you are doing local development (Option 1) and are using any of the Agilent tools you need to download python 32-bits or set up a 32-bit environment using conda:


```bash
# Set environment variables for 32-bit
set CONDA_FORCE_32BIT=1
set CONDA_SUBDIR=win-32

# Create and activate environment
conda create -n galago-tools python=3.9
conda activate galago-tools

# Install galago-tools
pip install galago-tools
```


## Using the CLI
```bash

## Starting the tools server manager. 
galago 

# List available tools
galago --list

# Start a specific tool server
galago-serve --port=50010 --tool=opentrons2

# Get tool information
galago --info opentrons2
```

## Building Distribution

Python distributions are automatically published via github workflows. See [RELEASE](RELEASE.md) for more information.

### Running Tests
```bash
# Run all tests
bin/make test
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. **[Fork Galago Tools →](https://github.com/sciencecorp/galago-tools/fork)**
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🏢 About Science Corporation

Science Corporation develops advanced technologies to understand and engineer the brain.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/sciencecorp/galago-tools/issues)
- **Documentation**: [Full Documentation](https://galago.bio/)