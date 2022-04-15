from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="yabms",
    version="0.1.1",
    description="Yet Another Bloody Match Scheduler",
    author="Alistair Lynn",
    author_email="alynn@studentrobotics.org",
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    zip_safe=True,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Programming Language :: Python :: 3",
    ],
    install_requires=[
        "z3-solver",
    ],
    entry_points={
        "console_scripts": [
            "yabms = yabms.cli:main",
        ],
    },
)
