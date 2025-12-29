from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings

from .models import User, Listing, Bid, Comment, Watchlist, Category, Notification
from .forms import ListingForm, BidForm, CommentForm


def index(request):
    listings = Listing.objects.filter(active=True).order_by('-created_at')
    return render(request, "auctions/index.html", {"listings": listings})


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url:
                return redirect(next_url)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {"message": "Invalid username and/or password."})
    return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {"message": "Passwords must match."})
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {"message": "Username already taken."})
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            return redirect('listing', listing_id=listing.id)
    else:
        form = ListingForm()
    return render(request, "auctions/create.html", {"form": form})


def listing_view(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    # Mark notifications for this listing as read for the viewing user
    if request.user.is_authenticated:
        request.user.notifications.filter(listing=listing, read=False).update(read=True)

    bid_form = BidForm()
    comment_form = CommentForm()
    in_watchlist = False
    if request.user.is_authenticated:
        in_watchlist = Watchlist.objects.filter(user=request.user, listing=listing).exists()

    error = None
    success = None

    if request.method == "POST":
        if 'place_bid' in request.POST:
            if not request.user.is_authenticated:
                return redirect('login')
            bid_form = BidForm(request.POST)
            if bid_form.is_valid():
                amount = bid_form.cleaned_data['amount']
                with transaction.atomic():
                    locked_listing = Listing.objects.select_for_update().get(pk=listing.id)
                    current = locked_listing.current_price()
                    if amount < locked_listing.starting_bid:
                        error = "Bid must be at least the starting bid."
                    elif locked_listing.bids.exists() and amount <= current:
                        error = "Bid must be greater than the current highest bid."
                    else:
                        # create the bid
                        new_bid = Bid.objects.create(
                            listing=locked_listing,
                            bidder=request.user,
                            amount=amount
                        )
                        success = "Your bid was placed."

                        # -----------------------------
                        # Create notification for owner
                        # -----------------------------
                        try:
                            notif_title = f"New bid on your listing: {locked_listing.title}"
                            notif_message = (
                                f"{request.user.username} placed a bid of ${new_bid.amount:.2f} "
                                f"on your listing \"{locked_listing.title}\"."
                            )
                            listing_url = reverse('listing', args=(locked_listing.id,))
                            Notification.objects.create(
                                recipient=locked_listing.owner,
                                title=notif_title,
                                message=notif_message,
                                listing=locked_listing,
                                url=listing_url,
                                owner_email=locked_listing.owner.email or ""
                            )

                            # Optional email alert to listing owner (controlled by settings)
                            if getattr(settings, 'EMAIL_NOTIFICATIONS_ENABLED', False) and locked_listing.owner.email:
                                subject = notif_title
                                body_lines = [
                                    notif_message,
                                    "",
                                    f"View the listing: {request.build_absolute_uri(listing_url)}",
                                ]
                                body = "\n".join([line for line in body_lines if line])
                                send_mail(
                                    subject,
                                    body,
                                    getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                                    [locked_listing.owner.email],
                                    fail_silently=True
                                )
                        except Exception:
                            # Fail silently for notification/email errors so bidding still succeeds
                            pass

                        return redirect('listing', listing_id=listing.id)

        elif 'add_comment' in request.POST:
            if not request.user.is_authenticated:
                return redirect('login')
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.listing = listing
                comment.commenter = request.user
                comment.save()
                return redirect('listing', listing_id=listing.id)

        elif 'toggle_watch' in request.POST:
            if not request.user.is_authenticated:
                return redirect('login')
            watch_item = Watchlist.objects.filter(user=request.user, listing=listing).first()
            if watch_item:
                watch_item.delete()
            else:
                Watchlist.objects.create(user=request.user, listing=listing)
            return redirect('listing', listing_id=listing.id)

        elif 'close_listing' in request.POST:
            if not request.user.is_authenticated or request.user != listing.owner:
                raise Http404
            top_bid = listing.bids.order_by('-amount').first()
            listing.winner = top_bid.bidder if top_bid else None
            listing.active = False
            listing.save()

            # Create in-app notification and include owner email
            if listing.winner:
                notif_title = f"You won the auction: {listing.title}"
                notif_message = (
                    f"Congratulations — you won the auction \"{listing.title}\" "
                    f"with a bid of ${top_bid.amount:.2f}."
                )
                listing_url = reverse('listing', args=(listing.id,))
                owner_email = listing.owner.email or ""

                Notification.objects.create(
                    recipient=listing.winner,
                    title=notif_title,
                    message=notif_message,
                    listing=listing,
                    url=listing_url,
                    owner_email=owner_email
                )

                # Optional email alert to winner
                try:
                    if getattr(settings, 'EMAIL_NOTIFICATIONS_ENABLED', False) and listing.winner.email:
                        subject = notif_title
                        body_lines = [
                            notif_message,
                            "",
                            f"Auction owner (to contact): {owner_email}" if owner_email else "",
                            f"View the listing: {request.build_absolute_uri(listing_url)}",
                            "",
                            "You can contact the auction owner to arrange payment/delivery."
                        ]
                        body = "\n".join([line for line in body_lines if line])
                        send_mail(
                            subject,
                            body,
                            getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                            [listing.winner.email],
                            fail_silently=True
                        )
                except Exception:
                    pass

            return redirect('listing', listing_id=listing.id)

    winner_bid = listing.bids.order_by('-amount').first()
    winner_user = listing.winner if listing.winner else (winner_bid.bidder if winner_bid else None)
    user_won = request.user.is_authenticated and (winner_user == request.user) and not listing.active
    current_price = listing.current_price()

    context = {
        "listing": listing,
        "bid_form": bid_form,
        "comment_form": comment_form,
        "in_watchlist": in_watchlist,
        "error": error,
        "success": success,
        "winner_bid": winner_bid,
        "winner_user": winner_user,
        "user_won": user_won,
        "current_price": current_price,
    }
    return render(request, "auctions/listing.html", context)


@login_required
def watchlist_view(request):
    items = Watchlist.objects.filter(user=request.user).select_related('listing').order_by('-added_at')
    listings = [w.listing for w in items]
    return render(request, "auctions/watchlist.html", {"listings": listings})


def categories_view(request):
    categories = Category.objects.all().order_by('name')
    return render(request, "auctions/categories.html", {"categories": categories})


def category_listings(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    listings = category.listings.filter(active=True).order_by('-created_at')
    return render(request, "auctions/category_listings.html", {
        "listings": listings,
        "category": category
    })

@login_required
def my_activity(request):
    user = request.user

    # Won auctions
    won_listings = Listing.objects.filter(winner=user).order_by('-created_at')

    # User's listings split into active and closed
    listings_created_active = Listing.objects.filter(owner=user, active=True).order_by('-created_at')
    listings_created_closed = Listing.objects.filter(owner=user, active=False).order_by('-created_at')

    # User's bids
    my_bids = Bid.objects.filter(bidder=user).select_related('listing').order_by('-timestamp')

    # Highest bid by the user per listing (for the badge)
    from django.db.models import Max
    highest_by_listing = my_bids.values('listing').annotate(max_amount=Max('amount'))
    highest_map = {entry['listing']: entry['max_amount'] for entry in highest_by_listing}

    context = {
        "won_listings": won_listings,
        "listings_created_active": listings_created_active,
        "listings_created_closed": listings_created_closed,
        "my_bids": my_bids,
        "highest_map": highest_map,
    }
    return render(request, "auctions/my_activity.html", context)


@login_required
def notifications_view(request):
    notifs = request.user.notifications.all()
    if request.method == "POST" and request.POST.get("mark_all_read"):
        notifs.update(read=True)
        return redirect('notifications')
    return render(request, "auctions/notifications.html", {"notifications": notifs})
