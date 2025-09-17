from rest_framework import permissions

class IsAssignedToUser(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.assigned_to == request.user
