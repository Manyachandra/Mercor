"""
Mercor Referral Network Implementation

This module implements the core referral network functionality including:
- Referral graph management with constraint enforcement
- Network reach calculations using BFS
- Influence metrics computation
- Top referrer rankings

Time Complexity Analysis:
- Adding referral: O(1) average case, O(n) worst case for cycle detection
- Computing reach: O(V + E) where V = vertices, E = edges
- Top k referrers: O(n log n) for sorting
- Influence metrics: O(V^2 * E) for all-pairs shortest paths
"""

from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
import heapq


class ReferralNetwork:
    """
    A directed acyclic graph representing referral relationships between users.
    
    Enforces constraints:
    - No self-referrals
    - Unique referrer per candidate
    - Graph remains acyclic
    """
    
    def __init__(self):
        """Initialize an empty referral network."""
        self.referrals: Dict[str, str] = {}  # candidate -> referrer
        self.reverse_referrals: Dict[str, Set[str]] = defaultdict(set)  # referrer -> candidates
        self.users: Set[str] = set()
    
    def add_referral(self, referrer: str, candidate: str) -> bool:
        """
        Add a referral relationship from referrer to candidate.
        
        Args:
            referrer: The user making the referral
            candidate: The user being referred
            
        Returns:
            bool: True if referral was added successfully, False otherwise
            
        Raises:
            ValueError: If constraints are violated
        """
        # Validate inputs
        if not referrer or not candidate:
            raise ValueError("Referrer and candidate must be non-empty strings")
        
        if referrer == candidate:
            raise ValueError("Self-referrals are not allowed")
        
        # Check if candidate already has a referrer
        if candidate in self.referrals:
            raise ValueError(f"Candidate {candidate} already has a referrer")
        
        # Check if adding this edge would create a cycle
        if self._would_create_cycle(referrer, candidate):
            raise ValueError("Adding this referral would create a cycle in the network")
        
        # Add the referral
        self.referrals[candidate] = referrer
        self.reverse_referrals[referrer].add(candidate)
        self.users.add(referrer)
        self.users.add(candidate)
        
        return True
    
    def _would_create_cycle(self, referrer: str, candidate: str) -> bool:
        """
        Check if adding an edge from referrer to candidate would create a cycle.
        
        Uses DFS to detect cycles in the potential graph.
        
        Args:
            referrer: The potential referrer
            candidate: The potential candidate
            
        Returns:
            bool: True if adding the edge would create a cycle
        """
        # If referrer is already reachable from candidate, adding the edge creates a cycle
        visited = set()
        stack = [candidate]
        
        while stack:
            current = stack.pop()
            if current == referrer:
                return True
            
            if current in visited:
                continue
                
            visited.add(current)
            
            # Add all candidates that current refers to the stack
            for next_candidate in self.reverse_referrals[current]:
                if next_candidate not in visited:
                    stack.append(next_candidate)
        
        return False
    
    def get_direct_referrals(self, user: str) -> List[str]:
        """
        Get all direct referrals made by a user.
        
        Args:
            user: The user whose direct referrals to retrieve
            
        Returns:
            List[str]: List of users directly referred by the given user
        """
        return list(self.reverse_referrals.get(user, set()))
    
    def get_total_referral_count(self, user: str) -> int:
        """
        Get total referral count (direct + indirect) for a user using BFS.
        
        Args:
            user: The user whose total referral count to compute
            
        Returns:
            int: Total number of users reachable from this user
        """
        if user not in self.users:
            return 0
        
        visited = set()
        queue = deque([user])
        count = 0
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
                
            visited.add(current)
            
            # Add all direct referrals to the queue
            for candidate in self.reverse_referrals[current]:
                if candidate not in visited:
                    queue.append(candidate)
                    count += 1
        
        return count
    
    def get_top_referrers(self, k: int) -> List[Tuple[str, int]]:
        """
        Get top k referrers by total referral count.
        
        Args:
            k: Number of top referrers to return
            
        Returns:
            List[Tuple[str, int]]: List of (user, total_referrals) tuples, sorted by count
        """
        referrer_counts = []
        
        for user in self.users:
            total_count = self.get_total_referral_count(user)
            if total_count > 0:  # Only include users who have made referrals
                referrer_counts.append((user, total_count))
        
        # Sort by count (descending) and return top k
        referrer_counts.sort(key=lambda x: x[1], reverse=True)
        return referrer_counts[:k]
    
    def get_unique_reach_expansion(self) -> List[Tuple[str, int]]:
        """
        Compute unique reach expansion using greedy set cover algorithm.
        
        This metric implements a greedy algorithm that repeatedly picks the user
        who can add the most new unique downstream users without overlap.
        Useful for targeted marketing campaigns and influencer selection.
        
        Algorithm: Greedy set cover approach
        1. Calculate reachable users for each user
        2. Iteratively select user with maximum new unique coverage
        3. Update remaining uncovered users after each selection
        4. Continue until all users are covered or no more coverage possible
        
        Returns:
            List[Tuple[str, int]]: List of (user, unique_reach) tuples, sorted by reach
        """
        if not self.users:
            return []
        
        # Calculate reachable users for each user
        user_reaches = {}
        for user in self.users:
            reachable = self._get_reachable_users(user)
            if reachable:
                user_reaches[user] = reachable
        
        if not user_reaches:
            return []
        
        # Greedy set cover algorithm
        selected_users = []
        remaining_uncovered = set()
        
        # Initialize with all users that can be reached by any referrer
        for reachable_set in user_reaches.values():
            remaining_uncovered.update(reachable_set)
        
        # Iteratively select users with maximum new coverage
        while remaining_uncovered and user_reaches:
            best_user = None
            best_new_coverage = 0
            
            # Find user with maximum new unique coverage
            for user, reachable in user_reaches.items():
                new_coverage = len(reachable.intersection(remaining_uncovered))
                if new_coverage > best_new_coverage:
                    best_new_coverage = new_coverage
                    best_user = user
            
            if best_user is None or best_new_coverage == 0:
                break
            
            # Select this user and update coverage
            selected_users.append((best_user, best_new_coverage))
            remaining_uncovered -= user_reaches[best_user]
            
            # Remove selected user from consideration
            del user_reaches[best_user]
        
        # Sort by coverage (descending)
        selected_users.sort(key=lambda x: x[1], reverse=True)
        return selected_users
    
    def _get_reachable_users(self, user: str) -> Set[str]:
        """
        Get set of all users reachable from a given user.
        
        Args:
            user: The user whose reachable users to compute
            
        Returns:
            Set[str]: Set of users reachable from this user
        """
        if user not in self.users:
            return set()
        
        reachable = set()
        queue = deque([user])
        
        while queue:
            current = queue.popleft()
            if current in reachable:
                continue
                
            reachable.add(current)
            
            # Add all direct referrals to the queue
            for candidate in self.reverse_referrals[current]:
                if candidate not in reachable:
                    queue.append(candidate)
        
        # Remove the user themselves from reachable set
        reachable.discard(user)
        return reachable
    
    def get_flow_centrality(self) -> List[Tuple[str, int]]:
        """
        Compute flow centrality for all users.
        
        Flow centrality measures how many shortest paths between other users
        pass through a given user, indicating their importance in the network.
        
        Algorithm: All-pairs shortest paths using BFS
        - For each pair of users (s, t), compute shortest path distance
        - A node v is on a shortest path from s to t if dist(s,v) + dist(v,t) == dist(s,t)
        - Count how many such shortest paths pass through each user
        
        Returns:
            List[Tuple[str, int]]: List of (user, centrality_score) tuples, sorted by score
        """
        if len(self.users) < 3:
            return []
        
        centrality_scores = {user: 0 for user in self.users}
        user_list = list(self.users)
        
        # Pre-compute all-pairs shortest paths for efficiency
        all_distances = {}
        for user in user_list:
            all_distances[user] = self._compute_shortest_paths(user)
        
        # Check all pairs of users (both directions)
        for i, user1 in enumerate(user_list):
            for j, user2 in enumerate(user_list):
                if i == j:  # Skip same user
                    continue
                
                # Check if there's a path from user1 to user2
                if user2 in all_distances[user1]:
                    shortest_distance = all_distances[user1][user2]
                    
                    # Check each user to see if they're on a shortest path
                    for user3 in self.users:
                        if user3 == user1 or user3 == user2:
                            continue
                        
                        # Check if user3 is on a shortest path from user1 to user2
                        if self._is_on_shortest_path(user1, user2, user3, 
                                                   all_distances[user1], all_distances[user3]):
                            centrality_scores[user3] += 1
        
        # Sort by centrality score (descending)
        sorted_users = sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_users
    
    def _compute_shortest_paths(self, start: str) -> Dict[str, int]:
        """
        Compute shortest path distances from start to all other users using BFS.
        
        Args:
            start: Starting user for shortest path computation
            
        Returns:
            Dict[str, int]: Dictionary mapping users to their shortest path distance from start
        """
        distances = {start: 0}
        queue = deque([start])
        
        while queue:
            current = queue.popleft()
            current_distance = distances[current]
            
            # Add all direct referrals to the queue
            for candidate in self.reverse_referrals[current]:
                if candidate not in distances:
                    distances[candidate] = current_distance + 1
                    queue.append(candidate)
        
        return distances
    
    def _is_on_shortest_path(self, start: str, end: str, target: str, 
                            distances_from_start: Dict[str, int], 
                            distances_from_target: Dict[str, int]) -> bool:
        """
        Check if target user is on a shortest path from start to end.
        
        A user v is on a shortest path from s to t if and only if:
        dist(s,v) + dist(v,t) == dist(s,t)
        
        Args:
            start: Starting user
            end: Ending user
            target: User to check if on shortest path
            distances_from_start: Shortest path distances from start
            distances_from_target: Shortest path distances from target
            
        Returns:
            bool: True if target is on a shortest path from start to end
        """
        if start == end or start == target or end == target:
            return False
        
        # Check if there's a path from start to end
        if end not in distances_from_start:
            return False
        
        # Check if target is reachable from start
        if target not in distances_from_start:
            return False
        
        # Check if end is reachable from target
        if end not in distances_from_target:
            return False
        
        # Check the shortest path condition: dist(s,v) + dist(v,t) == dist(s,t)
        dist_start_to_target = distances_from_start[target]
        dist_target_to_end = distances_from_target[end]
        dist_start_to_end = distances_from_start[end]
        
        return dist_start_to_target + dist_target_to_end == dist_start_to_end
    
    def get_network_stats(self) -> Dict[str, int]:
        """
        Get basic network statistics.
        
        Returns:
            Dict[str, int]: Dictionary with network statistics
        """
        total_users = len(self.users)
        total_referrals = len(self.referrals)
        active_referrers = len([u for u in self.users if self.get_total_referral_count(u) > 0])
        
        return {
            'total_users': total_users,
            'total_referrals': total_referrals,
            'active_referrers': active_referrers
        }
