from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from . import views
app_name = 'home'

urlpatterns = [
    path('create/', views.create, name='create'),
    path('', views.opening, name='opening'),
    path('activate/<uidb64>/<token>',views.activate,name="activate"),
    path('auctions', views.auctions, name='auctions'),
    path('<int:auction_id>/', views.detail, name='detail'),
    path('<int:auction_id>/bid/', views.bid, name='bid'),
    path('index', views.index, name="index"),
    path('my_auctions', views.my_auctions, name="my_auctions"),
    path('my_bids', views.my_bids, name="my_bids"),
    path('contact_us',views.contact_us,name="contact_us"),
    path('loginuser/', views.loginuser, name='loginuser'),
    path('signup', views.signup, name="signup"),
    path('logoutuser', views.logoutuser, name="logoutuser")
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
