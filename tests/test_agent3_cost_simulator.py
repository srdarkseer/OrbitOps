"""
Tests for Agent 3: Cost Simulator
"""

import pytest
from agents.agent3_cost_simulator import CostSimulatorAgent
from agents.base_agent import AgentStatus


class TestCostSimulatorAgent:
    """Test suite for CostSimulatorAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create an instance of CostSimulatorAgent"""
        return CostSimulatorAgent()
    
    @pytest.fixture
    def sample_architecture(self):
        """Sample architecture data for testing"""
        return {
            "provider": "aws",
            "compute": {
                "instances": [
                    {"id": "i-1", "monthly_cost": 100.0},
                    {"id": "i-2", "monthly_cost": 50.0}
                ]
            },
            "storage": {
                "buckets": [
                    {"id": "bucket-1", "monthly_cost": 20.0}
                ]
            },
            "networking": {
                "load_balancers": [
                    {"id": "lb-1", "monthly_cost": 30.0}
                ]
            }
        }
    
    @pytest.fixture
    def sample_inefficiencies(self):
        """Sample inefficiency data for testing"""
        return [
            {
                "type": "underutilized_instance",
                "resource_id": "i-1",
                "potential_savings": 50.0
            },
            {
                "type": "unused_storage",
                "resource_id": "bucket-1",
                "potential_savings": 10.0
            }
        ]
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly"""
        assert agent.agent_id == "agent3_cost_simulator"
        assert agent.name == "Cost Simulator"
        assert agent.get_status() == AgentStatus.IDLE
    
    def test_get_required_inputs(self, agent):
        """Test required inputs (should be flexible)"""
        required = agent.get_required_inputs()
        # Should be empty or flexible
        assert isinstance(required, list)
    
    def test_set_currency(self, agent):
        """Test setting currency"""
        agent.set_currency("EUR")
        assert agent._currency == "EUR"
    
    def test_set_pricing_data(self, agent):
        """Test setting pricing data"""
        pricing = {"ec2": {"t2.micro": 0.01}}
        agent.set_pricing_data(pricing)
        assert agent._pricing_data == pricing
    
    @pytest.mark.asyncio
    async def test_simulate_current_costs(self, agent, sample_architecture):
        """Test current cost simulation"""
        result = await agent._simulate_current_costs(sample_architecture)
        
        assert "current_costs" in result
        assert result["current_costs"]["monthly"] == 200.0  # 100 + 50 + 20 + 30
        assert result["current_costs"]["annual"] == 2400.0
        assert "breakdown" in result["current_costs"]
        assert result["current_costs"]["breakdown"]["compute"] == 150.0
        assert result["current_costs"]["breakdown"]["storage"] == 20.0
        assert result["current_costs"]["breakdown"]["networking"] == 30.0
    
    @pytest.mark.asyncio
    async def test_simulate_projected_costs(self, agent, sample_architecture, sample_inefficiencies):
        """Test projected cost simulation"""
        result = await agent._simulate_projected_costs(
            sample_architecture, sample_inefficiencies, "monthly"
        )
        
        assert "current_costs" in result
        assert "projected_costs" in result
        assert "savings" in result
        
        # Current should be 200
        assert result["current_costs"]["monthly"] == 200.0
        
        # Projected should be 200 - 60 = 140
        assert result["projected_costs"]["monthly"] == 140.0
        
        # Savings should be 60
        assert result["savings"]["monthly"] == 60.0
        assert result["savings"]["percentage"] == 30.0  # 60/200 * 100
    
    @pytest.mark.asyncio
    async def test_simulate_what_if_scenarios(self, agent, sample_architecture):
        """Test what-if scenario simulation"""
        scenarios = [
            {
                "name": "Add Server",
                "changes": [
                    {"type": "add_resource", "value": 75.0}
                ]
            },
            {
                "name": "Remove Load Balancer",
                "changes": [
                    {"type": "remove_resource", "value": 30.0}
                ]
            }
        ]
        
        result = await agent._simulate_what_if_scenarios(
            sample_architecture, scenarios, "monthly"
        )
        
        assert "scenarios" in result
        assert len(result["scenarios"]) == 2
        
        # First scenario should add 75
        assert result["scenarios"][0]["monthly_cost"] == 275.0
        assert result["scenarios"][0]["difference"] == 75.0
        
        # Second scenario should subtract 30
        assert result["scenarios"][1]["monthly_cost"] == 170.0
        assert result["scenarios"][1]["difference"] == -30.0
    
    @pytest.mark.asyncio
    async def test_compare_scenarios(self, agent, sample_architecture):
        """Test scenario comparison"""
        scenarios = [
            {
                "name": "Expensive",
                "changes": [{"type": "add_resource", "value": 100.0}]
            },
            {
                "name": "Cheap",
                "changes": [{"type": "remove_resource", "value": 50.0}]
            }
        ]
        
        result = await agent._compare_scenarios(
            sample_architecture, scenarios, "monthly"
        )
        
        assert "comparison" in result
        assert result["comparison"]["best_scenario"]["name"] == "Cheap"
        assert result["comparison"]["best_scenario"]["monthly_cost"] == 150.0
        assert result["comparison"]["worst_scenario"]["name"] == "Expensive"
        assert result["comparison"]["worst_scenario"]["monthly_cost"] == 300.0
    
    @pytest.mark.asyncio
    async def test_process_current_simulation(self, agent, sample_architecture):
        """Test processing current cost simulation"""
        result = await agent.process({
            "architecture": sample_architecture,
            "simulation_type": "current"
        })
        
        assert result.success
        assert "current_costs" in result.data
        assert agent.get_status() == AgentStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_process_projected_simulation(self, agent, sample_architecture, sample_inefficiencies):
        """Test processing projected cost simulation"""
        result = await agent.process({
            "architecture": sample_architecture,
            "inefficiencies": sample_inefficiencies,
            "simulation_type": "projected",
            "time_period": "annual"
        })
        
        assert result.success
        assert "projected_costs" in result.data
        assert "savings" in result.data
    
    @pytest.mark.asyncio
    async def test_process_what_if_simulation(self, agent, sample_architecture):
        """Test processing what-if simulation"""
        result = await agent.process({
            "architecture": sample_architecture,
            "simulation_type": "what_if",
            "scenarios": [
                {"name": "Test", "changes": [{"type": "add_resource", "value": 50.0}]}
            ]
        })
        
        assert result.success
        assert "scenarios" in result.data
    
    @pytest.mark.asyncio
    async def test_process_missing_inputs(self, agent):
        """Test processing with missing inputs"""
        result = await agent.process({})
        
        assert not result.success
        assert "error" in result or result.error is not None
    
    @pytest.mark.asyncio
    async def test_process_invalid_simulation_type(self, agent, sample_architecture):
        """Test processing with invalid simulation type"""
        result = await agent.process({
            "architecture": sample_architecture,
            "simulation_type": "invalid_type"
        })
        
        assert not result.success
        assert "error" in result or result.error is not None

