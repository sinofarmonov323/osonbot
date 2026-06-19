from setuptools import setup, find_packages

setup(
    name="osonbot",
    version="1.2.4",
    packages=find_packages(),
    install_requires=[
        'httpx', 'watchdog', 'pydantic'
    ],
    entry_points={
        "console_scripts": [
            "osonbot=osonbot.cli:main",
        ],
    },
    extras_require={
        'userbot': ['telethon']
    },
    author="Sino Farmonov",
    description="Simple Telegram bot framework with some built-in features.",
    python_requires=">=3.8",
)
