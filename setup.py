from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-book-generator",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An AI-powered book generation tool using OpenAI's GPT models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai-book-generator",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openai",
        "fpdf2",
        "python-dotenv",
        "PyPDF2",
    ],
) 