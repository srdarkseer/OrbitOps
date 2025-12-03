"""
Agent 2: Efficiency Analyzer

This agent analyzes cloud architecture to identify inefficiencies and optimization opportunities.
It uses LLM reasoning to understand patterns and suggest improvements.

Areas of analysis:
- Resource utilization
- Cost optimization opportunities
- Performance bottlenecks
- Security gaps
- Best practice violations
- Right-sizing opportunities
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentResult, AgentStatus


class EfficiencyAnalyzerAgent(BaseAgent):
    """
    Agent responsible for finding inefficiencies in cloud architecture.
    
    This agent analyzes architecture data from Agent 1 and identifies:
    - Underutilized resources
    - Over-provisioned instances
    - Missing optimizations
    - Cost-saving opportunities
    - Performance issues
    - Security improvements
    """
    
    def __init__(self):
        """Initialize the Efficiency Analyzer Agent"""
        super().__init__(
            agent_id="agent2_efficiency_analyzer",
            name="Efficiency Analyzer",
            description="Identifies inefficiencies and optimization opportunities in cloud architecture"
        )
    
    def get_required_inputs(self) -> List[str]:
        """
        Returns the required input keys for this agent.
        
        Required inputs:
        - architecture: Architecture data from Agent 1
        """
        return ["architecture"]
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Analyze the architecture for inefficiencies.
        
        Args:
            input_data: Dictionary containing:
                - architecture: Structured architecture data from Agent 1
                - analysis_depth: Optional - "basic", "detailed", "comprehensive"
                - focus_areas: Optional - List of areas to focus on
                
        Returns:
            AgentResult with inefficiency analysis
        """
        try:
            self.set_status(AgentStatus.PROCESSING)
            
            # Validate input
            is_valid, error = self.validate_input(input_data)
            if not is_valid:
                return AgentResult(
                    success=False,
                    error=error
                )
            
            architecture = input_data["architecture"]
            analysis_depth = input_data.get("analysis_depth", "detailed")
            focus_areas = input_data.get("focus_areas", [])
            
            # Perform analysis
            inefficiencies = await self._analyze_architecture(
                architecture, analysis_depth, focus_areas
            )
            
            # Prioritize findings
            prioritized = self._prioritize_inefficiencies(inefficiencies)
            
            # Calculate potential savings
            savings_estimate = self._estimate_savings(inefficiencies)
            
            self.set_status(AgentStatus.COMPLETED)
            
            return AgentResult(
                success=True,
                data={
                    "inefficiencies": prioritized,
                    "summary": {
                        "total_findings": len(inefficiencies),
                        "critical_count": len([i for i in inefficiencies if i.get("severity") == "critical"]),
                        "high_count": len([i for i in inefficiencies if i.get("severity") == "high"]),
                        "medium_count": len([i for i in inefficiencies if i.get("severity") == "medium"]),
                        "low_count": len([i for i in inefficiencies if i.get("severity") == "low"]),
                        "estimated_savings": savings_estimate
                    },
                    "recommendations": self._generate_recommendations(inefficiencies),
                    "analysis_metadata": {
                        "depth": analysis_depth,
                        "focus_areas": focus_areas or "all"
                    }
                },
                metadata={
                    "agent_id": self.agent_id,
                    "analysis_timestamp": "N/A"  # Will be calculated in real implementation
                }
            )
        
        except Exception as e:
            self.set_status(AgentStatus.ERROR)
            return AgentResult(
                success=False,
                error=f"Error analyzing efficiency: {str(e)}"
            )
    
    async def _analyze_architecture(
        self, architecture: Dict[str, Any], depth: str, focus_areas: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Analyze architecture for inefficiencies.
        
        Args:
            architecture: Architecture data to analyze
            depth: Analysis depth level
            focus_areas: Specific areas to focus on
            
        Returns:
            List of inefficiency findings
        """
        inefficiencies = []
        
        # Analyze compute resources
        if not focus_areas or "compute" in focus_areas:
            compute_issues = await self._analyze_compute(architecture.get("compute", {}))
            inefficiencies.extend(compute_issues)
        
        # Analyze storage resources
        if not focus_areas or "storage" in focus_areas:
            storage_issues = await self._analyze_storage(architecture.get("storage", {}))
            inefficiencies.extend(storage_issues)
        
        # Analyze networking
        if not focus_areas or "networking" in focus_areas:
            networking_issues = await self._analyze_networking(architecture.get("networking", {}))
            inefficiencies.extend(networking_issues)
        
        # Analyze security
        if not focus_areas or "security" in focus_areas:
            security_issues = await self._analyze_security(architecture.get("security", {}))
            inefficiencies.extend(security_issues)
        
        # Use LLM for advanced pattern detection if available
        if self._llm_client and depth in ["detailed", "comprehensive"]:
            llm_findings = await self._llm_analyze_patterns(architecture, depth)
            inefficiencies.extend(llm_findings)
        
        return inefficiencies
    
    async def _analyze_compute(self, compute_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze compute resources for inefficiencies"""
        findings = []
        
        instances = compute_data.get("instances", [])
        
        # Check for underutilized instances
        for instance in instances:
            utilization = instance.get("utilization", {})
            cpu_util = utilization.get("cpu", 0)
            memory_util = utilization.get("memory", 0)
            
            if cpu_util < 20 and memory_util < 20:
                findings.append({
                    "type": "underutilized_instance",
                    "resource_id": instance.get("id"),
                    "severity": "high",
                    "description": f"Instance {instance.get('id')} is underutilized (CPU: {cpu_util}%, Memory: {memory_util}%)",
                    "recommendation": "Consider right-sizing or consolidating instances",
                    "potential_savings": instance.get("monthly_cost", 0) * 0.5,  # Estimate 50% savings
                    "category": "compute"
                })
        
        # Check for over-provisioned instances
        for instance in instances:
            instance_type = instance.get("instance_type", "")
            if "large" in instance_type.lower() or "xlarge" in instance_type.lower():
                utilization = instance.get("utilization", {})
                if utilization.get("cpu", 0) < 30:
                    findings.append({
                        "type": "over_provisioned",
                        "resource_id": instance.get("id"),
                        "severity": "medium",
                        "description": f"Instance {instance.get('id')} may be over-provisioned",
                        "recommendation": "Consider downsizing to a smaller instance type",
                        "potential_savings": instance.get("monthly_cost", 0) * 0.3,
                        "category": "compute"
                    })
        
        return findings
    
    async def _analyze_storage(self, storage_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze storage resources for inefficiencies"""
        findings = []
        
        buckets = storage_data.get("buckets", [])
        
        # Check for unused or empty buckets
        for bucket in buckets:
            size = bucket.get("size_gb", 0)
            last_accessed = bucket.get("last_accessed_days_ago", 999)
            
            if size == 0:
                findings.append({
                    "type": "empty_bucket",
                    "resource_id": bucket.get("id"),
                    "severity": "low",
                    "description": f"Storage bucket {bucket.get('id')} is empty",
                    "recommendation": "Consider deleting if not needed",
                    "potential_savings": bucket.get("monthly_cost", 0),
                    "category": "storage"
                })
            elif last_accessed > 90:
                findings.append({
                    "type": "unused_storage",
                    "resource_id": bucket.get("id"),
                    "severity": "medium",
                    "description": f"Storage bucket {bucket.get('id')} hasn't been accessed in {last_accessed} days",
                    "recommendation": "Consider moving to cheaper storage tier or archiving",
                    "potential_savings": bucket.get("monthly_cost", 0) * 0.7,
                    "category": "storage"
                })
        
        return findings
    
    async def _analyze_networking(self, networking_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze networking for inefficiencies"""
        findings = []
        
        load_balancers = networking_data.get("load_balancers", [])
        
        # Check for idle load balancers
        for lb in load_balancers:
            active_connections = lb.get("active_connections", 0)
            if active_connections == 0:
                findings.append({
                    "type": "idle_load_balancer",
                    "resource_id": lb.get("id"),
                    "severity": "high",
                    "description": f"Load balancer {lb.get('id')} has no active connections",
                    "recommendation": "Consider removing if not in use",
                    "potential_savings": lb.get("monthly_cost", 0),
                    "category": "networking"
                })
        
        return findings
    
    async def _analyze_security(self, security_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze security for inefficiencies and gaps"""
        findings = []
        
        # Check for missing security configurations
        iam_roles = security_data.get("iam_roles", [])
        policies = security_data.get("policies", [])
        
        if len(iam_roles) == 0:
            findings.append({
                "type": "missing_iam",
                "resource_id": "global",
                "severity": "critical",
                "description": "No IAM roles detected - potential security risk",
                "recommendation": "Implement proper IAM roles and policies",
                "potential_savings": 0,  # Security improvement, not cost savings
                "category": "security"
            })
        
        return findings
    
    async def _llm_analyze_patterns(
        self, architecture: Dict[str, Any], depth: str
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to analyze patterns and find advanced inefficiencies.
        
        Args:
            architecture: Full architecture data
            depth: Analysis depth
            
        Returns:
            List of LLM-discovered inefficiencies
        """
        if not self._llm_client:
            return []
        
        # TODO: Implement LLM-based pattern analysis
        # This will use the LLM to understand complex patterns and suggest optimizations
        
        # Placeholder for LLM analysis
        return []
    
    def _prioritize_inefficiencies(
        self, inefficiencies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize inefficiencies by severity and potential impact.
        
        Args:
            inefficiencies: List of inefficiency findings
            
        Returns:
            Prioritized list (critical -> high -> medium -> low)
        """
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        return sorted(
            inefficiencies,
            key=lambda x: (
                severity_order.get(x.get("severity", "low"), 3),
                -x.get("potential_savings", 0)  # Higher savings first within same severity
            )
        )
    
    def _estimate_savings(self, inefficiencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Estimate potential cost savings from addressing inefficiencies.
        
        Args:
            inefficiencies: List of inefficiency findings
            
        Returns:
            Dictionary with savings estimates
        """
        total_savings = sum(i.get("potential_savings", 0) for i in inefficiencies)
        
        by_category = {}
        for inefficiency in inefficiencies:
            category = inefficiency.get("category", "other")
            if category not in by_category:
                by_category[category] = 0
            by_category[category] += inefficiency.get("potential_savings", 0)
        
        return {
            "total_monthly_savings": total_savings,
            "total_annual_savings": total_savings * 12,
            "by_category": by_category,
            "currency": "USD"  # Default, should be configurable
        }
    
    def _generate_recommendations(
        self, inefficiencies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations from inefficiencies.
        
        Args:
            inefficiencies: List of inefficiency findings
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Group by type and create consolidated recommendations
        by_type = {}
        for inefficiency in inefficiencies:
            issue_type = inefficiency.get("type")
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(inefficiency)
        
        for issue_type, issues in by_type.items():
            total_savings = sum(i.get("potential_savings", 0) for i in issues)
            recommendations.append({
                "type": issue_type,
                "count": len(issues),
                "total_potential_savings": total_savings,
                "action": issues[0].get("recommendation"),
                "affected_resources": [i.get("resource_id") for i in issues]
            })
        
        return recommendations

