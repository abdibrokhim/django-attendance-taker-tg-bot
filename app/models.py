from django.db import models


class Person(models.Model):
    tg_id = models.CharField(max_length=254)
    tg_username = models.CharField(max_length=254)
    tg_fullname = models.CharField(max_length=254)
    arrived_at = models.DateTimeField(blank=True, default=None, null=True)
    left_at = models.DateTimeField(blank=True, default=None, null=True)

    def __str__(self):
        return self.tg_id
