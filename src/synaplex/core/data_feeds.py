# synaplex/core/data_feeds.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .ids import AgentId


class DataFeed(ABC):
    """
    Abstract interface for external data sources.
    
    Data feeds provide structured, time-indexed data that can be included
    in agent percepts. They are part of "nature" (deterministic state),
    not "nurture" (manifolds).
    """
    
    def __init__(self, name: str) -> None:
        self.name = name
    
    @abstractmethod
    def get_data(self, tick: int, agent_id: Optional[AgentId] = None) -> Dict[str, Any]:
        """
        Get data for a specific tick.
        
        Args:
            tick: Current tick number
            agent_id: Optional agent ID for agent-specific data
        
        Returns:
            Dict of structured data
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_available(self, tick: int) -> bool:
        """Check if data is available for this tick."""
        raise NotImplementedError


class StaticDataFeed(DataFeed):
    """
    Static data feed that returns the same data every tick.
    
    Useful for configuration data, reference information, etc.
    """
    
    def __init__(self, name: str, data: Dict[str, Any]) -> None:
        super().__init__(name)
        self._data = data
    
    def get_data(self, tick: int, agent_id: Optional[AgentId] = None) -> Dict[str, Any]:
        """Return static data."""
        return self._data.copy()
    
    def is_available(self, tick: int) -> bool:
        """Always available."""
        return True


class TimeSeriesDataFeed(DataFeed):
    """
    Time series data feed indexed by tick.
    
    Useful for historical data, time-series analysis, etc.
    """
    
    def __init__(
        self,
        name: str,
        data: Dict[int, Dict[str, Any]],
        default: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize time series feed.
        
        Args:
            name: Feed name
            data: Dict mapping tick -> data dict
            default: Default data to return if tick not found
        """
        super().__init__(name)
        self._data = data
        self._default = default or {}
    
    def get_data(self, tick: int, agent_id: Optional[AgentId] = None) -> Dict[str, Any]:
        """Get data for specific tick, or default if not found."""
        return self._data.get(tick, self._default).copy()
    
    def is_available(self, tick: int) -> bool:
        """Available if data exists for this tick or default is set."""
        return tick in self._data or self._default is not None
    
    def add_data_point(self, tick: int, data: Dict[str, Any]) -> None:
        """Add a data point for a specific tick."""
        self._data[tick] = data


class CallableDataFeed(DataFeed):
    """
    Data feed that calls a function to get data.
    
    Useful for dynamic data sources, API calls, etc.
    """
    
    def __init__(
        self,
        name: str,
        getter: callable[[int, Optional[AgentId]], Dict[str, Any]],
        availability_check: Optional[callable[[int], bool]] = None,
    ) -> None:
        """
        Initialize callable feed.
        
        Args:
            name: Feed name
            getter: Function (tick, agent_id) -> data dict
            availability_check: Optional function (tick) -> bool
        """
        super().__init__(name)
        self._getter = getter
        self._availability_check = availability_check or (lambda t: True)
    
    def get_data(self, tick: int, agent_id: Optional[AgentId] = None) -> Dict[str, Any]:
        """Call getter function."""
        try:
            return self._getter(tick, agent_id) or {}
        except Exception:
            return {}
    
    def is_available(self, tick: int) -> bool:
        """Check availability."""
        try:
            return self._availability_check(tick)
        except Exception:
            return False


class DataFeedRegistry:
    """
    Registry for managing data feeds in a world.
    
    Feeds are registered by name and can be queried by agents.
    """
    
    def __init__(self) -> None:
        self._feeds: Dict[str, DataFeed] = {}
    
    def register(self, feed: DataFeed) -> None:
        """Register a data feed."""
        if feed.name in self._feeds:
            raise ValueError(f"Data feed '{feed.name}' is already registered")
        self._feeds[feed.name] = feed
    
    def get(self, name: str) -> Optional[DataFeed]:
        """Get a feed by name."""
        return self._feeds.get(name)
    
    def get_all(self, tick: int) -> Dict[str, Dict[str, Any]]:
        """
        Get data from all available feeds for a tick.
        
        Returns:
            Dict mapping feed_name -> feed_data
        """
        result = {}
        for name, feed in self._feeds.items():
            if feed.is_available(tick):
                try:
                    result[name] = feed.get_data(tick)
                except Exception:
                    # Skip feeds that fail
                    continue
        return result
    
    def list_feeds(self) -> List[str]:
        """List all registered feed names."""
        return list(self._feeds.keys())

