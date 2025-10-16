from setuptools import setup, find_packages

setup(
    name="osonbot",
    version="1.0.0",
    packages=find_packages(),
    requires=['httpx'],
    author="https://t.me/jackson_rodger",
    description="A simple and lightweight Telegram bot framework",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/sinofarmonov323/osonbot",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=["httpx"]
)
