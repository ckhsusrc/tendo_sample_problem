from os import path
from setuptools import setup


__package_name = 'solution'
__package_version = '0.1.0'
__package_description = 'Solution Code Sample'


def get_requirements():
    basedir = path.dirname(__file__)
    with open(path.join(basedir, 'requirements.txt')) as f:
        return [l.strip() for l in f if not l.startswith('-e ')]


# List run-time dependencies here.  These will be installed by pip when
# your project is installed. For an analysis of "install_requires" vs pip's
# requirements files see:
# https://packaging.python.org/en/latest/requirements.html
_install_requires = get_requirements()


setup(
    name=__package_name,
    version=__package_version,
    description=__package_description,
    author='CK Hsu',
    install_requires=_install_requires,
    packages=['solution'],
)
