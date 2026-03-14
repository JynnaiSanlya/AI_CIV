import os
import re
import json
import urllib.request
import urllib.error

class AIController:
    """Controls a civilization using AI API for decision-making."""

    def __init__(self, civilization_name, model_name="qwen-flash"):
        """Initialize AI controller with API client.
        
        Args:
            civilization_name: Name of the civilization being controlled
            model_name: Specific model name to use (e.g., "qwen-flash", "qwen-plus")
        """
        self.civilization_name = civilization_name
        self.model_type = "aliyun"
        self.model = model_name
        self.conversation_history = []
        
        # Load API keys from config.json
        with open("config.json", "r") as f:
            config = json.load(f)
        
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
            # Call Aliyun DashScope API using urllib
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
            
            # Convert payload to JSON string
            json_payload = json.dumps(payload).encode('utf-8')
            
            # Create request
            req = urllib.request.Request(
                self.endpoint,
                data=json_payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            # Send request
            with urllib.request.urlopen(req) as response:
                response_text_raw = response.read().decode('utf-8')
                response_data = json.loads(response_text_raw)
            
            # Check if response has output field (success)
            if "output" in response_data:
                response_text = response_data.get("output", {}).get("text", "")
            else:
                # Handle error case
                error_msg = response_data.get("message", f"Unknown error. Response: {response_text_raw}")
                raise Exception(f"Aliyun API error: {error_msg}")

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
