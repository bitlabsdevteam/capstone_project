#!/usr/bin/env python3
"""Setup script for Multi-Agent Web3 Application Builder"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

def run_command(command: List[str], cwd: Optional[Path] = None) -> bool:
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {' '.join(command)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {' '.join(command)}")
        print(f"Error: {e.stderr}")
        return False

def check_python_version() -> bool:
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies() -> bool:
    """Check if required system dependencies are available"""
    dependencies = {
        "git": "Git is required for version control",
        "node": "Node.js is required for some Web3 tools (optional)",
        "docker": "Docker is recommended for containerization (optional)"
    }
    
    all_good = True
    for dep, description in dependencies.items():
        if shutil.which(dep):
            print(f"✓ {dep} found")
        else:
            if dep in ["node", "docker"]:
                print(f"⚠ {dep} not found - {description}")
            else:
                print(f"✗ {dep} not found - {description}")
                all_good = False
    
    return all_good

def create_virtual_environment() -> bool:
    """Create Python virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    return run_command([sys.executable, "-m", "venv", "venv"])

def install_requirements() -> bool:
    """Install Python requirements"""
    venv_python = Path("venv") / "bin" / "python" if os.name != 'nt' else Path("venv") / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        print("✗ Virtual environment not found")
        return False
    
    print("Installing requirements...")
    return run_command([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"])

def create_directories() -> bool:
    """Create necessary directories"""
    directories = [
        "logs",
        "uploads",
        "config",
        "data",
        "temp",
        "artifacts"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True

def setup_environment_file() -> bool:
    """Setup environment configuration file"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from template")
        print("⚠ Please edit .env file with your actual configuration values")
        return True
    else:
        print("✗ .env.example file not found")
        return False

def create_sample_configs() -> bool:
    """Create sample configuration files"""
    config_dir = Path("config")
    
    # Sample LLM providers configuration
    llm_config = {
        "openai": {
            "name": "openai",
            "api_key": "${OPENAI_API_KEY}",
            "model": "gpt-4",
            "max_tokens": 4000,
            "temperature": 0.7,
            "enabled": True
        },
        "deepseek": {
            "name": "deepseek",
            "api_key": "${DEEPSEEK_API_KEY}",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat",
            "max_tokens": 4000,
            "temperature": 0.7,
            "enabled": True
        },
        "gemini": {
            "name": "gemini",
            "api_key": "${GEMINI_API_KEY}",
            "model": "gemini-pro",
            "max_tokens": 4000,
            "temperature": 0.7,
            "enabled": True
        }
    }
    
    # Sample Web3 networks configuration
    web3_config = {
        "ethereum": {
            "name": "ethereum",
            "rpc_url": "${ETHEREUM_RPC_URL}",
            "chain_id": 1,
            "currency_symbol": "ETH",
            "block_explorer_url": "https://etherscan.io",
            "enabled": True
        },
        "polygon": {
            "name": "polygon",
            "rpc_url": "${POLYGON_RPC_URL}",
            "chain_id": 137,
            "currency_symbol": "MATIC",
            "block_explorer_url": "https://polygonscan.com",
            "enabled": True
        },
        "bsc": {
            "name": "bsc",
            "rpc_url": "${BSC_RPC_URL}",
            "chain_id": 56,
            "currency_symbol": "BNB",
            "block_explorer_url": "https://bscscan.com",
            "enabled": True
        }
    }
    
    try:
        import json
        
        with open(config_dir / "llm_providers.json", "w") as f:
            json.dump(llm_config, f, indent=2)
        print("✓ Created sample LLM providers configuration")
        
        with open(config_dir / "web3_networks.json", "w") as f:
            json.dump(web3_config, f, indent=2)
        print("✓ Created sample Web3 networks configuration")
        
        return True
    except Exception as e:
        print(f"✗ Error creating sample configs: {e}")
        return False

def run_tests() -> bool:
    """Run basic tests to verify setup"""
    venv_python = Path("venv") / "bin" / "python" if os.name != 'nt' else Path("venv") / "Scripts" / "python.exe"
    
    print("Running basic import tests...")
    test_imports = [
        "import fastapi",
        "import pydantic",
        "import langchain",
        "import web3",
        "from app.core import get_settings"
    ]
    
    for test_import in test_imports:
        try:
            result = subprocess.run(
                [str(venv_python), "-c", test_import],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✓ {test_import}")
        except subprocess.CalledProcessError:
            print(f"✗ {test_import}")
            return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Multi-Agent Web3 Application Builder Setup")
    print("=" * 50)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Checking system dependencies", check_dependencies),
        ("Creating virtual environment", create_virtual_environment),
        ("Installing requirements", install_requirements),
        ("Creating directories", create_directories),
        ("Setting up environment file", setup_environment_file),
        ("Creating sample configurations", create_sample_configs),
        ("Running basic tests", run_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            failed_steps.append(step_name)
            print(f"❌ {step_name} failed")
        else:
            print(f"✅ {step_name} completed")
    
    print("\n" + "=" * 50)
    
    if failed_steps:
        print("❌ Setup completed with errors:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease resolve the errors and run setup again.")
        sys.exit(1)
    else:
        print("✅ Setup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Edit .env file with your actual API keys and configuration")
        print("   2. Review config/*.json files and adjust as needed")
        print("   3. Start the application with: python -m uvicorn main:app --reload")
        print("   4. Visit http://localhost:8000/docs for API documentation")
        print("\n🎉 Happy coding!")

if __name__ == "__main__":
    main()