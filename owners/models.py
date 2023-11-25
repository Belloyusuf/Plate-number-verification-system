from django.db import models



class TimeModels(models.Model):
    """ Automatic created and updated date and time"""
    created = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        abstract = True




class Owners(TimeModels):
    SEX_TYPE = (
        ("Male", "Male"),
        ("Female", "Female")
    )
    full_name = models.CharField(max_length=20)
    sex = models.CharField(choices=SEX_TYPE ,max_length=50)