import os.path

from setuptools import setup, find_packages


with open(os.path.dirname(os.path.abspath(__file__)) + '/README.md', 'r') as f:
    description = f.read()

setup(
    name='qemu-runner',
    version='1.4.1',
    description='Create self-contained wrappers around QEMU to hide & share long command-line invocations',
    url='https://github.com/Novakov/qemu-runner',
    long_description=description,
    long_description_content_type='text/markdown',
    author='Maciej Nowak',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: System :: Emulators',
        'Topic :: Utilities',
    ],
    packages=find_packages(where='src'),
    package_dir={
        '': 'src'
    },
    include_package_data=True,
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'qemu_make_runner=qemu_runner.make_runner.__main__:run'
        ]
    }
)
