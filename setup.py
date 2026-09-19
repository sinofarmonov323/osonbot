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
        'httpx',
        'watchdog',
        'pydantic',
    ],
    entry_points={
        "console_scripts": [
            "osonbot=osonbot.cli:main",
        ],
    },
    extras_require={
        'userbot': ['telethon'],
    },
    author="Sino Farmonov",
    author_email="sinofarmonov323@gmail.com",
    url="https://github.com/sinofarmonov323/osonbot",
    project_urls={
        "Documentation": "https://github.com/sinofarmonov323/osonbot#readme",
        "Source": "https://github.com/sinofarmonov323/osonbot",
        "Tracker": "https://github.com/sinofarmonov323/osonbot/issues",
    },
    description="Simple Telegram bot framework for building Telegram bots with handlers, states and media support.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    keywords=[
        "telegram",
        "telegram-bot",
        "bot-framework",
        "python",
        "asyncio",
        "state-machine",
        "chatbot",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.8",
    include_package_data=True,
)
