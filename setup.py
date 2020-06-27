import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PyAudioStream-TouwaStar",
    version="0.0.1",
    author="TouwaStar",
    author_email="yowosek@gmail.com",
    description="A library allowing for streaming and playback of audio files "
                "from server to client over a socket connection.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TouwaStar/PyAudioStream",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)