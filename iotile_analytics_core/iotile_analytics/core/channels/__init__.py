"""All of the supported ways to connect an AnalysisGroup with data."""

from .cloud_api import IOTileCloudChannel
from .channel import ChannelCaching

__all__ = ['IOTileCloudChannel', 'ChannelCaching']
