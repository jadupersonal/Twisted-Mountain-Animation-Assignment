import graphene
from graphene_django import DjangoObjectType
from .models import Task
from .serializers import TaskSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from graphene_django.views import GraphQLView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class TaskType(DjangoObjectType):
    class Meta:
        model = Task
        fields = ('id', 'title', 'status', 'created_at', 'assigned_to')

class Query(graphene.ObjectType):
    my_tasks = graphene.List(TaskType)

    def resolve_my_tasks(self, info, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentication required")
        return Task.objects.filter(assigned_to=user).order_by('-created_at')

class CreateTask(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String()
        status = graphene.String()

    ok = graphene.Boolean()
    task = graphene.Field(TaskType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, description=None, status=None):
        user = info.context.user
        if user.is_anonymous:
            return CreateTask(ok=False, errors=["Authentication required"], task=None)

        data = {
            'title': title,
            'status': status or 'todo',
        }
        serializer = TaskSerializer(data=data, context={'request': info.context})
        serializer.initial_data['assigned_to'] = user.pk 
        if serializer.is_valid():
            task = serializer.save(assigned_to=user)
            return CreateTask(ok=True, task=task, errors=None)
        else:
            errors = []
            for field, field_errors in serializer.errors.items():
                for e in field_errors:
                    errors.append(f"{field}: {e}")
            return CreateTask(ok=False, errors=errors, task=None)

class Mutation(graphene.ObjectType):
    create_task = CreateTask.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions

class ProtectedGraphQLView(GraphQLView):

    def dispatch(self, request, *args, **kwargs):
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        if auth.startswith('Token '):
            token_key = auth.split(' ', 1)[1].strip()
            try:
                token = Token.objects.select_related('user').get(key=token_key)
                request.user = token.user
            except Token.DoesNotExist:
                return HttpResponseForbidden("Invalid token")
        else:
            return HttpResponseForbidden("Authentication credentials were not provided. Use 'Authorization: Token <token>'")
        return super().dispatch(request, *args, **kwargs)
