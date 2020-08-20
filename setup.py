from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='rechtsinfo_api',
    version='0.1.0',
    description='Legal information API',
    long_description=readme,
    author='Niko Felger',
    author_email='niko.felger@gmail.com',
    url='https://github.com/tech4germany/rechtsinfo_api',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
