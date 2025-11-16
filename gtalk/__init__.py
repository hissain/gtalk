"""GTalk - Google AI Mode Terminal Query Tool

A command-line interface to interact with Google's AI Mode directly from your terminal.
Get AI-powered answers, code examples, and explanations without leaving your command line.

Author: Md. Sazzad Hissain Khan
Email: hissain.khan@gmail.com
License: MIT
Repository: https://github.com/hissain/gtalk
"""

__version__ = "1.0.6"
__author__ = "Md. Sazzad Hissain Khan"
__email__ = "hissain.khan@gmail.com"
__license__ = "MIT"
__url__ = "https://github.com/hissain/gtalk"

from .cli import main

__all__ = ["main", "__version__", "__author__", "__email__"]