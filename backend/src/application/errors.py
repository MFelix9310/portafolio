"""Errores de aplicacion. La capa web los traduce a codigos HTTP; nadie mas los ve."""

from __future__ import annotations


class ApplicationError(Exception):
    """Raiz de los errores esperados de un caso de uso."""


class NotFoundError(ApplicationError):
    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(f"{resource} no encontrado: {identifier}")
        self.resource = resource
        self.identifier = identifier


class ValidationError(ApplicationError):
    """Entrada sintacticamente valida pero incoherente con las reglas del dominio."""


class ConflictError(ApplicationError):
    """Choca con una clave unica ya existente.

    Se separa de `ValidationError` porque el cuerpo enviado es correcto: lo que falla
    es el estado actual de la base. La capa web lo traduce a 409, no a 422.
    """

    def __init__(self, resource: str, field: str, value: object) -> None:
        super().__init__(f"ya existe un {resource} con {field} = {value!r}")
        self.resource = resource
        self.field = field
        self.value = value


class ForbiddenOperationError(ApplicationError):
    """La operacion no existe para este recurso por diseno, no por permisos."""


class StorageError(ApplicationError):
    """Fallo del adaptador de almacenamiento de media."""
