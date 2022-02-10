# QEMU search precedence
If environment variable`QEMU_DEV` is set, it is used as path to QEMU executable.

If `QEMU_DEV` is not set, directories are searched for QEMU executable with name specified as `engine` in 
combined layer:
1. Directory specified by `QEMU_DIR` environment variable
2. Each ancestor directory containing runner, up to the root directory and `qemu` subdirectory at each level.
   If runner's path is `c:\dir1\dir2\runner.pyz`, then following directories are checked:
   1. `c:\dir1\dir2`
   2. `c:\dir1\dir2\qemu`
   3. `c:\dir1\`
   4. `c:\dir1\qemu`
   5. `c:\`
   6. `c:\qemu`
3. Directories in `PATH` environment variable.

On Windows, `PATHEXT` variable is used to determine executable extension.

# Layer search precedence
If layer path is absolute and file is not found, search process fails immediately.

If layer path is relative, following directories are searched:
1. Current directory
2. Directories specified as "search directories"
3. Directories specified in `QEMU_LAYER_DIR` environment variable
4. Packages embedded in runner (including `qemu_runner` package)
