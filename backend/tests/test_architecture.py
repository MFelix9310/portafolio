"""Regla de dependencia verificada por test (D2).

Momentum falla justo aqui: sus servicios de dominio importan `src.infrastructure` y
`src.application` porque nada lo comprobaba. Este test recorre el AST de cada modulo
y rompe el build si aparece un import prohibido.

Politica:

- `src/domain` solo puede importar la biblioteca estandar y otros modulos de
  `src/domain`. Ningun framework, ni siquiera indirectamente.
- `src/application` puede importar `src/domain` y stdlib, nunca `src/infrastructure`
  ni frameworks web.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = BACKEND_ROOT / "src"
DOMAIN_ROOT = SRC_ROOT / "domain"
APPLICATION_ROOT = SRC_ROOT / "application"

STDLIB = set(sys.stdlib_module_names)

# Nombres citados de forma explicita por el contrato, para que el fallo sea legible
# cuando alguien los cuele en dominio.
EXPLICITLY_BANNED_IN_DOMAIN = frozenset(
    {
        "fastapi",
        "pydantic",
        "pydantic_settings",
        "starlette",
        "supabase",
        "httpx",
        "jwt",
        "postgrest",
        "gotrue",
        "storage3",
        "uvicorn",
        "dotenv",
        "sqlalchemy",
    }
)


def _python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _module_name(path: Path) -> str:
    relative = path.relative_to(BACKEND_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _resolve_relative(module_name: str, node: ast.ImportFrom) -> str:
    """Convierte `from ..x import y` en el modulo absoluto que representa."""
    package = module_name.split(".")
    # Un `__init__` ya es el propio paquete; el resto sube un nivel adicional.
    is_package = (BACKEND_ROOT / Path(*package) / "__init__.py").exists()
    base = package if is_package else package[:-1]
    if node.level > 1:
        base = base[: -(node.level - 1)] or []
    suffix = node.module.split(".") if node.module else []
    return ".".join([*base, *suffix])


def _imported_modules(path: Path) -> list[tuple[str, int]]:
    """Devuelve (modulo absoluto importado, linea) para cada import del fichero."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    module_name = _module_name(path)
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                found.append((_resolve_relative(module_name, node), node.lineno))
            elif node.module:
                found.append((node.module, node.lineno))
    return found


def _root_package(module: str) -> str:
    return module.split(".", 1)[0]


DOMAIN_FILES = _python_files(DOMAIN_ROOT)
APPLICATION_FILES = _python_files(APPLICATION_ROOT)


def test_domain_tree_is_not_empty() -> None:
    # Un test verde porque no encontro ficheros no verifica nada.
    assert DOMAIN_FILES, "no se encontro ningun modulo bajo src/domain"
    assert APPLICATION_FILES, "no se encontro ningun modulo bajo src/application"


@pytest.mark.parametrize("path", DOMAIN_FILES, ids=lambda p: str(p.name))
def test_domain_only_imports_stdlib_and_itself(path: Path) -> None:
    offenders: list[str] = []
    for module, lineno in _imported_modules(path):
        if module.startswith("src.domain"):
            continue
        root = _root_package(module)
        if root in EXPLICITLY_BANNED_IN_DOMAIN:
            offenders.append(f"L{lineno}: framework prohibido '{module}'")
        elif module.startswith("src."):
            offenders.append(f"L{lineno}: capa externa '{module}'")
        elif root not in STDLIB:
            offenders.append(f"L{lineno}: dependencia de terceros '{module}'")
    assert not offenders, (
        f"{path.relative_to(BACKEND_ROOT)} viola la regla de dependencia:\n  "
        + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("path", APPLICATION_FILES, ids=lambda p: str(p.name))
def test_application_does_not_import_infrastructure(path: Path) -> None:
    offenders = [
        f"L{lineno}: '{module}'"
        for module, lineno in _imported_modules(path)
        if module.startswith("src.infrastructure")
    ]
    assert not offenders, (
        f"{path.relative_to(BACKEND_ROOT)} importa infraestructura:\n  "
        + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("path", APPLICATION_FILES, ids=lambda p: str(p.name))
def test_application_does_not_import_web_frameworks(path: Path) -> None:
    banned = {"fastapi", "starlette", "supabase", "uvicorn", "jwt"}
    offenders = [
        f"L{lineno}: '{module}'"
        for module, lineno in _imported_modules(path)
        if _root_package(module) in banned
    ]
    assert not offenders, (
        f"{path.relative_to(BACKEND_ROOT)} importa un framework web:\n  "
        + "\n  ".join(offenders)
    )


def test_domain_imports_resolve_to_existing_modules() -> None:
    """Un import relativo mal resuelto haria pasar el test por accidente."""
    for path in DOMAIN_FILES:
        for module, _ in _imported_modules(path):
            if not module.startswith("src."):
                continue
            target = BACKEND_ROOT / Path(*module.split("."))
            assert target.with_suffix(".py").exists() or (target / "__init__.py").exists(), (
                f"{path.name} importa '{module}', que no existe"
            )
