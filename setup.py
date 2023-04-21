from setuptools import setup, find_packages


setup(
    name='azplot',
    version='0.1',
    author="咚咚咚",
    author_email="azen.cell@foxmail.com",
    packages=find_packages(),
    url="https://github.com/AzenXu/azplot",
    install_requires=[
        "pyecharts>=2.0.2",
        "pandas>=1.5.3",
    ]
)