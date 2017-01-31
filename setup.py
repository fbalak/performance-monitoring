from setuptools import find_packages
from setuptools import setup

setup(
    name="tendrl-performance-monitoring",
    version="1.2",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*",
                                    "tests"]),
    namespace_packages=['tendrl'],
    url="http://www.redhat.com",
    author="Rohan Kanade.",
    author_email="rkanade@redhat.com",
    license="LGPL-2.1+",
    zip_safe=False,
    entry_points={
        'console_scripts': ['tendrl-performance-monitoring = '
                            'tendrl.performance_monitoring.manager'
                            ':main'
                            ]
    }
)
