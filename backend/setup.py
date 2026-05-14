from __future__ import annotations

import os
from pathlib import Path
from typing import List

from setuptools import Extension, setup
from setuptools.command.build_py import build_py as _build_py

COMPILED_MODULES = {
    "sandesh.api",
    "sandesh.dto",
    "sandesh.sdk.client",
    "sandesh.sdk.exceptions",
}


def _is_compiled_build() -> bool:
    raw_compiled = os.getenv("SANDESH_BUILD_COMPILED", "").strip().lower()
    raw_pure = os.getenv("SANDESH_BUILD_PURE", "").strip().lower()
    truthy = {"1", "true", "yes", "on"}
    falsy = {"0", "false", "no", "off"}

    if raw_compiled in truthy:
        return True
    if raw_compiled in falsy:
        return False
    if raw_pure in truthy:
        return False
    if raw_pure in falsy:
        return True
    # Default to compiled wheels so runtime sources stay hidden.
    return True


class build_py(_build_py):
    """Exclude Python sources for modules compiled into extensions."""

    def find_package_modules(self, package: str, package_dir: str):
        modules = super().find_package_modules(package, package_dir)
        if not _is_compiled_build():
            return modules
        filtered = []
        for pkg, mod, filepath in modules:
            full_name = f"{pkg}.{mod}" if pkg else mod
            if full_name in COMPILED_MODULES:
                continue
            filtered.append((pkg, mod, filepath))
        return filtered


def _compiled_extensions() -> List[Extension]:
    return [
        Extension(name=module, sources=[f"{module.replace('.', '/')}.py"])
        for module in sorted(COMPILED_MODULES)
    ]


def _maybe_cythonize() -> List[Extension]:
    if not _is_compiled_build():
        return []

    from Cython.Build import cythonize

    return cythonize(
        _compiled_extensions(),
        compiler_directives={
            "language_level": "3",
            "embedsignature": True,
            "boundscheck": False,
            "wraparound": False,
            "initializedcheck": False,
        },
        annotate=False,
    )


def _read_readme() -> str:
    readme = Path(__file__).with_name("README.md")
    return readme.read_text(encoding="utf-8")


setup(
    long_description=_read_readme(),
    long_description_content_type="text/markdown",
    ext_modules=_maybe_cythonize(),
    cmdclass={"build_py": build_py},
    zip_safe=False,
)
