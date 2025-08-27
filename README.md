# Web3Builder

## Project Overview

Web3Builder is an AI-powered platform that transforms natural language descriptions into complete Web3 applications. Built with modern technologies, it combines the power of artificial intelligence with blockchain development to democratize Web3 app creation.

### Features

- **AI-Powered Generation**: Convert natural language prompts into fully functional Web3 applications
- **Advanced Language Processing**: Comprehensive text analysis for sentiment analysis, keyword extraction, and entity linking
- **Multi-Chain Support**: Deploy on Ethereum, Polygon, BSC, and other popular blockchains
- **No-Code Interface**: Build complex dApps without writing a single line of code
- **Smart Contract Generation**: Automatically generate, test, and deploy smart contracts
- **Intelligent Document Analysis**: Process and analyze documents with advanced NLP capabilities

- **Modern UI/UX**: Beautiful, responsive interface built with Next.js and Tailwind CSS
- **Real-time Development**: Live preview and instant feedback during the building process

### Technologies Used

**Frontend:**
- Next.js 15 with TypeScript
- Tailwind CSS for styling
- Framer Motion for animations
- React Hook Form with Zod validation
- Lucide React icons

**Backend:**
- FastAPI (Python)
- LangChain for AI agent orchestration
- Multiple LLM providers (OpenAI, DeepSeek, Gemini)
- Natural Language Processing (spaCy, NLTK, scikit-learn)
- Graph-based language modeling with NetworkX
- Web3 integration libraries

**Infrastructure:**
- Docker & Docker Compose
- Vercel deployment ready
- Environment-based configuration

## Setup Instructions

### Local Environment

#### Prerequisites

Before running the application locally, ensure you have the following installed:

- **Node.js** (v18 or higher) - [Download here](https://nodejs.org/)
- **npm** or **yarn** package manager
- **Python** (v3.11 or higher) - [Download here](https://python.org/)
- **pip** package manager for Python
- **Git** for version control

#### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Vizuara_CapstoneProject
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and configuration
   ```

5. **Run the FastAPI backend:**
   ```bash
   python main.py
   # Or using uvicorn directly:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The backend will be available at `http://localhost:8000`
   API documentation: `http://localhost:8000/docs`

#### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

   The frontend will be available at `http://localhost:3000`

4. **Build for production:**
   ```bash
   npm run build
   npm run start
   # or
   yarn build
   yarn start
   ```

### Docker Setup

#### Prerequisites

- **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** - Usually included with Docker Desktop

#### Development Environment

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Vizuara_CapstoneProject
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and configuration
   ```

3. **Build and run development containers:**
   ```bash
   docker compose --profile dev up --build
   ```

   This will start both services with hot reload enabled:
   - Frontend: `http://localhost:3000`
   - Backend: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`

4. **Run in detached mode:**
   ```bash
   docker compose --profile dev up --build -d
   ```

5. **Stop the services:**
   ```bash
   docker compose --profile dev down
   ```

#### Production Environment

1. **Build and run production containers:**
   ```bash
   docker compose --profile prod up --build -d
   ```

2. **View logs:**
   ```bash
   docker compose --profile prod logs -f
   ```

3. **Stop production services:**
   ```bash
   docker compose --profile prod down
   ```

#### Individual Service Management

**Backend only:**
```bash
# Development
docker compose --profile dev up backend --build

# Production
docker compose --profile prod up backend-prod --build -d
```

**Frontend only:**
```bash
# Development
docker compose --profile dev up frontend --build

# Production
docker compose --profile prod up frontend-prod --build -d
```

#### Port Configuration

- **Frontend**: Port 3000 (mapped to host)
- **Backend**: Port 8000 (mapped to host)
- **Internal Communication**: Services communicate via Docker network `app-net`

#### Volume Management

**Development volumes:**
- Backend: `./app` and `./main.py` mounted for hot reload
- Frontend: `./frontend` mounted with `node_modules` cached in named volume

**Production volumes:**
- No host volumes mounted (self-contained containers)

## 🚀 Features

### 🤖 Agentic Framework
- **Langchain Integration**: Built on Langchain for robust agent orchestration
- **Multi-Agent Architecture**: Specialized agents for different aspects of Web3 development
- **LLM Integration**: Support for multiple providers (OpenAI, Anthropic, Groq, etc.)
- **Web3 Functionality**: Smart contract deployment, blockchain interaction, wallet integration
- **No-Code Interface**: Intuitive drag-and-drop interface for application building
- **Real-time Collaboration**: Multi-user development environment
- **Template Library**: Pre-built templates for common Web3 applications
- **Code Generation**: Automatic smart contract and frontend code generation
- **Testing Suite**: Integrated testing tools for Web3 applications
- **Deployment Pipeline**: One-click deployment to various blockchain networks
- **Multi-Agent Coordination**: Sophisticated agent management and workflow execution
- **Specialized Agents**: Web3Builder agent for smart contract and DApp generation

## 📁 Project Structure

```
Vizuara_CapstoneProject/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # App router pages
│   │   ├── components/      # Reusable UI components
│   │   │   ├── ui/         # Base UI components
│   │   │   ├── header.tsx  # Navigation header
│   │   │   └── prompt-input.tsx # Main prompt interface
│   │   ├── lib/            # Utility functions
│   │   └── styles/         # Global styles
│   ├── public/             # Static assets
│   ├── package.json        # Frontend dependencies
│   ├── tailwind.config.ts  # Tailwind CSS configuration
│   ├── next.config.ts      # Next.js configuration
│   └── Dockerfile          # Frontend Docker configuration
├── app/                     # FastAPI backend application
│   ├── agents/             # AI agent implementations
│   ├── api/                # API route handlers
│   ├── core/               # Core business logic
│   ├── models/             # Data models
│   ├── services/           # External service integrations
│   └── utils/              # Utility functions
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile.backend      # Backend Docker configuration
├── docker-compose.yml      # Docker orchestration
├── .env.example           # Environment variables template
└── README.md              # Project documentation
```

## 🔧 Environment Variables

### Backend Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GROQ_API_KEY=your_groq_api_key

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/vizuara

# Web3 Configuration
INFURA_PROJECT_ID=your_infura_project_id
ALCHEMY_API_KEY=your_alchemy_api_key

# Application Settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your_secret_key

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```env
# API Configuration
NEXT_PUBLIC_API_BASE=http://localhost:8000

# Web3 Configuration
NEXT_PUBLIC_WALLET_CONNECT_PROJECT_ID=your_wallet_connect_project_id

# Analytics (optional)
NEXT_PUBLIC_GA_ID=your_google_analytics_id
```



## 🤝 Contributing

We welcome contributions to the Vizuara project! Please follow these guidelines:

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and commit them: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

### Development Guidelines

- Follow the existing code style and conventions
- Write clear, descriptive commit messages
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

### Code Style

- **Frontend**: Follow Next.js and React best practices
- **Backend**: Follow PEP 8 Python style guide
- **TypeScript**: Use strict type checking
- **CSS**: Use Tailwind CSS utility classes

### Testing

```bash
# Frontend tests
cd frontend
npm run test

# Backend tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-repo/issues) page
2. Create a new issue with detailed information
3. Join our community discussions

## 🙏 Acknowledgments

- Built with [Next.js](https://nextjs.org/) and [FastAPI](https://fastapi.tiangolo.com/)
- UI components inspired by [Shadcn/ui](https://ui.shadcn.com/)
- Styling with [Tailwind CSS](https://tailwindcss.com/)
- Animations powered by [Framer Motion](https://www.framer.com/motion/)

---

**Happy Building! 🚀**