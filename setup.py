from setuptools import setup, find_packages

setup(
    name="fast_rabbit",
    version="0.1.7",
    packages=find_packages(),
    install_requires=[
        "aio_pika",
        "aiormq",
        "idna",
        "multidict",
        "pamqp",
        "yarl",
        "asyncio",
        "pydantic",
    ],
    python_requires=">=3.9",
    author="Shaun James Barney",
    author_email="shaunbarney@outlook.com",
    description="An asynchronous RabbitMQ client for Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/shaunbarney/fast_rabbit",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
