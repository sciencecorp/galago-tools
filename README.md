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

### Standard Installation

```bash
pip install galago-tools
```

### Development Installation

For development or the latest features:

```bash
# Clone the repository
git clone https://github.com/sciencecorp/galago-tools.git
cd galago-tools

# Install in development mode
pip install -e .
```

### 32-bit Windows Environment

Many legacy lab instruments require 32-bit Python on Windows. Set up a 32-bit environment using conda:

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

## 🔧 Quick Start

### Starting the Tools Server Manager

```bash 
galago 
```

### Using the CLI

```bash
# List available tools
galago --list

# Start a specific tool server
galago-serve --port=50010 --tool=opentrons2

# Get tool information
galago --info opentrons2
```

``

## 📋 Requirements

- **Python**: 3.9
- **Operating System**: Windows, macOS, Linux
- **Dependencies**: Listed in `requirements.txt`

## 🏗️ Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/sciencecorp/galago-tools.git
cd galago-tools

# Install galago indevelopment moode
pip install -e .
pip install -r requirements-dev.txt

# Generate protobuf interfaces (if needed)
bin/make proto

#Clear generated protobuf
bin/make clean_proto

#Run tools manager. 
bin/make run 

#or alternatively cli command 
galago

```


### Building Distribution

Python distributions are automatically published via github workflows. See see [RELEASE](RELEASE.md) for more information.

### Running Tests

```bash
# Run all tests
bin/make test
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
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
