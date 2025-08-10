"""
Unit tests for ReferralNetwork class.

Tests all functionality including:
- Referral addition and validation
- Network reach calculations
- Influence metrics
- Constraint enforcement
- Edge cases and error handling
"""

import pytest
from source.referral_network import ReferralNetwork


class TestReferralNetwork:
    """Test suite for ReferralNetwork class."""
    
    def setup_method(self):
        """Set up a fresh network before each test."""
        self.network = ReferralNetwork()
    
    def test_initialization(self):
        """Test network initialization."""
        assert self.network.referrals == {}
        assert self.network.reverse_referrals == {}
        assert self.network.users == set()
    
    def test_add_valid_referral(self):
        """Test adding a valid referral."""
        result = self.network.add_referral("alice", "bob")
        assert result is True
        assert "alice" in self.network.users
        assert "bob" in self.network.users
        assert self.network.referrals["bob"] == "alice"
        assert "bob" in self.network.reverse_referrals["alice"]
    
    def test_add_multiple_referrals(self):
        """Test adding multiple referrals from same referrer."""
        self.network.add_referral("alice", "bob")
        self.network.add_referral("alice", "charlie")
        
        assert len(self.network.referrals) == 2
        assert len(self.network.reverse_referrals["alice"]) == 2
        assert "bob" in self.network.reverse_referrals["alice"]
        assert "charlie" in self.network.reverse_referrals["alice"]
    
    def test_self_referral_prevention(self):
        """Test that self-referrals are prevented."""
        with pytest.raises(ValueError, match="Self-referrals are not allowed"):
            self.network.add_referral("alice", "alice")
    
    def test_duplicate_referrer_prevention(self):
        """Test that candidates can only have one referrer."""
        self.network.add_referral("alice", "bob")
        
        with pytest.raises(ValueError, match="Candidate bob already has a referrer"):
            self.network.add_referral("charlie", "bob")
    
    def test_cycle_prevention_simple(self):
        """Test that simple cycles are prevented."""
        self.network.add_referral("alice", "bob")
        
        with pytest.raises(ValueError, match="Adding this referral would create a cycle"):
            self.network.add_referral("bob", "alice")
    
    def test_cycle_prevention_complex(self):
        """Test that complex cycles are prevented."""
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "charlie")
        self.network.add_referral("charlie", "david")
        
        with pytest.raises(ValueError, match="Adding this referral would create a cycle"):
            self.network.add_referral("david", "alice")
    
    def test_empty_input_validation(self):
        """Test validation of empty inputs."""
        with pytest.raises(ValueError, match="Referrer and candidate must be non-empty strings"):
            self.network.add_referral("", "bob")
        
        with pytest.raises(ValueError, match="Referrer and candidate must be non-empty strings"):
            self.network.add_referral("alice", "")
        
        with pytest.raises(ValueError, match="Referrer and candidate must be non-empty strings"):
            self.network.add_referral(None, "bob")
    
    def test_get_direct_referrals(self):
        """Test retrieving direct referrals."""
        self.network.add_referral("alice", "bob")
        self.network.add_referral("alice", "charlie")
        self.network.add_referral("bob", "david")
        
        alice_referrals = self.network.get_direct_referrals("alice")
        bob_referrals = self.network.get_direct_referrals("bob")
        charlie_referrals = self.network.get_direct_referrals("charlie")
        
        assert set(alice_referrals) == {"bob", "charlie"}
        assert set(bob_referrals) == {"david"}
        assert charlie_referrals == []
    
    def test_get_total_referral_count_simple(self):
        """Test total referral count for simple case."""
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "charlie")
        
        assert self.network.get_total_referral_count("alice") == 2
        assert self.network.get_total_referral_count("bob") == 1
        assert self.network.get_total_referral_count("charlie") == 0
    
    def test_get_total_referral_count_complex(self):
        """Test total referral count for complex network."""
        # Create a tree structure
        self.network.add_referral("root", "child1")
        self.network.add_referral("root", "child2")
        self.network.add_referral("child1", "grandchild1")
        self.network.add_referral("child1", "grandchild2")
        self.network.add_referral("child2", "grandchild3")
        
        assert self.network.get_total_referral_count("root") == 5
        assert self.network.get_total_referral_count("child1") == 2
        assert self.network.get_total_referral_count("child2") == 1
        assert self.network.get_total_referral_count("grandchild1") == 0
    
    def test_get_total_referral_count_nonexistent_user(self):
        """Test total referral count for non-existent user."""
        assert self.network.get_total_referral_count("nonexistent") == 0
    
    def test_get_top_referrers(self):
        """Test getting top referrers."""
        self.network.add_referral("alice", "bob")
        self.network.add_referral("alice", "charlie")
        self.network.add_referral("bob", "david")
        self.network.add_referral("eve", "frank")
        
        top_2 = self.network.get_top_referrers(2)
        top_5 = self.network.get_top_referrers(5)
        
        assert len(top_2) == 2
        assert top_2[0][0] == "alice"  # alice has total reach 3 (bob, charlie, david)
        assert top_2[0][1] == 3
        
        # Both bob and eve have total reach 1, so either could be second
        # We just need to verify that the second user has reach 1
        assert top_2[1][1] == 1
        assert top_2[1][0] in ["bob", "eve"]
        
        assert len(top_5) == 3  # Only 3 users made referrals
        # The third user should also have reach 1
        assert top_5[2][1] == 1
        assert top_5[2][0] in ["bob", "eve"]
    
    def test_get_top_referrers_empty_network(self):
        """Test getting top referrers from empty network."""
        assert self.network.get_top_referrers(5) == []
    
    def test_get_top_referrers_k_larger_than_referrers(self):
        """Test getting top referrers when k is larger than available referrers."""
        self.network.add_referral("alice", "bob")
        
        top_5 = self.network.get_top_referrers(5)
        assert len(top_5) == 1
        assert top_5[0][0] == "alice"
    
    def test_get_unique_reach_expansion(self):
        """Test unique reach expansion using greedy set cover algorithm."""
        # Create a network with overlapping coverage
        # alice -> bob -> david1, alice -> charlie -> david2
        # This creates overlap where both bob and charlie can reach different users
        # but alice can reach all of them
        self.network.add_referral("alice", "bob")
        self.network.add_referral("alice", "charlie")
        self.network.add_referral("bob", "david1")
        self.network.add_referral("charlie", "david2")
        
        reach_expansion = self.network.get_unique_reach_expansion()
        
        # Since alice can reach all users (bob, charlie, david1, david2),
        # the greedy algorithm will select only alice and stop
        # This is correct behavior for set cover - we don't need additional users
        assert len(reach_expansion) == 1
        assert reach_expansion[0][0] == "alice"
        assert reach_expansion[0][1] == 4  # bob, charlie, david1, david2
    
    def test_get_unique_reach_expansion_empty_network(self):
        """Test unique reach expansion for empty network."""
        assert self.network.get_unique_reach_expansion() == []
    
    def test_get_flow_centrality_simple(self):
        """Test flow centrality for simple network."""
        # Create a simple chain: alice -> bob -> charlie
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "charlie")
        
        centrality = self.network.get_flow_centrality()
        
        # Debug output
        print(f"DEBUG: centrality = {centrality}")
        print(f"DEBUG: alice -> bob distance = {self.network._compute_shortest_paths('alice')}")
        print(f"DEBUG: bob -> charlie distance = {self.network._compute_shortest_paths('bob')}")
        print(f"DEBUG: charlie -> bob distance = {self.network._compute_shortest_paths('charlie')}")
        
        # bob is on the shortest path between alice and charlie
        # dist(alice, bob) = 1, dist(bob, charlie) = 1, dist(alice, charlie) = 2
        # 1 + 1 = 2, so bob is on the shortest path
        assert len(centrality) == 3
        assert centrality[0][0] == "bob"  # bob has highest centrality
        assert centrality[0][1] == 1
        
        # Both alice and charlie have 0 centrality, so order can vary
        assert centrality[1][1] == 0  # second user has 0 centrality
        assert centrality[2][1] == 0  # third user has 0 centrality
        
        # Verify that alice and charlie are both in the result with 0 centrality
        user_names = [user for user, score in centrality]
        assert "alice" in user_names
        assert "charlie" in user_names
    
    def test_get_flow_centrality_insufficient_users(self):
        """Test flow centrality with insufficient users."""
        assert self.network.get_flow_centrality() == []
        
        self.network.add_referral("alice", "bob")
        assert self.network.get_flow_centrality() == []
    
    def test_get_flow_centrality_complex(self):
        """Test flow centrality for complex network with multiple shortest paths."""
        # Create a diamond structure: root -> left -> bottom1, root -> right -> bottom2
        # This creates multiple shortest paths from root to different bottom users
        self.network.add_referral("root", "left")
        self.network.add_referral("root", "right")
        self.network.add_referral("left", "bottom1")
        self.network.add_referral("right", "bottom2")
        
        centrality = self.network.get_flow_centrality()
        
        # left and right should have highest centrality as they are on shortest paths
        # from root to bottom1 and bottom2 respectively (distance 2)
        # root has 0 centrality as it's not between any other users
        # bottom1 and bottom2 have 0 centrality as they're not between any other users
        assert len(centrality) == 5
        
        # Find left and right centrality scores
        left_centrality = next(score for user, score in centrality if user == "left")
        right_centrality = next(score for user, score in centrality if user == "right")
        root_centrality = next(score for user, score in centrality if user == "root")
        bottom1_centrality = next(score for user, score in centrality if user == "bottom1")
        bottom2_centrality = next(score for user, score in centrality if user == "bottom2")
        
        # left and right should have the same centrality (they're symmetric)
        assert left_centrality == right_centrality
        assert left_centrality > 0  # They should be on shortest paths
        
        # root, bottom1, and bottom2 should have 0 centrality
        assert root_centrality == 0
        assert bottom1_centrality == 0
        assert bottom2_centrality == 0
    
    def test_get_network_stats(self):
        """Test network statistics."""
        self.network.add_referral("alice", "bob")
        self.network.add_referral("alice", "charlie")
        self.network.add_referral("bob", "david")
        
        stats = self.network.get_network_stats()
        
        assert stats["total_users"] == 4
        assert stats["total_referrals"] == 3
        assert stats["active_referrers"] == 2  # alice and bob
    
    def test_get_network_stats_empty(self):
        """Test network statistics for empty network."""
        stats = self.network.get_network_stats()
        
        assert stats["total_users"] == 0
        assert stats["total_referrals"] == 0
        assert stats["active_referrers"] == 0
    
    def test_complex_network_scenario(self):
        """Test a complex network scenario with multiple levels."""
        # Create a multi-level referral tree
        self.network.add_referral("ceo", "manager1")
        self.network.add_referral("ceo", "manager2")
        self.network.add_referral("manager1", "employee1")
        self.network.add_referral("manager1", "employee2")
        self.network.add_referral("manager2", "employee3")
        self.network.add_referral("employee1", "intern1")
        self.network.add_referral("employee2", "intern2")
        
        # Test reach calculations
        assert self.network.get_total_referral_count("ceo") == 7
        assert self.network.get_total_referral_count("manager1") == 4  # employee1, employee2, intern1, intern2
        assert self.network.get_total_referral_count("manager2") == 1  # employee3
        assert self.network.get_total_referral_count("employee1") == 1  # intern1
        
        # Test top referrers (sorted by total reach including indirect referrals)
        top_referrers = self.network.get_top_referrers(3)
        assert top_referrers[0][0] == "ceo"
        assert top_referrers[0][1] == 7
        assert top_referrers[1][0] == "manager1"
        assert top_referrers[1][1] == 4  # employee1, employee2, intern1, intern2
        
        # Test influence metrics
        reach_expansion = self.network.get_unique_reach_expansion()
        assert reach_expansion[0][0] == "ceo"
        assert reach_expansion[0][1] == 7
        
        # Test flow centrality
        centrality = self.network.get_flow_centrality()
        assert len(centrality) == 8  # All users have some centrality
    
    def test_constraint_enforcement_under_load(self):
        """Test constraint enforcement under high load."""
        # Try to create a large network while maintaining constraints
        for i in range(100):
            referrer = f"user_{i}"
            candidate = f"user_{i+1}"
            self.network.add_referral(referrer, candidate)
        
        # Verify no cycles exist
        stats = self.network.get_network_stats()
        assert stats["total_users"] == 101
        assert stats["total_referrals"] == 100
        
        # Verify the network is acyclic by checking reach
        assert self.network.get_total_referral_count("user_0") == 100
        assert self.network.get_total_referral_count("user_50") == 50
        assert self.network.get_total_referral_count("user_100") == 0

    def test_get_unique_reach_expansion_greedy_behavior(self):
        """Test unique reach expansion to demonstrate greedy set cover behavior."""
        # Create a network where multiple users are needed to cover all users
        # alice -> bob -> david1
        # charlie -> david2
        # eve -> frank
        # This creates a scenario where no single user can cover all others
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "david1")
        self.network.add_referral("charlie", "david2")
        self.network.add_referral("eve", "frank")
        
        reach_expansion = self.network.get_unique_reach_expansion()
        
        # The greedy algorithm should select users in order of their coverage
        # alice can reach 2 users (bob, david1)
        # charlie can reach 1 user (david2)
        # eve can reach 1 user (frank)
        # bob, david1, david2, frank have no reach
        assert len(reach_expansion) == 3  # alice, charlie, eve
        
        # alice should be first with coverage 2
        assert reach_expansion[0][0] == "alice"
        assert reach_expansion[0][1] == 2  # bob, david1
        
        # charlie and eve should be next, each with coverage 1
        remaining_users = [user for user, _ in reach_expansion[1:]]
        assert "charlie" in remaining_users
        assert "eve" in remaining_users
        
        # Verify their coverage
        charlie_coverage = next(coverage for user, coverage in reach_expansion if user == "charlie")
        eve_coverage = next(coverage for user, coverage in reach_expansion if user == "eve")
        assert charlie_coverage == 1  # david2
        assert eve_coverage == 1      # frank

    def test_get_unique_reach_expansion_no_user_reaches(self):
        """Test unique reach expansion when no users have reachable users."""
        # Create a network where users exist but have no referrals
        # This should result in no user_reaches being populated
        # We need to create users without any referrals
        self.network.users.add("isolated_user1")
        self.network.users.add("isolated_user2")
        
        reach_expansion = self.network.get_unique_reach_expansion()
        
        # Should return empty list when no users have reachable users
        assert reach_expansion == []

    def test_get_unique_reach_expansion_no_reachable_users(self):
        """Test unique reach expansion when no users have reachable users."""
        # Create a network where users exist but have no referrals
        # This should result in no user_reaches being populated
        # We need to create users without any referrals
        self.network.users.add("isolated_user1")
        self.network.users.add("isolated_user2")
        
        reach_expansion = self.network.get_unique_reach_expansion()
        
        # Should return empty list when no users have reachable users
        assert reach_expansion == []

    def test_get_unique_reach_expansion_break_conditions(self):
        """Test unique reach expansion break conditions in greedy algorithm."""
        # Create a network where the greedy algorithm will hit break conditions
        self.network.add_referral("alice", "bob")
        self.network.add_referral("charlie", "david")
        
        reach_expansion = self.network.get_unique_reach_expansion()
        
        # Should work normally - both users have coverage
        assert len(reach_expansion) == 2
        
        # The order can vary, so check both are present
        users = [user for user, _ in reach_expansion]
        assert "alice" in users
        assert "charlie" in users
        
        # Check coverage values
        alice_coverage = next(coverage for user, coverage in reach_expansion if user == "alice")
        charlie_coverage = next(coverage for user, coverage in reach_expansion if user == "charlie")
        assert alice_coverage == 1  # bob
        assert charlie_coverage == 1  # david



    def test_get_reachable_users_nonexistent_user(self):
        """Test _get_reachable_users with nonexistent user."""
        # Test the early return when user not in self.users
        reachable = self.network._get_reachable_users("nonexistent")
        assert reachable == set()

    def test_get_reachable_users_isolated_user(self):
        """Test _get_reachable_users with user who has no referrals."""
        self.network.add_referral("alice", "bob")
        
        # bob has no referrals, so should return empty set
        reachable = self.network._get_reachable_users("bob")
        assert reachable == set()

    def test_get_reachable_users_self_reference_removal(self):
        """Test _get_reachable_users removes self from reachable set."""
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "charlie")
        
        # alice should be able to reach bob and charlie, but not herself
        reachable = self.network._get_reachable_users("alice")
        assert "alice" not in reachable
        assert "bob" in reachable
        assert "charlie" in reachable

    def test_get_reachable_users_visited_continue(self):
        """Test _get_reachable_users when a user is already visited."""
        # Create a network: alice -> bob -> charlie
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "charlie")
        
        # Test the visited continue logic
        reachable = self.network._get_reachable_users("alice")
        # Should include bob and charlie but not alice herself
        assert "alice" not in reachable
        assert "bob" in reachable
        assert "charlie" in reachable



    def test_get_flow_centrality_break_condition(self):
        """Test flow centrality when no users are on shortest paths."""
        # Create a simple chain where no user is between others
        self.network.add_referral("alice", "bob")
        
        centrality = self.network.get_flow_centrality()
        # Should return empty list for < 3 users
        assert centrality == []

    def test_get_flow_centrality_no_paths(self):
        """Test flow centrality when there are no paths between users."""
        # Create isolated users
        self.network.add_referral("alice", "bob")
        self.network.add_referral("charlie", "david")
        
        centrality = self.network.get_flow_centrality()
        
        # Should have 4 users but no paths between different components
        assert len(centrality) == 4
        # All centrality scores should be 0
        for _, score in centrality:
            assert score == 0

    def test_get_flow_centrality_continue_conditions(self):
        """Test flow centrality continue conditions in nested loops."""
        # Create a network that will exercise the continue statements
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "charlie")
        
        centrality = self.network.get_flow_centrality()
        
        # Should work normally
        assert len(centrality) == 3
        # bob should have centrality > 0
        bob_centrality = next(score for user, score in centrality if user == "bob")
        assert bob_centrality > 0

    def test_compute_shortest_paths_isolated_user(self):
        """Test _compute_shortest_paths with user who has no referrals."""
        self.network.add_referral("alice", "bob")
        
        # bob has no referrals
        distances = self.network._compute_shortest_paths("bob")
        assert distances == {"bob": 0}

    def test_is_on_shortest_path_edge_cases(self):
        """Test _is_on_shortest_path with various edge cases."""
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "charlie")
        
        # Test with same start and end
        result = self.network._is_on_shortest_path("alice", "alice", "bob", {}, {})
        assert result == False
        
        # Test with target same as start
        result = self.network._is_on_shortest_path("alice", "charlie", "alice", {}, {})
        assert result == False
        
        # Test with target same as end
        result = self.network._is_on_shortest_path("alice", "charlie", "charlie", {}, {})
        assert result == False

    def test_is_on_shortest_path_no_path_conditions(self):
        """Test _is_on_shortest_path when no path exists."""
        self.network.add_referral("alice", "bob")
        
        # Test when end is not reachable from start
        distances_from_start = {"alice": 0, "bob": 1}
        distances_from_target = {"bob": 0, "charlie": 1}
        
        result = self.network._is_on_shortest_path("alice", "charlie", "bob", 
                                                 distances_from_start, distances_from_target)
        assert result == False
        
        # Test when target is not reachable from start
        distances_from_start = {"alice": 0, "bob": 1}
        distances_from_target = {"bob": 0, "charlie": 1}
        
        result = self.network._is_on_shortest_path("alice", "bob", "charlie", 
                                                 distances_from_start, distances_from_target)
        assert result == False
        
        # Test when end is not reachable from target
        distances_from_start = {"alice": 0, "bob": 1, "charlie": 2}
        distances_from_target = {"bob": 0}
        
        result = self.network._is_on_shortest_path("alice", "charlie", "bob", 
                                                 distances_from_start, distances_from_target)
        assert result == False

    def test_is_on_shortest_path_shortest_path_condition(self):
        """Test _is_on_shortest_path shortest path condition."""
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "charlie")
        
        # Test the actual shortest path condition
        distances_from_start = {"alice": 0, "bob": 1, "charlie": 2}
        distances_from_target = {"bob": 0, "charlie": 1}
        
        # bob should be on shortest path from alice to charlie
        # dist(alice, bob) = 1, dist(bob, charlie) = 1, dist(alice, charlie) = 2
        # 1 + 1 = 2, so condition should be true
        result = self.network._is_on_shortest_path("alice", "charlie", "bob", 
                                                 distances_from_start, distances_from_target)
        assert result == True
        
        # Test when condition is false
        # dist(alice, bob) = 1, dist(bob, charlie) = 2, dist(alice, charlie) = 2
        # 1 + 2 = 3 != 2, so condition should be false
        distances_from_target = {"bob": 0, "charlie": 2}
        result = self.network._is_on_shortest_path("alice", "charlie", "bob", 
                                                 distances_from_start, distances_from_target)
        assert result == False

    def test_would_create_cycle_visited_continue(self):
        """Test cycle detection when a candidate is already visited."""
        # Create a network: alice -> bob -> charlie
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "charlie")
        
        # Test the cycle detection logic by checking if it would create a cycle
        # This should hit the continue statement when next_candidate is visited
        would_create = self.network._would_create_cycle("charlie", "alice")
        assert would_create == True  # Should detect the cycle
        
        # Verify the network structure
        assert "alice" in self.network.users
        assert "bob" in self.network.users
        assert "charlie" in self.network.users

    def test_would_create_cycle_next_candidate_not_visited(self):
        """Test cycle detection when next_candidate is not visited."""
        # Create a network: alice -> bob -> charlie
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "charlie")
        
        # Add another user that bob refers to, but this one won't create a cycle
        self.network.add_referral("bob", "david")
        
        # Test the cycle detection logic
        # This should hit the if next_candidate not in visited: condition
        would_create = self.network._would_create_cycle("david", "alice")
        assert would_create == True  # Should detect the cycle through bob -> charlie -> alice
        
        # Verify the network structure
        assert "david" in self.network.users

    def test_get_total_referral_count_visited_continue(self):
        """Test get_total_referral_count when a user is already visited."""
        # Create a network: alice -> bob -> charlie
        self.network.add_referral("alice", "bob")
        self.network.add_referral("bob", "charlie")
        
        # Test the visited continue logic by counting from alice
        # The visited set should prevent counting the same user twice
        count = self.network.get_total_referral_count("alice")
        # Should count bob and charlie (2 users)
        assert count == 2


