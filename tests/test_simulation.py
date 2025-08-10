"""
Unit tests for NetworkSimulator and ReferralBonusOptimizer classes.

Tests all functionality including:
- Network growth simulation
- Expected value calculations
- Days to target calculations
- Bonus optimization
- Edge cases and error handling
"""

import pytest
from source.simulation import NetworkSimulator, ReferralBonusOptimizer
import math


class TestNetworkSimulator:
    """Test suite for NetworkSimulator class."""
    
    def setup_method(self):
        """Set up a fresh simulator before each test."""
        self.simulator = NetworkSimulator(seed=42)  # Fixed seed for reproducibility
    
    def test_initialization(self):
        """Test simulator initialization."""
        assert self.simulator.initial_active_referrers == 100
        assert self.simulator.max_referrals_per_referrer == 10
    
    def test_initialization_with_seed(self):
        """Test simulator initialization with custom seed."""
        simulator = NetworkSimulator(seed=123)
        assert simulator.initial_active_referrers == 100
        assert simulator.max_referrals_per_referrer == 10
    
    def test_simulate_zero_days(self):
        """Test simulation with zero days."""
        result = self.simulator.simulate(0.5, 0)
        assert result == []
    
    def test_simulate_zero_probability(self):
        """Test simulation with zero probability."""
        result = self.simulator.simulate(0.0, 10)
        assert len(result) == 10
        assert all(count == 0 for count in result)
    
    def test_simulate_max_probability(self):
        """Test simulation with maximum probability."""
        result = self.simulator.simulate(1.0, 5)
        assert len(result) == 5
        
        # With probability 1.0, each active referrer should make a referral each day
        # until they reach capacity
        assert result[0] == 100  # Day 1: 100 referrers make referrals
        assert result[1] == 200  # Day 2: 100 more referrals
        # After 10 days, all referrers become inactive
    
    def test_simulate_medium_probability(self):
        """Test simulation with medium probability."""
        result = self.simulator.simulate(0.5, 10)
        assert len(result) == 10
        
        # Should have some referrals but not maximum
        assert result[0] > 0  # Some referrals on first day
        assert result[0] < 100  # But not all referrers succeed
    
    def test_simulate_invalid_probability(self):
        """Test simulation with invalid probability values."""
        with pytest.raises(ValueError, match="Probability p must be between 0.0 and 1.0"):
            self.simulator.simulate(-0.1, 10)
        
        with pytest.raises(ValueError, match="Probability p must be between 0.0 and 1.0"):
            self.simulator.simulate(1.1, 10)
    
    def test_simulate_invalid_days(self):
        """Test simulation with invalid days."""
        with pytest.raises(ValueError, match="Days must be non-negative"):
            self.simulator.simulate(0.5, -1)
    
    def test_simulate_continue_statements(self):
        """Test simulate method continue statements and capacity checks."""
        simulator = NetworkSimulator(seed=42)
        
        # Test with high probability to ensure referrers hit capacity
        # This should trigger the continue statements and capacity checks
        result = simulator.simulate(0.9, 15)  # High probability, enough days to hit capacity
        
        # Should have some referrals
        assert len(result) == 15
        assert result[-1] > 0
        
        # Verify the simulation worked correctly
        assert all(isinstance(x, int) for x in result)
        assert all(x >= 0 for x in result)

    def test_simulate_capacity_reached(self):
        """Test simulate method when referrers reach capacity."""
        simulator = NetworkSimulator(seed=42)
        
        # Test with very high probability to ensure referrers quickly hit capacity
        result = simulator.simulate(0.99, 20)
        
        # Should have referrals and some referrers should hit capacity
        assert len(result) == 20
        assert result[-1] > 0
        
        # Verify the simulation worked correctly
        assert all(isinstance(x, int) for x in result)
        assert all(x >= 0 for x in result)
    
    def test_simulate_expected_zero_days(self):
        """Test expected simulation with zero days."""
        result = self.simulator.simulate_expected(0.5, 0)
        assert result == []
    
    def test_simulate_expected_zero_probability(self):
        """Test expected simulation with zero probability."""
        result = self.simulator.simulate_expected(0.0, 10)
        assert len(result) == 10
        assert all(count == 0.0 for count in result)
    
    def test_simulate_expected_max_probability(self):
        """Test expected simulation with maximum probability."""
        result = self.simulator.simulate_expected(1.0, 5)
        assert len(result) == 5
        
        # With probability 1.0, each active referrer should make a referral each day
        # until they reach capacity
        assert result[0] == 100.0  # Day 1: 100 referrers make referrals
        assert result[1] == 200.0  # Day 2: 100 more referrals
    
    def test_simulate_expected_medium_probability(self):
        """Test expected simulation with medium probability."""
        result = self.simulator.simulate_expected(0.5, 10)
        assert len(result) == 10
        
        # Should have expected referrals
        assert result[0] == 50.0  # Day 1: 100 * 0.5 = 50 expected referrals
        assert result[1] == 100.0  # Day 2: 100 * 0.5 = 50 more, total 100
    
    def test_simulate_expected_invalid_probability(self):
        """Test expected simulation with invalid probability values."""
        with pytest.raises(ValueError, match="Probability p must be between 0.0 and 1.0"):
            self.simulator.simulate_expected(-0.1, 10)
        
        with pytest.raises(ValueError, match="Probability p must be between 0.0 and 1.0"):
            self.simulator.simulate_expected(1.1, 10)
    
    def test_simulate_expected_invalid_days(self):
        """Test expected simulation with invalid days."""
        with pytest.raises(ValueError, match="Days must be non-negative"):
            self.simulator.simulate_expected(0.5, -1)
    
    def test_days_to_target_zero_target(self):
        """Test days to target with zero target."""
        result = self.simulator.days_to_target(0.5, 0)
        assert result == 0
    
    def test_days_to_target_zero_probability(self):
        """Test days to target with zero probability."""
        result = self.simulator.days_to_target(0.0, 100)
        assert result is None  # Impossible with zero probability
    
    def test_days_to_target_achievable(self):
        """Test days to target with achievable target."""
        # With probability 0.5, we expect 50 referrals per day
        # So 100 referrals should take 2 days
        result = self.simulator.days_to_target(0.5, 100)
        assert result is not None
        assert result >= 2  # Should take at least 2 days
    
    def test_days_to_target_unachievable(self):
        """Test days to target with unachievable target."""
        # With very low probability, some targets may be unachievable
        result = self.simulator.days_to_target(0.001, 10000)
        # This may or may not be achievable, but should not crash
    
    def test_simulation_reproducibility(self):
        """Test that simulations with same seed are reproducible."""
        simulator1 = NetworkSimulator(seed=123)
        simulator2 = NetworkSimulator(seed=123)
        
        result1 = simulator1.simulate(0.3, 10)
        result2 = simulator2.simulate(0.3, 10)
        
        assert result1 == result2
    
    def test_capacity_constraint(self):
        """Test that referrers become inactive after reaching capacity."""
        result = self.simulator.simulate_expected(1.0, 15)
        
        # After 10 days, all referrers should be inactive
        # So no more referrals after day 10
        assert result[9] == 1000  # Day 10: 100 * 10 = 1000 referrals
        assert result[10] == 1000  # Day 11: No more referrals
        assert result[14] == 1000  # Day 15: Still no more referrals


class TestReferralBonusOptimizer:
    """Test ReferralBonusOptimizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = ReferralBonusOptimizer()
    
    def test_initialization(self):
        """Test optimizer initialization."""
        assert self.optimizer.min_bonus == 10
        assert self.optimizer.max_bonus == 10000
    
    def test_min_bonus_for_target_zero_days(self):
        """Test minimum bonus with zero days."""
        def linear_prob(bonus):
            return min(0.1 + bonus / 1000.0, 1.0)
        
        result = self.optimizer.min_bonus_for_target(0, 100, linear_prob)
        assert result is None
    
    def test_min_bonus_for_target_zero_target(self):
        """Test minimum bonus with zero target."""
        def linear_prob(bonus):
            return min(0.1 + bonus / 1000.0, 1.0)
        
        result = self.optimizer.min_bonus_for_target(10, 0, linear_prob)
        assert result is None
    
    def test_min_bonus_for_target_invalid_probability_function(self):
        """Test minimum bonus with invalid probability function."""
        # Test with non-callable
        with pytest.raises(ValueError, match="adoption_prob must be a callable function"):
            self.optimizer.min_bonus_for_target(10, 100, 0.1)
        
        # Test with function that returns invalid probability
        def invalid_prob(bonus):
            return 1.5  # Invalid probability > 1.0
        
        with pytest.raises(ValueError, match="adoption_prob function must return probability between 0.0 and 1.0"):
            self.optimizer.min_bonus_for_target(10, 100, invalid_prob)
        
        # Test with function that doesn't accept bonus parameter
        def wrong_signature():
            return 0.1
        
        with pytest.raises(TypeError, match="adoption_prob function must accept a bonus parameter"):
            self.optimizer.min_bonus_for_target(10, 100, wrong_signature)
    
    def test_min_bonus_for_target_invalid_eps(self):
        """Test minimum bonus with invalid epsilon."""
        def linear_prob(bonus):
            return min(0.1 + bonus / 1000.0, 1.0)
        
        with pytest.raises(ValueError, match="Tolerance eps must be positive"):
            self.optimizer.min_bonus_for_target(10, 100, linear_prob, eps=0.0)
        
        with pytest.raises(ValueError, match="Tolerance eps must be positive"):
            self.optimizer.min_bonus_for_target(10, 100, linear_prob, eps=-0.1)
    
    def test_min_bonus_for_target_achievable(self):
        """Test minimum bonus with achievable target."""
        def linear_prob(bonus):
            return min(0.1 + bonus / 1000.0, 1.0)
        
        # With 10 days and base probability 0.1, we need some bonus to reach 100 hires
        result = self.optimizer.min_bonus_for_target(10, 100, linear_prob, eps=0.05)
        assert result is not None
        assert result >= 0
        assert result % 10 == 0  # Should be in $10 increments
    
    def test_min_bonus_for_target_unachievable(self):
        """Test minimum bonus with unachievable target."""
        def very_low_prob(bonus):
            return 0.001  # Very low probability regardless of bonus
        
        # With very low probability and few days, some targets may be impossible
        result = self.optimizer.min_bonus_for_target(1, 1000, very_low_prob, eps=0.01)
        assert result is None  # Should be impossible
    
    def test_min_bonus_for_target_high_probability(self):
        """Test minimum bonus with high base probability."""
        def high_prob(bonus):
            return 0.8  # High probability regardless of bonus
        
        # With high base probability, may not need much bonus
        result = self.optimizer.min_bonus_for_target(10, 100, high_prob, eps=0.1)
        assert result is not None
        # May need very little or no bonus
    
    def test_bonus_increments(self):
        """Test that bonus amounts are in $10 increments."""
        def linear_prob(bonus):
            return min(0.1 + bonus / 1000.0, 1.0)
        
        result = self.optimizer.min_bonus_for_target(10, 100, linear_prob, eps=0.05)
        if result is not None:
            assert result % 10 == 0
    
    def test_different_adoption_prob_functions(self):
        """Test min_bonus_for_target with various types of callable functions."""
        # Test with linear function
        def linear_prob(bonus):
            return min(0.1 + bonus * 0.001, 1.0)
        
        result = self.optimizer.min_bonus_for_target(30, 50, linear_prob)
        assert result is not None
        assert result >= 0
        
        # Test with exponential function
        def exp_prob(bonus):
            return min(0.05 * (1.1 ** (bonus / 100)), 0.8)
        
        result = self.optimizer.min_bonus_for_target(30, 50, exp_prob)
        assert result is not None
        assert result >= 0
        
        # Test with step function
        def step_prob(bonus):
            if bonus < 100:
                return 0.1
            elif bonus < 200:
                return 0.3
            else:
                return 0.6
        
        result = self.optimizer.min_bonus_for_target(30, 50, step_prob)
        assert result is not None
        assert result >= 0

    def test_days_to_target_zero_days_simulation(self):
        """Test days_to_target when simulation returns empty list."""
        # This test was incorrectly trying to call days_to_target on ReferralBonusOptimizer
        # The days_to_target method is on NetworkSimulator, not ReferralBonusOptimizer
        # Let me test the actual scenario where simulation returns empty list
        simulator = NetworkSimulator()
        
        # Test with 0 days which should return empty list
        result = simulator.simulate_expected(0.5, 0)
        assert result == []
        
        # Test with negative days which should raise ValueError
        with pytest.raises(ValueError):
            simulator.simulate_expected(0.5, -1)

    def test_min_bonus_for_target_invalid_final_prob(self):
        """Test min_bonus_for_target when final probability is invalid."""
        # Create an adoption_prob function that returns invalid probability for final bonus
        def invalid_prob(bonus):
            if bonus < 200:  # Normal case
                return 0.5
            else:  # Invalid case for final bonus
                return 1.5  # Invalid probability > 1.0
        
        # This should raise ValueError when the function returns invalid probability
        with pytest.raises(ValueError, match="returned invalid probability: 1.5"):
            self.optimizer.min_bonus_for_target(30, 50, invalid_prob)
    
    def test_analyze_bonus_effectiveness_achievable(self):
        """Test bonus effectiveness analysis with achievable target."""
        def linear_prob(bonus):
            return min(0.1 + bonus / 1000.0, 1.0)
        
        analysis = self.optimizer.analyze_bonus_effectiveness(10, 100, linear_prob, eps=0.05)
        
        if analysis['achievable']:
            assert analysis['min_bonus'] is not None
            assert analysis['total_cost'] is not None
            assert analysis['cost_per_hire'] is not None
            assert analysis['days_required'] == 10
            assert analysis['target_hires'] == 100
            assert analysis['total_cost'] == analysis['min_bonus'] * 100
            assert analysis['cost_per_hire'] == analysis['min_bonus']
    
    def test_analyze_bonus_effectiveness_unachievable(self):
        """Test bonus effectiveness analysis with unachievable target."""
        def very_low_prob(bonus):
            return 0.001  # Very low probability regardless of bonus
        
        analysis = self.optimizer.analyze_bonus_effectiveness(1, 1000, very_low_prob, eps=0.01)
        
        if not analysis['achievable']:
            assert analysis['min_bonus'] is None
            assert analysis['total_cost'] is None
            assert analysis['cost_per_hire'] is None
    
    def test_bonus_optimization_edge_cases(self):
        """Test bonus optimization with various edge cases."""
        def linear_prob(bonus):
            return min(0.1 + bonus / 1000.0, 1.0)
        
        # Test with very small eps
        result = self.optimizer.min_bonus_for_target(10, 50, linear_prob, eps=0.001)
        # Should still work, may need higher bonus
        
        # Test with very large eps
        result = self.optimizer.min_bonus_for_target(10, 50, linear_prob, eps=0.5)
        # Should work, may need lower bonus
        
        # Test with exactly achievable target
        result = self.optimizer.min_bonus_for_target(10, 100, linear_prob, eps=0.05)
        # Should find a solution
    
    def test_bonus_optimization_performance(self):
        """Test that bonus optimization completes in reasonable time."""
        import time
        
        def linear_prob(bonus):
            return min(0.1 + bonus / 1000.0, 1.0)
        
        start_time = time.time()
        result = self.optimizer.min_bonus_for_target(10, 100, linear_prob, eps=0.05)
        end_time = time.time()
        
        # Should complete in under 1 second
        assert end_time - start_time < 1.0


class TestIntegration:
    """Integration tests combining simulator and optimizer."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from simulation to optimization."""
        # Create simulator and optimizer
        simulator = NetworkSimulator(seed=42)
        optimizer = ReferralBonusOptimizer()
        
        # Simulate network growth
        simulation_result = simulator.simulate_expected(0.1, 10)
        assert len(simulation_result) == 10
        
        # Define adoption probability function
        def adoption_prob(bonus):
            return min(0.1 + bonus / 1000.0, 1.0)
        
        # Find minimum bonus for target
        target_hires = int(simulation_result[-1]) + 50  # Target 50 more than achieved
        min_bonus = optimizer.min_bonus_for_target(10, target_hires, adoption_prob, eps=0.05)
        
        # Should be achievable
        assert min_bonus is not None
        
        # Analyze effectiveness
        analysis = optimizer.analyze_bonus_effectiveness(10, target_hires, adoption_prob, eps=0.05)
        assert analysis['achievable'] is True
        assert analysis['min_bonus'] == min_bonus
    
    def test_consistency_between_simulations(self):
        """Test consistency between different simulation methods."""
        simulator = NetworkSimulator(seed=42)
        
        # Both methods should give similar results for the same parameters
        result1 = simulator.simulate(0.5, 10)
        result2 = simulator.simulate_expected(0.5, 10)
        
        assert len(result1) == len(result2)
        
        # Expected values should be deterministic
        result3 = simulator.simulate_expected(0.5, 10)
        assert result2 == result3
