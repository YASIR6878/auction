# notifications.py
from django.core.mail import send_mail

def send_winner_notification(winner, auction):
    # Notify the winner
    winner_subject = 'Congratulations! You won the auction'
    winner_message = f'Congratulations! You won the auction for {auction.title}.'
    winner_from_email = 'olx6094@gmail.com'  # Replace with your email
    winner_recipient_list = [winner.email]

    send_mail(winner_subject, winner_message, winner_from_email, winner_recipient_list, fail_silently=False)

    # Notify the owner
    owner_subject = f'Your product {auction.title} has been sold'
    owner_message = f'Your product {auction.title} has been sold in the auction. The winner is {winner.username}.'
    owner_from_email = 'olx6094@gmail.com'  # Replace with your email
    owner_recipient_list = [auction.user.email]

    send_mail(owner_subject, owner_message, owner_from_email, owner_recipient_list, fail_silently=False)
