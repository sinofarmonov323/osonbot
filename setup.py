from pathlib import Path

from setuptools import setup, find_packages


README_PATH = Path(__file__).with_name("README.md")
README_BYTES = README_PATH.read_bytes()
README_ENCODING = "utf-16" if README_BYTES.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8"
LONG_DESCRIPTION = README_BYTES.decode(README_ENCODING)

setup(
    name="osonbot",
    version="1.2.9",
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
    url="https://github.com/sinofarmonov323/osonbot",
    description="Simple Telegram bot framework with some built-in features that makes the writing telegram bots easier.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
)
