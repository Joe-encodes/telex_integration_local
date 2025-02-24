from setuptools import setup, find_packages

setup(
    name="telex_integration",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "httpx",
        "pydantic",
    ],
)