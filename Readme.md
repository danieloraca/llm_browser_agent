# Browser Agent: AI Agent that Controls Browser and Performs Tasks

A smart AI agent designed to control your browser and execute tasks based on natural language instructions. Built on Playwright, LangChain, and advanced LLMs, this agent combines intelligent decision-making with human-like interaction to navigate websites, analyze page content, and perform a wide range of tasks.

## 🌟 Overview

Browser Agent empowers you to:
- Navigate websites autonomously
- Interact with page elements via realistic cursor movements
- Interpret page content and structure with advanced DOM analysis
- Execute search queries, fill forms, click buttons, and scroll pages
- Perform any browser-based task given by the user

All while simulating realistic human behaviors through natural mouse movements, typing patterns, and interaction timing.

## ✨ Key Features

- **Natural Human-Like Interaction**: Realistic mouse movements, variable typing speeds, and natural pauses
- **Visual Element Recognition**: Advanced DOM analysis to find and interact with elements based on descriptions
- **Intelligent Page Analysis**: Comprehensive page content extraction and structure understanding
- **Cross-Browser Compatibility**: Works with Chrome browser
- **LLM-Powered Decision Making**: Uses Groq's LLaMa-3.3-70b model for task understanding
- **Session Persistence**: Option to connect to existing browser sessions

## 🛠️ Requirements

- Python 3.9+
- Chrome browser installed
- OpenAI or Groq API key (for LLM capabilities)
- Playwright-compatible OS (Windows, macOS, Linux)

## 📋 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/rkvalandas/browser_agent.git
   cd browser_agent
   ```

2. **Set up a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

5. **Configure environment variables**
   - Create a .env file in the project root (see Configuration section)


## 🚀 Getting Started

### Basic Setup

1. **Create your .env file with API keys:**
   ```
   # API Keys
   # GROQ_API_KEY=your_groq_api_key
   OPENAI_API_KEY=your_google_api_key
   
   # Browser settings
   BROWSER_HEADLESS=false  # Set to true for headless operation
   ```

2. **Start the application:**
   ```bash
   python main.py
   ```

3. **Enter natural language instructions** when prompted. Examples:
   - "Go to amazon.com and search for wireless headphones under 1000 and buy it"
   - "Navigate to weather.com and check the forecast for New York"


## 🎬 Video Demonstration

See our AI Browser Agent in action through these demonstration videos:

### Demo 1: Basic Web Navigation
[![AI Browser Navigation Demo](https://img.youtube.com/vi/Xp3w5H4-pOw/0.jpg)](https://www.youtube.com/embed/Xp3w5H4-pOw "Click to Watch Demo")

*Watch how the agent navigates to websites and extracts information.*

### Advanced Configuration

Edit config.py to customize browser behavior:

```python
# Browser launch options
BROWSER_OPTIONS = {
    "headless": os.getenv("BROWSER_HEADLESS", "false").lower() == "true",
    "channel": "chrome",  # Browser to use
    "args": [
        "--start-maximized",  # Start with maximized window
        "--disable-notifications",  # Prevent notification prompts
        "--disable-extensions"  # Disable browser extensions
    ]
}

# Connection to existing browsers
BROWSER_CONNECTION = {
    "use_existing": True,  # Connect to running Chrome instance
    "cdp_endpoint": "http://localhost:9222",  # DevTools Protocol endpoint
    "fallback_to_new": True  # Launch new if connection fails
}
```


## 🧩 Architecture

The system comprises several key components:

1. **VirtualBrowserController** (`browser_controller.py`)
   - Core class that provides high-level browser interaction methods
   - Implements human-like mouse movements and typing patterns
   - Handles element finding and interaction

2. **Browser Setup** (`browser_setup.py`)
   - Manages browser initialization and connection
   - Injects scripts for cursor visualization
   - Configures navigation interception

3. **LangChain Agent** (`agent.py`)
   - Implements the AI reasoning layer using Groq's LLaMa model
   - Processes natural language instructions
   - Makes decisions about web navigation and interaction

4. **Agent Tools** (`agent_tools.py`)
   - Defines the tools available to the agent
   - Maps agent decisions to browser controller methods

5. **Input Helpers** (`input_helpers.py`)
   - Utility functions for human-like input behaviors
   - Implements cursor movement, clicking, and typing

## 🔍 Key Capabilities

### Page Analysis
The system analyzes web pages using advanced DOM traversal to:
- Extract visible text content
- Identify interactive elements (buttons, links, inputs)
- Understand page structure and hierarchies
- Recognize form fields and associated labels

### Element Selection
The AI can find elements using various methods:
- Text content matching
- Element type filtering
- Positional awareness
- Context-based identification
- Visual appearance analysis

### Human-like Interaction
Interactions mimic human behavior with:
- Natural mouse acceleration/deceleration
- Variable typing speed with realistic pauses
- Appropriate wait times between actions
- Scrolling with natural timing

## 🔧 Troubleshooting

### Common Issues

1. **Browser Connection Issues**
   - Ensure Chrome is running with `--remote-debugging-port=9222` if using existing browser
   - Check firewall settings aren't blocking connections
   - Try setting `use_existing: False` to launch a new browser

2. **Element Interaction Failures**
   - Try running in non-headless mode (`BROWSER_HEADLESS=false`)
   - Use more specific element descriptions
   - Check if the page uses unusual JavaScript frameworks

3. **API Key Issues**
   - Verify your Groq API key in the .env file
   - Check for trailing spaces in the API key
   - Ensure you have sufficient API quota

## 📊 Advanced Usage

### Running in Headless Mode

For server environments, set `BROWSER_HEADLESS=true` in your .env file.
This runs the browser without a visible UI, suitable for automated tasks.

### Custom Prompting

The agent uses a sophisticated prompt template defined in agent.py. Advanced users can modify this template to tune the agent's behavior for specific tasks.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⭐ Support This Project

If you find this project useful, please consider giving it a star on GitHub! It helps make the project more visible and encourages continued development.

[![GitHub stars](https://img.shields.io/github/stars/rkvalandas/browser_agent.svg?style=social&label=Star)](https://github.com/rkvalandas/browser_agent)

*Your feedback and contributions are greatly appreciated!*