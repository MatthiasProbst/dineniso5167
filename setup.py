import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dineniso5167",
    version='0.0.0',
    author="Matthias Probst",
    author_email="matthias.probst@kit.edu",
    description="Implementation of DIN EN ISO 5167 to calculate volume flow rate using an orifice",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MatthiasProbst/dineniso5167.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        'numpy',
        'matplotlib',
    ],
)
