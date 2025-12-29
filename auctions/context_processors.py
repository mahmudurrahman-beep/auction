def notifications_count(request):
    if request.user.is_authenticated:
        unread = request.user.notifications.filter(read=False).count()
        return {"notifications_unread_count": unread}
    return {"notifications_unread_count": 0}
