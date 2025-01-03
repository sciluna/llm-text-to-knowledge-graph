from setuptools import setup, find_packages


setup(
    name="textToKnowledgeGraph",
    version="0.1.0",
    author="Favour James",
    author_email="favour.ujames196@gmail.com",
    description="A Python package to generate BEL statements and CX2 networks.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ndexbio/llm-text-to-knowledge-graph",  
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "langchain==0.3.13",
        "langchain_core==0.3.27",
        "langchain_openai==0.2.13",
        "lxml==5.2.1",
        "ndex2>=3.8.0,<4.0.0",
        "pandas",
        "pydantic==2.10.4",
        "python-dotenv==1.0.1",
        "Requests==2.32.3"
    ],
    entry_points={
        "console_scripts": [
            "textToKnowledgeGraph=textToKnowledgeGraph.main:main",  # CLI entry point
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
