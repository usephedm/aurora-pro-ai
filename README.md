# 🤖 Aurora Pro AI

Production-grade AI Operating System with multi-agent orchestration, browser automation, local LLM inference, and comprehensive self-healing capabilities.

[![CI/CD Pipeline](https://github.com/usephedm/aurora-pro-ai/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/usephedm/aurora-pro-ai/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

- **Multi-Agent Orchestration**: Coordinate multiple AI agents with sequential, parallel, or pipeline execution modes
- **FastAPI Backend**: High-performance async REST API with automatic documentation
- **Streamlit GUI**: Interactive web interface for agent management and task execution
- **Local LLM Support**: Ollama integration for privacy-focused local inference
- **Cloud LLM Support**: OpenAI, HuggingFace integration for powerful cloud models
- **Redis Caching**: Fast in-memory caching for improved performance
- **SQLite Database**: Lightweight persistent storage for agents, tasks, and metrics
- **Security Hardening**: JWT authentication, input sanitization, bcrypt password hashing
- **Health Monitoring**: Kubernetes-ready health probes and Prometheus metrics
- **Plugin System**: Extensible architecture for custom functionality
- **Browser Automation**: Playwright integration for web scraping and automation
- **Production-Ready**: Docker deployment with comprehensive logging and monitoring

## 📋 Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (for local development)

## 🏗️ Architecture

```
aurora-pro-ai/
├── src/                    # Core source code
│   ├── api/               # FastAPI application
│   │   ├── main.py        # API entry point
│   │   └── routes/        # API endpoints
│   ├── agents/            # Multi-agent system
│   │   ├── base_agent.py  # Base agent class
│   │   ├── llm_agent.py   # LLM agent implementation
│   │   └── orchestrator.py # Agent orchestration
│   ├── cache/             # Redis cache management
│   ├── core/              # Core utilities
│   │   ├── config.py      # Configuration management
│   │   ├── logging.py     # Structured logging
│   │   └── security.py    # Security utilities
│   ├── db/                # Database models and connection
│   ├── gui/               # Streamlit GUI
│   └── utils/             # Utility modules
├── config/                # Configuration templates
├── docker/                # Docker configurations
├── docs/                  # Documentation
├── scripts/               # Deployment scripts
├── tests/                 # Test suite
├── plugins/               # Plugin directory
├── .github/workflows/     # CI/CD pipelines
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Service orchestration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
└── deploy.sh             # One-click deployment script
```

## 🚀 Quick Start

### One-Click Deployment

```bash
# Clone the repository
git clone https://github.com/usephedm/aurora-pro-ai.git
cd aurora-pro-ai

# Run the deployment script
./deploy.sh
```

The script will:
1. Check prerequisites (Docker, Docker Compose)
2. Create `.env` file from template
3. Build Docker images
4. Start all services
5. Wait for services to be healthy
6. Display access URLs

### Manual Deployment

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Build and start services
docker-compose up -d

# 3. Check service health
docker-compose ps
```

## 🌐 Access Services

After deployment, access the following services:

- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Streamlit GUI**: http://localhost:8501
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Ollama**: http://localhost:11434

## 📚 Usage Examples

### Using the API

```bash
# Create an agent
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-agent",
    "agent_type": "llm",
    "model_name": "llama2",
    "provider": "ollama"
  }'

# Execute a task
curl -X POST http://localhost:8000/api/v1/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "my-agent",
    "prompt": "Hello, what can you do?"
  }'

# List agents
curl http://localhost:8000/api/v1/agents/
```

### Using the GUI

1. Navigate to http://localhost:8501
2. Go to "Agents" page
3. Create a new agent
4. Go to "Tasks" page
5. Execute tasks with your agent

### Using Python SDK

```python
import requests

API_URL = "http://localhost:8000"

# Create agent
response = requests.post(
    f"{API_URL}/api/v1/agents/",
    json={
        "name": "python-agent",
        "agent_type": "llm",
        "model_name": "llama2",
        "provider": "ollama"
    }
)

# Execute task
response = requests.post(
    f"{API_URL}/api/v1/tasks/execute",
    json={
        "agent": "python-agent",
        "prompt": "Explain quantum computing"
    }
)

print(response.json())
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
APP_NAME=aurora-pro-ai
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=sqlite:///./data/aurora.db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# LLM Configuration
OLLAMA_BASE_URL=http://ollama:11434
OPENAI_API_KEY=your-key-here
DEFAULT_MODEL=llama2

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Multi-Agent
MAX_AGENTS=10
ORCHESTRATION_MODE=sequential
```

See `.env.example` for all available options.

## 🧪 Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_orchestrator.py -v
```

## 🔌 Plugin Development

Create custom plugins by extending the `BasePlugin` class:

```python
from src.utils.plugins import BasePlugin

class Plugin(BasePlugin):
    def __init__(self):
        super().__init__(
            name="my_plugin",
            version="1.0.0",
            description="My custom plugin"
        )
    
    def initialize(self, config):
        # Initialize plugin
        return True
    
    def execute(self, *args, **kwargs):
        # Execute plugin functionality
        return "Result"
    
    def cleanup(self):
        # Cleanup resources
        pass
```

Place your plugin in `plugins/my_plugin/__init__.py` and enable it via the API or configuration.

## 📊 Monitoring

### Prometheus Metrics

Access Prometheus at http://localhost:9090 to view:
- Request counts and durations
- Agent execution metrics
- System health metrics

### Grafana Dashboards

Access Grafana at http://localhost:3000 (admin/admin) for:
- Visual dashboards
- Custom alerts
- Metric exploration

## 🔒 Security

Aurora Pro AI implements several security measures:

- **JWT Authentication**: Token-based API authentication
- **Password Hashing**: Bcrypt for secure password storage
- **Input Sanitization**: Protection against injection attacks
- **CORS Configuration**: Controlled cross-origin access
- **Rate Limiting**: Protection against abuse
- **Security Headers**: HTTP security headers

## 🛠️ Development

```bash
# Clone repository
git clone https://github.com/usephedm/aurora-pro-ai.git
cd aurora-pro-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run API locally
python -m uvicorn src.api.main:app --reload

# Run GUI locally
streamlit run src/gui/app.py

# Run tests
pytest tests/ -v

# Format code
black src/

# Lint code
flake8 src/
```

## 📖 Documentation

- [API Documentation](docs/API.md)
- [Interactive API Docs](http://localhost:8000/docs)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Plugin Development](docs/PLUGINS.md)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Streamlit for the interactive GUI framework
- Ollama for local LLM support
- The open-source community

## 📧 Support

For issues and questions:
- GitHub Issues: https://github.com/usephedm/aurora-pro-ai/issues
- Documentation: [docs/](docs/)

## 🗺️ Roadmap

- [ ] Advanced agent types (vision, audio)
- [ ] Distributed orchestration
- [ ] WebSocket support for real-time updates
- [ ] Advanced monitoring and alerting
- [ ] Kubernetes deployment templates
- [ ] More LLM provider integrations

---

Made with ❤️ by the Aurora Pro AI team
