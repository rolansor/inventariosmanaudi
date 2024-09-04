from django import template


register = template.Library()


@register.filter(name='pertenece_grupo')
def pertenece_grupo(user, group_name):
    return user.groups.filter(name=group_name).exists()
