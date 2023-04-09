import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name = 'fmiprecice',
    version = '0.1.0',
    author = "Leonard Willeke",
    author_email = "st150067@stud.uni-stuttgart.de",
    description = "A tool to co-simulate FMU models with the coupling library preCICE.",
    license = "LGPL-3.0",
    url = "https://github.com/precice/fmi-runner",
    packages=['fmiprecice'],
    long_description=read('README.md'),
    python_requires=">=3.0",
    install_requires = [
        'pyprecice>=2.0',
        'fmpy',
        'numpy',
    ],
    entry_points={
        'console_scripts': ['fmiprecice=fmiprecice.runner:main']},
)
