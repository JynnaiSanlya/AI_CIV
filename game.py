import sys
import time
import json
import os
from civilization import Civilization
from ai_controller import AIController
from era_event import EraEvent

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
        self.max_turns = 50  # Increased from 10 to 50 for longer games
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
        
        # Load era events from configuration file
        self.era_events = self._load_era_events()
        
        # Track which events have been triggered for each civilization and era
        self.triggered_events = {
            "civ1": set(),
            "civ2": set()
        }
        
        # War penalties tracking
        self.war_penalties = {
            "civ1": False,
            "civ2": False
        }
        
        # Era events history for display
        self.era_events_history = []
        
        # Load internal events
        self.internal_events = self._load_internal_events()
        
        # Track internal events cooldowns for each civilization
        self.internal_events_cooldowns = {
            "civ1": {},
            "civ2": {}
        }
        
        # Track active continuous effects for each civilization
        self.active_effects = {
            "civ1": [],
            "civ2": []
        }
        
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
        """Handle internal events for both civilizations."""
        for civ, civ_key in [(self.civ1, "civ1"), (self.civ2, "civ2")]:
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
        ai = self.ai1 if civ == self.civ1 else self.ai2
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
        
        # Record the event
        self.internal_events_history.append({
            "turn": self.current_turn,
            "civ": civ_key,
            "civ_name": civ.name,
            "event": event_data["name"],
            "description": event_data["description"],
            "decision": decision
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
        
        # Get diplomacy decisions from both civilizations
        civ1_decision = self.ai1.get_diplomacy_decision(
            self.civ1.to_dict(), 
            self.civ2.to_dict(), 
            self.current_turn,
            self.civ1.wars_initiated
        )
        
        civ2_decision = self.ai2.get_diplomacy_decision(
            self.civ2.to_dict(), 
            self.civ1.to_dict(), 
            self.current_turn,
            self.civ2.wars_initiated
        )
        
        # Handle trade proposals (only one proposal per turn, prioritize civ1 then civ2)
        trade_handled = False
        
        # Check if civ1 wants to trade
        if civ1_decision["trade"] and not trade_handled:
            proposer = self.civ1
            responder = self.civ2
            ai = self.ai1
            offer = civ1_decision["trade_offer"]
            request = civ1_decision["trade_request"]
            
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
                    trade_handled = True
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
        
        # Check if civ2 wants to trade (only if no trade has been handled yet)
        if civ2_decision["trade"] and not trade_handled:
            proposer = self.civ2
            responder = self.civ1
            ai = self.ai2
            offer = civ2_decision["trade_offer"]
            request = civ2_decision["trade_request"]
            
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
                    trade_handled = True
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
        
        # Handle war declarations (only one war per turn, prioritize civ1 then civ2)
        war_handled = False
        
        # Check if civ1 wants to declare war
        if civ1_decision["war"] and not war_handled:
            attacker = self.civ1
            defender = self.civ2
            
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
                self.war_penalties["civ1"] = True
                war_handled = True
        
        # Check if civ2 wants to declare war (only if no war has been handled yet)
        if civ2_decision["war"] and not war_handled:
            attacker = self.civ2
            defender = self.civ1
            
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
                self.war_penalties["civ2"] = True
                war_handled = True
        
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
        if random.random() > event.probability:
            return
        
        print(f"\nERA EVENT for {civ.name} ({civ.era}): {event.name}")
        print(f"Description: {event.description}")
        print(f"Cost: {event.cost}")
        print(f"Reward: {event.reward}")
        print(f"Penalty if declined: {event.penalty}")
        
        # Check if civilization can afford the event
        can_afford = True
        for resource, amount in event.cost.items():
            if getattr(civ, resource, 0) < amount:
                can_afford = False
                break
        
        event_result = ""
        if not can_afford:
            event_result = "cannot_afford"
            print(f"{civ.name} cannot afford the event. Applying penalty.")
            # Apply penalty
            for resource, amount in event.penalty.items():
                setattr(civ, resource, max(0, getattr(civ, resource, 0) + amount))
        else:
            # Get AI decision
            # For simplicity, we'll assume AI always accepts if it can afford
            # In a more advanced implementation, we'd ask the AI for a decision
            event_result = "accepted"
            print(f"{civ.name} accepts the event. Applying cost and reward.")
            
            # Apply cost
            for resource, amount in event.cost.items():
                setattr(civ, resource, getattr(civ, resource, 0) - amount)
            
            # Apply reward
            for resource, amount in event.reward.items():
                setattr(civ, resource, getattr(civ, resource, 0) + amount)
        
        # Mark event as triggered
        self.triggered_events[civ_key].add(event_key)
        
        # Record the event to history for display in web UI
        self.era_events_history.append({
            "turn": self.current_turn,
            "civ": civ_key,
            "civ_name": civ.name,
            "era": civ.era,
            "event": event.name,
            "description": event.description,
            "cost": event.cost,
            "reward": event.reward,
            "penalty": event.penalty,
            "result": event_result
        })
    
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
                
                # Handle internal events for both civilizations
                self.handle_internal_events()
                
                # Handle era events for both civilizations
                self.handle_era_event(self.civ1, self.ai1, "civ1")
                self.handle_era_event(self.civ2, self.ai2, "civ2")
                
                # Apply active effects before diplomacy phase
                self.apply_active_effects(self.civ1, "civ1")
                self.apply_active_effects(self.civ2, "civ2")
                
                # Diplomacy phase (trade and war)
                self.handle_diplomacy()
                
                # Apply active effects before civilization turns
                self.apply_active_effects(self.civ1, "civ1")
                
                # Civilization 1's turn
                self.handle_civilization_turn(self.civ1, self.civ2, self.ai1)
                time.sleep(1)  # Pause for readability
                
                # Apply active effects before civilization 2's turn
                self.apply_active_effects(self.civ2, "civ2")
                
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
