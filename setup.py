from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mangaba",
    # Keep in step with pyproject.toml and mangaba/__init__.py — hatchling is
    # the real build backend; this file is only a legacy shim.
    version="4.0.0",
    author="Mangaba AI Team",
    author_email="contato@mangaba.ai",
    description="Professional multi-agent AI framework with event-driven flows, ReAct reasoning, RAG, knowledge bases, memory, MCP/A2A interop, and function calling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Mangaba-ai/mangaba_ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    keywords="ai, gemini, google, chatbot, artificial intelligence",
    project_urls={
        "Bug Reports": "https://github.com/Mangaba-ai/mangaba_ai/issues",
        "Source": "https://github.com/Mangaba-ai/mangaba_ai",
        "Documentation": "https://github.com/Mangaba-ai/mangaba_ai#readme",
    },
)
