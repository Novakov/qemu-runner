# QEMU Runner
This project allows creation of self-contained runner for QEMU with embedded command line arguments. Command line arguments are described in files called **layers**. They are simple INI files that can be combined together to express more complex command lines.

```shell
> cat ./arm_virt.ini
[general]
engine = qemu-system-arm

[machine]
@=virt

> cat ./ram_2G.ini
[general]
memory = 2G

> qemu_make_runner -l ./arm_virt.ini ./ram_2G.ini -o ./my_runner.pyz
> python ./my_runner.pyz --dry-run kernel.elf arg1 arg2  # --dry-run to see effective command line instead of running QEMU
qemu-system-arm -machine virt -kernel kernel.elf -append 'arg1 arg2'
```

Resulting `my_runner.pyz` file is ZIP file with `qemu_runner` package and layers. Runner has no extra dependencies, using only Python 3.8+ standard library. QEMU is found according to search precedence described below.

Existing runner can be used as base for next runner. **Derived runner** will contain all layers from base runner along with additional layers specified when deriving. This features allows extending base runner with project specific settings without being aware of base settings.

```shell
> cat ./semihosting.ini
[semihosting-config]
enable=on
target=native

> python ./my_runner.pyz --layers ./semihosting.ini --derive ./derived.pyz
> python ./derived.pyz --dry-run kernel.elf arg1 arg2  # --dry-run to see effective command line instead of running QEMU
qemu-system-arm -machine virt -semihosting-config enable=on,target=native -kernel kernel.elf -append 'arg1 arg2'
```

Runner provides following features, consult `--help` output for details:
* GDB server settings
* Start with CPU halted
* Inspect command line

# QEMU search precedence
If environment variable `QEMU_DEV` is set, it is used as path to QEMU executable.
If environment variable `QEMU_DEV` is not set but argument `--qemu` is specified it is used as path to QEMU executable.

If `QEMU_DEV` is not set, directories are searched for QEMU executable with name specified as `engine` in 
combined layer:
1. Directory specified by `QEMU_DIR` environment variable
2. Directory specified by `--qemu-dir` argument
3. Each ancestor directory containing runner, up to the root directory and `qemu` subdirectory at each level.
   If runner's path is `c:\dir1\dir2\runner.pyz`, then following directories are checked:
   1. `c:\dir1\dir2`
   2. `c:\dir1\dir2\qemu`
   3. `c:\dir1\`
   4. `c:\dir1\qemu`
   5. `c:\`
   6. `c:\qemu`
4. Repeat step 2 with path of base runner in case of derived runners with `--tract-qemu` option.
5. Repeat step 2 with path of passed as `--qemu-dir` when runner was derived.
6. Directories in `PATH` environment variable.

On Windows, `PATHEXT` variable is used to determine executable extension.

# Environment variables
Several environment variables influences the way QEMU command line is constructed:
* `QEMU_FLAGS` - arguments to be added to the QEMU command line during execution 
* `QEMU_RUNNER_FLAGS` - arguments will be interpreted exactly as if they were added to runner execution. 

Example:
```shell
shell> QEMU_FLAGS = '-d int' QEMU_RUNNER_FLAGS = '--halted' ./runner.pyz --dry-run kernel.elf
qemu-system-arm -machine virt -d int -S -kernel kernel.elf
```

# Layer search precedence
If layer path is absolute and file is not found, search process fails immediately.

If layer path is relative, following directories are searched:
1. Current directory
2. Packages declaring entry point `qemu_runner_layer_packages` (see below)

# Layer file format
**Layers** are plain INI files with sections describing QEMU command line. Layers can be combined together allowing user to build bigger command line from simpler building blocks.

Values are interpreted as strings unless specified otherwise. When value is described as boolean, values `1`, `yes`, `true` and `on` are interpreted as true, values `0`, `no`, `false` and `off` are interpreted as false. Other values are invalid.

## Section `[general]`
Section `[general]` describes most common QEMU arguments. 

Available settings:
* `engine` - Name of QEMU executable (e.g.: `qemu-system-arm`, `qemu-system-sparc`)
* `cpu` - CPU to use in machine (`-cpu option`)
* `memory` - RAM memory size, supports suffixes like `M`, `G` (e.g. `20M`, `4G`)
* `gdb` (boolean) - If true QEMU will be started with gdbserver enabled.
* `gdb_dev` - Use specified value as gdbserver listend address. If not used, default QEMU address will be used (`tcp::1234` at the time this document is written). Note that specifing only `gdb_dev` does not enable gdbserver.
* `halted` - Freeze QEMU CPU at startup.

## Section `[name]`
Each section corresponds to single QEMU argument, e.g. section `[machine]` corresponds to `-machine` argument. Value specified as `@` key will be used as direct argument value (machine name, device type, etc). Remaining arguments will be added as key-value properties (note: for `id` property see next section).

For example, layer:
```ini
[machine]
@=virt
usb=on
gic-version=2
```

will be translated into

```
-machine virt,usb=on,gic-version=2
```

## Section `[name:id]`
As INI file syntax does not allow duplicated section names it is not possible to describe many QEMU arguments without additional syntax: `-device`, `-netdev`, etc. These arguments can be differentiated by `id` property which can be specified as section name in format `argument_name:id`.

For example, layer:
```ini
[device:d1]
@=type1
arg1=10
arg2=20

[device:d2]
@=type1
arg1=10
arg2=20

[device:d3]
@=type2
arg3=10
arg4=20
```

translates into:

```
-device type1,id=d1,arg1=10,arg2=20 -device type1,id=d2,arg1=10,arg2=20 -device type2,id=d3,arg3=10,arg4=20
```


## Variable resolution
In sections `[name]` and `[name:id]` it is possible to use variables which will be resolved directly before building complete command lines. Variables are in form `${VARIABLE_NAME}`.

Currently available variables:

| Variable name | Value                                                           |
|---------------|-----------------------------------------------------------------|
| `KERNEL_DIR`  | Directory containing kernel executable (path is not normalized) |

## How layers are combined
Layers can be combined by applying one layer on top of the another. Operation 'build layer `LResult` by applying layer `LAdd` on top of `LBase`' is defined as follows:
* `[general]` (except `cmdline`) - `LResult` contains all settings from layers `LAdd` and `LBase`, values in `LAdd` override values in `LBase`
* `[general]`, `cmdline` value  - `LResult` contains `cmdline` from `LBase` followed by `LAdd` (command line arguments are combined)
* `[name]`
  * If `LBase` does not contain section `[name]`, `LResult` will contain section from `LAdd`.
  * If `LBase` contains section `[name]`, `LResult` will contain `[name]` with all settings from `LBase` and `LAdd`, values in `LAdd` override values in `LBase`.
* `[name:id]`
  * The same rules as with section `[name]` applies, `id` is treated as part of section name.

Note:
* It is not possible to remove section by applying another layer
* It is not possible to change `id` property
* It is not possible to remove argument from section

# Putting layers into pip-installable package
It is possible to distribute layers as pure Python package that can be installed using `pip`. Layers distributes in that way are always visible and there is no need to specify full path to file.

Creating package with layers:
1. Create Python package `layers_pkg`, add empty `__init__.py` file.
2. Put layer files into `layers_pkg/layers` folder, it is possible to use more complex directory structure.
3. Add `MANIFEST.in` file with `recursive-include layers_pkg/layers *.ini` in it.
4. Add `setup.py` file:
```python
from setuptools import setup

setup(
    name='layers-pkg',
    version='1.0.0',
    packages=['layers_pkg'],
    zip_safe=True,
    include_package_data=True,
    entry_points={
        'qemu_runner_layer_packages': ['layers_pkg=layers_pkg'] # Always use `package_name=package_name`
    }
)
```
5. Create Python package using tools of your choice (`python setup.py` or `pyproject-build`)

Package might contain other files, as it is normal Python package.

**NOTE:** This is simplified process of creating Python package, refer to Python documentation for more details.

`qemu_runner` tools uses `qemu_runner_layer_packages` entry point to discover all registered packages, from each entry point module portion is used in search for layers.