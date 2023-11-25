from django.db import models



class TimeModels(models.Model):
    """ Automatic created and updated date and time"""
    created = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        abstract = True



# Owners models 
class Owners(TimeModels):
    SEX_TYPE = (
        ("Male", "Male"),
        ("Female", "Female")
    )
    MARITAL_STATUS = (
        ("Single", "Single"),
        ("Married", "Married"),
        ("Divorced", "Divorced")
    )
    OCCUPATION = (
        ("Student", "Student"),
        ("Civil Servant", "Civil Servant"),
        ("Business", "Business")
    )

    full_name = models.CharField(max_length=20)
    sex = models.CharField(choices=SEX_TYPE ,max_length=50)
    marital_status = models.CharField(choices=MARITAL_STATUS ,max_length=50)
    occupation = models.CharField(choices=OCCUPATION, max_length=50)
    date_of_birth = models.DateField(auto_now=False, auto_now_add=False)
    phone = models.CharField(max_length=20)
    email = models.EmailField(max_length=254)
    residential_address = models.CharField(max_length=50)
    state = models.CharField(max_length=15)
    nationality = models.CharField(max_length=15)



