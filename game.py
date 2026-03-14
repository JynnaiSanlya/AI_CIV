import sys
import time
from civilization import Civilization
from ai_controller import AIController

class CivilizationGame:
    """Main game class for AI civilization simulation."""
    
    def __init__(self, model_name1="qwen-flash", model_name2="qwen-plus"):
        """Initialize the game with two civilizations.
        
        Args:
            model_name1: Specific model name for civilization 1 (e.g., "qwen-flash")
            model_name2: Specific model name for civilization 2 (e.g., "qwen-plus")
        """
        # Create two civilizations
        self.civ1 = Civilization("Atlantis", "blue")
        self.civ2 = Civilization("Eldorado", "gold")
        
        # Create AI controllers using different Alibaba models
        self.ai1 = AIController(self.civ1.name, model_name=model_name1)
        self.ai2 = AIController(self.civ2.name, model_name=model_name2)
        
        # Game settings
        self.max_turns = 10
        self.current_turn = 0
        
        # Model information for display
        self.model_info = {
            "civ1": model_name1,
            "civ2": model_name2
        }
        
        # Diplomacy history
        self.diplomacy_history = []
        
        # Action history for each civilization
        self.action_history = {
            "civ1": [],
            "civ2": []
        }
        
    def print_game_state(self):
        """Print the current game state for both civilizations."""
        print(f"\n{'='*60}")
        print(f"Turn {self.current_turn}")
        print('='*60)
        print(self.civ1.get_state_description())
        print(self.civ2.get_state_description())
        print('='*60)
    
    def handle_civilization_turn(self, civ, opponent, ai):
        """Handle a single turn for a civilization.
        
        Args:
            civ: The civilization taking the turn
            opponent: The opposing civilization
            ai: The AI controller for the civilization
        """
        print(f"\n{civ.name}'s Turn ({ai.model_type} AI):")
        
        # Get AI decisions (now returns a list of actions)
        decisions = ai.get_decision(civ.to_dict(), opponent.to_dict(), self.current_turn)
        
        # Apply each action in sequence
        turn_actions = []
        for i, decision in enumerate(decisions):
            # Check if we have any action points left
            if civ.current_action_points <= 0:
                print(f"No more action points left for {civ.name}. Stopping actions.")
                break
                
            action_type, amount = decision
            
            # Apply action
            result = civ.apply_action(action_type, amount)
            print(f"Action {i+1}: {action_type} {amount}")
            print(f"Result: {result}")
            
            # Record history for each action
            action_record = {
                "turn": self.current_turn,
                "action": action_type,
                "amount": amount,
                "result": result,
                "state": civ.to_dict()
            }
            civ.history.append(action_record)
            turn_actions.append(action_record)
        
        # Record turn actions to game history
        civ_key = "civ1" if civ == self.civ1 else "civ2"
        self.action_history[civ_key].append({
            "turn": self.current_turn,
            "actions": turn_actions
        })
        
        # Update civilization state after all actions
        civ.update_turn()
    
    def check_game_end(self):
        """Check if the game has ended."""
        # Check if max turns reached
        if self.current_turn >= self.max_turns:
            return True, "Game reached maximum turns!"
        
        # Check if one civilization's loyalty has dropped to 0
        if self.civ1.loyalty <= 0:
            return True, f"{self.civ1.name} has collapsed due to low loyalty!"
        if self.civ2.loyalty <= 0:
            return True, f"{self.civ2.name} has collapsed due to low loyalty!"
        
        # Check if one civilization is far advanced
        if self.civ1.technology >= 100 and self.civ1.technology > self.civ2.technology * 2:
            return True, f"{self.civ1.name} has achieved technological dominance!"
        if self.civ2.technology >= 100 and self.civ2.technology > self.civ1.technology * 2:
            return True, f"{self.civ2.name} has achieved technological dominance!"
        
        # Check if population collapse
        if self.civ1.population <= 0:
            return True, f"{self.civ1.name} has collapsed!"
        if self.civ2.population <= 0:
            return True, f"{self.civ2.name} has collapsed!"
        
        return False, ""
    
    def handle_diplomacy(self):
        """Handle diplomacy actions (trade and war) at the beginning of each turn."""
        print(f"\n{'='*60}")
        print("DIPLOMACY PHASE")
        print('='*60)
        
        # Randomly decide if either civilization wants to propose trade or attack
        import random
        
        # 30% chance for trade proposal
        if random.random() < 0.3:
            # Decide which civilization proposes trade
            proposer, responder = random.choice([(self.civ1, self.civ2), (self.civ2, self.civ1)])
            
            # Generate trade proposal (simple AI logic)
            # Offer resources for technology, or population for resources
            if proposer.resources > responder.resources:
                # Proposer has more resources, offer resources for technology
                offer_resources = random.randint(10, 50)
                offer_population = 0
                offer_technology = 0
                request_resources = 0
                request_population = 0
                request_technology = random.randint(1, 3)
            else:
                # Proposer has less resources, offer technology for resources
                offer_resources = 0
                offer_population = 0
                offer_technology = random.randint(1, 2)
                request_resources = random.randint(20, 60)
                request_population = 0
                request_technology = 0
            
            print(f"\n{proposer.name} proposes trade to {responder.name}:")
            print(f"  Offers: {offer_resources} resources, {offer_population} population, {offer_technology} technology")
            print(f"  Requests: {request_resources} resources, {request_population} population, {request_technology} technology")
            
            # Check if trade is possible (both have enough to offer)
            if (proposer.resources >= offer_resources and
                proposer.population >= offer_population and
                proposer.technology >= offer_technology and
                responder.resources >= request_resources and
                responder.population >= request_population and
                responder.technology >= request_technology):
                
                # Ask responder to accept trade
                if responder.propose_trade(proposer, 
                                         request_resources, request_population, request_technology,
                                         offer_resources, offer_population, offer_technology):
                    # Execute the trade
                    result = proposer.execute_trade(responder, 
                                                 offer_resources, offer_population, offer_technology,
                                                 request_resources, request_population, request_technology)
                    print(f"  {responder.name} accepts! {result}")
                    
                    # Record trade in history
                    self.diplomacy_history.append({
                        "turn": self.current_turn,
                        "type": "trade",
                        "proposer": proposer.name,
                        "responder": responder.name,
                        "offer": {
                            "resources": offer_resources,
                            "population": offer_population,
                            "technology": offer_technology
                        },
                        "request": {
                            "resources": request_resources,
                            "population": request_population,
                            "technology": request_technology
                        },
                        "result": "accepted",
                        "details": result
                    })
                else:
                    print(f"  {responder.name} rejects the trade.")
                    
                    # Record rejected trade in history
                    self.diplomacy_history.append({
                        "turn": self.current_turn,
                        "type": "trade",
                        "proposer": proposer.name,
                        "responder": responder.name,
                        "offer": {
                            "resources": offer_resources,
                            "population": offer_population,
                            "technology": offer_technology
                        },
                        "request": {
                            "resources": request_resources,
                            "population": request_population,
                            "technology": request_technology
                        },
                        "result": "rejected"
                    })
            else:
                print(f"  Trade cannot be completed due to insufficient resources.")
        
        # 20% chance for attack
        if random.random() < 0.2:
            # Decide which civilization attacks
            attacker, defender = random.choice([(self.civ1, self.civ2), (self.civ2, self.civ1)])
            
            # Check warmonger limit: max 2 wars per era (except last era)
            if attacker.era != "Future" and attacker.wars_initiated >= 2:
                print(f"\n{attacker.name} cannot declare more wars this era! (Limit: 2 wars per era)")
                
                # Record failed war declaration
                self.diplomacy_history.append({
                    "turn": self.current_turn,
                    "type": "war_declaration",
                    "attacker": attacker.name,
                    "defender": defender.name,
                    "result": "failed",
                    "reason": "war limit reached"
                })
            else:
                print(f"\n{attacker.name} declares war on {defender.name}!")
                result, plunder_resources, plunder_population = attacker.attack(defender)
                
                print(f"  {result}")
                if plunder_resources > 0 or plunder_population > 0:
                    print(f"  {attacker.name} plundered {plunder_resources} resources and {plunder_population} population!")
                
                # Increment war count for attacker
                attacker.wars_initiated += 1
                
                # Record war in history
                self.diplomacy_history.append({
                    "turn": self.current_turn,
                    "type": "war",
                    "attacker": attacker.name,
                    "defender": defender.name,
                    "result": result,
                    "plunder": {
                        "resources": plunder_resources,
                        "population": plunder_population
                    }
                })
        
        print('='*60)
    
    def run(self):
        """Run the main game loop."""
        print("Starting AI Civilization Simulation!")
        print(f"Two civilizations will compete for {self.max_turns} turns.")
        print(f"{self.civ1.name} is controlled by aliyun AI (qwen-flash)")
        print(f"{self.civ2.name} is controlled by aliyun AI (qwen-plus)")
        print("\nPress Ctrl+C to exit at any time.")
        
        try:
            for self.current_turn in range(1, self.max_turns + 1):
                # Print current state
                self.print_game_state()
                
                # Check game end conditions
                game_ended, reason = self.check_game_end()
                if game_ended:
                    print(f"\nGame Over! {reason}")
                    break
                
                # Diplomacy phase (trade and war)
                self.handle_diplomacy()
                
                # Civilization 1's turn
                self.handle_civilization_turn(self.civ1, self.civ2, self.ai1)
                time.sleep(1)  # Pause for readability
                
                # Civilization 2's turn
                self.handle_civilization_turn(self.civ2, self.civ1, self.ai2)
                time.sleep(1)  # Pause for readability
                
                # Apply culture influence after both turns
                print("\nCULTURE INFLUENCE PHASE")
                print("="*60)
                
                # Both civilizations apply culture influence on each other
                influence_result1 = self.civ1.apply_culture_influence(self.civ2)
                if influence_result1:
                    print(f"{influence_result1}")
                
                influence_result2 = self.civ2.apply_culture_influence(self.civ1)
                if influence_result2:
                    print(f"{influence_result2}")
                
                print("="*60)
                
                # Save game state every 10 turns
                if self.current_turn % 10 == 0:
                    self.save_game()
                    
        except KeyboardInterrupt:
            print("\nGame interrupted by user.")
        finally:
            # Final state
            self.print_game_state()
            self.save_game()
            self.print_final_summary()
    
    def save_game(self):
        """Save the current game state to a file."""
        import json
        game_state = {
            "turn": self.current_turn,
            "civ1": self.civ1.to_dict(),
            "civ2": self.civ2.to_dict()
        }
        with open(f"game_state_turn_{self.current_turn}.json", "w") as f:
            json.dump(game_state, f, indent=2)
    
    def print_final_summary(self):
        """Print a final summary of the game with detailed scoring."""
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        
        # Calculate scores
        score1 = self.civ1.calculate_score()
        score2 = self.civ2.calculate_score()
        
        # Compare final states
        print(f"{self.civ1.name} vs {self.civ2.name}")
        print(f"Era: {self.civ1.era} vs {self.civ2.era}")
        print(f"Technology: {self.civ1.technology} vs {self.civ2.technology}")
        print(f"Population: {self.civ1.population} vs {self.civ2.population}")
        print(f"Military: {self.civ1.military} vs {self.civ2.military}")
        print(f"Resources: {self.civ1.resources} vs {self.civ2.resources}")
        
        print("\n" + "-"*60)
        print("DETAILED SCORING")
        print("-"*60)
        
        # Show scoring breakdown for each civilization
        for civ in [self.civ1, self.civ2]:
            print(f"\n{civ.name} Score Breakdown:")
            print(f"  Technology (40%): {civ.technology} × 4 = {civ.technology * 4} points")
            print(f"  Population (25%): {civ.population} × 0.25 = {round(civ.population * 0.25)} points")
            print(f"  Military (20%): {civ.military} × 2 = {civ.military * 2} points")
            print(f"  Resources (10%): {civ.resources} × 0.1 = {round(civ.resources * 0.1)} points")
            print(f"  Loyalty (5%): {civ.loyalty} × 0.5 = {round(civ.loyalty * 0.5)} points")
            
            # Calculate era bonus
            era_bonus = {
                "Primitive": 0,
                "Ancient": 50,
                "Medieval": 150,
                "Modern": 300,
                "Future": 500
            }[civ.era]
            print(f"  Era Bonus: {era_bonus} points")
            
            # Calculate milestone bonuses
            tech_milestone = 0
            if civ.technology >= 100:
                tech_milestone = 100
            elif civ.technology >= 50:
                tech_milestone = 50
            elif civ.technology >= 20:
                tech_milestone = 20
            
            pop_milestone = 0
            if civ.population >= 1000:
                pop_milestone = 100
            elif civ.population >= 500:
                pop_milestone = 50
            elif civ.population >= 200:
                pop_milestone = 20
            
            print(f"  Technology Milestone: {tech_milestone} points")
            print(f"  Population Milestone: {pop_milestone} points")
            print(f"  Total Score: {civ.calculate_score()} points")
        
        print("\n" + "-"*60)
        print("FINAL RESULT")
        print("-"*60)
        
        # Determine winner based on total score
        print(f"Final Scores:")
        print(f"  {self.civ1.name}: {score1} points")
        print(f"  {self.civ2.name}: {score2} points")
        
        if score1 > score2:
            winner = self.civ1.name
            margin = score1 - score2
        elif score2 > score1:
            winner = self.civ2.name
            margin = score2 - score1
        else:
            winner = "Tie"
            margin = 0
        
        print(f"\nWinner: {winner}")
        if margin > 0:
            print(f"Winning Margin: {margin} points")
        print("="*60)

if __name__ == "__main__":
    game = CivilizationGame()
    game.run()
