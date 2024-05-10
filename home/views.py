from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from .tokens import account_activation_token
from .formss import ContactForm
from .models import Auction, Bid
from datetime import datetime, timezone

# Main page

def opening(request):
     if request.user.is_anonymous:
          return render(request,'opening.html')
     else:
          return redirect('home:index')
      

def loginuser(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('pass1')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home:index')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def logoutuser(request):
    logout(request)
    return redirect('home:loginuser')

def signup(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            pass1 = form.cleaned_data['pass1']
            pass2 = form.cleaned_data['pass2']

            if pass1 == pass2:
                if get_user_model().objects.filter(username=username).exists():
                    messages.error(request, 'Username already exists.')
                elif get_user_model().objects.filter(email=email).exists():
                    messages.error(request, 'Email already exists.')
                else:
                    user = get_user_model().objects.create_user(username=username, email=email, password=pass1)
                    user.is_active = False
                    user.save()
                    token = account_activation_token.make_token(user)
                    user.confirmation_token = token
                    user.save()
                    activateEmail(request, user, email)
                    messages.success(request, 'Account created successfully. Check your email for activation instructions.')
            else:
                messages.error(request, 'Passwords do not match.')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = ContactForm()
    return render(request, 'signup.html', {'form': form})

def index(request):
      if request.user.is_authenticated:
        # First get all auctions and resolve them
        user=request.user
        auction_list = Auction.objects.all()
        for a in auction_list:
            a.resolve()
        # Get all active auctions, oldest first
        latest_auction_list = auction_list.filter(is_active=True).order_by('date_added')
        return render(request, 'index.html', {'title': "Active auctions",'user':user, 'auction_list': latest_auction_list})
      else:
         return redirect('home:loginuser')

def auctions(request):
    if request.user.is_anonymous:
          return redirect('home:loginuser')
    else:
       auction_list = Auction.objects.order_by('-date_added')
       for a in auction_list:
           a.resolve()
       return render(request, 'index.html', {'title': "All auctions", 'auction_list': auction_list})

# Details on some auction

def detail(request, auction_id):
        if request.user.is_anonymous:
          return redirect('home:loginuser')
        else:
           auction = get_object_or_404(Auction, pk=auction_id)
           auction.resolve()
           already_bid = False
           if request.user.is_authenticated:
               
               if auction.author == request.user:
                   own_auction = True
                   return render(request, 'detail.html', {'auction': auction, 'own_auction': own_auction})
       
               user_bid = Bid.objects.filter(bidder=request.user).filter(auction=auction).first()
               if user_bid:
                   already_bid = True
                   bid_amount = user_bid.amount
                   return render(request, 'detail.html', {'auction': auction, 'already_bid': already_bid, 'bid_amount': bid_amount})
       
           return render(request, 'detail.html', {'auction': auction, 'already_bid': already_bid})

# Bid on some auction
def bid(request, auction_id):
        if request.user.is_anonymous:
          return redirect('home:loginuser')
        else:
         
            auction = get_object_or_404(Auction, pk=auction_id)
            auction.resolve()
            bid = Bid.objects.filter(bidder=request.user).filter(auction=auction).first()
            if not auction.is_active:
                return render(request, 'detail.html', {
                    'auction': auction,
                    'error_message': "The auction has expired.",
                })
        
            try:
                bid_amount = request.POST['amount']
                # Prevent user from entering an empty or invalid bid
                highest_bid = Bid.objects.filter(auction=auction).order_by('-amount').first()
                if highest_bid:
                 if not bid_amount or int(bid_amount) < highest_bid.amount:
                    raise(KeyError)
                else:
                      if not bid_amount or int(bid_amount) < auction.min_value:
                       raise(KeyError)
                if not bid:
                    # Create new Bid object if it does not exist
                    bid = Bid()
                    bid.auction = auction
                    bid.bidder = request.user
                bid.amount = bid_amount
                bid.date = datetime.now(timezone.utc)
                bid.save()
            except (KeyError):
                # Redisplay the auction details.
                return render(request, 'detail.html', {
                    'auction': auction,
                    'error_message': "Invalid bid amount.",
                })
            else:
                
        
                return redirect('home:index')
        


# Create auction

def create(request):
        if request.user.is_anonymous:
          return redirect('home:loginuser')
        else:
         if request.method == 'POST':
             title = request.POST.get('title')
             duration = request.POST.get('duration')
             min_value = request.POST.get('min_value')
             contact = request.POST.get('contact')
             description = request.POST.get('description')
             img = request.FILES.get('img')
             if title and duration and min_value and contact:
                 auction = Auction.objects.create(
                     author=request.user,
                     title=title,
                     duration=duration,
                     min_value=min_value,
                     contact=contact,
                     desc=description,
                     image=img,
                     date_added=datetime.now(timezone.utc)
                 )
                 registered_user_emails = get_registered_user_emails()
                 send_email_to_all(registered_user_emails,auction.title)
                 return redirect('home:my_auctions')
             else:
                 messages.error(request, "Please fill all the required fields.")
         return render(request, 'create.html')


def my_auctions(request):
        if request.user.is_anonymous:
          return redirect('home:loginuser')
        else:
          my_auctions_list = Auction.objects.filter(author=request.user).order_by('-date_added')
          for a in my_auctions_list:
              a.resolve()
          return render(request, 'my_auctions.html', {'my_auctions_list': my_auctions_list})

def my_bids(request):
        if request.user.is_anonymous:
          return redirect('home:loginuser')
        else:
          my_bids_list = Bid.objects.filter(bidder=request.user).order_by('-date')
          for b in my_bids_list:
              b.auction.resolve()
          return render(request, 'my_bids.html', {'my_bids_list': my_bids_list})

def activateEmail(request,user,to_email):
    subject='Confirm Your Signup'
    message=render_to_string('activate_account.html',{
        'user':user.username,
        'domain':get_current_site(request).domain,
        'uid':urlsafe_base64_encode(force_bytes(user.pk)),
        'token':account_activation_token.make_token(user),
        "protocol":'https' if request.is_secure()else 'http'
    })
    email=EmailMessage(subject,message,to=[to_email])
    if email.send():
       messages.success(request,f'Dear <b>{user}<b>,Please check your email <b>{to_email}<b>for Confirmation.')
    else:
        messages.error(request,'Check Your Email again!')

from django.contrib import messages

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except User.DoesNotExist:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Account activated successfully. You can now log in.')
        return redirect('home:loginuser')
    else:
        messages.error(request, 'Activation Link is Expired or invalid.')
        return redirect('home:signup')


def contact_us(request):
    if request.method == 'POST':
        name = request.POST['name']
        user_email = request.POST['email']
        message = request.POST['message']

        # Create an EmailMessage instance
        email = EmailMessage(
            'User Review',
            f'Name: {name}\nEmail: {user_email}\nMessage: {message}',
            user_email,
            ['yasirmanzoor6878@gmail.com'],  # Receiver
        )

        # Send the email
        email.send()
    return render(request, 'contact.html')


from django.contrib.auth.models import User
def get_registered_user_emails():
    registered_users = User.objects.all()
    user_emails = [user.email for user in registered_users if user.email]
    return user_emails


from django.core.mail import send_mail
def send_email_to_all(all_user_emails, message):
    subject="New product has been added to Auction!"
    send_mail(subject, message, None, all_user_emails)