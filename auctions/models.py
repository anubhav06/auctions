from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.deletion import CASCADE
from django.db.models.fields import FilePathField


class User(AbstractUser):
    #pass
    
    def __str__(self):
        return f"{self.username}"



class Listings(models.Model):

    title = models.CharField(max_length=64) 
    description = models.CharField(max_length=192)
    price = models.DecimalField(max_digits=10000, decimal_places=2)
    photo = models.CharField(max_length=1100)
    category = models.CharField(max_length=64)
    active = models.BooleanField(default=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")

    def __str__(self):
        return f"{self.id} : {self.user} - {self.title} - {self.category} - {self.active}"


class Watchlist(models.Model):
    watchlister = models.ForeignKey(User, blank=True, on_delete=models.CASCADE, related_name="watchlister")
    listing = models.ForeignKey(Listings, blank=True ,on_delete=models.CASCADE, related_name="list")

    def __str__(self):
        return f"{self.watchlister}: {self.listing}"


class Bids(models.Model):
    quote = models.DecimalField(max_digits=1000000, decimal_places=2)
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bidder")
    listing = models.ForeignKey(Listings, on_delete=models.CASCADE, related_name="listing")

    def __str__(self):
        return f"[ {self.quote} by {self.bidder} to {self.listing} ]"



class Comments(models.Model):
    comment = models.CharField(max_length=100)
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="commenter")
    auction = models.ForeignKey(Listings, on_delete=models.CASCADE, related_name="auction")

    def __str__(self):
        return f"{self.commenter} says {self.comment} for {self.auction}"