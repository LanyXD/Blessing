from django.contrib import admin
from .models import Log, LogDetail

class LogDetailInline(admin.TabularInline):
    model = LogDetail
    extra = 0

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'logout_time')
    inlines = [LogDetailInline]

@admin.register(LogDetail)
class LogDetailAdmin(admin.ModelAdmin):
    list_display = ('log', 'action', 'affected_table', 'date')