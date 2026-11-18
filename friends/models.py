from django.conf import settings
from django.db import models
from django.db.models import Q

PENDING = "pending"
ACCEPTED = "accepted"


class Friendship(models.Model):
    STATUS = [(PENDING, "Pendiente"), (ACCEPTED, "Aceptada")]

    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_requests")
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_requests")
    status = models.CharField(max_length=10, choices=STATUS, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["from_user", "to_user"], name="unique_friendship_direction")]
        ordering = ["-created_at"]
        verbose_name = "amistad"
        verbose_name_plural = "amistades"

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"


def friend_ids(user):
    rows = (
        Friendship.objects.filter(status=ACCEPTED)
        .filter(Q(from_user=user) | Q(to_user=user))
        .values_list("from_user_id", "to_user_id")
    )
    ids = set()
    for first, second in rows:
        ids.add(second if first == user.id else first)
    return ids


def relation_map(user):
    mapping = {}
    rows = Friendship.objects.filter(Q(from_user=user) | Q(to_user=user)).values_list(
        "from_user_id", "to_user_id", "status"
    )
    for first, second, status in rows:
        other = second if first == user.id else first
        if status == ACCEPTED:
            mapping[other] = "friends"
        elif first == user.id:
            mapping[other] = "sent"
        else:
            mapping[other] = "received"
    return mapping


def attach_relations(viewer, people):
    people = list(people)
    mapping = relation_map(viewer) if viewer.is_authenticated else {}
    for person in people:
        if viewer.is_authenticated and person.id == viewer.id:
            person.relation = "self"
        else:
            person.relation = mapping.get(person.id, "none")
    return people