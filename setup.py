"""Setup script for standalone cd_ripper tool."""
import setuptools

with open("README.md", 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name="cd_ripper",
    version="0.0.1",
    author="Connor Novak",
    author_email="connor.r.novak@gmail.com",
    description="Small tool for ripping music off of cds and adding music tags",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=[
        "tqdm",
        "plac",
    ],
    python_requires=">=3.6",
)
