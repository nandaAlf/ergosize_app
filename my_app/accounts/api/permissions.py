# from rest_framework.permissions import BasePermission

# class IsAdmin(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == 'admin'

# class IsInvestigator(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == 'investigador'

# class IsGeneralUser(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == 'usuario'
    
# class IsCreator(BasePermission):
#     """Allow access only to object creator or admin users."""
#     def has_object_permission(self, request, view, obj):
#         # SAFE_METHODS handled elsewhere if needed
#         return (
#             request.user.is_authenticated and
#             (
#                 obj.supervisor == request.user
#             )
#         )

from rest_framework.permissions import BasePermission, SAFE_METHODS

# class HasRole(BasePermission):
#     """Permission checking if the authenticated user has one of the allowed roles."""
#     def __init__(self, *allowed_roles):
#         self.allowed_roles = allowed_roles

#     def has_permission(self, request, view):
#         return (
#             request.user.is_authenticated and
#             request.user.role in self.allowed_roles
#         )

# class IsCreator(BasePermission):
#     """Only allow object creator to edit/destroy."""
#     def has_permission(self, request, view):
#         # Allow access to detail actions so has_object_permission runs
#         return request.user.is_authenticated

#     def has_object_permission(self, request, view, obj):
#         # Allow read-only for everyone authenticated
#         if request.method in SAFE_METHODS:
#             return True
#         # Only the supervisor who created it
#         return obj.supervisor == request.user

# class IsCreatorOrAdmin(BasePermission):
#     """Allow access only to object creator or admin for object-level actions."""
#     def has_permission(self, request, view):
#         return request.user.is_authenticated

#     def has_object_permission(self, request, view, obj):
#         # Lectura solo por admin o creador
#         if request.method in SAFE_METHODS:
#             return (
#                 request.user.role == 'admin'
#                 or obj.supervisor == request.user
#             )
#         # Escritura/eliminación con las mismas reglas
#         return (
#             request.user.role == 'admin'
#             or obj.supervisor == request.user
#         )


class HasRole(BasePermission):
    """
    Permite el acceso a usuarios autenticados cuyo rol esté en allowed_roles.
    """
    allowed_roles = ()

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )

class IsAdminOrInvestigator(HasRole):
    allowed_roles = ('admin', 'investigador')

class IsCreatorOrAdmin(BasePermission):
    """
    Permite al supervisor del estudio o al administrador.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # En este caso obj será un Study
        return (
            request.user.role == 'admin' or
            obj.supervisor == request.user
        ) 
class IsAdmin(BasePermission):
    """
      Solo usuarios con rol 'admin'.
    """
    def has_permission(self, request, view):
        # Solo usuarios autenticados entran aquí; detalles se comprueban en has_object_permission
        return request.user.is_authenticated and request.user.role == 'admin'

class IsInvestigator(BasePermission):
    """
    Solo usuarios con rol 'investigador'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'investigador'

class IsInvestigatorOfPerson(BasePermission):
    """
    Autorización objeto:
    Permite ver/editar/crear/eliminar una Person únicamente si:
     - El usuario es administrador, o
     - El usuario es investigador y supervisa al menos un estudio en el que
       esa persona tiene mediciones.
    """
    def has_permission(self, request, view):
        # Abrimos la vista solo a admin o investigadores
        return (
            request.user.is_authenticated and 
            request.user.role in ('admin','investigador')
        )

    def has_object_permission(self, request, view, person):
        # Admin puede siempre
        if request.user.role == 'admin':
            return True

        # Para investigador, comprobamos que exista al menos
        # una medición de esta persona en un estudio que él supervisa.
        return person.measurements.filter(
            study__supervisor=request.user
        ).exists()