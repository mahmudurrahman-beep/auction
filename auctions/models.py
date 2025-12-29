from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    pass

class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name

class Listing(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True, null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="listings"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="listings"
    )
    active = models.BooleanField(default=True)
    # optional persisted winner (recommended)
    winner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_listings'
    )
    created_at = models.DateTimeField(default=timezone.now)

    def current_price(self):
        highest = self.bids.order_by('-amount').first()
        return highest.amount if highest else self.starting_bid

    def highest_bidder(self):
        highest = self.bids.order_by('-amount').first()
        return highest.bidder if highest else None

    def __str__(self):
        return f"{self.title} (${self.current_price()})"

class Bid(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="bids"
    )
    bidder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bids"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-amount', '-timestamp']

    def __str__(self):
        return f"{self.amount} by {self.bidder} on {self.listing}"

class Comment(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    commenter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Comment by {self.commenter} on {self.listing}"

class Watchlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watchlist_items"
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="watched_by"
    )
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'listing')

    def __str__(self):
        return f"{self.user} watches {self.listing}"
    
    
class Notification(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=140)
    message = models.TextField(blank=True)
    listing = models.ForeignKey(
        'Listing',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    url = models.CharField(max_length=255, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    # store the auction owner's email at the time the notification is created
    owner_email = models.EmailField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.username}: {self.title}"

