from setuptools import setup, find_packages

setup(
    name='osonbot',
    version='1.6.0',
    description='A simple and extensible chatbot framework.',
    author='Your Name',
    packages=find_packages(),
    install_requires=[
        'httpx', 'watchdog'
    ],
    website='https://github.com/sinofarmonov323/osonbot'
)
