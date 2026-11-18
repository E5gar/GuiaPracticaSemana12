from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render

from events.models import Event, Registration
from friends.models import attach_relations, friend_ids

from .forms import LoginForm, ProfileForm, RegisterForm

User = get_user_model()


class HuancaLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if not form.cleaned_data.get("remember"):
            self.request.session.set_expiry(0)
        return response


def register_view(request):
    if request.user.is_authenticated:
        return redirect("events:home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Tu cuenta fue creada. Ya puedes explorar e inscribirte en eventos.")
            return redirect("events:home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile_view(request, username):
    person = get_object_or_404(User.objects.select_related("profile"), username=username, is_active=True)
    attach_relations(request.user, [person])
    events = (
        Event.objects.filter(organizer=person, is_published=True)
        .with_stats(request.user)
        .order_by("-starts_at")[:6]
    )
    context = {
        "person": person,
        "events": events,
        "events_count": Event.objects.filter(organizer=person, is_published=True).count(),
        "friends_count": len(friend_ids(person)),
        "registrations_count": Registration.objects.filter(user=person).count(),
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil fue actualizado.")
            return redirect("accounts:profile", username=request.user.username)
    else:
        form = ProfileForm(instance=profile, user=request.user)
    return render(request, "accounts/profile_edit.html", {"form": form})