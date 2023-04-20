#!/usr/bin/env python

from setuptools import setup, find_packages

long_discription = """
    This program takes images from the image directory,
    and shows them in a random order one by one on a webpage.
    Were it will ask the evaluator for questions for each image as given in the configuration.ini file.
    The evaluations for a image will be stored in an answer database whenever the evaluator clicks on the next image buton
    finaly, it will store these responces in a datasheet after the last image has been shown. 
"""

setup(
    name='image_questionaire',
    version="0.1.0-alpha",
    discription='Framwork to help in the workflow of evaluating images',
    author='Tarkan Bilgic',
    author_email='tarkan.bilgicpub@gmail.com',
    url="https://github.com/TarkanNB/imageEvaluator",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status:: 3-Alpha",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix"
    ],
    python_requires=">=3.9",
    install_requires=[
        "streamlit >= 1.20"
    ],
    project_urls={
        "Source": "https://github.com/TarkanNB/imageEvaluator"
    },
    )
