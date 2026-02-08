# RapidKit Core

Open Source Code Generation Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

- Clean Architecture FastAPI applications
- Modular structure with dependency injection
- Comprehensive testing setup
- Docker-ready deployments
- CLI tools for rapid development
- **Free tier with community support**

## 📦 Installation

```bash
pip install rapidkit-core
```

## 🛠️ Usage

```bash
rapidkit create project
cd myapp
rapidkit info
```

## 🐳 Docker Support

RapidKit includes comprehensive Docker support:

### Quick Start with Docker

```bash
# Create and run with Docker
rapidkit create myapp
cd myapp
docker-compose up --build

# Access at http://localhost:8000
```

### Docker Commands

```bash
# Development
docker-compose up --build      # Build and run with hot reload
docker-compose up -d           # Run in background
docker-compose logs -f         # View logs

# Production
docker-compose -f docker-compose.prod.yml up -d  # Production deployment

# Maintenance
docker-compose down            # Stop services
docker-compose down -v         # Remove volumes
```

## 📚 Documentation

For detailed documentation, visit our [docs](https://github.com/getrapidkit/rapidkit-core).

## 🤝 Contributing

We welcome contributions! Please see our
[contributing guide](https://github.com/getrapidkit/rapidkit-core/blob/main/CONTRIBUTING.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../../../LICENSE) file for
details.

## 🌟 Community

- Join our [Discord](https://discord.gg/rapidkit) for community support
- Follow us on [Twitter](https://twitter.com/getrapidkit) for updates
- Check out our [GitHub Discussions](https://github.com/getrapidkit/rapidkit-core/discussions) for
  Q&A
