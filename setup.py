from setuptools import setup, find_packages

setup(
    name="osonbot",
    version="1.2.1",
    packages=find_packages(),
    install_requires=[
        'httpx', 'watchdog', 'pydantic'
    ],
    entry_points={
        "console_scripts": [
            "osonbot=osonbot.cli:main",
        ],
    },
    author="Sino Farmonov",
    description="Simple Telegram bot framework with some built-in features.",
    python_requires=">=3.8",
)