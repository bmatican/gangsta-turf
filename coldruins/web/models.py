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
      if self.owner is not None:
        owner = self.owner.user.id
        clan = self.owner.clan
        if clan is not None:
          clan = clan.id
      return {
        'db_id' : self.id,
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
        candidate_locations = cls.objects.exclude(owner=None)
        for location in candidate_locations.filter(last_payment__lt=when):
            if location.owner is None:
                continue
            location.make_clan_payment()
        for location in candidate_locations.filter(last_payment=None):
            if location.owner is None:
                continue
            location.make_clan_payment()

    def make_clan_payment(self):
        if self.owner is not None:
            clan = self.owner.clan
            if clan is not None:
                clan_member_cnt = clan.members.count()
                reward = LOCATION_REWARDS[self.category]
                multiplier = 1.0
                for clan_member in clan.members.all():
                    mul = multiplier
                    # twice for the owner...
                    if clan_member.id == self.owner.id:
                        mul = 2 * multiplier
                    clan_member.add_resources(reward, mul / clan_member_cnt)
            else:
                reward = LOCATION_REWARDS[self.category]
                multiplier = 2.0
                self.owner.add_resources(reward, multiplier)
            self.last_payment = now()
            self.save()


class Checkin(models.Model):
    user = models.ForeignKey('UserMeta', related_name='user_checkins')
    location = models.ForeignKey(Location, related_name='location_checkins')
    time = models.DateTimeField(default=now)

    def __unicode__(self):
        return 'Checkin by {} at {}'.format(self.user,
                                            self.location.name)

    @classmethod
    @transaction.commit_on_success
    def make_checkin(cls, user, location_id):
        loc = Location.objects.get(fb_id=location_id)
        cls.objects.create(
            user_id=user.meta.id,
            location_id=loc.id
        ).save()
        reward = LOCATION_REWARDS[loc.category]
        user.meta.add_resources(reward, 1.0)
        loc.make_clan_payment()
        if loc.owner is None:
            loc.owner = user.meta
            loc.save()
        user.meta.latest_location = loc
        user.meta.save()
        return {
            'reward' : list(reward),
            'total' : list(user.meta.get_resources()),
        }


class UserMeta(models.Model):
    user = models.OneToOneField(User, related_name='meta',
        primary_key=True)
    clan = models.ForeignKey(Clan, related_name='members',
        blank=True, null=True)
    latest_location = models.ForeignKey(Location, related_name='+',
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

    def buy_troops(self, unit_id, count):
      if int(unit_id) not in dict(UNITS):
        return None
      elif self._can_subtract(UNIT_PRICES[unit_id], count):
        return self.subtract_resources(UNIT_PRICES[unit_id], count)


class Troops(models.Model):
    owner = models.ForeignKey(UserMeta, related_name='troops')
    location = models.ForeignKey(Location, related_name='troops',
        blank=True, null=True)
    unit = models.IntegerField(choices=UNITS)
    count = models.IntegerField(default=1)

    class Meta:
        verbose_name_plural = 'troops'
        unique_together = (('owner', 'location', 'unit'),)

    def __unicode__(self):
        return '{} x {} belonging to {} stationed in {}'.format(
            self.count, self.unit, self.owner, self.location)

    @staticmethod
    def update_count(owner, location, unit, delta):
        try:
            t = Troops.objects.get(owner=owner, location=location, unit=unit)
        except Troops.DoesNotExist:
            t = Troops(owner=owner, location=location, unit=unit,
                       count=0)
        t.count += delta

        assert t.count >= 0
        if t.count == 0:
            t.delete()
        else:
            t.save()

    @transaction.commit_on_success
    def move(self, where, count=None):
        assert self.location is not None

        if count is None:
            count = self.count

        distance = 10          # FIXME
        tm = TroopMovement(
            owner=self.owner, unit=self.unit, count=count,
            lfrom=self.location, lto=where,
            leave_time=now(), arrive_time=now() + distance)
        tm.save()

        Troops.update_count(self.owner, self.location, self.unit, -count)

    @transaction.commit_on_success
    def station(self, where, count=None):
        assert self.location is None

        if count is None:
            count = self.count
        Troops.update_count(self.owner, where, self.unit, count)
        Troops.update_count(self.owner, None, self.unit, -count)

    @transaction.commit_on_success
    def pickup(self, where, count=None):
        assert self.location is not None

        if count is None:
            count = self.count
        Troops.update_count(self.owner, None, self.unit, count)
        Troops.update_count(self.owner, self.location, self.unit, -count)

    @classmethod
    def make_troops(cls, user_id, location_db_id, unit_id, count):
        if int(unit_id) in dict(UNITS):
            Troops.update_count(user_id, location_db_id, unit_id, count)

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
        Troops.update_count(
            owner=self.owner, unit=self.unit, location=self.lto,
            delta=self.count)
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
    start = models.DateTimeField(default=now)

    FIGHT_DURATION = 0.5

    @classmethod
    def end_pending_fights(cls):
        when = now() - datetime.timedelta(hours=cls.FIGHT_DURATION)
        for fight in cls.objects.filter(start__lt=when):
            fight.end_fight()

    @transaction.commit_on_success
    def end_fight(self):
        assert \
            self.start + datetime.timedelta(hours=cls.FIGHT_DURATION) >= now()

        powers_by_clan, powers_by_user = self.fighting_powers()
        total_power = sum(powers_by_clan.itervalues())
        winner = max(powers_by_clan.iteritems(), key=lambda x: x[1])

        # TODO: give spoils to the winner and his clan

        if winner[1] * 100 < total_power * 40:
            # Not enough of a clear victory for territory domination
            pf = PastFight(location=self.location,
                           old_owner=self.location.owner,
                           new_owner=None)
            pf.save()
            self.location.owner = None
            self.location.save()
            return

        if winner[0][0] == 'user':
            # Winner has no clan
            pf = PastFight(location=self.location,
                           old_owner=self.location.owner,
                           new_owner=winner[0][1])
            pf.save()
            self.location.owner = winner[0][1]
            self.location.save()
            return

        clan = winner[0][1]
        if clan.id == self.location.owner.clan_id:
            pf = PastFight(location=self.location,
                           old_owner=self.location.owner,
                           new_owner=self.location.owner)
            pf.save()
        else:
            new_owner = None
            for user in power_by_users:
                if user.clan_id == clan.id:
                    if new_owner is None or \
                       power_by_users[user] > power_by_users[new_owner]:
                        new_owner = user

            pf = PastFight(location=self.location,
                           old_owner=self.location.owner,
                           new_owner=new_owner)
            pf.save()
            self.location.owner = new_owner
            self.location.save()


    def fighting_powers(self):
        troops_A = cls.objects.filter(location=self.location) \
            .select_related('owner__clan').all()
        users_in_location = UserMeta.objects.filter(
            latest_location=self.location).all()
        troops_B = cls.objects \
            .filter(location=None, owner__in=users_in_location) \
            .select_related('owner__clan').all()

        by_clan = {}
        by_user = {}
        for t in troops_A + troops_B:
            unit_power = UNIT_POWER[t.unit] * t.count

            if t.owner.clan is None:
                key = ('user', t.owner)
            else:
                key = ('clan', t.owner.clan)
            if key not in by_clan:
                by_clan[key] = 0
            by_clan[key] += unit_power

            if t.owner not in by_user:
                by_user[t.owner] = 0
            by_user[t.owner] += unit_power
        return by_clan, by_user


class PastFight(models.Model):
    location = models.ForeignKey(Location, related_name='past_fights')
    old_owner = models.ForeignKey(Clan, related_name='+')
    new_owner = models.ForeignKey(Clan, related_name='+')
