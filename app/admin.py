from django.contrib import admin
from .models import Person


class PersonAdmin(admin.ModelAdmin):
    list_display = ('tg_id', 'tg_username', 'tg_fullname', 'arrived_at', 'left_at')


admin.site.register(Person, PersonAdmin)
