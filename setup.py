from setuptools import setup, find_packages

setup(
    name="promptbench",
    version="1.1.0",
    description="A Framework for Auditing Demographic Bias in Large Language Model Responses",
    author="Parth Mudgal, Suryansh Rastogi, Siddharth Sharma",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "pandas==3.0.6",
        "scipy==1.18.1",
        "streamlit==1.64.0",
        "matplotlib==3.11.2",
        "statsmodels==0.15.0",
        "sentence-transformers==6.1.0",
    ],
    entry_points={
        "console_scripts": [
            "promptbench=promptbench.cli:main",
        ],
    },
)
