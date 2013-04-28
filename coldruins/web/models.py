from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils.timezone import now

import datetime


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
)

UNIT_PRICES = (
    (1, (1, 1, 0, 0, 0)),
    (2, (2, 1, 1, 0, 0)),
    (3, (3, 0, 1, 1, 0)),
    (4, (4, 0, 0, 1, 1)),
)


UNIT_POWER = dict((
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
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
    owner = models.ForeignKey('UserMeta', related_name='owned_locations',
        blank=True, null=True)
    last_payment = models.DateTimeField(blank=True, null=True, default=None)

    PAYMENT_PERIOD = 1

    def __unicode__(self):
        return '{} ({})'.format(
            self.name, dict(LOCATION_CATEGORIES)[self.category])

    def export(self):
      owner = None
      clan = None
      if self.owner != None:
        owner = self.owner.user.id
        clan = self.owner.clan
        if clan != None:
          clan = clan.id
      return {
        'fb_id' : self.fb_id,
        'name' : self.name,
        'lat' : self.lat,
        'lon' : self.lon,
        'category' : self.category,
        'owner' : owner,
        'last_payment' : self.last_payment,
        'clan' : clan
      }

    @classmethod
    def make_pending_payments(cls):
        when = now() - datetime.timedelta(hours=cls.PAYMENT_PERIOD)
        for location in cls.objects.filter(last_payment__lt=when):
            if location.owner is None:
                continue
            location.make_clan_payment()

    def make_clan_payment(self):
        if self.owner != None:
            clan = self.owner.clan
            if clan != None:
                clan_member_cnt = clan.members.count()
                reward = LOCATION_REWARD[self.category]
                multiplier = 1.0
                for clan_member in clan.members.all():
                    mul = multiplier
                    # twice for the owner...
                    if clan_member.id == self.owner.id:
                        mul = 2 * multiplier
                    clan_member.add_resources(reward, mul / clan_member_cnt)


class Checkin(models.Model):
    user = models.ForeignKey(User, related_name='user_checkins')
    location = models.ForeignKey(Location, related_name='location_checkins')
    time = models.DateTimeField(auto_now_add=True)

    @classmethod
    def make_checkin(cls, user, location_id):
        loc = Location.objects.get(fb_id=location_id)
        cls.objects.create(
            user_id=user.id,
            location_id=loc.id
        ).save()
        reward = LOCATION_REWARDS[loc.category]
        user.meta.add_resources(reward, 1.0)
        loc.make_clan_payment()
        if loc.owner == None:
            loc.owner = user.meta
            loc.save()
        print 'here'
        print user.meta.get_resources()
        return {
            'reward' : reward,
            'total' : user.meta.get_resources()
        }

    def __unicode__(self):
      return 'Checkin by user {} at {}'.format(self.user.id, self.location.name)



class UserMeta(models.Model):
    user = models.OneToOneField(User, related_name='meta',
        primary_key=True)
    clan = models.ForeignKey(Clan, related_name='members',
        blank=True, null=True)
    fb_token = models.TextField()
    resourceA = models.FloatField(default=0)
    resourceB = models.FloatField(default=0)
    resourceC = models.FloatField(default=0)
    resourceD = models.FloatField(default=0)
    resourceE = models.FloatField(default=0)

    def __unicode__(self):
        return 'User {} of clan {}: ({}, {}, {}, {}, {})'.format(
            self.user, self.clan,
            self.resourceA, self.resourceB, self.resourceC,
            self.resourceD, self.resourceE)

    def get_resources(self):
        res = list(LOCATION_REWARDS[1]) # something to fill up
        for i in LOCATION_REWARDS.keys():
            key = 'resource' + chr(ord('A') - 1 + i)
            r = getattr(self, key)
            res[i - 1] = r
        return tuple(res)

    def add_resources(self, resources, mult=1.0):
        backup = list(resources)
        for i in LOCATION_REWARDS.keys():
            key = 'resource' + chr(ord('A') - 1 + i)
            r = getattr(self, key)
            newr = (r + resources[i - 1] * mult)
            backup[i - 1] = newr
            setattr(self, key, newr)
        self.save()
        return tuple(backup)

    def _can_subtract(self, resources, mult=1.0):
        for i in LOCATION_REWARDS.keys():
            key = 'resource' + chr(ord('A') - 1 + i)
            r = getattr(self, key)
            if r < resources[i - 1] * mult:
              return False
        return True

    def subtract_resources(self, resources, mult=1):
        if self._can_subtract(resources, mult):
            return self.add_resources(neg, -mult)
        else:
            return None

    def buy_troops(self, unit_id, numbers):
      if unit_id not in UNITS:
        return None
      elif self._can_subtract(UNIT_PRICES[unit_id], numbers):
        return self.subtract_resources(UNIT_PRICES[unit_id], numbers)


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

    @classmethod
    def get_troops(cls, location_id):
        troops = cls.objects.filter(location_id=location_id).all()
        d = {}
        for t in troops:
            count = d.setdefault(t.unit, 0)
            d[t.unit] = count + t.count
        return d


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

    @classmethod
    def move_pending_troops(cls):
        for tm in cls.objects.filter(arrive_time__gte=now()):
            tm.troop_arrive()


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
