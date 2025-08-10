"""
Mercor Network Growth Simulation and Bonus Optimization

This module implements:
- Network growth simulation with probabilistic referral success
- Referral bonus optimization using binary search
- Mathematical modeling of referral adoption rates

Time Complexity Analysis:
- simulate: O(days * active_referrers)
- days_to_target: O(log(target_total) * active_referrers)
- min_bonus_for_target: O(log(bonus_range) * days * active_referrers)
"""

import math
from typing import List, Optional, Tuple
import random


class NetworkSimulator:
    """
    Simulates network growth based on referral success probability and capacity constraints.
    
    Model Parameters:
    - Start with 100 active referrers
    - Maximum 10 referrals per referrer before becoming inactive
    - Daily probability p of successful referral
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the network simulator.
        
        Args:
            seed: Random seed for reproducible results (None for random)
        """
        self.random_generator = random.Random(seed)
        self.initial_active_referrers = 100
        self.max_referrals_per_referrer = 10
    
    def simulate(self, p: float, days: int) -> List[int]:
        """
        Simulate network growth over specified number of days.
        
        Args:
            p: Probability of successful referral per day (0.0 to 1.0)
            days: Number of days to simulate
            
        Returns:
            List[int]: Cumulative expected referrals for each day
            
        Raises:
            ValueError: If p is not between 0 and 1, or days is negative
        """
        if not 0.0 <= p <= 1.0:
            raise ValueError("Probability p must be between 0.0 and 1.0")
        
        if days < 0:
            raise ValueError("Days must be non-negative")
        
        if days == 0:
            return []
        
        cumulative_referrals = []
        current_total = 0
        
        # Track active referrers and their referral counts
        active_referrers = self.initial_active_referrers
        referrer_counts = {i: 0 for i in range(active_referrers)}
        
        for day in range(days):
            daily_referrals = 0
            
            # Process each active referrer
            referrers_to_deactivate = []
            
            for referrer_id in list(referrer_counts.keys()):  # Use list to avoid modification during iteration
                if referrer_counts[referrer_id] >= self.max_referrals_per_referrer:
                    referrers_to_deactivate.append(referrer_id)
                    continue
                
                # Attempt referral with probability p
                if self.random_generator.random() < p:
                    daily_referrals += 1
                    referrer_counts[referrer_id] += 1
                    
                    # Check if referrer should become inactive
                    if referrer_counts[referrer_id] >= self.max_referrals_per_referrer:
                        referrers_to_deactivate.append(referrer_id)
            
            # Deactivate referrers who have reached capacity
            for referrer_id in referrers_to_deactivate:
                if referrer_id in referrer_counts:
                    del referrer_counts[referrer_id]
            
            # Update active referrers count
            active_referrers = len(referrer_counts)
            
            # Update cumulative total
            current_total += daily_referrals
            cumulative_referrals.append(current_total)
        
        return cumulative_referrals
    
    def simulate_expected(self, p: float, days: int) -> List[float]:
        """
        Simulate network growth using expected values (deterministic).
        
        This version uses mathematical expectation rather than random sampling,
        providing deterministic results useful for analysis.
        
        Args:
            p: Probability of successful referral per day (0.0 to 1.0)
            days: Number of days to simulate
            
        Returns:
            List[float]: Cumulative expected referrals for each day
        """
        if not 0.0 <= p <= 1.0:
            raise ValueError("Probability p must be between 0.0 and 1.0")
        
        if days < 0:
            raise ValueError("Days must be non-negative")
        
        if days == 0:
            return []
        
        cumulative_referrals = []
        current_total = 0.0
        
        # Track active referrers and their expected referral counts
        active_referrers = self.initial_active_referrers
        referrer_counts = {i: 0.0 for i in range(active_referrers)}
        
        for day in range(days):
            daily_referrals = 0.0
            
            # Process each active referrer
            referrers_to_deactivate = []
            
            for referrer_id in range(active_referrers):
                if referrer_id not in referrer_counts:
                    continue
                    
                if referrer_counts[referrer_id] >= self.max_referrals_per_referrer:
                    referrers_to_deactivate.append(referrer_id)
                    continue
                
                # Expected referrals for this referrer today
                expected_today = p
                daily_referrals += expected_today
                referrer_counts[referrer_id] += expected_today
                
                # Check if referrer should become inactive
                if referrer_counts[referrer_id] >= self.max_referrals_per_referrer:
                    referrers_to_deactivate.append(referrer_id)
            
            # Deactivate referrers who have reached capacity
            for referrer_id in referrers_to_deactivate:
                if referrer_id in referrer_counts:
                    del referrer_counts[referrer_id]
            
            # Update active referrers count
            active_referrers = len(referrer_counts)
            
            # Update cumulative total
            current_total += daily_referrals
            cumulative_referrals.append(current_total)
        
        return cumulative_referrals
    
    def days_to_target(self, p: float, target_total: int) -> Optional[int]:
        """
        Calculate days needed to reach target total referrals.
        
        Uses binary search over simulation results to find the minimum days.
        
        Args:
            p: Probability of successful referral per day
            target_total: Target number of total referrals
            
        Returns:
            Optional[int]: Minimum days needed, or None if impossible
        """
        if target_total <= 0:
            return 0
        
        if p <= 0.0:
            return None  # Impossible with zero probability
        
        # Estimate upper bound for binary search
        # With 100 referrers making max 10 referrals each, theoretical max is 1000
        # But we need to account for daily probability
        max_days = 1000  # Conservative upper bound
        
        # Binary search for minimum days
        left, right = 0, max_days
        
        while left < right:
            mid = (left + right) // 2
            simulation_result = self.simulate_expected(p, mid)
            
            if not simulation_result:
                left = mid + 1
                continue
            
            final_total = simulation_result[-1]
            
            if final_total >= target_total:
                right = mid
            else:
                left = mid + 1
        
        # Verify the result
        if left <= max_days:
            final_simulation = self.simulate_expected(p, left)
            if final_simulation and final_simulation[-1] >= target_total:
                return left
        
        return None


class ReferralBonusOptimizer:
    """
    Optimizes referral bonus amounts to achieve hiring targets.
    
    Implements binary search over possible bonus values to find the minimum
    bonus required to meet hiring goals within specified constraints.
    
    The adoption_prob parameter is a callable function that takes a bonus amount
    and returns the corresponding adoption probability, supporting arbitrary
    monotonic functions for flexible modeling.
    """
    
    def __init__(self):
        """
        Initialize the bonus optimizer.
        
        Note: No base adoption probability is stored as it's now provided
        as a callable function for each optimization call.
        """
        self.min_bonus = 10  # Minimum bonus increment
        self.max_bonus = 10000  # Maximum bonus to consider
    
    def min_bonus_for_target(self, days: int, target_hires: int, 
                           adoption_prob: callable, eps: float = 0.01) -> Optional[int]:
        """
        Find minimum bonus amount to achieve hiring target.
        
        Uses binary search over bonus values to find the minimum bonus
        that achieves the target within the specified tolerance.
        
        Args:
            days: Number of days available for hiring
            target_hires: Target number of hires to achieve
            adoption_prob: Callable function that takes bonus amount and returns 
                          adoption probability (0.0 to 1.0). Must be monotonic.
            eps: Tolerance for probability adjustment (default 0.01)
            
        Returns:
            Optional[int]: Minimum bonus amount in $10 increments, or None if impossible
            
        Raises:
            ValueError: If adoption_prob is not callable or returns invalid probabilities
            TypeError: If adoption_prob function signature is incorrect
        """
        if days <= 0 or target_hires <= 0:
            return None
        
        if not callable(adoption_prob):
            raise ValueError("adoption_prob must be a callable function")
        
        if eps <= 0.0:
            raise ValueError("Tolerance eps must be positive")
        
        # Validate the adoption_prob function by testing it
        try:
            test_prob = adoption_prob(0)
            if not isinstance(test_prob, (int, float)) or not 0.0 <= test_prob <= 1.0:
                raise ValueError("adoption_prob function must return probability between 0.0 and 1.0")
        except Exception as e:
            if isinstance(e, ValueError):
                # Re-raise ValueError as-is
                raise
            else:
                # For other exceptions, raise TypeError
                raise TypeError(f"adoption_prob function must accept a bonus parameter: {e}")
        
        # Create simulator for this scenario
        simulator = NetworkSimulator()
        
        # Check if target is achievable with maximum bonus
        max_prob = adoption_prob(self.max_bonus)
        if not 0.0 <= max_prob <= 1.0:
            raise ValueError(f"adoption_prob({self.max_bonus}) returned invalid probability: {max_prob}")
        
        max_bonus_simulation = simulator.simulate_expected(max_prob, days)
        
        if not max_bonus_simulation or max_bonus_simulation[-1] < target_hires:
            return None  # Target impossible even with maximum bonus
        
        # Binary search for minimum bonus
        left, right = 0, self.max_bonus
        
        while left < right:
            mid = (left + right) // 2
            # Round to nearest $10 increment
            mid = (mid // 10) * 10
            
            # Calculate adjusted probability based on bonus using the callable
            adjusted_prob = adoption_prob(mid)
            if not 0.0 <= adjusted_prob <= 1.0:
                raise ValueError(f"adoption_prob({mid}) returned invalid probability: {adjusted_prob}")
            
            # Simulate with adjusted probability
            simulation_result = simulator.simulate_expected(adjusted_prob, days)
            
            if not simulation_result:
                left = mid + 10
                continue
            
            final_hires = simulation_result[-1]
            
            if final_hires >= target_hires:
                right = mid
            else:
                left = mid + 10
        
        # Verify the result
        if left <= self.max_bonus:
            final_prob = adoption_prob(left)
            if not 0.0 <= final_prob <= 1.0:
                raise ValueError(f"adoption_prob({left}) returned invalid probability: {final_prob}")
            
            final_simulation = simulator.simulate_expected(final_prob, days)
            if final_simulation and final_simulation[-1] >= target_hires:
                return left
        
        return None
    
    def analyze_bonus_effectiveness(self, days: int, target_hires: int, 
                                  adoption_prob: callable, eps: float = 0.01) -> dict:
        """
        Analyze the effectiveness of different bonus amounts.
        
        Args:
            days: Number of days available for hiring
            target_hires: Target number of hires to achieve
            adoption_prob: Callable function that takes bonus amount and returns 
                          adoption probability (0.0 to 1.0)
            eps: Maximum probability increase (for backward compatibility)
            
        Returns:
            dict: Analysis results including cost-benefit information
        """
        min_bonus = self.min_bonus_for_target(days, target_hires, adoption_prob, eps)
        
        if min_bonus is None:
            return {
                'achievable': False,
                'min_bonus': None,
                'total_cost': None,
                'cost_per_hire': None
            }
        
        # Calculate total cost and cost per hire
        total_cost = min_bonus * target_hires
        cost_per_hire = min_bonus
        
        return {
            'achievable': True,
            'min_bonus': min_bonus,
            'total_cost': total_cost,
            'cost_per_hire': cost_per_hire,
            'days_required': days,
            'target_hires': target_hires
        }
