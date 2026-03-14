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

Opponent Civilization State:
- Name: {opponent_state['name']}
- Era: {opponent_state['era']}
- Resources: {opponent_state['resources']}
- Population: {opponent_state['population']}
- Military: {opponent_state['military']}
- Technology: {opponent_state['technology']}

Available Actions:
1. develop_technology [amount] - Invest resources to develop technology. Resource Cost: amount * 20, Action Cost: 2
2. build_military [amount] - Recruit soldiers and build weapons. Resource Cost: amount * 15, Action Cost: 2
3. grow_population [amount] - Support population growth. Resource Cost: amount * 10, Action Cost: 1
4. gather_resources [amount] - Collect more resources. Resource Cost: 0, Action Cost: 1, Dynamic Limit: max(1, population // 10 + technology * 2)

Rules:
- You can choose multiple actions per turn (one per line)
- The amount must be a positive integer for each action
- You cannot spend more resources than you have in total
- You cannot exceed your available action points (each action costs a specific number of action points)
- The gather_resources action has a dynamic upper limit based on population and technology: max(1, population // 10 + technology * 2)
- Your decisions should be based on your civilization's current needs, available action points, and the opponent's state
- Actions will be executed in the order you provide
- You start with 5 action points per turn, and gain +1 action point for each new era you enter

Example Decision:
grow_population 2
develop_technology 1
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
            pattern = r'(develop_technology|build_military|grow_population|gather_resources)\s+(\d+)'
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
