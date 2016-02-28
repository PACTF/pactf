"""Register app with Django"""

from django.apps import AppConfig

from ctflex.constants import APP_NAME, VERBOSE_NAME


class CtflexConfig(AppConfig):
    name = APP_NAME
    verbose_name = VERBOSE_NAME

# region Add permission to group (obsolete)
#
# COMPETE_PERMISSION_CODENAME = 'compete'
# COMPETITOR_GROUP_NAME = 'ctflex.competitors'
#
# def add_group_permissions(sender, **kwargs):
#     """Configure groups and permissions for the app (meant to be called after flushing)"""
#
#     # Obtain Model References
#     GlobalPermission = sender.get_model('GlobalPermission')
#     Group = apps.get_model('auth', 'Group')
#
#     # Create Permissions
#     competePermission, created = GlobalPermission.objects.get_or_create(
#         codename=COMPETE_PERMISSION_CODENAME,
#         name="Has an associated competitor"
#     )
#     competePermission.save()
#
#     # Create Groups
#     competitorGroup, created = Group.objects.get_or_create(name=COMPETITOR_GROUP_NAME)
#     competitorGroup.save()
#
#     # Add Permissions to Groups
#     competitorGroup.permissions.add(competePermission)
#     competitorGroup.save()
#
# CtflexConfig.ready = lambda self:
#
# endregion
