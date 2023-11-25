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
    VEHICLE_CATEGORIES = (
        ("Government", "Government"),
        ("Commercial", "Commercial"),
        ("Private", "Private")
    )

    VEHICLE_SUB_CATEGORY = (
        ("Diplomatic and Foreign Mission", "Diplomatic and Foreign Mission"),
        ("Federal Parastatals/Agencies/Department", "Federal Parastatals/Agencies/Department"),
        ("LGA", "LGA"),
        ("Military/Paramilitaries", "Military/Paramilitaries"),
        ("State Ministries/Agencies/Department")
    )

    VEHICLE_MAKE = (
        (100, 100),
        (1617, 1617),
        (190, 190),
        (420, 420),
        ("5 SERIES", "5 SERIES")
    )

    FUEL_TYPE = (
        ("Petrol", "Petrol"),
        ("Diesel", "Diesel"),
        ("Bio-Fuel", "Bio-Fuel")
    )

    VEHICLE_TYPE = (
        ("Telsa", "Telsa"),
        ("BMW", "BMW"),
        ("Ferrari", "Ferrari"),
        ("Honda", "Honda"),
        ("Toyota", "Toyota"),
        ("Audi", "Audi"),
        ("Jeep", "Jeep"),
        ("Mazda", "Mazda"),
        ("Nissan", "Nissan")
    )

    ENGINE_CAPACITY =(
        ("Above 3.0", "Above 3.0"),
        ("Below 1.6", "Below 1.6"),
        ("Between 1.6 and 2.0", "Between 1.6 and 2.0"),
        ("Between 2.1 and 3.0", "Between 2.1 and 3.0")
    )

    vehicle_category = models.CharField(choices=VEHICLE_CATEGORIES, max_length=15)
    vehicle_sub_category = models.CharField(choices=VEHICLE_SUB_CATEGORY, max_length=15)
    old_plate_number = models.CharField(max_length=20)
    vehicle_make = models.CharField(max_length=10)
    color = models.CharField(max_length=10)
    fuel_type = models.CharField(choices=FUEL_TYPE, max_length=50)
    year_of_manufacture = models.CharField(max_length=4, help_text="2000")
    model = models.CharField(max_length=10)
    engine_number = models.CharField(max_length=10)
    policy_number = models.CharField(max_length=10)
    vehicle_type = models.CharField(("Vehicle Type/Group"), choices=VEHICLE_TYPE, max_length=50)
    chassis_no = models.CharField(("Chassis Number"), max_length=15)
    engine_capacity = models.CharField(choices=ENGINE_CAPACITY, max_length=50)
    tank_capacity = models.CharField(max_length=5)
    odometer = models.CharField(max_length=15)

    def __str__(self):
        return self.owner
    

