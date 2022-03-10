from setuptools import setup, find_packages

setup(
    name='qemu-runner',
    version='1.0.0',
    packages=find_packages(where='src'),
    package_dir={
        '': 'src'
    },
    # package_data={
    #     'qemu_runner.make_runner': ['main.py.in']
    # },
    include_package_data=True,
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'qemu_make_runner=qemu_runner.make_runner.__main__:run'
        ]
    }
)
