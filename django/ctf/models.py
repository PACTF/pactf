from os.path import join
import importlib.machinery

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group, Permission

import markdown2


# region User Models (by wrapping)

class Team(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40, unique=True)
    score = models.IntegerField(default=0)

    def __str__(self):
        return "<Team #{} {!r}>".format(self.id, self.name)


class Competitor(models.Model):
    """Represents a competitor 'profile'

    Django's User class's fields are shunned. The only ones that are used are:

        username, password, is_active, is_staff, date_joined

    """

    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)

    # Shunned fields
    first_name = models.CharField("First name", max_length=30, blank=True)
    last_name = models.CharField("Last name", max_length=30, blank=True)
    email = models.EmailField("Email", unique=True)

    def __str__(self):
        return "<Competitor #{} {!r}>".format(self.id, self.user.name)


# endregion


# region Contest Models

class CtfProblem(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=20)

    points = models.IntegerField()
    description = models.TextField()
    description_html = models.TextField(editable=False)
    hint = models.TextField(default='')
    hint_html = models.TextField(editable=False, blank=True, null=True)

    grader = models.FilePathField(
        help_text="Basename of the grading script from PROBLEM_DIR",
        path=settings.PROBLEMS_DIR, recursive=True, match=r'^.*\.py$'
    )

    def __str__(self):
        return "<Problem #{} {!r}>".format(self.id, self.name)

    def grade(self, flag):
        # FIXME(Yatharth): Have real team id forwarded
        if not flag:
            return False, "Empty flag"

        grader_path = join(settings.PROBLEMS_DIR, self.grader)
        grader = importlib.machinery.SourceFileLoader('grader', grader_path).load_module()
        correct, message = grader.grade(1, flag)
        return correct, message

    def save(self, **kwargs):
        EXTRAS = ('fenced-code-blocks', 'smarty-pants', 'spoiler')

        # markdown's safe_mode is deprecated
        self.description_html = markdown2.markdown(self.description, extras=EXTRAS, safe_mode='escape')
        self.hint_html = markdown2.markdown(self.hint, extras=EXTRAS, safe_mode='escape')
        self.full_clean()
        super().save(**kwargs)


# FIXME(Yatharth): Review Submission model
# FIXME(Yatharth): Write __str__ method
class Submission(models.Model):
    p_id = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True)
    # FIXME: Rename to competitor
    user = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, editable=False, blank=True)
    flag = models.CharField(max_length=80)
    correct = models.NullBooleanField()

    def save(self, **kwargs):
        self.team = self.user.team
        super().save(**kwargs)

# endregion



# region Permissions and Groups
#
# class GlobalPermissionManager(models.Manager):
#     def get_query_set(self):
#         return super(GlobalPermissionManager, self).filter(content_type__name='global_permission')
#
#
# class GlobalPermission(Permission):
#     """A global permission, not attached to a model"""
#
#     objects = GlobalPermissionManager()
#
#     class Meta:
#         proxy = True
#
#     def save(self, *args, **kwargs):
#         content_type, created = ContentType.objects.get_or_create(
#             model="global_permission", app_label=self._meta.app_label
#         )
#         self.content_type = content_type
#         super().save(*args, **kwargs)
#
# @receiver(post_save, sender=Competitor, dispatch_uid='ctf.competitor_post_save_add_to_group')
# def competitor_post_save_add_to_group(sender, instance, created, **kwargs):
#     if created:
#         competitorGroup = Group.objects.get(name=COMPETITOR_GROUP_NAME)
#         instance.user.groups.add(competitorGroup)
#
#
# @receiver(post_delete, sender=Competitor, dispatch_uid='ctf.competitor_post_delete_remove_from_group')
# def competitor_post_delete_remove_from_group(sender, instance, created, **kwargs):
#     if created:
#         competitorGroup = Group.objects.get(name=COMPETITOR_GROUP_NAME)
#         instance.user.groups.remove(competitorGroup)
#
# endregion


# region User Models (by substitution)
#
# class CompetitorManager(BaseUserManager):
#     def create_user(username, fullname, email, team, password=None):
#         pass
#
#     def create_superuser(self, username, fullname, email, team, password):
#         pass
#
# class Competitor(AbstractBaseUser):
#     username = models.CharField(max_length=40, unique=True)
#     fullname = models.CharField(max_length=100)
#     email = models.EmailField()
#     team = models.ForeignKey(Team, on_delete=models.CASCADE)
#
#     USERNAME_FIELD = 'username'
#     REQUIRED_FIELDS = ['fullname', 'email', 'team']
#
#     def get_short_name(self):
#         return self.username
#
#     def get_full_name(self):
#         return self.fullname
#
#     objects = CompetitorManager()
#
# endregion
