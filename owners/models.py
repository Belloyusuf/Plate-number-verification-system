from django.db import models



class TimeModels(models.Model):
    """ Automatic created and updated date and time"""
    created = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        abstract = True


# Owners models 
class Owner(TimeModels):

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

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Owner'
        verbose_name_plural = 'Owners'


# Car Registration model 
class CarRegisteration(TimeModels):
    """ Car registration details  """
    owner = models.ForeignKey(Owner, verbose_name=("Owner"), on_delete=models.CASCADE)
    car_name = models.CharField(max_length=15)
    drivers_license = models.CharField(max_length=50)
    vehicle_insurance = models.CharField(("Vehicle Insurance Number"), max_length=50)
    nin = models.CharField(("NIN"), max_length=15)
    proof_address = models.CharField(max_length=50)
    tin = models.CharField(("Tax Identification Number"), max_length=15)
    custom_clearance = models.ImageField(upload_to="customclearance", height_field=None, width_field=None, max_length=None)
    vehicle_engine = models.CharField(("Vehicle Engine Number"), max_length=15)
    proof_of_ownership = models.ImageField(upload_to="proof", height_field=None, width_field=None, max_length=None)
    passport = models.ImageField(("Two passport of ownership"), upload_to=None, height_field=None, width_field=None, max_length=None)


    def __str__(self):
        return self.owner
    