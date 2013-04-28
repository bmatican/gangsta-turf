from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils.timezone import now


LOCATION_CATEGORIES = (
    (1, 'Food & Drinks'),
    (2, 'Arts & Entertainment'),
    (3, 'Shopping & Retail'),
    (4, 'Companies & Education'),
    (5, 'Attractions'),
)


LOCATION_REWARDS = dict((
    (1, (1, 0, 0, 0, 0)),
    (2, (0, 1, 0, 0, 0)),
    (3, (0, 0, 1, 0, 0)),
    (4, (0, 0, 0, 1, 0)),
    (5, (0, 0, 0, 0, 1)),
))

UNITS = (
    (1, 'Unit 1'),
    (2, 'Unit 3'),
    (3, 'Unit 3'),
    (4, 'Unit 4'),
    (5, 'Unit 5'),
    (6, 'Unit 6'),
    (7, 'Unit 7'),
    (8, 'Unit 8'),
    (9, 'Unit 9'),
    (10, 'Unit 10'),
)


UNIT_POWER = dict((
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
    (6, 6),
    (7, 7),
    (8, 8),
    (9, 9),
    (10, 10),
))


class Clan(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __unicode__(self):
        return 'Clan {}'.format(self.name)

    def get_clan_power_in_location(self, location):
        troops = Troops.objects \
            .filter(location=location) \
            .filter(owner__clan=self)

        power = 0
        for troop in troops:
            power += UNIT_POWER[troop.unit] * troop.count
        return power


class Location(models.Model):
    fb_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=64)
    lon = models.FloatField()
    lat = models.FloatField()
    category = models.IntegerField(choices=LOCATION_CATEGORIES)
    owner = models.ForeignKey(Clan, related_name='owned_locations',
        blank=True, null=True)
    last_payment = models.DateTimeField(blank=True, null=True, default=None)

    def __unicode__(self):
        return '{} ({})'.format(
            self.name, dict(LOCATION_CATEGORIES)[self.category])


class Checkin(models.Model):
    user = models.ForeignKey(User, related_name='user_checkins')
    location = models.ForeignKey(Location, related_name='location_checkins')
    time = models.DateTimeField(auto_now_add=True)

    @classmethod
    def make_checkin(cls, user, location_id):
      loc = Location.objects.get(id=location_id)
      cls.objects.create(
        user_id=user.id,
        location_id=location_id,
      ).save()
      reward = LOCATION_REWARDS[loc.category]
      user.meta.add_resources(reward)
      return reward


class UserMeta(models.Model):
    user = models.OneToOneField(User, related_name='meta',
        primary_key=True)
    clan = models.ForeignKey(Clan, related_name='members',
        blank=True, null=True)
    fb_token = models.TextField()
    resourceA = models.IntegerField(default=0)
    resourceB = models.IntegerField(default=0)
    resourceC = models.IntegerField(default=0)
    resourceD = models.IntegerField(default=0)
    resourceE = models.IntegerField(default=0)

    def add_resources(self, resources):
      for i in LOCATION_REWARDS.keys():
        key = 'resource' + chr(ord('A') - 1 + i)
        r = getattr(self, key)
        setattr(self, key, (r + resources[i - 1]))

    def subtract_resources(self, resources):
      neg = resources
      for i in xrange(len(resources)):
        neg[i] = -resources[i]
      self.add_resources(neg)

    def __unicode__(self):
        return 'User {} of clan {}: ({}, {}, {}, {}, {})'.format(
            self.user, self.clan,
            self.resourceA, self.resourceB, self.resourceC,
            self.resourceD, self.resourceE)


class Troops(models.Model):
    owner = models.ForeignKey(UserMeta, related_name='troops')
    unit = models.IntegerField(choices=UNITS)
    count = models.IntegerField(default=1)
    location = models.ForeignKey(Location, related_name='troops')

    class Meta:
        verbose_name_plural = 'troops'

    def __unicode__(self):
        return '{} x {} belonging to {} stationed in {}'.format(
            self.count, self.unit, self.owner, self.location)

    @transaction.commit_on_success
    def move(self, where):
        distance = 10          # FIXME
        tm = TroopMovement(
            owner=self.owner, unit=self.unit, count=self.count,
            lfrom=self.location, lto=where,
            leave_time=now(), arrive_time=now() + distance)
        tm.save()
        self.delete()


class TroopMovement(models.Model):
    owner = models.ForeignKey(UserMeta, related_name='moving_troops')
    unit = models.IntegerField(choices=UNITS)
    count = models.IntegerField(default=1)
    lfrom = models.ForeignKey(Location, related_name='leaving_troops')
    lto = models.ForeignKey(Location, related_name='arriving_troops')
    leave_time = models.DateTimeField()
    arrive_time = models.DateTimeField()

    def __unicode__(self):
        return '{} x {} belonging to {} moving from {} to {}'.format(
            self.count, self.unit, self.owner, self.lfrom, self.lto)

    @transaction.commit_on_success
    def troop_arrive(self):
        assert self.arrive_time <= now()
        t = Troops(owner=self.owner, unit=self.unit, count=self.count,
                   location=self.lto)
        t.save()
        self.delete()

    def troop_send_back(self):
        assert self.lto != self.lfrom
        self.lto = self.lfrom
        self.arrive_time = now() + (now() - self.leave_time)
        self.save()


class OngoingFight(models.Model):
    location = models.OneToOneField(Location, related_name='ongoing_fight')
    offender = models.ForeignKey(Clan, related_name='+')
    start = models.DateTimeField(default=now)


class PastFight(models.Model):
    DEFENDER = 1
    OFFENDER = 2
    CHOICES = ((DEFENDER, 'defender'), (OFFENDER, 'offender'))

    location = models.ForeignKey(Location, related_name='past_fights')
    defender = models.ForeignKey(Clan, related_name='+')
    offender = models.ForeignKey(Clan, related_name='+')
    winner = models.IntegerField(choices=CHOICES)
