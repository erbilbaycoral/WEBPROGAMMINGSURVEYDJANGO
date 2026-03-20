import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

REGION_CHOICES = [
    ('Marmara', 'Marmara'),
    ('Ege', 'Ege'),
    ('İç Anadolu', 'İç Anadolu'),
    ('Akdeniz', 'Akdeniz'),
    ('Karadeniz', 'Karadeniz'),
    ('Doğu Anadolu', 'Doğu Anadolu'),
    ('Güneydoğu Anadolu', 'Güneydoğu Anadolu'),
    ('Genel', 'Genel (Tüm Türkiye)'),
]

COUNTRY_CHOICES = [
    ('Türkiye', 'Türkiye'),
    ('ABD', 'Amerika Birleşik Devletleri'),
    ('Almanya', 'Almanya'),
    ('İngiltere', 'İngiltere'),
    ('Fransa', 'Fransa'),
]

QUESTION_TYPE_CHOICES = [
    ('Genel', 'Genel (Tüm Ülke)'),
    ('Bölgesel', 'Bölgesel'),
]

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES, default='Türkiye')
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPE_CHOICES, default='Genel')
    region = models.CharField(max_length=50, choices=REGION_CHOICES, default='Genel', blank=True, null=True)
    is_private_results = models.BooleanField(default=False)

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    last_username_change = models.DateTimeField(blank=True, null=True)
    country_preference = models.CharField(max_length=50, choices=COUNTRY_CHOICES, default='Türkiye')

    def __str__(self):
        return f"{self.user.username} Profile"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)
