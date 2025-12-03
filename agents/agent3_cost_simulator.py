"""
Agent 3: Cost Simulator

This agent runs cost simulations and projections based on:
- Current architecture costs
- Proposed changes from efficiency analysis
- Different pricing models
- Time-based projections
- What-if scenarios

It helps predict the financial impact of infrastructure changes.
"""

from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent, AgentResult, AgentStatus
from agents.cost_utils import (
    calculate_monthly_to_annual,
    calculate_savings_percentage,
    format_cost,
    calculate_total_cost_breakdown
)
from datetime import datetime, timedelta
import json


class CostSimulatorAgent(BaseAgent):
    """
    Agent responsible for running cost simulations and projections.
    
    This agent can:
    - Calculate current infrastructure costs
    - Simulate cost impact of proposed changes
    - Project costs over time
    - Compare different pricing models
    - Generate cost reports and visualizations
    """
    
    def __init__(self):
        """Initialize the Cost Simulator Agent"""
        super().__init__(
            agent_id="agent3_cost_simulator",
            name="Cost Simulator",
            description="Runs cost simulations and projections for cloud infrastructure"
        )
        self._pricing_data = {}  # Will store pricing information
        self._currency = "USD"
    
    def get_required_inputs(self) -> List[str]:
        """
        Returns the required input keys for this agent.
        
        Required inputs:
        - architecture: Architecture data from Agent 1
        OR
        - inefficiencies: Inefficiency data from Agent 2
        """
        return []  # Flexible - can work with either architecture or inefficiencies
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Run cost simulations based on input data.
        
        Args:
            input_data: Dictionary containing:
                - architecture: Optional - Architecture data
                - inefficiencies: Optional - Inefficiency findings
                - simulation_type: "current", "projected", "what_if", "comparison"
                - time_period: Optional - "monthly", "annual", or custom days
                - scenarios: Optional - List of scenarios to simulate
                
        Returns:
            AgentResult with cost simulation data
        """
        try:
            self.set_status(AgentStatus.PROCESSING)
            
            # Determine what we're working with
            architecture = input_data.get("architecture")
            inefficiencies = input_data.get("inefficiencies")
            
            if not architecture and not inefficiencies:
                return AgentResult(
                    success=False,
                    error="Either 'architecture' or 'inefficiencies' must be provided"
                )
            
            simulation_type = input_data.get("simulation_type", "current")
            time_period = input_data.get("time_period", "monthly")
            scenarios = input_data.get("scenarios", [])
            
            # Run appropriate simulation
            if simulation_type == "current":
                result_data = await self._simulate_current_costs(architecture)
            elif simulation_type == "projected":
                result_data = await self._simulate_projected_costs(
                    architecture, inefficiencies, time_period
                )
            elif simulation_type == "what_if":
                result_data = await self._simulate_what_if_scenarios(
                    architecture, scenarios, time_period
                )
            elif simulation_type == "comparison":
                result_data = await self._compare_scenarios(
                    architecture, scenarios, time_period
                )
            else:
                return AgentResult(
                    success=False,
                    error=f"Unknown simulation_type: {simulation_type}"
                )
            
            self.set_status(AgentStatus.COMPLETED)
            
            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "agent_id": self.agent_id,
                    "simulation_type": simulation_type,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        except Exception as e:
            self.set_status(AgentStatus.ERROR)
            return AgentResult(
                success=False,
                error=f"Error running cost simulation: {str(e)}"
            )
    
    async def _simulate_current_costs(
        self, architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate current infrastructure costs.
        
        Args:
            architecture: Architecture data
            
        Returns:
            Current cost breakdown
        """
        costs = {
            "compute": 0.0,
            "storage": 0.0,
            "networking": 0.0,
            "security": 0.0,
            "other": 0.0
        }
        
        # Calculate compute costs
        compute_resources = architecture.get("compute", {})
        for instance in compute_resources.get("instances", []):
            costs["compute"] += instance.get("monthly_cost", 0)
        
        # Calculate storage costs
        storage_resources = architecture.get("storage", {})
        for bucket in storage_resources.get("buckets", []):
            costs["storage"] += bucket.get("monthly_cost", 0)
        
        # Calculate networking costs
        networking_resources = architecture.get("networking", {})
        for lb in networking_resources.get("load_balancers", []):
            costs["networking"] += lb.get("monthly_cost", 0)
        
        total = sum(costs.values())
        breakdown_analysis = calculate_total_cost_breakdown(costs)
        
        return {
            "current_costs": {
                "monthly": total,
                "annual": calculate_monthly_to_annual(total),
                "breakdown": costs,
                "breakdown_percentages": breakdown_analysis["percentages"],
                "largest_category": breakdown_analysis["largest_category"],
                "currency": self._currency
            },
            "resource_count": {
                "compute": len(compute_resources.get("instances", [])),
                "storage": len(storage_resources.get("buckets", [])),
                "networking": len(networking_resources.get("load_balancers", []))
            }
        }
    
    async def _simulate_projected_costs(
        self,
        architecture: Dict[str, Any],
        inefficiencies: List[Dict[str, Any]],
        time_period: str
    ) -> Dict[str, Any]:
        """
        Project costs after implementing efficiency improvements.
        
        Args:
            architecture: Current architecture
            inefficiencies: List of inefficiency findings
            time_period: Time period for projection
            
        Returns:
            Projected cost data
        """
        # Get current costs
        current = await self._simulate_current_costs(architecture)
        current_monthly = current["current_costs"]["monthly"]
        
        # Calculate potential savings
        total_savings = sum(
            i.get("potential_savings", 0) for i in inefficiencies
        )
        
        # Projected costs after optimizations
        projected_monthly = current_monthly - total_savings
        
        # Calculate time period multiplier
        if time_period == "monthly":
            multiplier = 1
        elif time_period == "annual":
            multiplier = 12
        else:
            # Assume it's a number of days
            try:
                days = int(time_period)
                multiplier = days / 30.0
            except:
                multiplier = 1
        
        savings_percentage = calculate_savings_percentage(current_monthly, projected_monthly)
        
        return {
            "current_costs": current["current_costs"],
            "projected_costs": {
                "monthly": projected_monthly,
                "annual": calculate_monthly_to_annual(projected_monthly),
                "currency": self._currency
            },
            "savings": {
                "monthly": total_savings,
                "annual": calculate_monthly_to_annual(total_savings),
                "percentage": savings_percentage,
                "currency": self._currency
            },
            "projection_period": time_period,
            "projected_total": projected_monthly * multiplier
        }
    
    async def _simulate_what_if_scenarios(
        self,
        architecture: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
        time_period: str
    ) -> Dict[str, Any]:
        """
        Simulate what-if scenarios.
        
        Args:
            architecture: Current architecture
            scenarios: List of scenario definitions
            time_period: Time period for simulation
            
        Returns:
            Scenario simulation results
        """
        current = await self._simulate_current_costs(architecture)
        current_monthly = current["current_costs"]["monthly"]
        
        scenario_results = []
        
        for scenario in scenarios:
            scenario_name = scenario.get("name", "Unnamed Scenario")
            changes = scenario.get("changes", [])
            
            # Calculate scenario cost
            scenario_cost = current_monthly
            for change in changes:
                change_type = change.get("type")
                change_value = change.get("value", 0)
                
                if change_type == "add_resource":
                    scenario_cost += change_value
                elif change_type == "remove_resource":
                    scenario_cost -= change_value
                elif change_type == "modify_resource":
                    scenario_cost += change_value  # Change value is delta
                elif change_type == "scale":
                    # Scale existing resources
                    scale_factor = change.get("factor", 1.0)
                    affected_cost = change.get("affected_cost", 0)
                    scenario_cost += affected_cost * (scale_factor - 1.0)
            
            difference = scenario_cost - current_monthly
            difference_percentage = calculate_savings_percentage(
                current_monthly, scenario_cost
            ) if scenario_cost < current_monthly else -calculate_savings_percentage(
                scenario_cost, current_monthly
            ) if scenario_cost > current_monthly else 0
            
            scenario_results.append({
                "name": scenario_name,
                "monthly_cost": scenario_cost,
                "annual_cost": calculate_monthly_to_annual(scenario_cost),
                "difference": difference,
                "difference_percentage": difference_percentage,
                "changes": changes
            })
        
        return {
            "current_costs": current["current_costs"],
            "scenarios": scenario_results,
            "time_period": time_period,
            "currency": self._currency
        }
    
    async def _compare_scenarios(
        self,
        architecture: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
        time_period: str
    ) -> Dict[str, Any]:
        """
        Compare multiple scenarios side by side.
        
        Args:
            architecture: Current architecture
            scenarios: List of scenarios to compare
            time_period: Time period for comparison
            
        Returns:
            Comparison results
        """
        what_if_results = await self._simulate_what_if_scenarios(
            architecture, scenarios, time_period
        )
        
        # Find best and worst scenarios
        scenario_results = what_if_results["scenarios"]
        if scenario_results:
            best = min(scenario_results, key=lambda x: x["monthly_cost"])
            worst = max(scenario_results, key=lambda x: x["monthly_cost"])
        else:
            best = worst = None
        
        return {
            **what_if_results,
            "comparison": {
                "best_scenario": best,
                "worst_scenario": worst,
                "cost_range": {
                    "min": best["monthly_cost"] if best else 0,
                    "max": worst["monthly_cost"] if worst else 0,
                    "spread": (worst["monthly_cost"] - best["monthly_cost"]) if best and worst else 0
                }
            }
        }
    
    def set_currency(self, currency: str) -> None:
        """Set the currency for cost calculations"""
        self._currency = currency
    
    def set_pricing_data(self, pricing_data: Dict[str, Any]) -> None:
        """Set pricing data for more accurate calculations"""
        self._pricing_data = pricing_data

