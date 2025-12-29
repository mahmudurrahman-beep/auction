# auctions/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.admin import UserAdmin

from .models import (
    User,
    Category,
    Listing,
    Bid,
    Comment,
    Watchlist,
    Notification,
)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "owner",
        "current_price_display",
        "winner_display",
        "active",
        "category",
        "created_at",
    )
    list_filter = ("active", "category", "created_at", "owner")
    search_fields = ("title", "description", "owner__username")
    readonly_fields = ("created_at", "winner")
    actions = ("close_auctions", "reopen_auctions")

    def current_price_display(self, obj):
        price = obj.current_price()
        return f"${price:.2f}"
    current_price_display.short_description = "Current Price"

    def winner_display(self, obj):
        return obj.winner.username if obj.winner else "-"
    winner_display.short_description = "Winner"

    def close_auctions(self, request, queryset):
        """
        Close selected auctions. For each closed listing, set the highest bidder
        as the winner (if any) and mark active=False.
        """
        closed_count = 0
        for listing in queryset.filter(active=True):
            top_bid = listing.bids.order_by("-amount", "-timestamp").first()
            if top_bid:
                listing.winner = top_bid.bidder
            else:
                listing.winner = None
            listing.active = False
            listing.save()
            closed_count += 1
        self.message_user(request, f"Closed {closed_count} auction(s).")
    close_auctions.short_description = "Close selected auctions"

    def reopen_auctions(self, request, queryset):
        """
        Reopen selected auctions. Mark active=True and clear winner so auction
        can accept new bids again.
        """
        reopened_count = 0
        for listing in queryset.filter(active=False):
            listing.active = True
            listing.winner = None
            listing.save()
            reopened_count += 1
        self.message_user(request, f"Reopened {reopened_count} auction(s).")
    reopen_auctions.short_description = "Reopen selected auctions"


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "listing_link", "bidder", "amount", "timestamp")
    list_filter = ("timestamp", "bidder")
    search_fields = ("listing__title", "bidder__username")
    ordering = ("-amount", "-timestamp")

    def listing_link(self, obj):
        url = reverse("admin:auctions_listing_change", args=(obj.listing.id,))
        return format_html('<a href="{}">{}</a>', url, obj.listing.title)
    listing_link.short_description = "Listing"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "listing_link", "commenter", "short_content", "timestamp")
    search_fields = ("content", "commenter__username", "listing__title")
    list_filter = ("timestamp",)

    def listing_link(self, obj):
        url = reverse("admin:auctions_listing_change", args=(obj.listing.id,))
        return format_html('<a href="{}">{}</a>', url, obj.listing.title)
    listing_link.short_description = "Listing"

    def short_content(self, obj):
        return (obj.content[:75] + "...") if len(obj.content) > 75 else obj.content
    short_content.short_description = "Content"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "listing", "added_at")
    search_fields = ("user__username", "listing__title")
    list_filter = ("added_at",)


# Register the custom User model with default UserAdmin
admin.site.register(User, UserAdmin)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "title", "owner_email", "read", "created_at")
    list_filter = ("read", "created_at")
    search_fields = ("recipient__username", "title", "message", "owner_email")
