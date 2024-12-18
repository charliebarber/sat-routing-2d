from setuptools import setup, find_packages

setup(
    name="satrouting",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "networkx>=2.5",
        "matplotlib>=3.3.0",
    ],
    python_requires=">=3.8",
    description="Satellite network routing with spare capacity zones",
    author="Charlie Barber",
)