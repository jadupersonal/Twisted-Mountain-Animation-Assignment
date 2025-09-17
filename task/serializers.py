from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    assigned_to = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Task
        fields = ['id', 'title', 'status', 'created_at', 'assigned_to']
        read_only_fields = ['id', 'created_at', 'assigned_to']
