# synaplex/cognition/tools.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class Tool(ABC):
    """
    Abstract base class for tools that agents can use during reasoning.

    Tools are functions that agents can call to interact with the external world
    or perform computations. They return structured data (not text).
    """

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @abstractmethod
    def call(self, **kwargs: Any) -> Any:
        """
        Execute the tool with given arguments.

        Returns:
            Structured data (dict, list, primitive) - not text
        """
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dict for LLM tool calling."""
        return {
            "name": self.name,
            "description": self.description,
        }


class FunctionTool(Tool):
    """
    Tool wrapper for a simple callable function.
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
    ) -> None:
        super().__init__(name, description)
        self._func = func

    def call(self, **kwargs: Any) -> Any:
        """Call the wrapped function."""
        try:
            return self._func(**kwargs)
        except Exception as e:
            # Return error as structured data
            return {"error": str(e), "tool": self.name}


class ToolRegistry:
    """
    Registry for managing available tools.

    Tools are registered by name and can be looked up by agents.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def register_function(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
    ) -> None:
        """Register a function as a tool."""
        tool = FunctionTool(name, description, func)
        self.register(tool)

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_all(self, tool_names: Optional[List[str]] = None) -> Dict[str, Tool]:
        """
        Get tools by name list, or all tools if None.

        Args:
            tool_names: Optional list of tool names to retrieve

        Returns:
            Dict of tool_name -> Tool
        """
        if tool_names is None:
            return self._tools.copy()

        return {name: self._tools[name] for name in tool_names if name in self._tools}

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def to_llm_format(self, tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Convert tools to LLM tool calling format.

        Args:
            tool_names: Optional list of tool names to include

        Returns:
            List of tool dicts in LLM format
        """
        tools = self.get_all(tool_names)
        return [tool.to_dict() for tool in tools.values()]


class ToolContext:
    """
    Context for tool execution.

    Provides access to:
    - environment state
    - other agents (via projections)
    - world-specific resources
    """

    def __init__(self, env_state: Optional[Any] = None) -> None:
        self._env_state = env_state
        self._extras: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """Set a context value."""
        self._extras[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self._extras.get(key, default)

    @property
    def env_state(self) -> Optional[Any]:
        """Get the environment state."""
        return self._env_state
