import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tgalice",
    version="0.1.7",
    author="David Dale",
    author_email="dale.david@mail.ru",
    description="Yet another common wrapper for Alice skills and Facebook/Telegram bots",
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
        'flask',
        'pymessenger',
        'pymorphy2',
        'pyTelegramBotAPI',
        'pyyaml',
        'requests',  # it is needed by other packages, and somehow it is installed wrongly
        'textdistance',
    ]
)
