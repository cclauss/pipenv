import os
import sys
from typing import Optional

from pipenv import exceptions
from pipenv.patched.pip._vendor.packaging.version import parse as parse_version
from pipenv.patched.pip._vendor.typing_extensions import TYPE_CHECKING
from pipenv.utils import err
from pipenv.utils.dependencies import python_version
from pipenv.utils.pipfile import ensure_pipfile
from pipenv.utils.shell import shorten_path
from pipenv.utils.virtualenv import ensure_virtualenv

if TYPE_CHECKING:
    from pipenv.patched.pip._vendor.typing_extensions import STRING_TYPE

if sys.version_info < (3, 10):
    from pipenv.vendor import importlib_metadata
else:
    import importlib.metadata as importlib_metadata


def ensure_project(
    project,
    python=None,
    validate=True,
    system=False,
    warn=True,
    site_packages=None,
    deploy=False,
    skip_requirements=False,
    pypi_mirror=None,
    clear=False,
    pipfile_categories=None,
):
    """Ensures both Pipfile and virtualenv exist for the project."""

    # Automatically use an activated virtualenv.
    if project.s.PIPENV_USE_SYSTEM or project.virtualenv_exists:
        system_or_exists = True
    else:
        system_or_exists = system  # default to False
    if not project.pipfile_exists and deploy:
        raise exceptions.PipfileNotFound
    # Skip virtualenv creation when --system was used.
    if not system_or_exists:
        ensure_virtualenv(
            project,
            python=python,
            site_packages=site_packages,
            pypi_mirror=pypi_mirror,
        )
        if warn:
            # Warn users if they are using the wrong version of Python.
            if project.required_python_version:
                path_to_python = project._which("python") or project._which("py")
                if path_to_python and project.required_python_version not in (
                    python_version(path_to_python) or ""
                ):
                    err.print(
                        f"[red][bold]Warning[/bold][/red]: Your Pipfile requires"
                        f"[bold]{python_version}[/bold] [cyan]{project.required_python_version}[/cyan],"
                        f"but you are using [cyan]{python_version(path_to_python)}[/cyan]"
                        f"from [green]{shorten_path(path_to_python)}[/green]."
                    )
                    err.print(
                        "[green]$ pipenv --rm[/green] and rebuilding the virtual environment "
                        "may resolve the issue."
                    )
                    if not deploy:
                        err.print("[yellow]$ pipenv check[/yellow] will surely fail.")
                    else:
                        raise exceptions.DeployException
    # Ensure the Pipfile exists.
    ensure_pipfile(
        project,
        validate=validate,
        skip_requirements=skip_requirements,
        system=system,
        pipfile_categories=pipfile_categories,
    )
    os.environ["PIP_PYTHON_PATH"] = project.python(system=system)


def get_setuptools_version() -> Optional["STRING_TYPE"]:
    try:
        setuptools_dist = importlib_metadata.distribution("setuptools")
        return str(setuptools_dist.version)
    except ImportError:
        return None


def get_default_pyproject_backend():
    # type: () -> STRING_TYPE
    st_version = get_setuptools_version()
    if st_version is not None:
        parsed_st_version = parse_version(st_version)
        if parsed_st_version >= parse_version("40.8.0"):
            return "setuptools.build_meta:__legacy__"
    return "setuptools.build_meta"
