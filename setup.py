import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pangolin-tool", # Replace with your own username
    version="0.0.1",
    author="Edward Lufadeju",
    author_email="edward@ncade.com",
    description="Pangolin is a graphical image segmentation/annotation tool written in Python using Qt.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/edluffy/pangolin",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Natural Language :: English",
    ],
    python_requires='>=3.6',
)
