# -*- coding: utf-8 -*-
from datetime import timedelta, time
from django.db import models
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import Product, Order


class ReservableProduct(models.Model):
    """Products that have reservable properties."""

    product = models.OneToOneField(Product, verbose_name=_(u"reservable product"), related_name="reservable")
    check_out_time = models.TimeField(verbose_name=_(u"sign out time"), default=time(hour=12))
    check_in_time = models.TimeField(verbose_name=_(u"sign in time"), default=time(hour=15))
    available_count = models.IntegerField(verbose_name=_(u"available quantity"), default=1)

    class Meta:
        verbose_name = _('reservable product')
        verbose_name_plural = _('reservable products')

    def __str__(self):
        return self.product.safe_translation_getter("name") or self.product.sku

    def get_reserved_dates(self, start, end):
        """Get a list of reserved dates, between and including start and end.

        Args:
            start (datetime)
            end (datetime)

        Returns:
            list of datetimes or []
        """
        return Reservation.get_reserved_days_for_period(start, end, self)


class Reservation(models.Model):
    """A single reservation."""

    reservable = models.ForeignKey(
        ReservableProduct, verbose_name=_(u"reservable product"), related_name="reservations")
    order = models.ForeignKey(
        Order, verbose_name=_("order"), related_name="reservations", null=True, blank=True)
    start_time = models.DateTimeField(verbose_name=_(u"starts"))
    end_time = models.DateTimeField(verbose_name=_(u"ends"))

    adults = models.IntegerField(verbose_name=_(u"adults"), default=1)
    children = models.IntegerField(verbose_name=_(u"children"), default=0)

    class Meta:
        verbose_name = _('reservation')
        verbose_name_plural = _('reservations')

    def __str__(self):
        return str(self.reservable)

    def save(self, *args, **kwargs):
        # Validate end_time is past start_time
        if self.end_time <= self.start_time:
            raise ValueError
        return super(Reservation, self).save(*args, **kwargs)

    @staticmethod
    def get_reserved_days_for_period(start_time, end_time, reservable=None):
        """Get a list of reserved dates, between and including start and end.

        Args:
            start_time (datetime)
            end_time (datetime)
            reservable (ReservableProduct, optional)    - optionally filter by reservable

        Returns:
            list of datetimes or []
        """
        reservations = Reservation.objects.filter(
            start_time__gte=start_time,
            end_time__lte=end_time
        )
        if reservable:
            reservations = reservations.filter(reservable=reservable)
        dates = []
        for reservation in reservations:
            current = reservation.start_time.date()
            while current <= reservation.end_time.date():
                dates.append(current)
                current += timedelta(days=1)
        return dates
