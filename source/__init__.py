"""
Mercor Referral Network Package

This package contains the core implementation of the Mercor Referral Network challenge:
- ReferralNetwork: Core referral graph management
- NetworkSimulator: Network growth simulation
- ReferralBonusOptimizer: Bonus optimization algorithms
"""

from .referral_network import ReferralNetwork
from .simulation import NetworkSimulator, ReferralBonusOptimizer

__version__ = "1.0.0"
__author__ = "Mercor Challenge Implementation"
__all__ = ["ReferralNetwork", "NetworkSimulator", "ReferralBonusOptimizer"]
