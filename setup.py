import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pybackup",
    version="0.0.1",
    author="Eliran Shabat",
    author_email="shabat.eliran@gmail.com",
    license='MIT',
    description="Python package for backup",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elirshabat/py-backup",
    packages=setuptools.find_packages(),
    install_requires=[
        'PyYAML',
        'tqdm'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
