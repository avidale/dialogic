import os
import setuptools

description = "Yet another common wrapper for Alice/Salut skills and Facebook/Telegram/VK bots"
long_description = description
if os.path.exists("README_en.md"):
    with open("README_en.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()


setuptools.setup(
    name="dialogic",
    version="0.3.10",
    author="David Dale",
    author_email="dale.david@mail.ru",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/avidale/dialogic",
    packages=setuptools.find_packages(),
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'attrs',
        'flask',
        'pymessenger',
        'pymorphy2',
        'pyTelegramBotAPI',
        'pyyaml',
        'requests',
        'textdistance',
        'colorama',
    ],
    extras_require={
        'rumorph': ['pymorphy2[fast]', 'pymorphy2-dicts-ru'],  # todo: move them out of main requirements
        'server': ['flask', 'pymessenger', 'pyTelegramBotAPI'],  # todo: move them out of main requirements
        'w2v':  ['numpy', 'pyemd'],
    }
)
