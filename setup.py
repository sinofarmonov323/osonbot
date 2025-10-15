from setuptools import setup, find_packages

setup(
    name="osonbot",
    version="0.1.0",
    packages=find_packages(),
    requires=['httpx'],
    author="https://t.me/jackson_rodger",
    description="A simple and lightweight Telegram bot framework using httpx",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=["httpx"]
)
