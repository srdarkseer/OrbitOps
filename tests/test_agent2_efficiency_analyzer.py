"""
Tests for Agent 2: Efficiency Analyzer
"""

import pytest
from agents.agent2_efficiency_analyzer import EfficiencyAnalyzerAgent
from agents.base_agent import AgentStatus


class TestEfficiencyAnalyzerAgent:
    """Test suite for EfficiencyAnalyzerAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create an instance of EfficiencyAnalyzerAgent"""
        return EfficiencyAnalyzerAgent()
    
    @pytest.fixture
    def sample_architecture(self):
        """Sample architecture data for testing"""
        return {
            "provider": "aws",
            "resources": [],
            "services": ["ec2", "s3"],
            "compute": {
                "instances": [
                    {
                        "id": "i-123456",
                        "instance_type": "t2.large",
                        "utilization": {"cpu": 15, "memory": 10},
                        "monthly_cost": 50.0
                    },
                    {
                        "id": "i-789012",
                        "instance_type": "t2.micro",
                        "utilization": {"cpu": 80, "memory": 75},
                        "monthly_cost": 10.0
                    }
                ]
            },
            "storage": {
                "buckets": [
                    {
                        "id": "bucket-empty",
                        "size_gb": 0,
                        "last_accessed_days_ago": 0,
                        "monthly_cost": 5.0
                    },
                    {
                        "id": "bucket-unused",
                        "size_gb": 100,
                        "last_accessed_days_ago": 120,
                        "monthly_cost": 20.0
                    }
                ]
            },
            "networking": {
                "load_balancers": [
                    {
                        "id": "lb-idle",
                        "active_connections": 0,
                        "monthly_cost": 30.0
                    }
                ]
            },
            "security": {
                "iam_roles": [],
                "policies": []
            }
        }
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly"""
        assert agent.agent_id == "agent2_efficiency_analyzer"
        assert agent.name == "Efficiency Analyzer"
        assert agent.get_status() == AgentStatus.IDLE
    
    def test_get_required_inputs(self, agent):
        """Test required inputs"""
        required = agent.get_required_inputs()
        assert "architecture" in required
        assert len(required) == 1
    
    def test_validate_input_missing_architecture(self, agent):
        """Test input validation with missing architecture"""
        is_valid, error = agent.validate_input({})
        assert not is_valid
        assert "architecture" in error.lower()
    
    def test_validate_input_with_architecture(self, agent, sample_architecture):
        """Test input validation with valid input"""
        is_valid, error = agent.validate_input({"architecture": sample_architecture})
        assert is_valid
        assert error is None
    
    @pytest.mark.asyncio
    async def test_analyze_compute_underutilized(self, agent, sample_architecture):
        """Test detection of underutilized compute instances"""
        compute_data = sample_architecture["compute"]
        findings = await agent._analyze_compute(compute_data)
        
        # Should find the underutilized instance
        underutilized = [f for f in findings if f["type"] == "underutilized_instance"]
        assert len(underutilized) > 0
        assert underutilized[0]["resource_id"] == "i-123456"
        assert underutilized[0]["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_analyze_storage_empty_bucket(self, agent, sample_architecture):
        """Test detection of empty storage buckets"""
        storage_data = sample_architecture["storage"]
        findings = await agent._analyze_storage(storage_data)
        
        # Should find the empty bucket
        empty_buckets = [f for f in findings if f["type"] == "empty_bucket"]
        assert len(empty_buckets) > 0
        assert empty_buckets[0]["resource_id"] == "bucket-empty"
    
    @pytest.mark.asyncio
    async def test_analyze_storage_unused_bucket(self, agent, sample_architecture):
        """Test detection of unused storage buckets"""
        storage_data = sample_architecture["storage"]
        findings = await agent._analyze_storage(storage_data)
        
        # Should find the unused bucket
        unused_buckets = [f for f in findings if f["type"] == "unused_storage"]
        assert len(unused_buckets) > 0
        assert unused_buckets[0]["resource_id"] == "bucket-unused"
    
    @pytest.mark.asyncio
    async def test_analyze_networking_idle_lb(self, agent, sample_architecture):
        """Test detection of idle load balancers"""
        networking_data = sample_architecture["networking"]
        findings = await agent._analyze_networking(networking_data)
        
        # Should find the idle load balancer
        idle_lbs = [f for f in findings if f["type"] == "idle_load_balancer"]
        assert len(idle_lbs) > 0
        assert idle_lbs[0]["resource_id"] == "lb-idle"
    
    @pytest.mark.asyncio
    async def test_analyze_security_missing_iam(self, agent, sample_architecture):
        """Test detection of missing security configurations"""
        security_data = sample_architecture["security"]
        findings = await agent._analyze_security(security_data)
        
        # Should find missing IAM
        missing_iam = [f for f in findings if f["type"] == "missing_iam"]
        assert len(missing_iam) > 0
        assert missing_iam[0]["severity"] == "critical"
    
    def test_prioritize_inefficiencies(self, agent):
        """Test prioritization of inefficiencies"""
        inefficiencies = [
            {"severity": "low", "potential_savings": 10},
            {"severity": "critical", "potential_savings": 100},
            {"severity": "high", "potential_savings": 50},
            {"severity": "medium", "potential_savings": 20}
        ]
        
        prioritized = agent._prioritize_inefficiencies(inefficiencies)
        
        # Should be sorted by severity (critical first)
        assert prioritized[0]["severity"] == "critical"
        assert prioritized[1]["severity"] == "high"
        assert prioritized[2]["severity"] == "medium"
        assert prioritized[3]["severity"] == "low"
    
    def test_estimate_savings(self, agent):
        """Test savings estimation"""
        inefficiencies = [
            {"potential_savings": 50, "category": "compute"},
            {"potential_savings": 30, "category": "storage"},
            {"potential_savings": 20, "category": "compute"}
        ]
        
        savings = agent._estimate_savings(inefficiencies)
        
        assert savings["total_monthly_savings"] == 100
        assert savings["total_annual_savings"] == 1200
        assert savings["by_category"]["compute"] == 70
        assert savings["by_category"]["storage"] == 30
    
    @pytest.mark.asyncio
    async def test_process_success(self, agent, sample_architecture):
        """Test successful processing"""
        result = await agent.process({"architecture": sample_architecture})
        
        assert result.success
        assert "inefficiencies" in result.data
        assert "summary" in result.data
        assert "recommendations" in result.data
        assert agent.get_status() == AgentStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_process_invalid_input(self, agent):
        """Test processing with invalid input"""
        result = await agent.process({})
        
        assert not result.success
        assert "error" in result or result.error is not None
        assert agent.get_status() == AgentStatus.ERROR

