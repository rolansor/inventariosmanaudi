from django import template
from django.contrib.auth.decorators import user_passes_test


register = template.Library()


@register.filter(name='pertenece_grupo')
def pertenece_grupo(user, group_name):
    return user.groups.filter(name=group_name).exists()


def control_acceso(group_name):
    def in_group(user):
        if user.is_authenticated:
            return user.groups.filter(name=group_name).exists() or user.is_superuser
        return False
    return user_passes_test(in_group)
