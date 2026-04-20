from django.db import models
from apps.accounts.models import User

class Log(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'log'

    def __str__(self):
        return f'{self.user} - {self.login_time}'


class LogDetail(models.Model):
    log = models.ForeignKey(Log, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    affected_table = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'log_detail'

    def __str__(self):
        return f'{self.action} - {self.affected_table}'