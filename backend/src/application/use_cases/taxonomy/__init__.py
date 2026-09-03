"""Casos de uso de areas y subareas.

No hay `SaveArea` ni borrado de areas: las tres son rutas del frontend y solo se
editan. Las subareas conservan el ciclo completo.
"""

from .delete_subarea import DeleteSubarea
from .list_subareas import ListSubareas
from .save_subarea import SaveSubarea
from .update_area import UpdateArea

__all__ = ["DeleteSubarea", "ListSubareas", "SaveSubarea", "UpdateArea"]
