from setuptools import find_packages
from setuptools import setup


setup(
    name="tendrl_node_monitoring",
    version="0.1",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*",
                                    "tests"]),
    namespace_packages=['tendrl'],
    url="http://www.redhat.com",
    author="Anmol Babu",
    author_email="anbabu@redhat.com",
    license="LGPL-2.1+",
    zip_safe=False
)
