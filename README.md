# GTalk - Google AI Mode Terminal Query Tool

[![PyPI version](https://badge.fury.io/py/gtalk.svg)](https://badge.fury.io/py/gtalk)
[![Python Support](https://img.shields.io/pypi/pyversions/gtalk.svg)](https://pypi.org/project/gtalk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful command-line interface to interact with Google's AI Mode directly from your terminal. Get AI-powered answers, code examples, and explanations without leaving your command line!

## ✨ Features

- 🚀 **Interactive Mode** - Keep querying without restarting
- 💻 **Code Block Support** - Properly formatted code examples
- ⚡ **Fast** - Browser session reused across queries
- 🎯 **Clean Output** - Well-formatted, readable responses
- 🔄 **Both Modes** - Interactive or single-query mode

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install gtalk
```

### From Source

```bash
git clone https://github.com/hissain/gtalk.git
cd gtalk
pip install -e .
```

### Additional Requirements

You'll also need ChromeDriver installed:

**macOS:**
```bash
brew install chromedriver
# If you get a security warning:
xattr -d com.apple.quarantine $(which chromedriver)
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# Fedora
sudo dnf install chromedriver
```

**Windows:**
Download from [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads) and add to PATH

## 🚀 Quick Start

### Interactive Mode

Simply run:
```bash
gtalk
```

Then start asking questions:
```
Query> What is Python?
Query> Write a binary search function
Query> How do I reverse a string in JavaScript?
Query> quit
```

### Single Query Mode

```bash
gtalk "What is machine learning?"
```

## 📖 Usage Examples

### Getting Code Examples

```bash
Query> Write a Python function for bubble sort
```

Output includes both explanation and code:
```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
```

### Learning Concepts

```bash
Query> Explain binary trees
Query> What is the difference between TCP and UDP?
Query> How does async/await work in JavaScript?
```

### Quick References

```bash
Query> Git command to undo last commit
Query> Python list comprehension syntax
Query> Docker commands cheat sheet
```

## 🎮 Interactive Commands

Once in interactive mode:

| Command | Description |
|---------|-------------|
| `[any text]` | Query Google AI Mode |
| `help` | Show available commands |
| `clear` | Clear the screen |
| `quit`, `exit`, `q` | Exit the program |
| `Ctrl+C` | Force exit |
| `Ctrl+D` | Alternative exit |

## ⚙️ Configuration

GTalk uses headless Chrome by default. The browser session is reused across queries for better performance.

## 🐛 Troubleshooting

### CAPTCHA Detected

If you see "Google has detected automated access":
- Wait a few minutes between queries
- Use a VPN or different network
- Reduce query frequency

### ChromeDriver Not Found

Make sure ChromeDriver is installed and in your PATH:
```bash
# Check if chromedriver is available
which chromedriver

# macOS: Install via Homebrew
brew install chromedriver
```

### No Summary Found

If no AI summary is returned:
- Try rephrasing your query
- Use question format: "What is...", "How to...", "Explain..."
- Some queries may not trigger AI Mode

## 🔒 Privacy & Rate Limiting

- GTalk makes direct requests to Google
- No data is stored or logged by this tool
- Respect Google's rate limits - avoid excessive automated queries
- Consider delays between queries if using programmatically

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and personal use only. It interacts with Google Search's public interface. Please use responsibly and in accordance with Google's Terms of Service.

## 🙏 Acknowledgments

- Built with [Selenium](https://www.selenium.dev/)
- Parsing powered by [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- Inspired by the need for quick terminal-based AI assistance

## 📮 Contact & Support

- **Author**: Md. Sazzad Hissain Khan
- **Email**: hissain.khan@gmail.com
- **GitHub**: [@hissain](https://github.com/hissain)
- **Issues**: [GitHub Issues](https://github.com/hissain/gtalk/issues)

---

Made with ❤️ by [Md. Sazzad Hissain Khan](https://github.com/hissain)