"""
Civilization class representing a civilization's state and attributes
"""

class Civilization:
    def __init__(self, name, color):
        self.name = name
        self.color = color

        # Core attributes - adjusted for better balance
        self.resources = 300  # Increased starting resources
        self.population = 30  # Reduced starting population
        self.military = 5      # Reduced starting military
        self.technology = 1
        self.loyalty = 100  # New attribute: loyalty (0-100)
        self.culture = 0  # New attribute: culture (0+)
        self.action_points = 5  # Base action points per turn
        self.current_action_points = 5  # Current available action points

        # Development stage
        self.era = "Primitive"
        self.turn = 0
        
        # War tracking for warmonger limit
        self.wars_initiated = 0  # Number of wars initiated in current era
        self.previous_era = "Primitive"  # Track previous era to reset war count

        # Resource allocation settings (set by AI)
        self.resource_allocation = {
            "population": 0.7,  # 70% of available resources to population
            "military": 0.3     # 30% of available resources to military
        }

        # Action point costs for different actions
        self.action_costs = {
            "develop_technology": 2,  # Most expensive
            "build_military": 2,       # Expensive
            "grow_population": 1,      # Moderate
            "gather_resources": 1,     # Least expensive
            "develop_culture": 1       # Moderate
        }

        # History tracking
        self.history = []

    def update_turn(self, war_penalty=False):
        """Update civilization state for a new turn with resource consumption and loyalty.
        
        Args:
            war_penalty: Whether the civilization is under war penalty (halved growth)
        """
        self.turn += 1

        # Update era-based action points
        # Every two new eras adds 1 action point
        era_action_points = {
            "Primitive": 5,          # Base action points
            "Classical": 5,          # Same as primitive
            "Medieval": 6,           # +1 after 2 eras
            "Renaissance": 6,        # Same as medieval
            "Industrial": 7,         # +1 after 4 eras
            "Modern": 7,             # Same as industrial
            "Information": 8,        # +1 after 6 eras
            "Future": 8              # Same as information
        }
        self.action_points = era_action_points.get(self.era, 5)
        
        # Reset current action points at the start of each turn
        self.current_action_points = self.action_points

        # Get era bonuses
        era_bonuses = {
            "Primitive": 0.0,          # No bonus
            "Classical": 0.05,          # 5% bonus
            "Medieval": 0.15,           # 15% bonus
            "Renaissance": 0.25,        # 25% bonus
            "Industrial": 0.4,          # 40% bonus
            "Modern": 0.6,              # 60% bonus
            "Information": 0.8,         # 80% bonus
            "Future": 1.0               # 100% bonus
        }
        bonus = era_bonuses.get(self.era, 0.0)
        
        # Fertility rate decreases with higher era (ancient societies have more children)
        fertility_rates = {
            "Primitive": 0.07,          # 7% growth
            "Classical": 0.065,         # 6.5% growth
            "Medieval": 0.055,          # 5.5% growth
            "Renaissance": 0.05,        # 5% growth
            "Industrial": 0.03,         # 3% growth
            "Modern": 0.02,             # 2% growth
            "Information": 0.015,       # 1.5% growth
            "Future": 0.01              # 1% growth
        }
        fertility_rate = fertility_rates.get(self.era, 0.05)
        
        # Apply war penalty if applicable (halve growth)
        growth_multiplier = 0.5 if war_penalty else 1.0
        
        # Natural growth with era-based fertility rate
        population_growth = max(1, int(self.population * fertility_rate * growth_multiplier))
        self.population += population_growth
        
        # Resources grow faster with higher era bonus
        base_resource_growth = int(self.population * 0.3 * growth_multiplier)
        bonus_resource_growth = int(base_resource_growth * bonus)
        self.resources += max(5, base_resource_growth + bonus_resource_growth)
        
        # Culture grows naturally with population and era bonus
        base_culture_growth = int(self.population * 0.1 * growth_multiplier)
        bonus_culture_growth = int(base_culture_growth * bonus)
        self.culture += max(1, base_culture_growth + bonus_culture_growth)

        # Calculate resource consumption
        # Population consumes resources (1 resource per person)
        population_consumption = self.population
        # Military consumes more resources (3 resources per soldier)
        military_consumption = self.military * 3
        total_consumption = population_consumption + military_consumption
        
        # Apply resource consumption - ensure resources don't go negative
        if total_consumption > self.resources:
            # Can't afford full consumption, only consume what's available
            self.resources = 0
            
            # Calculate how many people can't be fed
            unfed_people = self.population
            # Some unfed people die (10-30% of population)
            starvation_deaths = max(1, unfed_people // 10)
            self.population = max(0, self.population - starvation_deaths)
            
            # Loyalty decreases with deficit (increased penalty)
            loyalty_loss = min(20, unfed_people // 25 + 2)  # Increased from min(10, unfed_people // 50 + 1)
            self.loyalty = max(0, self.loyalty - loyalty_loss)
        else:
            # Can afford full consumption
            self.resources -= total_consumption
            
            # Handle loyalty based on resource situation
            if self.resources > 100:
                # Resource surplus - loyalty increases slightly
                loyalty_gain = min(5, self.resources // 100)
                self.loyalty = min(100, self.loyalty + loyalty_gain)
            elif self.resources > 0:
                # Resources can meet needs but not surplus - small loyalty recovery
                loyalty_recovery = 1  # Small loyalty recovery
                self.loyalty = min(100, self.loyalty + loyalty_recovery)
            # If resources are 0, loyalty remains stable
        
        # Calculate era progression score based on technology and culture
        # Technology has higher weight (80%), culture has smaller weight (20%)
        era_score = self.technology * 0.8 + self.culture * 0.2
        
        # Update era based on combined technology and culture score
        # Increased thresholds to make each era longer
        if era_score >= 105:
            self.era = "Future"
        elif era_score >= 90:
            self.era = "Information"
        elif era_score >= 75:
            self.era = "Modern"
        elif era_score >= 60:
            self.era = "Industrial"
        elif era_score >= 45:
            self.era = "Renaissance"
        elif era_score >= 30:
            self.era = "Medieval"
        elif era_score >= 15:
            self.era = "Classical"
        else:
            self.era = "Primitive"
        
        # Reset war count if era has changed
        if self.era != self.previous_era:
            self.wars_initiated = 0
            self.previous_era = self.era

    def get_state_description(self):
        """Get a text description of current civilization state"""
        return f"""
Civilization: {self.name}
Era: {self.era}
Turn: {self.turn}
Resources: {self.resources}
Population: {self.population}
Military: {self.military}
Technology: {self.technology}
Loyalty: {self.loyalty}
Action Points: {self.current_action_points}/{self.action_points}
"""

    def apply_action(self, action_type, amount):
        """Apply an action decided by AI with era-based cost reductions and action point consumption."""
        # Check if we have enough action points for this action
        if action_type not in self.action_costs:
            return f"Action failed - unknown action type: {action_type}"
        
        action_cost = self.action_costs[action_type]
        if self.current_action_points < action_cost:
            return f"Action failed - insufficient action points (need {action_cost}, have {self.current_action_points})"
        
        # Get era cost reduction bonuses (higher era = lower cost)
        era_cost_bonuses = {
            "Primitive": 0.0,          # No cost reduction
            "Classical": 0.025,        # 2.5% cost reduction
            "Medieval": 0.05,          # 5% cost reduction
            "Renaissance": 0.1,        # 10% cost reduction
            "Industrial": 0.2,         # 20% cost reduction
            "Modern": 0.3,             # 30% cost reduction
            "Information": 0.4,        # 40% cost reduction
            "Future": 0.5              # 50% cost reduction
        }
        cost_reduction = era_cost_bonuses.get(self.era, 0.0)
        
        if action_type == "develop_technology":
            base_cost = amount * 20
            # Apply cost reduction based on era
            cost = int(base_cost * (1 - cost_reduction))
            if self.resources >= cost:
                # Consume action points
                self.current_action_points -= action_cost
                self.resources -= cost
                self.technology += amount
                return f"Developed technology +{amount} (cost: {cost}, AP: {action_cost})"

        elif action_type == "build_military":
            # Check if we have enough population to train military
            if self.population < amount:
                return f"Action failed - not enough population (need {amount}, have {self.population})"
                
            base_cost = amount * 15
            cost = int(base_cost * (1 - cost_reduction))
            if self.resources >= cost:
                # Consume action points
                self.current_action_points -= action_cost
                # Convert population to military
                self.population -= amount
                self.military += amount
                self.resources -= cost
                return f"Built military +{amount} (cost: {cost}, converted {amount} population, AP: {action_cost})"

        elif action_type == "grow_population":
            base_cost = amount * 10
            cost = int(base_cost * (1 - cost_reduction))
            if self.resources >= cost:
                # Consume action points
                self.current_action_points -= action_cost
                self.resources -= cost
                self.population += amount
                return f"Grew population +{amount} (cost: {cost}, AP: {action_cost})"

        elif action_type == "gather_resources":
            # Calculate dynamic upper limit based on population and technology
            # Formula: max(1, population // 10 + technology * 2)
            upper_limit = max(1, self.population // 10 + self.technology * 2)
            # Ensure amount doesn't exceed upper limit
            actual_amount = min(amount, upper_limit)
            
            base_gained = actual_amount * 10
            # Resource gathering is more efficient with higher era
            era_gain_bonus = {
                "Primitive": 0.0,
                "Classical": 0.05,
                "Medieval": 0.15,
                "Renaissance": 0.25,
                "Industrial": 0.4,
                "Modern": 0.6,
                "Information": 0.8,
                "Future": 1.0
            }
            gain_bonus = era_gain_bonus.get(self.era, 0.0)
            gained = int(base_gained * (1 + gain_bonus))
            # Consume action points
            self.current_action_points -= action_cost
            self.resources += gained
            
            if actual_amount < amount:
                return f"Gathered resources +{gained} (AP: {action_cost}, limited to {actual_amount} due to population/technology constraints)"
            else:
                return f"Gathered resources +{gained} (AP: {action_cost})"
        
        elif action_type == "develop_culture":
            base_cost = amount * 10
            cost = int(base_cost * (1 - cost_reduction))
            if self.resources >= cost:
                # Consume action points
                self.current_action_points -= action_cost
                self.resources -= cost
                self.culture += amount
                return f"Developed culture +{amount} (cost: {cost}, AP: {action_cost})"

        return "Action failed - insufficient resources"

    def to_dict(self):
        """Convert to dictionary for display"""
        return {
            "name": self.name,
            "era": self.era,
            "turn": self.turn,
            "resources": self.resources,
            "population": self.population,
            "military": self.military,
            "technology": self.technology,
            "culture": self.culture,
            "loyalty": self.loyalty,
            "action_points": self.action_points,
            "current_action_points": self.current_action_points,
            "color": self.color
        }
    
    def calculate_score(self):
        """Calculate civilization's final score based on various metrics."""
        # Base scores with weights
        score = 0
        
        # Technology is most important (40% weight)
        score += self.technology * 4
        
        # Population is second (25% weight)
        score += self.population * 0.25
        
        # Military (20% weight)
        score += self.military * 2
        
        # Culture (10% weight)
        score += self.culture * 0.2
        
        # Resources (10% weight)
        score += self.resources * 0.1
        
        # Loyalty (5% weight)
        score += self.loyalty * 0.5
        
        # Era bonus (additional points based on development stage)
        era_bonus = {
            "Primitive": 0,
            "Classical": 50,
            "Medieval": 150,
            "Renaissance": 250,
            "Industrial": 400,
            "Modern": 600,
            "Information": 800,
            "Future": 1000
        }
        score += era_bonus.get(self.era, 0)
        
        # Technology milestone bonus
        if self.technology >= 100:
            score += 100
        elif self.technology >= 50:
            score += 50
        elif self.technology >= 20:
            score += 20
        
        # Population milestone bonus
        if self.population >= 1000:
            score += 100
        elif self.population >= 500:
            score += 50
        elif self.population >= 200:
            score += 20
        
        return round(score)
    
    def propose_trade(self, opponent, offer_resources, offer_population, offer_technology, 
                     request_resources, request_population, request_technology):
        """Propose a trade to another civilization."""
        # Calculate total offer value
        offer_value = offer_resources + offer_population * 10 + offer_technology * 20
        # Calculate total request value
        request_value = request_resources + request_population * 10 + request_technology * 20
        
        # Simple AI decision: accept if request value is <= offer value * 1.2 (20% profit margin)
        return request_value <= offer_value * 1.2
    
    def execute_trade(self, opponent, offer_resources, offer_population, offer_technology, 
                     request_resources, request_population, request_technology):
        """Execute a trade agreement."""
        # Apply the trade, ensuring resources don't go negative
        # Proposer's side
        self.resources = max(0, self.resources - offer_resources + request_resources)
        self.population = max(0, self.population - offer_population + request_population)
        self.technology = max(0, self.technology - offer_technology + request_technology)
        
        # Responder's side
        opponent.resources = max(0, opponent.resources + offer_resources - request_resources)
        opponent.population = max(0, opponent.population + offer_population - request_population)
        opponent.technology = max(0, opponent.technology + offer_technology - request_technology)
        
        # Trade encouragement mechanism
        # Tech low side gets small tech boost based on tech difference
        tech_diff = abs(self.technology - opponent.technology)
        if tech_diff > 0:
            if self.technology < opponent.technology:
                # Proposer has lower tech
                tech_boost = min(1, tech_diff // 5)  # Small boost, max 1 per trade
                self.technology += tech_boost
                tech_boost_msg = f" {self.name} gained {tech_boost} technology (trade bonus)"
            else:
                # Opponent has lower tech
                tech_boost = min(1, tech_diff // 5)  # Small boost, max 1 per trade
                opponent.technology += tech_boost
                tech_boost_msg = f" {opponent.name} gained {tech_boost} technology (trade bonus)"
            
            # Tech high side gets small loyalty boost
            if self.technology > opponent.technology:
                # Proposer has higher tech
                loyalty_boost = 1  # Small loyalty boost
                self.loyalty = min(100, self.loyalty + loyalty_boost)
                loyalty_boost_msg = f" {self.name} gained {loyalty_boost} loyalty (trade bonus)"
            else:
                # Opponent has higher tech
                loyalty_boost = 1  # Small loyalty boost
                opponent.loyalty = min(100, opponent.loyalty + loyalty_boost)
                loyalty_boost_msg = f" {opponent.name} gained {loyalty_boost} loyalty (trade bonus)"
        else:
            tech_boost_msg = ""
            loyalty_boost_msg = ""
        
        return f"Traded {offer_resources} resources, {offer_population} population, {offer_technology} technology for {request_resources} resources, {request_population} population, {request_technology} technology{tech_boost_msg}{loyalty_boost_msg}"
    
    def calculate_military_strength(self):
        """Calculate military strength considering era and army size."""
        # Era multiplier
        era_multipliers = {
            "Primitive": 1,
            "Classical": 2,
            "Medieval": 3,
            "Renaissance": 4,
            "Industrial": 6,
            "Modern": 8,
            "Information": 12,
            "Future": 16
        }
        era_multiplier = era_multipliers.get(self.era, 1)
        
        # Total military strength
        return self.military * era_multiplier
    
    def apply_culture_influence(self, opponent):
        """Apply culture influence on another civilization."""
        # Calculate culture difference
        culture_diff = self.culture - opponent.culture
        
        if culture_diff > 0:
            # This civilization has higher culture
            # Calculate influence based on culture difference
            influence_strength = min(5, culture_diff // 100 + 1)  # Max 5 points of influence
            
            # Increase own loyalty
            self.loyalty = min(100, self.loyalty + influence_strength)
            
            # Decrease opponent loyalty
            opponent.loyalty = max(0, opponent.loyalty - influence_strength)
            
            # Absorb a small amount of population from opponent
            # Only absorb if opponent has at least 10 population
            if opponent.population >= 10:
                absorbed_population = min(1, influence_strength // 2)  # At most 2 population per turn
                opponent.population = max(0, opponent.population - absorbed_population)
                self.population += absorbed_population
                
                return f"""{self.name}'s culture influenced {opponent.name}:
  - {self.name} loyalty +{influence_strength}
  - {opponent.name} loyalty -{influence_strength}
  - Absorbed {absorbed_population} population from {opponent.name}"""
        
        return ""
    
    def attack(self, opponent):
        """Attack another civilization and calculate battle results."""
        # Calculate military strength for both sides
        attacker_strength = self.calculate_military_strength()
        defender_strength = opponent.calculate_military_strength()
        
        # Calculate damage
        attacker_damage = max(1, int(defender_strength * 0.3))
        defender_damage = max(1, int(attacker_strength * 0.25))
        
        # Apply damage
        self.military = max(0, self.military - defender_damage)
        opponent.military = max(0, opponent.military - attacker_damage)
        
        # Determine winner
        if self.military > opponent.military:
            winner = self
            loser = opponent
            result = f"{self.name} defeated {opponent.name} in battle!"
        elif opponent.military > self.military:
            winner = opponent
            loser = self
            result = f"{opponent.name} defeated {self.name} in battle!"
        else:
            result = "The battle was a draw!"
            return result, 0, 0
        
        # Calculate plunder (capped at 40% of loser's resources and population, increased from 20%)
        max_plunder_resources = int(loser.resources * 0.4)
        max_plunder_population = int(loser.population * 0.4)
        
        # Plunder based on remaining military strength (increased factor for better gains)
        plunder_factor = winner.military / (winner.military + 5)  # Normalized factor, increased from (winner.military + 10)
        plunder_resources = max(0, int(max_plunder_resources * plunder_factor))
        plunder_population = max(0, int(max_plunder_population * plunder_factor))
        
        # Apply plunder, ensuring loser's resources and population don't go negative
        actual_plunder_resources = min(plunder_resources, loser.resources)
        actual_plunder_population = min(plunder_population, loser.population)
        
        winner.resources += actual_plunder_resources
        winner.population += actual_plunder_population
        loser.resources -= actual_plunder_resources
        loser.population -= actual_plunder_population
        
        # Update plunder values for return message
        plunder_resources = actual_plunder_resources
        plunder_population = actual_plunder_population
        
        # Update loyalty due to war
        if winner == self:
            # Attacker won
            self.loyalty = max(0, self.loyalty + 5)  # Attacking and winning increases loyalty
            opponent.loyalty = max(0, opponent.loyalty - 5)  # Losing decreases loyalty (reduced from -10)
        elif winner == opponent:
            # Attacker lost
            self.loyalty = max(0, self.loyalty - 10)  # Attacking and losing decreases loyalty
            opponent.loyalty = min(100, opponent.loyalty + 5)  # Defending and winning increases loyalty
        else:
            # Draw - both lose some loyalty
            self.loyalty = max(0, self.loyalty - 5)
            opponent.loyalty = max(0, opponent.loyalty - 5)
        
        # Plunder culture if there's a winner
        if winner and loser:
            # Calculate culture plunder (capped at 20% of loser's culture)
            max_plunder_culture = int(loser.culture * 0.2)
            plunder_culture = int(max_plunder_culture * plunder_factor)
            actual_plunder_culture = min(plunder_culture, loser.culture)
            
            winner.culture += actual_plunder_culture
            loser.culture -= actual_plunder_culture
            
            # Add culture plunder to return message
            result += f" {winner.name} plundered {actual_plunder_culture} culture!"
        
        return result, plunder_resources, plunder_population
