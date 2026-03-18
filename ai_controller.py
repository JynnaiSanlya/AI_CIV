import os
import re
import json
import urllib.request
import urllib.error

class AIController:
    """Controls a civilization using AI API for decision-making."""

    def __init__(self, civilization_name, model_name="qwen-flash", model_type="aliyun"):
        """Initialize AI controller with API client.
        
        Args:
            civilization_name: Name of the civilization being controlled
            model_name: Specific model name to use (e.g., "qwen-flash", "qwen-plus", "abab6-chat")
            model_type: Type of model API to use (e.g., "aliyun", "minimax")
        """
        self.civilization_name = civilization_name
        self.model_type = model_type
        self.model = model_name
        self.conversation_history = []
        
        # Load API keys from config.json
        with open("config.json", "r") as f:
            config = json.load(f)
        
        # Configure API based on model_type
        if self.model_type == "aliyun":
            self.api_key = config.get("aliyun_api_key")
            self.endpoint = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        elif self.model_type == "minimax":
            self.api_key = config.get("minimax_api_key")
            self.endpoint = "https://api.minimax.chat/v1/text/chatcompletion"
        else:
            # Default to aliyun if model_type is unknown
            self.model_type = "aliyun"
            self.api_key = config.get("aliyun_api_key")
            self.endpoint = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    def _build_prompt(self, civ_state, opponent_state, turn_number):
        """Build prompt for AI decision-making."""
        return f"""
You are the leader of {self.civilization_name}, a civilization in a turn-based strategy game.

Current Turn: {turn_number}

Your Civilization State:
- Name: {civ_state['name']}
- Era: {civ_state['era']}
- Resources: {civ_state['resources']}
- Population: {civ_state['population']}
- Military: {civ_state['military']}
- Technology: {civ_state['technology']}
- Culture: {civ_state['culture']}
- Loyalty: {civ_state['loyalty']}
- Action Points: {civ_state['current_action_points']}/{civ_state['action_points']}

Opponent Civilization State:
- Name: {opponent_state['name']}
- Era: {opponent_state['era']}
- Resources: {opponent_state['resources']}
- Population: {opponent_state['population']}
- Military: {opponent_state['military']}
- Technology: {opponent_state['technology']}
- Culture: {opponent_state['culture']}
- Loyalty: {opponent_state['loyalty']}
- Action Points: {opponent_state['current_action_points']}/{opponent_state['action_points']}

Available Actions:
1. develop_technology [amount] - Invest resources to develop technology. Resource Cost: amount * 20, Action Cost: 2
2. build_military [amount] - Recruit soldiers and build weapons. Resource Cost: amount * 15, Action Cost: 2
3. grow_population [amount] - Support population growth. Resource Cost: amount * 10, Action Cost: 1
4. gather_resources [amount] - Collect more resources. Resource Cost: 0, Action Cost: 1, Dynamic Limit: max(1, population // 10 + technology * 2)
5. develop_culture [amount] - Develop cultural influence. Resource Cost: amount * 10, Action Cost: 1

Game Rules:

1. Era System:
   - 8 Eras: Primitive → Classical → Medieval → Renaissance → Industrial → Modern → Information → Future
   - Era Progress: Calculated as (Technology * 0.8 + Culture * 0.2)
   - Higher thresholds for longer eras: Primitive (0-14), Classical (15-29), Medieval (30-44), Renaissance (45-59), Industrial (60-74), Modern (75-89), Information (90-104), Future (105+)
   - Action Points: Start with 5, +1 every TWO new eras (Primitive:5, Classical:5, Medieval:6, Renaissance:6, Industrial:7, Modern:7, Information:8, Future:8)

2. Culture System:
   - Culture grows naturally with population
   - High culture affects loyalty and can absorb enemy population
   - Culture contributes to era progression (20% weight)
   - Culture can be plundered in war but not traded
   - Culture is included in final scoring

3. War System:
   - Attackers winning: +5 loyalty
   - Attackers losing: -10 loyalty
   - Defenders winning: +5 loyalty
   - Defenders losing: -5 loyalty (reduced penalty)
   - War initiators: Next turn population and resource growth halved

4. Era Events:
   - Each era has specific events with probability of occurrence
   - Events require resources/population investment for rewards or penalty avoidance
   - Examples: Natural Disasters (Primitive), Barbarian Invasion (Classical), Cultural Renaissance (Medieval), etc.

5. General Rules:
   - You can choose multiple actions per turn (one per line)
   - The amount must be a positive integer for each action
   - You cannot spend more resources than you have in total
   - You cannot exceed your available action points (each action costs specific AP)
   - The gather_resources action has a dynamic upper limit: max(1, population // 10 + technology * 2)
   - Actions will be executed in the order you provide
   - If you cannot afford any other actions except gather_resources, you should try to gather resources
   - When gathering resources, you should gather as much as possible up to the dynamic limit, since there is no cost to gather resources
   - Always gather resources at the maximum possible amount if you have action points left and no other actions to perform

6. Strategic Guidelines:
   - **Balance is key**: Maintain a good balance between population growth, technology development, military strength, and culture
   - **Long-term planning**: Consider the long-term effects of your decisions, not just immediate gains
   - **Adapt to your era**: Different eras require different strategies. For example, early eras focus on population and resources, while later eras emphasize technology and culture
   - **Know your opponent**: Adjust your strategy based on your opponent's strengths and weaknesses. If they have a strong military, focus on defense; if they have high culture, counter with your own culture development
   - **Technology drives progress**: Technology contributes 80% to era progression and unlocks better abilities
   - **Culture matters**: High culture improves loyalty and can influence enemy populations
   - **Loyalty is critical**: Low loyalty can lead to population loss and instability
   - **Resource management**: Ensure you have enough resources to support your growth plans
   - **Military strength**: Maintain a balanced military to defend against attacks and deter aggression
   - **Seize opportunities**: Take advantage of events and trade opportunities that arise

Example Decision:
grow_population 2
develop_technology 1
develop_culture 1
gather_resources 3

Your Decision:
"""

    def get_decision(self, civ_state, opponent_state, turn_number):
        """
        Get AI decisions for the current turn.

        Args:
            civ_state: Dictionary with civilization's current state
            opponent_state: Dictionary with opponent's current state
            turn_number: Current turn number

        Returns:
            list: List of tuples (action_type, amount) where action_type is one of:
                  'develop_technology', 'build_military', 'grow_population', 'gather_resources'
        """
        prompt = self._build_prompt(civ_state, opponent_state, turn_number)

        try:
            # Build payload based on model_type
            if self.model_type == "aliyun":
                # Call Aliyun DashScope API
                payload = {
                    "model": self.model,
                    "input": {
                        "prompt": prompt
                    },
                    "parameters": {
                        "max_tokens": 1024,
                        "temperature": 0.7
                    }
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            elif self.model_type == "minimax":
                # Call MiniMax API
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            else:
                raise Exception(f"Unsupported model type: {self.model_type}")
            
            # Convert payload to JSON string
            json_payload = json.dumps(payload).encode('utf-8')
            
            # Create request
            req = urllib.request.Request(
                self.endpoint,
                data=json_payload,
                headers=headers
            )
            
            # Send request with timeout
            with urllib.request.urlopen(req, timeout=10) as response:
                response_text_raw = response.read().decode('utf-8')
                response_data = json.loads(response_text_raw)
            
            # Parse response based on model_type
            if self.model_type == "aliyun":
                # Check if response has output field (success)
                if "output" in response_data:
                    response_text = response_data.get("output", {}).get("text", "")
                else:
                    # Handle error case
                    error_msg = response_data.get("message", f"Unknown error. Response: {response_text_raw}")
                    raise Exception(f"Aliyun API error: {error_msg}")
            elif self.model_type == "minimax":
                # Check if response has choices field (success)
                if "choices" in response_data:
                    response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    # Handle error case
                    error_msg = response_data.get("error", {}).get("message", f"Unknown error. Response: {response_text_raw}")
                    raise Exception(f"MiniMax API error: {error_msg}")

            # Extract all actions from response using regex
            actions = []
            pattern = r'(develop_technology|build_military|grow_population|gather_resources|develop_culture)\s+(\d+)'
            matches = re.finditer(pattern, response_text)
            
            for match in matches:
                action_type = match.group(1)
                amount = int(match.group(2))
                actions.append((action_type, amount))
            
            if actions:
                return actions
            else:
                # Default action if parsing fails
                return [("develop_technology", 1)]

        except Exception as e:
            print(f"Error getting AI decision: {e}")
            # Fallback to default action
            return [("develop_technology", 1)]

    def get_diplomacy_decision(self, civ_state, opponent_state, turn_number, wars_initiated):
        """
        Get AI diplomacy decisions (trade and war).

        Args:
            civ_state: Dictionary with civilization's current state
            opponent_state: Dictionary with opponent's current state
            turn_number: Current turn number
            wars_initiated: Number of wars initiated by this civilization

        Returns:
            dict: Dictionary containing diplomacy decisions
        """
        prompt = self._build_diplomacy_prompt(civ_state, opponent_state, turn_number, wars_initiated)

        try:
            # Build payload based on model_type
            if self.model_type == "aliyun":
                # Call Aliyun DashScope API
                payload = {
                    "model": self.model,
                    "input": {
                        "prompt": prompt
                    },
                    "parameters": {
                        "max_tokens": 1024,
                        "temperature": 0.7
                    }
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            elif self.model_type == "minimax":
                # Call MiniMax API
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            else:
                raise Exception(f"Unsupported model type: {self.model_type}")
            
            # Convert payload to JSON string
            json_payload = json.dumps(payload).encode('utf-8')
            
            # Create request
            req = urllib.request.Request(
                self.endpoint,
                data=json_payload,
                headers=headers
            )
            
            # Send request with timeout
            with urllib.request.urlopen(req, timeout=10) as response:
                response_text_raw = response.read().decode('utf-8')
                response_data = json.loads(response_text_raw)
            
            # Parse response based on model_type
            if self.model_type == "aliyun":
                # Check if response has output field (success)
                if "output" in response_data:
                    response_text = response_data.get("output", {}).get("text", "")
                else:
                    # Handle error case
                    error_msg = response_data.get("message", f"Unknown error. Response: {response_text_raw}")
                    raise Exception(f"Aliyun API error: {error_msg}")
            elif self.model_type == "minimax":
                # Check if response has choices field (success)
                if "choices" in response_data:
                    response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    # Handle error case
                    error_msg = response_data.get("error", {}).get("message", f"Unknown error. Response: {response_text_raw}")
                    raise Exception(f"MiniMax API error: {error_msg}")

            # Parse diplomacy decision
            diplomacy_decision = {
                "trade": False,
                "war": False,
                "trade_offer": {
                    "resources": 0,
                    "population": 0,
                    "technology": 0
                },
                "trade_request": {
                    "resources": 0,
                    "population": 0,
                    "technology": 0
                }
            }

            # Check if AI wants to trade
            if "TRADE DECISION: YES" in response_text:
                diplomacy_decision["trade"] = True
                # Extract trade offer
                offer_pattern = r'TRADE OFFER:\s*resources=(\d+),\s*population=(\d+),\s*technology=(\d+)'
                offer_match = re.search(offer_pattern, response_text)
                if offer_match:
                    diplomacy_decision["trade_offer"] = {
                        "resources": int(offer_match.group(1)),
                        "population": int(offer_match.group(2)),
                        "technology": int(offer_match.group(3))
                    }
                # Extract trade request
                request_pattern = r'TRADE REQUEST:\s*resources=(\d+),\s*population=(\d+),\s*technology=(\d+)'
                request_match = re.search(request_pattern, response_text)
                if request_match:
                    diplomacy_decision["trade_request"] = {
                        "resources": int(request_match.group(1)),
                        "population": int(request_match.group(2)),
                        "technology": int(request_match.group(3))
                    }

            # Check if AI wants to declare war
            if "WAR DECISION: YES" in response_text:
                diplomacy_decision["war"] = True

            return diplomacy_decision

        except Exception as e:
            print(f"Error getting AI diplomacy decision: {e}")
            # Fallback to no trade and no war
            return diplomacy_decision

    def _build_diplomacy_prompt(self, civ_state, opponent_state, turn_number, wars_initiated):
        """
        Build prompt for AI diplomacy decision-making.
        """
        return f"""
You are the leader of {self.civilization_name}, a civilization in a turn-based strategy game.

Current Turn: {turn_number}

Your Civilization State:
- Name: {civ_state['name']}
- Era: {civ_state['era']}
- Resources: {civ_state['resources']}
- Population: {civ_state['population']}
- Military: {civ_state['military']}
- Technology: {civ_state['technology']}
- Culture: {civ_state['culture']}
- Loyalty: {civ_state['loyalty']}
- Wars Initiated this Era: {wars_initiated}/2

Opponent Civilization State:
- Name: {opponent_state['name']}
- Era: {opponent_state['era']}
- Resources: {opponent_state['resources']}
- Population: {opponent_state['population']}
- Military: {opponent_state['military']}
- Technology: {opponent_state['technology']}
- Culture: {opponent_state['culture']}
- Loyalty: {opponent_state['loyalty']}

Diplomacy Options:
1. TRADE: Propose a trade with the opponent civilization
2. WAR: Declare war on the opponent civilization
3. PEACE: Do nothing (continue in peace)

Trade Rules:
- You can offer resources, population, or technology
- You can request resources, population, or technology
- Both civilizations must have enough resources to complete the trade
- You cannot offer more than you have
- You cannot request more than the opponent has

War Rules:
- You can declare war only if you have not already initiated 2 wars this era (except Future era)
- **War Benefits**:
  - Attackers winning: +5 loyalty, plunder up to 40% of opponent's resources, up to 40% of opponent's population, and up to 20% of opponent's culture
  - Defenders winning: +5 loyalty
  - Plundered resources, population, and culture are directly added to your civilization
  - War can significantly accelerate your civilization's growth if successful
- **War Risks**:
  - Attackers losing: -10 loyalty, potential loss of military units
  - Defenders losing: -5 loyalty (reduced penalty), up to 40% loss of resources, population, and 20% loss of culture
  - War initiators: Next turn population and resource growth halved
- **Military Advantage**: If your military strength is significantly higher than your opponent, you have a high chance of winning
- **Era Advantage**: Higher eras have stronger military multipliers, giving you an edge over lower-era civilizations

Your Decision:
Please decide whether to propose trade, declare war, or do nothing.

For trade, specify the exact resources, population, and technology you want to offer and request.

Example Trade Decision:
TRADE DECISION: YES
TRADE OFFER: resources=30, population=0, technology=0
TRADE REQUEST: resources=0, population=0, technology=2

Example War Decision:
TRADE DECISION: NO
WAR DECISION: YES

Example Peace Decision:
TRADE DECISION: NO
WAR DECISION: NO

Your Decision:
"""

    def get_internal_event_decision(self, civ_state, event_data):
        """
        Get AI decision for an internal event.
        
        Args:
            civ_state: Dictionary with civilization's current state
            event_data: Dictionary with event information and options
            
        Returns:
            str: The key of the selected option
        """
        prompt = self._build_internal_event_prompt(civ_state, event_data)

        try:
            # Build payload based on model_type
            if self.model_type == "aliyun":
                # Call Aliyun DashScope API
                payload = {
                    "model": self.model,
                    "input": {
                        "prompt": prompt
                    },
                    "parameters": {
                        "max_tokens": 512,
                        "temperature": 0.7
                    }
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            elif self.model_type == "minimax":
                # Call MiniMax API
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 512
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            else:
                raise Exception(f"Unsupported model type: {self.model_type}")
            
            # Convert payload to JSON string
            json_payload = json.dumps(payload).encode('utf-8')
            
            # Create request
            req = urllib.request.Request(
                self.endpoint,
                data=json_payload,
                headers=headers
            )
            
            # Send request with timeout
            with urllib.request.urlopen(req, timeout=10) as response:
                response_text_raw = response.read().decode('utf-8')
                response_data = json.loads(response_text_raw)
            
            # Parse response based on model_type
            if self.model_type == "aliyun":
                # Check if response has output field (success)
                if "output" in response_data:
                    response_text = response_data.get("output", {}).get("text", "")
                else:
                    # Handle error case
                    error_msg = response_data.get("message", f"Unknown error. Response: {response_text_raw}")
                    raise Exception(f"Aliyun API error: {error_msg}")
            elif self.model_type == "minimax":
                # Check if response has choices field (success)
                if "choices" in response_data:
                    response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    # Handle error case
                    error_msg = response_data.get("error", {}).get("message", f"Unknown error. Response: {response_text_raw}")
                    raise Exception(f"MiniMax API error: {error_msg}")

            # Extract option key from response
            import re
            pattern = r'DECISION: (.+)'
            match = re.search(pattern, response_text)
            if match:
                decision = match.group(1).strip()
                return decision
            else:
                # Default to first option if parsing fails
                return list(event_data.get("options", {}).keys())[0]

        except Exception as e:
            print(f"Error getting AI internal event decision: {e}")
            # Fallback to first option
            return list(event_data.get("options", {}).keys())[0]

    def _build_internal_event_prompt(self, civ_state, event_data):
        """
        Build prompt for AI internal event decision-making.
        """
        # Format options
        options_text = ""
        for option_key, option_data in event_data.get("options", {}).items():
            options_text += f"{option_key}: {option_data['name']} - {option_data['description']}\n"
            if "cost" in option_data:
                cost_text = ", ".join([f"{k}: {v}" for k, v in option_data["cost"].items()])
                options_text += f"  Cost: {cost_text}\n"
            if "effects" in option_data:
                effects = option_data["effects"]
                effects_text = f"  Effects: {effects['type']} effect\n"
                if effects["type"] == "continuous" or effects["type"] == "mixed":
                    duration = effects.get("duration", 0) if effects["type"] == "continuous" else effects.get("continuous", {}).get("duration", 0)
                    effects_text += f"  Duration: {duration} turns\n"
                options_text += effects_text
        
        return f"""
You are the leader of {self.civilization_name}, a civilization in a turn-based strategy game.

Your Civilization State:
- Name: {civ_state['name']}
- Era: {civ_state['era']}
- Resources: {civ_state['resources']}
- Population: {civ_state['population']}
- Military: {civ_state['military']}
- Technology: {civ_state['technology']}
- Culture: {civ_state['culture']}
- Loyalty: {civ_state['loyalty']}

Current Event:
Name: {event_data['name']}
Description: {event_data['description']}

Strategic Guidelines for Event Decisions:
1. **Align with current needs**: Choose options that address your civilization's current weaknesses or enhance its strengths
2. **Consider long-term vs short-term**: Evaluate both immediate benefits and long-term consequences
3. **Resource availability**: Ensure you can afford any costs associated with the option
4. **Balance development**: Maintain a balance between military, technology, culture, and population growth
5. **Adapt to era**: Different eras favor different strategies (early: population/resources, late: technology/culture)
6. **Loyalty is key**: Prioritize options that maintain or improve loyalty
7. **Opportunity cost**: Consider what you might be giving up by choosing one option over another
8. **Risk assessment**: Evaluate the risks and rewards of each option

Available Options:
{options_text}

Your Decision:
Carefully analyze each option and choose the one that best serves your civilization's interests. Use the format:
DECISION: [option_key]

For example:
DECISION: encourage

Your Decision:
"""
