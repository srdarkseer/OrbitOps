"""
Base Agent Framework for OrbitOps

This module provides the abstract base class that all specialized agents will inherit from.
It defines the common interface and shared functionality for all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AgentStatus(Enum):
    """Status of an agent"""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentResult:
    """Result returned by an agent after processing"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """
    Abstract base class for all OrbitOps agents.
    
    All specialized agents (Architecture Reader, Efficiency Analyzer, etc.)
    must inherit from this class and implement the required methods.
    """
    
    def __init__(self, agent_id: str, name: str, description: str):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name of the agent
            description: Description of what the agent does
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self._llm_client = None  # Will be initialized with LLM client
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Main processing method that each agent must implement.
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            AgentResult containing the processing results
        """
        pass
    
    @abstractmethod
    def get_required_inputs(self) -> list[str]:
        """
        Returns a list of required input keys for this agent.
        
        Returns:
            List of required input field names
        """
        pass
    
    def set_status(self, status: AgentStatus) -> None:
        """Update the agent's status"""
        self.status = status
    
    def get_status(self) -> AgentStatus:
        """Get the current agent status"""
        return self.status
    
    def set_llm_client(self, llm_client: Any) -> None:
        """Set the LLM client for the agent"""
        self._llm_client = llm_client
    
    def validate_input(self, input_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate that input_data contains all required inputs.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required = self.get_required_inputs()
        missing = [key for key in required if key not in input_data]
        
        if missing:
            return False, f"Missing required inputs: {', '.join(missing)}"
        return True, None
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id}, name={self.name}, status={self.status.value})"
