from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create_listing, name="create"),
    path("listing/<int:listing_id>", views.listing_view, name="listing"),
    path("watchlist", views.watchlist_view, name="watchlist"),
    path("categories", views.categories_view, name="categories"),
    path("categories/<int:category_id>", views.category_listings, name="category_listings"),
    path("my_activity", views.my_activity, name="my_activity"),
    path("notifications", views.notifications_view, name="notifications"),

]
