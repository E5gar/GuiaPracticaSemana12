from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, UpdateView

from config.sanitizers import safe_redirect_target
from friends.models import attach_relations, friend_ids

from .forms import ActionForm, EventFilterForm, EventForm, ReactionForm
from .models import Category, Event, Reaction, Registration

User = get_user_model()


def home(request):
    upcoming = Event.objects.filter(is_published=True, ends_at__gte=timezone.now())
    featured = upcoming.with_stats(request.user).order_by("starts_at")[:6]
    circle = []
    if request.user.is_authenticated:
        ids = friend_ids(request.user)
        if ids:
            circle = (
                upcoming.filter(
                    Q(organizer_id__in=ids)
                    | Q(id__in=Registration.objects.filter(user_id__in=ids).values("event_id"))
                )
                .exclude(organizer=request.user)
                .with_stats(request.user)
                .order_by("starts_at")[:3]
            )
    context = {
        "featured": featured,
        "circle": circle,
        "categories": Category.objects.all(),
        "stats": {
            "events": upcoming.count(),
            "members": User.objects.filter(is_active=True).count(),
            "registrations": Registration.objects.count(),
        },
    }
    return render(request, "events/home.html", context)


def event_list(request):
    form = EventFilterForm(request.GET or None)
    events = Event.objects.filter(is_published=True, ends_at__gte=timezone.now())
    if form.is_bound and form.is_valid():
        data = form.cleaned_data
        if data["q"]:
            events = events.filter(
                Q(title__icontains=data["q"])
                | Q(description__icontains=data["q"])
                | Q(venue__icontains=data["q"])
            )
        if data["category"]:
            events = events.filter(category=data["category"])
        today = timezone.localdate()
        if data["when"] == "today":
            events = events.filter(starts_at__date=today)
        elif data["when"] == "week":
            events = events.filter(starts_at__date__range=(today, today + timedelta(days=7)))
        elif data["when"] == "month":
            events = events.filter(starts_at__year=today.year, starts_at__month=today.month)
        if data["price"] == "free":
            events = events.filter(price=0)
        elif data["price"] == "paid":
            events = events.filter(price__gt=0)
    events = events.with_stats(request.user).order_by("starts_at")
    page_obj = Paginator(events, 9).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    context = {"form": form, "page_obj": page_obj, "querystring": params.urlencode()}
    return render(request, "events/event_list.html", context)


def event_detail(request, pk):
    event = get_object_or_404(Event.objects.with_stats(request.user), pk=pk)
    if not event.is_published and event.organizer_id != request.user.id:
        raise Http404
    attendees = list(User.objects.filter(event_registrations__event=event).select_related("profile")[:24])
    organizer = event.organizer
    if request.user.is_authenticated:
        attach_relations(request.user, attendees + [organizer])
    context = {
        "event": event,
        "attendees": attendees,
        "organizer": organizer,
        "is_owner": request.user.is_authenticated and event.organizer_id == request.user.id,
    }
    return render(request, "events/event_detail.html", context)


class EventCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"
    permission_required = "events.add_event"

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Tu evento fue publicado.")
        return response


class OwnedEventMixin(LoginRequiredMixin, PermissionRequiredMixin):
    def get_queryset(self):
        queryset = Event.objects.all()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(organizer=self.request.user)


class EventUpdateView(OwnedEventMixin, UpdateView):
    form_class = EventForm
    template_name = "events/event_form.html"
    permission_required = "events.change_event"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Los cambios del evento fueron guardados.")
        return response


class EventDeleteView(OwnedEventMixin, DeleteView):
    template_name = "events/event_confirm_delete.html"
    permission_required = "events.delete_event"
    success_url = reverse_lazy("events:mine")

    def form_valid(self, form):
        messages.success(self.request, "El evento fue eliminado.")
        return super().form_valid(form)


@login_required
def my_events(request):
    events = Event.objects.filter(organizer=request.user).with_stats(request.user).order_by("-starts_at")
    return render(request, "events/my_events.html", {"events": events})


@login_required
def my_registrations(request):
    registered = Registration.objects.filter(user=request.user).values("event_id")
    events = Event.objects.filter(id__in=registered).with_stats(request.user).order_by("starts_at")
    now = timezone.now()
    upcoming = [event for event in events if event.ends_at >= now]
    past = [event for event in events if event.ends_at < now]
    return render(request, "events/my_registrations.html", {"upcoming": upcoming, "past": past})


@login_required
@require_POST
def toggle_registration(request, pk):
    event = get_object_or_404(Event, pk=pk, is_published=True)
    form = ActionForm(request.POST)
    if not form.is_valid():
        messages.error(request, "No se pudo procesar la solicitud.")
        return redirect(event)
    existing = Registration.objects.filter(event=event, user=request.user)
    if existing.exists():
        existing.delete()
        messages.info(request, "Cancelaste tu inscripción.")
    elif event.organizer_id == request.user.id:
        messages.error(request, "Eres el organizador de este evento.")
    elif event.is_past:
        messages.error(request, "Este evento ya finalizó.")
    elif event.registrations.count() >= event.capacity:
        messages.error(request, "El evento alcanzó su aforo máximo.")
    else:
        Registration.objects.create(event=event, user=request.user)
        messages.success(request, "Quedaste inscrito en el evento.")
    return redirect(safe_redirect_target(request, event.get_absolute_url()))


@login_required
@require_POST
def react(request, pk):
    event = get_object_or_404(Event, pk=pk, is_published=True)
    form = ReactionForm(request.POST)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if not form.is_valid():
        if is_ajax:
            return JsonResponse({"ok": False}, status=400)
        messages.error(request, "Reacción no válida.")
        return redirect(event)
    kind = form.cleaned_data["kind"]
    current = Reaction.objects.filter(event=event, user=request.user).first()
    if current and current.kind == kind:
        current.delete()
        mine = None
    elif current:
        current.kind = kind
        current.save(update_fields=["kind"])
        mine = kind
    else:
        Reaction.objects.create(event=event, user=request.user, kind=kind)
        mine = kind
    if is_ajax:
        totals = {row["kind"]: row["total"] for row in event.reactions.values("kind").annotate(total=Count("id"))}
        counts = {key: totals.get(key, 0) for key, _ in Reaction.KINDS}
        return JsonResponse({"ok": True, "counts": counts, "mine": mine})
    return redirect(safe_redirect_target(request, event.get_absolute_url()))