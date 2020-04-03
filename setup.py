import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tgalice",
    version="0.2.5",
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
    ],
    extras_require={
        'rumorph': ['pymorphy2[fast]', 'pymorphy2-dicts-ru'],  # todo: move them out of main requirements
        'server': ['flask', 'pymessenger', 'pyTelegramBotAPI'],  # todo: move them out of main requirements
        'w2v':  ['numpy', 'pyemd'],
    }
)
