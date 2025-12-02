"""
OrbitOps Orchestrator

This module coordinates the execution of multiple agents in a workflow.
It manages agent dependencies, execution order, and data flow between agents.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
from agents.base_agent import BaseAgent, AgentResult, AgentStatus


class WorkflowStatus(Enum):
    """Status of the orchestrator workflow"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class AgentTask:
    """Represents a task for an agent in the workflow"""
    agent: BaseAgent
    agent_id: str
    dependencies: List[str]  # List of agent_ids this task depends on
    input_mapping: Dict[str, str]  # Maps output keys from dependencies to input keys


class Orchestrator:
    """
    Orchestrator that coordinates multiple agents in a workflow.
    
    Manages:
    - Agent execution order based on dependencies
    - Data flow between agents
    - Error handling and recovery
    - Workflow status tracking
    """
    
    def __init__(self):
        """Initialize the orchestrator"""
        self.agents: Dict[str, BaseAgent] = {}
        self.workflow: List[AgentTask] = []
        self.status = WorkflowStatus.PENDING
        self.results: Dict[str, AgentResult] = {}
        self.execution_log: List[Dict[str, Any]] = []
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent: The agent instance to register
        """
        self.agents[agent.agent_id] = agent
    
    def add_task(
        self,
        agent_id: str,
        dependencies: Optional[List[str]] = None,
        input_mapping: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Add a task to the workflow.
        
        Args:
            agent_id: ID of the agent to execute
            dependencies: List of agent_ids that must complete before this task
            input_mapping: Maps output keys from dependencies to this agent's input keys
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not registered")
        
        task = AgentTask(
            agent=self.agents[agent_id],
            agent_id=agent_id,
            dependencies=dependencies or [],
            input_mapping=input_mapping or {}
        )
        self.workflow.append(task)
    
    def _build_input_data(self, task: AgentTask) -> Dict[str, Any]:
        """
        Build input data for a task based on its dependencies and input mapping.
        
        Args:
            task: The task to build input for
            
        Returns:
            Dictionary of input data for the agent
        """
        input_data = {}
        
        for dep_id in task.dependencies:
            if dep_id not in self.results:
                raise ValueError(f"Dependency {dep_id} has no result")
            
            dep_result = self.results[dep_id]
            if not dep_result.success:
                raise ValueError(f"Dependency {dep_id} failed: {dep_result.error}")
            
            # Map outputs from dependency to inputs for this task
            if dep_result.data:
                if task.input_mapping:
                    # Use explicit mapping
                    for output_key, input_key in task.input_mapping.items():
                        if output_key in dep_result.data:
                            input_data[input_key] = dep_result.data[output_key]
                else:
                    # Pass all data through
                    input_data.update(dep_result.data)
        
        return input_data
    
    def _validate_workflow(self) -> tuple[bool, Optional[str]]:
        """
        Validate that the workflow is properly structured.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for circular dependencies
        agent_ids = {task.agent_id for task in self.workflow}
        
        for task in self.workflow:
            for dep_id in task.dependencies:
                if dep_id not in agent_ids:
                    return False, f"Dependency {dep_id} not found in workflow"
        
        # Simple cycle detection (can be enhanced)
        visited = set()
        
        def has_cycle(agent_id: str, path: set) -> bool:
            if agent_id in path:
                return True
            if agent_id in visited:
                return False
            
            visited.add(agent_id)
            path.add(agent_id)
            
            task = next((t for t in self.workflow if t.agent_id == agent_id), None)
            if task:
                for dep_id in task.dependencies:
                    if has_cycle(dep_id, path.copy()):
                        return True
            
            return False
        
        for task in self.workflow:
            if has_cycle(task.agent_id, set()):
                return False, f"Circular dependency detected involving {task.agent_id}"
        
        return True, None
    
    async def execute(self, initial_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the workflow with all registered agents.
        
        Args:
            initial_input: Initial input data for the first agent(s)
            
        Returns:
            Dictionary containing all results from the workflow
        """
        # Validate workflow
        is_valid, error = self._validate_workflow()
        if not is_valid:
            self.status = WorkflowStatus.FAILED
            raise ValueError(f"Invalid workflow: {error}")
        
        self.status = WorkflowStatus.RUNNING
        self.results = {}
        self.execution_log = []
        
        if initial_input:
            # Store initial input as a special result
            self.results["__initial__"] = AgentResult(
                success=True,
                data=initial_input
            )
        
        # Topological sort to determine execution order
        execution_order = self._topological_sort()
        
        try:
            for agent_id in execution_order:
                task = next(t for t in self.workflow if t.agent_id == agent_id)
                
                # Build input data
                input_data = self._build_input_data(task)
                
                # Execute agent
                self._log_execution(agent_id, "starting", input_data)
                task.agent.set_status(AgentStatus.PROCESSING)
                
                result = await task.agent.process(input_data)
                
                task.agent.set_status(
                    AgentStatus.COMPLETED if result.success else AgentStatus.ERROR
                )
                
                self.results[agent_id] = result
                self._log_execution(agent_id, "completed", result)
                
                if not result.success:
                    self.status = WorkflowStatus.FAILED
                    return {
                        "status": "failed",
                        "failed_at": agent_id,
                        "error": result.error,
                        "results": self.results
                    }
            
            self.status = WorkflowStatus.COMPLETED
            return {
                "status": "completed",
                "results": self.results,
                "execution_log": self.execution_log
            }
        
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            return {
                "status": "failed",
                "error": str(e),
                "results": self.results
            }
    
    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort to determine execution order.
        
        Returns:
            List of agent_ids in execution order
        """
        # Build dependency graph
        in_degree = {task.agent_id: len(task.dependencies) for task in self.workflow}
        graph = {task.agent_id: [] for task in self.workflow}
        
        for task in self.workflow:
            for dep_id in task.dependencies:
                if dep_id in graph:
                    graph[dep_id].append(task.agent_id)
        
        # Kahn's algorithm
        queue = [agent_id for agent_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            agent_id = queue.pop(0)
            result.append(agent_id)
            
            for dependent in graph[agent_id]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        if len(result) != len(self.workflow):
            raise ValueError("Workflow has circular dependencies")
        
        return result
    
    def _log_execution(self, agent_id: str, event: str, data: Any) -> None:
        """Log an execution event"""
        self.execution_log.append({
            "agent_id": agent_id,
            "event": event,
            "data": data,
            "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else None
        })
    
    def get_status(self) -> WorkflowStatus:
        """Get the current workflow status"""
        return self.status
    
    def reset(self) -> None:
        """Reset the orchestrator to initial state"""
        self.status = WorkflowStatus.PENDING
        self.results = {}
        self.execution_log = []
        for agent in self.agents.values():
            agent.set_status(AgentStatus.IDLE)

