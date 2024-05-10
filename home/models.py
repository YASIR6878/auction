from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, datetime, timezone
from math import ceil
from django.core.mail import send_mail
# Auction duration in minutes



class Auction(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    desc = models.CharField(max_length=2000, blank=True)
    contact=models.TextField(default=7889307466)
    image = models.ImageField(upload_to='item_images/', blank=True)
    min_value = models.IntegerField()
    date_added = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    duration = models.PositiveIntegerField(default=5)  # Default duration in minutes
    winner = models.ForeignKey(User, on_delete=models.SET("(deleted)"),
                               blank=True,
                               null=True,
                               related_name="auction_winner",
                               related_query_name="auction_winner")
    final_value = models.IntegerField(blank=True, null=True)

    def resolve(self):
        if self.is_active:
            if self.has_expired():
                highest_bid = Bid.objects.filter(auction=self).order_by('-amount', '-date').first()
                if highest_bid:
                    self.winner = highest_bid.bidder
                    self.final_value = highest_bid.amount
                    self.is_active = False
                    self.save()
                    if self.winner is not None:
                       self.handle_resolution()
                else:
                    self.is_active=False
                    self.winner=None
                    self.save()
        highest_bid = Bid.objects.filter(auction=self).order_by('-amount', '-date').first()
        if highest_bid:
            return highest_bid.amount
        else:
             return None   
  
        

    # Helper function that determines if the auction has expired
    def has_expired(self):
        now = datetime.now(timezone.utc)
        expiration = self.date_added + timedelta(minutes=self.duration)
        if now > expiration:
            return True
        else:
            return False

    # Returns the ceiling of remaining_time in minutes
    @property
    def remaining_minutes(self):
        if self.is_active:
            now = datetime.now(timezone.utc)
            expiration = self.date_added + timedelta(minutes=self.duration)
            minutes_remaining = ceil((expiration - now).total_seconds() / 60)
            if minutes_remaining<0:
                return 0
            else:
                return(minutes_remaining)
        else:
            return(0)

    def handle_resolution(self):
        # Send notification to the winner
        send_winner_notification(self.winner, self)

        # Send notification to the owner (author) of the auction
        send_owner_notification(self.author, self)

    # ... (other methods)


class Bid(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    amount = models.IntegerField()
    # is_cancelled = models.BooleanField(default=False)
    date = models.DateTimeField('when the bid was made')

def send_winner_notification(winner, auction):
       subject = 'Congratulations! You won the auction'
       message = f'Congratulations! You won the auction for {auction.title}.'
       from_email = 'olx6094@gmail.com'  # Replace with your email
       recipient_list = [auction.winner.email]
   
       send_mail(subject, message, from_email, recipient_list, fail_silently=False)

def send_owner_notification(owner, auction):
        subject = f'Your product {auction.title} has been sold'
        message = f'Your product {auction.title} has been sold in the auction. The winner is {auction.winner.username}.'
        from_email = 'olx6094@gmail.com'  # Replace with your email
        recipient_list = [owner.email]
    
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

