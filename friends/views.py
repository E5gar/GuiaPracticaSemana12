from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from config.sanitizers import safe_redirect_target

from .forms import FriendActionForm, FriendSearchForm
from .models import ACCEPTED, PENDING, Friendship, attach_relations, friend_ids

User = get_user_model()


@login_required
def friend_list(request):
    ids = friend_ids(request.user)
    friends = User.objects.filter(id__in=ids).select_related("profile").order_by("first_name", "username")
    friends = attach_relations(request.user, friends)
    return render(request, "friends/friend_list.html", {"friends": friends})


@login_required
def friend_search(request):
    form = FriendSearchForm(request.GET or None)
    people = User.objects.filter(is_active=True).exclude(pk=request.user.pk).select_related("profile")
    term = form.cleaned_data["q"] if form.is_bound and form.is_valid() else ""
    if term:
        people = people.filter(
            Q(username__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term)
        )
    results = attach_relations(request.user, people.order_by("-date_joined")[:24])
    return render(request, "friends/friend_search.html", {"form": form, "results": results, "term": term})


@login_required
def friend_requests(request):
    received = list(
        Friendship.objects.filter(to_user=request.user, status=PENDING).select_related(
            "from_user", "from_user__profile"
        )
    )
    sent = list(
        Friendship.objects.filter(from_user=request.user, status=PENDING).select_related(
            "to_user", "to_user__profile"
        )
    )
    for item in received:
        item.from_user.relation = "received"
    for item in sent:
        item.to_user.relation = "sent"
    return render(request, "friends/friend_requests.html", {"received": received, "sent": sent})


@login_required
@require_POST
def friend_action(request):
    destination = safe_redirect_target(request, "friends:list")
    form = FriendActionForm(request.POST)
    if not form.is_valid():
        messages.error(request, "No se pudo procesar la solicitud.")
        return redirect(destination)
    me = request.user
    target = get_object_or_404(User, pk=form.cleaned_data["user_id"], is_active=True)
    action = form.cleaned_data["action"]
    if target == me:
        messages.error(request, "No puedes agregarte a ti mismo.")
        return redirect(destination)
    outgoing = Friendship.objects.filter(from_user=me, to_user=target)
    incoming = Friendship.objects.filter(from_user=target, to_user=me)
    if action == "send":
        if incoming.filter(status=PENDING).exists():
            incoming.update(status=ACCEPTED)
            messages.success(request, "Ahora son amigos.")
        elif outgoing.exists() or incoming.exists():
            messages.info(request, "Ya existe una relación con esta persona.")
        else:
            Friendship.objects.create(from_user=me, to_user=target)
            messages.success(request, "Solicitud enviada.")
    elif action == "accept":
        if incoming.filter(status=PENDING).update(status=ACCEPTED):
            messages.success(request, "Solicitud aceptada.")
    elif action == "decline":
        incoming.filter(status=PENDING).delete()
        messages.info(request, "Solicitud rechazada.")
    elif action == "cancel":
        outgoing.filter(status=PENDING).delete()
        messages.info(request, "Solicitud cancelada.")
    elif action == "remove":
        outgoing.filter(status=ACCEPTED).delete()
        incoming.filter(status=ACCEPTED).delete()
        messages.info(request, "Amistad eliminada.")
    return redirect(destination)