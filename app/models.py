from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.forms import ValidationError
from django.utils import timezone
from django.contrib.auth.models import Group
from django.core.serializers import serialize
from django.utils.translation import gettext_lazy
import json


class UserManager(BaseUserManager):
    def _create_user(self, email, password, is_staff, is_superuser, name=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        now = timezone.now()
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            is_staff=is_staff,
            is_superuser=is_superuser,
            last_login=now,
            date_joined=now,
            is_active=True,
            name=name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)
    
    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=254, unique=True)
    name = models.CharField(max_length=254, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.email


class Restaurant(models.Model):
    # Django automatically adds an id field to the model
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    latitude = models.FloatField(
        validators=[
            MinValueValidator(-90.0, message="Latitude must be at least -90"),
            MaxValueValidator(90.0, message="Latitude must be at most 90")
        ]
    )
    longitude = models.FloatField(
        validators=[
            MinValueValidator(-180.0, message="Longitude must be at least -90"),
            MaxValueValidator(180.0, message="Longitude must be at most 90")
        ]
    )
    contact_info = models.CharField(max_length=200)
    menu_text = models.CharField(max_length=500, blank=True)
    admin_group = models.ForeignKey(Group, null=True, on_delete=models.SET_NULL)

    def get_average_rating(self):
        reviews = self.reviews.all()
        if len(reviews) == 0:
            return "N/A"
        return round(sum(review.rating for review in reviews) / len(reviews), 2)

    def get_average_cleanliness(self):
        reports = self.reports.filter(report_type='CL')
        if len(reports) == 0:
            return "N/A"
        return round(sum(report.rating for report in reports) / len(reports), 2)

    def get_average_crowdedness(self):
        reports = self.reports.filter(report_type='CR')
        if len(reports) == 0:
            return "N/A"
        return round(sum(report.rating for report in reports) / len(reports), 2)

    def get_average_friendliness(self):
        reports = self.reports.filter(report_type='FR')
        if len(reports) == 0:
            return "N/A"
        return round(sum(report.rating for report in reports) / len(reports), 2)

    def get_average_menu_quality(self):
        reports = self.reports.filter(report_type='MQ')
        if len(reports) == 0:
            return "N/A"
        return round(sum(report.rating for report in reports) / len(reports), 2)

    # Don't let methods with invalid coordinates be saved to the database
    def save(self, *args, **kwargs):
        if not (-90 <= self.latitude <= 90) or not (-180 <= self.longitude <= 180):
            raise ValidationError(
                "Invalid coordinates: Latitude must be between -90 and 90 and longitude must be between -180 and 180."
            )

        is_new = self._state.adding
        super(Restaurant, self).save(*args, **kwargs)

        if is_new or not self.admin_group:
            correct_group, created = Group.objects.get_or_create(name=str(self.pk) + ' admin')
            if created or self.admin_group != correct_group:
                self.admin_group = correct_group
                super(Restaurant, self).save(update_fields=['admin_group'])


    def __str__(self):
        return self.name


class Review(models.Model):
    user = models.ForeignKey(get_user_model(), related_name='reviews', on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1, message="Rating must be at least 1"),
            MaxValueValidator(5, message="Rating must be at most 5")
        ]
    )
    review_text = models.CharField(max_length=500)

    # Automatically set timestamp to current time and date
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} rated {self.restaurant} {self.rating}/5\n" \
               f"{self.review_text[:20]}..."


class Report(models.Model):
    # https://stackoverflow.com/questions/54802616/how-can-one-use-enums-as-a-choice-field-in-a-django-model
    class ReportType(models.TextChoices):
        CLEANLINESS = 'CL', gettext_lazy('Cleanliness')
        CROWDEDNESS = 'CR', gettext_lazy('Crowdedness')
        FRIENDLINESS = 'FR', gettext_lazy('Friendliness')
        MENU_QUALITY = 'MQ', gettext_lazy('Menu Quality')

    user = models.ForeignKey(get_user_model(), related_name='%(class)ss', on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, related_name='%(class)ss', on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1, message="Rating must be at least 1"),
            MaxValueValidator(5, message="Rating must be at most 5")
        ]
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    report_type = models.CharField(
        max_length=2,
        choices=ReportType.choices,
        default=ReportType.CLEANLINESS
    )

    def get_report_type(self):
        return self.ReportType(self.report_type).label

    def __str__(self):
        return f"{self.user} reported {self.restaurant}'s {self.get_report_type()} as {self.rating}/5\n"


class RestaurantRequest(models.Model):
    corresponding_restaurant = models.ForeignKey(Restaurant, null=True, on_delete=models.SET_NULL)
    requester = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(
        validators=[
            MinValueValidator(-90.0, message="Latitude must be at least -90"),
            MaxValueValidator(90.0, message="Latitude must be at most 90")
        ],
        blank=True
    )
    longitude = models.FloatField(
        validators=[
            MinValueValidator(-180.0, message="Longitude must be at least -90"),
            MaxValueValidator(180.0, message="Longitude must be at most 90")
        ],
        blank=True
    )
    menu_text = models.CharField(max_length=500, blank=True)
    contact_info = models.CharField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        if self.corresponding_restaurant is None:
            if self.latitude is None:
                self.latitude = 0
            if self.longitude is None:
                self.longitude = 0
            return super(RestaurantRequest, self).save(*args, **kwargs)
        corr_restaurant = self.corresponding_restaurant
        if self.name is None or self.name == '':
            self.name = corr_restaurant.name
        if self.address is None or self.address == '':
            self.address = corr_restaurant.address
        if self.latitude is None:
            self.latitude = corr_restaurant.latitude
        if self.longitude is None:
            self.longitude = corr_restaurant.longitude
        if self.contact_info is None or self.contact_info == '':
            self.contact_info = corr_restaurant.contact_info
        if self.menu_text is None or self.menu_text == '':
            self.menu_text = corr_restaurant.menu_text

        return super(RestaurantRequest, self).save(*args, **kwargs)

    def approve(self):
        if self.corresponding_restaurant is not None:
            existing_restaurant = self.corresponding_restaurant
            existing_restaurant.name = self.name
            existing_restaurant.address = self.address
            existing_restaurant.latitude = self.latitude
            existing_restaurant.longitude = self.longitude
            existing_restaurant.contact_info = self.contact_info
            existing_restaurant.menu_text = self.menu_text
            existing_restaurant.save()
        else:
            Restaurant.objects.create(
                name=self.name,
                address=self.address,
                latitude=self.latitude,
                longitude=self.longitude,
                contact_info=self.contact_info,
                menu_text=self.menu_text,
                admin_group=None
            )
        self.delete()


class RejectionMessage(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    for_what = models.CharField(max_length=100, blank=True)
    message = models.CharField(max_length=500)
    read = models.BooleanField(default=False)

    def __str__(self):
        return self.message
