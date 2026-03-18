import sys
import time
import json
import os
from civilization import Civilization
from ai_controller import AIController
from era_event import EraEvent

class CivilizationGame:
    """Main game class for AI civilization simulation."""
    
    def __init__(self, civ_configs=None):
        """Initialize the game with multiple civilizations.
        
        Args:
            civ_configs: List of civilization configurations, each containing:
                - name: Civilization name
                - color: Civilization color
                - model_name: AI model name
                - model_type: AI model API type
        """
        # Default civilization configurations if none provided
        if civ_configs is None:
            civ_configs = [
                {"name": "Atlantis", "color": "blue", "model_name": "qwen-flash", "model_type": "aliyun"},
                {"name": "Eldorado", "color": "gold", "model_name": "qwen-plus", "model_type": "aliyun"}
            ]
        
        # Limit to a reasonable number of civilizations (max 8)
        civ_configs = civ_configs[:8]
        
        # Game settings
        self.max_turns = 50  # Increased from 10 to 50 for longer games
        self.current_turn = 0
        
        # Initialize civilization and AI controller dictionaries
        self.civilizations = {}
        self.ai_controllers = {}
        self.model_info = {}
        
        # Create civilizations and AI controllers
        for i, config in enumerate(civ_configs, 1):
            civ_id = f"civ{i}"
            self.civilizations[civ_id] = Civilization(config["name"], config["color"])
            self.ai_controllers[civ_id] = AIController(
                self.civilizations[civ_id].name, 
                model_name=config["model_name"], 
                model_type=config["model_type"]
            )
            self.model_info[civ_id] = f"{config['model_type']}:{config['model_name']}"
        
        # Diplomacy history
        self.diplomacy_history = []
        
        # Action history for each civilization
        self.action_history = {civ_id: [] for civ_id in self.civilizations}
        
        # Load era events from configuration file
        self.era_events = self._load_era_events()
        
        # Track which events have been triggered for each civilization and era
        self.triggered_events = {civ_id: set() for civ_id in self.civilizations}
        
        # War penalties tracking
        self.war_penalties = {civ_id: False for civ_id in self.civilizations}
        
        # Era events history for display
        self.era_events_history = []
        
        # Load internal events
        self.internal_events = self._load_internal_events()
        
        # Track internal events cooldowns for each civilization
        self.internal_events_cooldowns = {civ_id: {} for civ_id in self.civilizations}
        
        # Track active continuous effects for each civilization
        self.active_effects = {civ_id: [] for civ_id in self.civilizations}
        
        # Internal events history for display
        self.internal_events_history = []
    
    def _load_era_events(self):
        """Load era events from JSON configuration file.
        
        Returns:
            dict: Dictionary mapping era names to EraEvent objects
        """
        config_path = os.path.join(os.path.dirname(__file__), 'era_events.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                era_events_data = config.get('era_events', {})
                
                # Convert dictionaries to EraEvent objects
                era_events = {}
                for era_name, event_data in era_events_data.items():
                    try:
                        era_events[era_name] = era_events_data[era_name]
                    except (ValueError, KeyError) as e:
                        print(f"Warning: Invalid event data for era '{era_name}': {e}")
                        continue
                
                return era_events
                
        except FileNotFoundError:
            print(f"Warning: Era events configuration file not found at {config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse era events configuration: {e}")
            return {}
        except Exception as e:
            print(f"Unexpected error loading era events: {e}")
            return {}
    
    def _load_internal_events(self):
        """Load internal events from JSON configuration file.
        
        Returns:
            dict: Dictionary mapping event IDs to event data
        """
        config_path = os.path.join(os.path.dirname(__file__), 'internal_events.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('internal_events', {})
                
        except FileNotFoundError:
            print(f"Warning: Internal events configuration file not found at {config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse internal events configuration: {e}")
            return {}
        except Exception as e:
            print(f"Unexpected error loading internal events: {e}")
            return {}
    
    def handle_internal_events(self):
        """Handle internal events for all civilizations."""
        for civ_key, civ in self.civilizations.items():
            self._check_and_trigger_internal_event(civ, civ_key)
        
    def _check_and_trigger_internal_event(self, civ, civ_key):
        """Check if an internal event should be triggered for a civilization.
        
        Args:
            civ: The civilization object
            civ_key: The key for the civilization ("civ1" or "civ2")
        """
        import random
        
        # Check each internal event
        for event_id, event_data in self.internal_events.items():
            # Check cooldown
            if event_id in self.internal_events_cooldowns[civ_key]:
                if self.internal_events_cooldowns[civ_key][event_id] > 0:
                    # Decrease cooldown
                    self.internal_events_cooldowns[civ_key][event_id] -= 1
                    continue
                else:
                    # Cooldown expired, remove it
                    del self.internal_events_cooldowns[civ_key][event_id]
            
            # Check if event should trigger
            if random.random() < event_data.get("trigger_probability", 0):
                # Trigger the event
                self._handle_internal_event(civ, civ_key, event_id, event_data)
                # Set cooldown
                self.internal_events_cooldowns[civ_key][event_id] = event_data.get("cooldown_turns", 10)
                break
    
    def _handle_internal_event(self, civ, civ_key, event_id, event_data):
        """Handle a specific internal event for a civilization.
        
        Args:
            civ: The civilization object
            civ_key: The key for the civilization ("civ1" or "civ2")
            event_id: The ID of the event being handled
            event_data: The event data dictionary
        """
        print(f"\nINTERNAL EVENT for {civ.name}: {event_data['name']}")
        print(f"Description: {event_data['description']}")
        print("Options:")
        
        # Display options
        options = event_data.get("options", {})
        option_list = list(options.keys())
        for i, (option_key, option_data) in enumerate(options.items(), 1):
            print(f"{i}. {option_data['name']}: {option_data['description']}")
        
        # Get AI decision
        ai = self.ai_controllers[civ_key]
        decision = ai.get_internal_event_decision(civ.to_dict(), event_data)
        
        # Process the decision
        if decision in options:
            option_data = options[decision]
            print(f"{civ.name} chooses: {option_data['name']}")
            
            # Check if option has cost
            cost = option_data.get("cost", {})
            can_afford = True
            for resource, amount in cost.items():
                if getattr(civ, resource, 0) < amount:
                    can_afford = False
                    break
            
            if can_afford:
                # Apply cost
                for resource, amount in cost.items():
                    setattr(civ, resource, getattr(civ, resource) - amount)
                    print(f"  Cost: {resource} - {amount}")
                
                # Apply effects
                self._apply_internal_event_effects(civ, civ_key, option_data['effects'])
            else:
                print(f"  {civ.name} cannot afford this option. Choosing default option.")
                # Choose the first option as default
                default_option = option_list[0]
                self._apply_internal_event_effects(civ, civ_key, options[default_option]['effects'])
        else:
            print(f"  Invalid decision. Choosing default option.")
            # Choose the first option as default
            default_option = option_list[0]
            self._apply_internal_event_effects(civ, civ_key, options[default_option]['effects'])
        
        # Get decision details
        if decision in options:
            decision_data = options[decision]
        else:
            default_option = option_list[0]
            decision_data = options[default_option]
            decision = default_option
        
        # Extract effects for display
        effects_list = []
        effects = decision_data['effects']
        if effects['type'] == 'immediate':
            for resource, amount in effects.items():
                if resource != 'type':
                    effects_list.append({
                        'type': 'immediate',
                        'resource': resource,
                        'change': amount,
                        'duration': 0
                    })
        elif effects['type'] == 'continuous' or effects['type'] == 'mixed':
            duration = effects.get('duration', 0)
            for key, value in effects.items():
                if key not in ['type', 'duration', 'immediate', 'continuous']:
                    if isinstance(value, (int, float)):
                        # For simple boost/penalty effects
                        effects_list.append({
                            'type': effects['type'],
                            'resource': key,
                            'change': value,
                            'duration': duration
                        })
                    elif isinstance(value, bool):
                        # For boolean effects
                        effects_list.append({
                            'type': effects['type'],
                            'resource': key,
                            'change': value,
                            'duration': duration
                        })
            
            # Handle mixed effects
            if effects['type'] == 'mixed':
                for resource, amount in effects.get('immediate', {}).items():
                    effects_list.append({
                        'type': 'immediate',
                        'resource': resource,
                        'change': amount,
                        'duration': 0
                    })
        
        # Record the event
        self.internal_events_history.append({
            "turn": self.current_turn,
            "civ": civ_key,
            "civ_name": civ.name,
            "event_name": event_data["name"],
            "event_description": event_data["description"],
            "decision": decision,
            "decision_name": decision_data["name"],
            "decision_description": decision_data["description"],
            "effects": effects_list,
            "result": "completed"
        })
    
    def _apply_internal_event_effects(self, civ, civ_key, effects):
        """Apply the effects of an internal event option.
        
        Args:
            civ: The civilization object
            civ_key: The key for the civilization ("civ1" or "civ2")
            effects: The effects dictionary from the event option
        """
        effect_type = effects.get("type", "immediate")
        
        if effect_type == "immediate":
            # Apply immediate effects
            for resource, amount in effects.items():
                if resource != "type":
                    current_value = getattr(civ, resource, 0)
                    setattr(civ, resource, max(0, current_value + amount))
                    print(f"  Effect: {resource} + {amount}")
        
        elif effect_type == "continuous":
            # Add continuous effect
            duration = effects.get("duration", 5)
            self.active_effects[civ_key].append({
                "effect": effects,
                "remaining_turns": duration
            })
            print(f"  Effect: {effects.get('description', 'Continuous effect')} for {duration} turns")
        
        elif effect_type == "mixed":
            # Apply immediate effects
            immediate_effects = effects.get("immediate", {})
            for resource, amount in immediate_effects.items():
                current_value = getattr(civ, resource, 0)
                setattr(civ, resource, max(0, current_value + amount))
                print(f"  Immediate Effect: {resource} + {amount}")
            
            # Add continuous effect
            continuous_effects = effects.get("continuous", {})
            if continuous_effects:
                duration = continuous_effects.get("duration", 5)
                self.active_effects[civ_key].append({
                    "effect": continuous_effects,
                    "remaining_turns": duration
                })
                print(f"  Continuous Effect: {continuous_effects.get('description', 'Continuous effect')} for {duration} turns")
    
    def apply_active_effects(self, civ, civ_key):
        """Apply active continuous effects to a civilization.
        
        Args:
            civ: The civilization object
            civ_key: The key for the civilization ("civ1" or "civ2")
        """
        # Process active effects
        effects_to_remove = []
        for i, effect_entry in enumerate(self.active_effects[civ_key]):
            effect = effect_entry["effect"]
            remaining_turns = effect_entry["remaining_turns"]
            
            # Apply the effect for this turn
            if "culture_growth_boost" in effect:
                # This will be handled in the civilization's update_turn method
                pass
            elif "culture_growth_penalty" in effect:
                # This will be handled in the civilization's update_turn method
                pass
            elif "population_growth_boost" in effect:
                # This will be handled in the civilization's update_turn method
                pass
            elif "resource_growth_boost" in effect:
                # This will be handled in the civilization's update_turn method
                pass
            elif "resource_growth_penalty" in effect:
                # This will be handled in the civilization's update_turn method
                pass
            elif "loyalty_gain" in effect:
                civ.loyalty = min(100, civ.loyalty + effect["loyalty_gain"])
                print(f"  Active Effect: {civ.name} loyalty +{effect['loyalty_gain']}")
            elif "loyalty_risk" in effect:
                import random
                if random.random() < effect["loyalty_risk"]:
                    civ.loyalty = max(0, civ.loyalty + effect["loyalty_risk_amount"])
                    print(f"  Active Effect: {civ.name} loyalty {effect['loyalty_risk_amount']}")
            
            # Decrease remaining turns
            remaining_turns -= 1
            effect_entry["remaining_turns"] = remaining_turns
            
            # Mark effect for removal if duration expired
            if remaining_turns <= 0:
                effects_to_remove.append(i)
        
        # Remove expired effects (in reverse order to avoid index issues)
        for i in reversed(effects_to_remove):
            removed_effect = self.active_effects[civ_key].pop(i)
            print(f"  Effect expired: {removed_effect['effect'].get('description', 'Continuous effect')}")
        
    def print_game_state(self):
        """Print the current game state for all civilizations."""
        print(f"\n{'='*60}")
        print(f"Turn {self.current_turn}")
        print('='*60)
        for civ in self.civilizations.values():
            print(civ.get_state_description())
        print('='*60)
    
    def handle_civilization_turn(self, civ, civ_key, ai):
        """Handle a single turn for a civilization.
        
        Args:
            civ: The civilization taking the turn
            civ_key: The key for the civilization
            ai: The AI controller for the civilization
        """
        print(f"\n{civ.name}'s Turn ({ai.model_type} AI):")
        
        # Get AI decisions with information about all other civilizations
        other_civs = [c for cid, c in self.civilizations.items() if cid != civ_key]
        
        if other_civs:
            # Get all other civilizations' data
            all_opponents_data = [oc.to_dict() for oc in other_civs]
            # Use the first opponent as primary, but pass all to the AI
            primary_opponent = other_civs[0].to_dict()
            decisions = ai.get_decision(civ.to_dict(), primary_opponent, self.current_turn, all_opponents_data)
        else:
            # If only one civilization, use itself as opponent
            decisions = ai.get_decision(civ.to_dict(), civ.to_dict(), self.current_turn, [])
        
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
        self.action_history[civ_key].append({
            "turn": self.current_turn,
            "actions": turn_actions
        })
        
        # Check if civilization is under war penalty
        war_penalty = self.war_penalties[civ_key]
        
        # Update civilization state after all actions
        civ.update_turn(war_penalty)
        
        # Reset war penalty for next turn
        if war_penalty:
            self.war_penalties[civ_key] = False
    
    def check_game_end(self):
        """Check if the game has ended."""
        # Check if max turns reached
        if self.current_turn >= self.max_turns:
            return True, "Game reached maximum turns!"
        
        # Collect all civilization data for checks
        civs = list(self.civilizations.values())
        
        # Check if any civilization's loyalty has dropped to 0
        for civ in civs:
            if civ.loyalty <= 0:
                return True, f"{civ.name} has collapsed due to low loyalty!"
        
        # Check if population collapse for any civilization
        for civ in civs:
            if civ.population <= 0:
                return True, f"{civ.name} has collapsed!"
        
        # Check if one civilization is far advanced compared to all others
        for i, civ in enumerate(civs):
            if civ.technology >= 100:
                # Check if this civilization is more than twice as advanced as all others
                all_others = [c for j, c in enumerate(civs) if i != j]
                if all(civ.technology > other.technology * 2 for other in all_others):
                    return True, f"{civ.name} has achieved technological dominance!"
        
        return False, ""
    
    def handle_diplomacy(self):
        """Handle diplomacy actions (trade and war) at the beginning of each turn."""
        print(f"\n{'='*60}")
        print("DIPLOMACY PHASE")
        print('='*60)
        
        # Get diplomacy decisions for all civilization pairs
        diplomacy_decisions = {}
        civ_ids = list(self.civilizations.keys())
        
        # For each civilization pair, get diplomacy decisions
        for i, civ_id in enumerate(civ_ids):
            for j, other_civ_id in enumerate(civ_ids):
                if i != j:  # Only for different civilizations
                    # Create a unique key for each pair (civ1_civ2 format)
                    pair_key = f"{civ_id}_{other_civ_id}"
                    civ = self.civilizations[civ_id]
                    other_civ = self.civilizations[other_civ_id]
                    diplomacy_decisions[pair_key] = self.ai_controllers[civ_id].get_diplomacy_decision(
                        civ.to_dict(),
                        other_civ.to_dict(),
                        self.current_turn,
                        civ.wars_initiated
                    )
        
        # Handle trade proposals for all civilization pairs
        for i, proposer_id in enumerate(civ_ids):
            for j, responder_id in enumerate(civ_ids):
                if i == j:  # Skip trading with oneself
                    continue
                
                proposer = self.civilizations[proposer_id]
                responder = self.civilizations[responder_id]
                pair_key = f"{proposer_id}_{responder_id}"
                
                # Check if proposer wants to trade with this specific responder
                if pair_key in diplomacy_decisions and diplomacy_decisions[pair_key]["trade"]:
                    decision = diplomacy_decisions[pair_key]
                    offer = decision["trade_offer"]
                    request = decision["trade_request"]
                    
                    # Extract trade details
                    offer_resources = offer["resources"]
                    offer_population = offer["population"]
                    offer_technology = offer["technology"]
                    request_resources = request["resources"]
                    request_population = request["population"]
                    request_technology = request["technology"]
                    
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
        
        # Handle war declarations for all civilization pairs
        for i, attacker_id in enumerate(civ_ids):
            for j, defender_id in enumerate(civ_ids):
                if i == j:  # Skip attacking oneself
                    continue
                
                attacker = self.civilizations[attacker_id]
                defender = self.civilizations[defender_id]
                pair_key = f"{attacker_id}_{defender_id}"
                
                # Check if attacker wants to declare war on this specific defender
                if pair_key in diplomacy_decisions and diplomacy_decisions[pair_key]["war"]:
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
                        
                        # Apply war penalty: next turn's growth will be halved for the attacker
                        self.war_penalties[attacker_id] = True
        
        print('='*60)
    
    def handle_era_event(self, civ, ai, civ_key):
        """Handle era events for a civilization.
        
        Args:
            civ: The civilization to handle the event for
            ai: The AI controller for the civilization
            civ_key: The key for the civilization in the triggered_events dictionary
        """
        # Check if event has already been triggered for this era
        event_key = f"{civ_key}_{civ.era}"
        if event_key in self.triggered_events[civ_key]:
            return
        
        # Check if era has an event defined
        if civ.era not in self.era_events:
            return
        
        event = self.era_events[civ.era]
        
        # Roll for event occurrence
        import random
        if random.random() > event['probability']:
            return
        
        print(f"\nERA EVENT for {civ.name} ({civ.era}): {event['name']}")
        print(f"Description: {event['description']}")
        print(f"Cost: {event['cost']}")
        print(f"Reward: {event['reward']}")
        print(f"Penalty if declined: {event['penalty']}")
        
        # Check if civilization can afford the event
        can_afford = True
        for resource, amount in event['cost'].items():
            if getattr(civ, resource, 0) < amount:
                can_afford = False
                break
        
        event_result = ""
        if not can_afford:
            event_result = "cannot_afford"
            print(f"{civ.name} cannot afford the event. Applying penalty.")
            # Apply penalty
            for resource, amount in event['penalty'].items():
                setattr(civ, resource, max(0, getattr(civ, resource, 0) + amount))
        else:
            # Get AI decision
            # For simplicity, we'll assume AI always accepts if it can afford
            # In a more advanced implementation, we'd ask the AI for a decision
            event_result = "accepted"
            print(f"{civ.name} accepts the event. Applying cost and reward.")
            
            # Apply cost
            for resource, amount in event['cost'].items():
                setattr(civ, resource, getattr(civ, resource, 0) - amount)
            
            # Apply reward
            for resource, amount in event['reward'].items():
                setattr(civ, resource, getattr(civ, resource, 0) + amount)
        
        # Mark event as triggered
        self.triggered_events[civ_key].add(event_key)
        
        # Record the event to history for display in web UI
        self.era_events_history.append({
            "turn": self.current_turn,
            "civ": civ_key,
            "civ_name": civ.name,
            "era": civ.era,
            "event": event['name'],
            "description": event['description'],
            "cost": event['cost'],
            "reward": event['reward'],
            "penalty": event['penalty'],
            "result": event_result
        })
    
    def run(self):
        """Run the main game loop."""
        # Print game start information
        civ_count = len(self.civilizations)
        print("Starting AI Civilization Simulation!")
        print(f"{civ_count} civilizations will compete for {self.max_turns} turns.")
        for civ_id, civ in self.civilizations.items():
            model_info = self.model_info[civ_id]
            print(f"{civ.name} is controlled by {model_info}")
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
                
                # Handle internal events for all civilizations
                self.handle_internal_events()
                
                # Handle era events for all civilizations
                for civ_id, civ in self.civilizations.items():
                    self.handle_era_event(civ, self.ai_controllers[civ_id], civ_id)
                
                # Apply active effects before diplomacy phase
                for civ_id, civ in self.civilizations.items():
                    self.apply_active_effects(civ, civ_id)
                
                # Diplomacy phase (trade and war)
                self.handle_diplomacy()
                
                # Apply active effects before civilization turns
                for civ_id, civ in self.civilizations.items():
                    self.apply_active_effects(civ, civ_id)
                
                # Civilization turns (parallel execution for better performance)
                import threading
                threads = []
                
                # Create and start a thread for each civilization's turn
                for civ_id, civ in self.civilizations.items():
                    thread = threading.Thread(
                        target=self.handle_civilization_turn,
                        args=(civ, civ_id, self.ai_controllers[civ_id])
                    )
                    threads.append(thread)
                    thread.start()
                
                # Wait for all threads to complete
                for thread in threads:
                    thread.join()
                
                time.sleep(0.5)  # Short pause for readability
                
                # Apply active effects after civilization turns
                for civ_id, civ in self.civilizations.items():
                    self.apply_active_effects(civ, civ_id)
                
                # Apply culture influence after all turns
                print("\nCULTURE INFLUENCE PHASE")
                print("="*60)
                
                # All civilizations apply culture influence on each other
                civ_ids = list(self.civilizations.keys())
                for i, attacker_id in enumerate(civ_ids):
                    for j, defender_id in enumerate(civ_ids):
                        if i == j:  # Skip influencing oneself
                            continue
                        
                        attacker = self.civilizations[attacker_id]
                        defender = self.civilizations[defender_id]
                        
                        influence_result = attacker.apply_culture_influence(defender)
                        if influence_result:
                            print(f"{influence_result}")
                
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
            "civilizations": {}
        }
        for civ_id, civ in self.civilizations.items():
            game_state["civilizations"][civ_id] = civ.to_dict()
        with open(f"game_state_turn_{self.current_turn}.json", "w") as f:
            json.dump(game_state, f, indent=2)
    
    def print_final_summary(self):
        """Print a final summary of the game with detailed scoring."""
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        
        # Calculate scores for all civilizations
        scores = {}
        for civ_id, civ in self.civilizations.items():
            scores[civ] = civ.calculate_score()
        
        # Compare final states
        print("CIVILIZATION COMPARISON:")
        for civ_id, civ in self.civilizations.items():
            print(f"\n{civ.name}:")
            print(f"  Era: {civ.era}")
            print(f"  Technology: {civ.technology}")
            print(f"  Population: {civ.population}")
            print(f"  Military: {civ.military}")
            print(f"  Resources: {civ.resources}")
            print(f"  Culture: {civ.culture}")
            print(f"  Loyalty: {civ.loyalty}")
        
        print("\n" + "-"*60)
        print("DETAILED SCORING")
        print("-"*60)
        
        # Show scoring breakdown for each civilization
        for civ_id, civ in self.civilizations.items():
            print(f"\n{civ.name} Score Breakdown:")
            print(f"  Technology (40%): {civ.technology} × 4 = {civ.technology * 4} points")
            print(f"  Population (25%): {civ.population} × 0.25 = {round(civ.population * 0.25)} points")
            print(f"  Military (20%): {civ.military} × 2 = {civ.military * 2} points")
            print(f"  Culture (10%): {civ.culture} × 0.2 = {round(civ.culture * 0.2)} points")
            print(f"  Resources (10%): {civ.resources} × 0.1 = {round(civ.resources * 0.1)} points")
            print(f"  Loyalty (5%): {civ.loyalty} × 0.5 = {round(civ.loyalty * 0.5)} points")
            
            # Calculate era bonus
            era_bonus = {
                "Primitive": 0,
                "Classical": 50,
                "Medieval": 150,
                "Renaissance": 250,
                "Industrial": 400,
                "Modern": 600,
                "Information": 800,
                "Future": 1000
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
        max_score = -1
        winner = None
        for civ, score in scores.items():
            print(f"  {civ.name}: {score} points")
            if score > max_score:
                max_score = score
                winner = civ.name
                winning_civ = civ
            elif score == max_score:
                winner = "Tie"
        
        print(f"\nWinner: {winner}")
        if winner != "Tie":
            # Calculate winning margin
            scores_list = sorted(scores.values(), reverse=True)
            if len(scores_list) > 1:
                margin = scores_list[0] - scores_list[1]
                print(f"Winning Margin: {margin} points")
        print("="*60)

    def run_turn(self):
        """Run a single turn of the game."""
        # Print current state
        self.print_game_state()
        
        # Handle era events for all civilizations
        for civ_id, civ in self.civilizations.items():
            self.handle_era_event(civ, self.ai_controllers[civ_id], civ_id)
        
        # Apply active effects before diplomacy phase
        for civ_id, civ in self.civilizations.items():
            self.apply_active_effects(civ, civ_id)
        
        # Diplomacy phase (trade and war)
        self.handle_diplomacy()
        
        # Apply active effects before civilization turns
        for civ_id, civ in self.civilizations.items():
            self.apply_active_effects(civ, civ_id)
        
        # Civilization turns
        for civ_id, civ in self.civilizations.items():
            self.handle_civilization_turn(civ, civ_id, self.ai_controllers[civ_id])
        
        # Apply active effects after civilization turns
        for civ_id, civ in self.civilizations.items():
            self.apply_active_effects(civ, civ_id)
        
        # Apply culture influence after all turns
        print("\nCULTURE INFLUENCE PHASE")
        print("="*60)
        
        # All civilizations apply culture influence on each other
        civ_ids = list(self.civilizations.keys())
        for i, attacker_id in enumerate(civ_ids):
            for j, defender_id in enumerate(civ_ids):
                if i == j:  # Skip influencing oneself
                    continue
                
                attacker = self.civilizations[attacker_id]
                defender = self.civilizations[defender_id]
                
                influence_result = attacker.apply_culture_influence(defender)
                if influence_result:
                    print(f"{influence_result}")
        
        print("="*60)

if __name__ == "__main__":
    # Test with 3 civilizations
    civ_configs = [
        {"name": "Atlantis", "color": "blue", "model_name": "qwen-flash", "model_type": "aliyun"},
        {"name": "Eldorado", "color": "gold", "model_name": "abab6.5s-chat", "model_type": "minimax"},
        {"name": "Zimbabwe", "color": "green", "model_name": "qwen-plus", "model_type": "aliyun"}
    ]
    game = CivilizationGame(civ_configs)
    game.run()
