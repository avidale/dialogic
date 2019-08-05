import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tgalice",
    version="0.1.5",
    author="David Dale",
    author_email="dale.david@mail.ru",
    description="Yet another common wrapper for Telegram bots and Alice skills",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/avidale/tgalice",
    packages=setuptools.find_packages(),
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'pyTelegramBotAPI',
        'textdistance',
        'pyyaml',
        'flask',
        'pymessenger',
        'pymorphy2'
    ]
)
