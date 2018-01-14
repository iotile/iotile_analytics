"""A collection of useful numerical utility functions."""

from .domain import find_domain, combine_domains
from .envelope import envelope
from .aggregator import TimeseriesSelector

__all__ = ['find_domain', 'combine_domains', 'envelope', 'TimeseriesSelector']
