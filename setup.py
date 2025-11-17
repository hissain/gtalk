from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gtalk",
    version="1.0.8",
    license="MIT",
    maintainer="Md. Sazzad Hissain Khan",
    maintainer_email="hissain.khan@gmail.com",
    author="Md. Sazzad Hissain Khan",
    author_email="hissain.khan@gmail.com",
    description="A command-line interface to interact with Google's AI Mode",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hissain/gtalk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=[
        "selenium>=4.15.0",
        "beautifulsoup4>=4.12.0",
    ],
    entry_points={
        "console_scripts": [
            "gtalk=gtalk.cli:main",
        ],
    },
    keywords="google ai mode cli terminal search assistant chatbot",
    project_urls={
        "Bug Reports": "https://github.com/hissain/gtalk/issues",
        "Source": "https://github.com/hissain/gtalk",
        "Documentation": "https://github.com/hissain/gtalk#readme",
    },
)
