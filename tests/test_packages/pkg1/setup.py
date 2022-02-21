from setuptools import setup

setup(
    name='pkg1',
    version='1.0.0',
    packages=['pkg1'],
    zip_safe=True,
    include_package_data=True,
    entry_points={
        'qemu_runner_layer_packages': ['pkg1=pkg1']
    }
)
