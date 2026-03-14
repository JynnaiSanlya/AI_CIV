import http.server
import socketserver
import json
import threading
import time
from game import CivilizationGame

# Web server settings
PORT = 8000

# Game state to be sent to the client
game_state = {
    "turn": 0,
    "civ1": None,
    "civ2": None,
    "game_ended": False,
    "reason": ""
}

# Game instance
game = None

# HTML template for the web GUI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Civilization Simulation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #1a1a1a;
            color: #ffffff;
            margin: 0;
            padding: 20px;
        }
        
        h1 {
            text-align: center;
            color: #4a90e2;
        }
        
        .game-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .turn-info {
            text-align: center;
            font-size: 24px;
            margin-bottom: 30px;
            color: #f39c12;
        }
        
        .civilizations {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }
        
        .civ-panel {
            width: 48%;
            background-color: #2c2c2c;
            border: 2px solid #444;
            border-radius: 10px;
            padding: 20px;
        }
        
        .civ-name {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #4a90e2;
        }
        
        .civ-era {
            font-size: 18px;
            margin-bottom: 20px;
            color: #f39c12;
        }
        
        .civ-image {
            width: 100%;
            height: 150px;
            background-color: #333;
            margin-bottom: 20px;
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: #fff;
        }
        
        .era-primitive { background-color: #505050; } /* Campfire */
        .era-ancient { background-color: #8b4513; } /* Tent */
        .era-medieval { background-color: #a52a2a; } /* Wooden Hut */
        .era-modern { background-color: #d3d3d3; color: #000; } /* Small Buildings */
        .era-future { background-color: #87ceeb; color: #000; } /* Skyscrapers */
        
        .resources {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .resource {
            background-color: #333;
            padding: 15px;
            border-radius: 5px;
        }
        
        .resource-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .resource-bar {
            width: 100%;
            height: 20px;
            background-color: #444;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .resource-fill {
            height: 100%;
            transition: width 0.5s ease;
        }
        
        .resource-value {
            text-align: right;
            font-size: 14px;
            margin-top: 5px;
        }
        
        /* Resource colors */
        .resource-fill.resources { background-color: #4a90e2; } /* Blue */
        .resource-fill.population { background-color: #2ecc71; } /* Green */
        .resource-fill.military { background-color: #e74c3c; } /* Red */
        .resource-fill.technology { background-color: #f1c40f; } /* Yellow */
        .resource-fill.loyalty { background-color: #e67e22; } /* Orange */
        .resource-fill.action_points { background-color: #9b59b6; } /* Purple */
        
        .diplomacy {
            background-color: #2c2c2c;
            border: 2px solid #444;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }
        
        .diplomacy-title {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #4a90e2;
        }
        
        .diplomacy-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .civ-relation {
            display: flex;
            align-items: center;
        }
        
        .civ-icon {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            margin-right: 10px;
        }
        
        .actions {
            display: flex;
            gap: 20px;
        }
        
        .action-icon {
            width: 50px;
            height: 50px;
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        .action-trade { background-color: #00ffff; color: #000; } /* Cyan */
        .action-war { background-color: #ff0000; color: #fff; } /* Red */
        
        .game-over {
            text-align: center;
            font-size: 36px;
            color: #e74c3c;
            margin-top: 50px;
        }
    </style>
</head>
<body>
    <div class="game-container">
        <h1>AI Civilization Simulation</h1>
        
        <div class="turn-info">
            Turn <span id="turn">0</span>
        </div>
        
        <div class="civilizations">
            <div class="civ-panel" id="civ1-panel">
                <div class="civ-name" id="civ1-name">Civilization 1</div>
                <div class="civ-era" id="civ1-era">Primitive</div>
                <div class="civ-image" id="civ1-image">Campfire</div>
                <div class="resources" id="civ1-resources"></div>
            </div>
            
            <div class="civ-panel" id="civ2-panel">
                <div class="civ-name" id="civ2-name">Civilization 2</div>
                <div class="civ-era" id="civ2-era">Primitive</div>
                <div class="civ-image" id="civ2-image">Campfire</div>
                <div class="resources" id="civ2-resources"></div>
            </div>
        </div>
        
        <div class="diplomacy">
            <div class="diplomacy-title">Diplomacy</div>
            <div class="diplomacy-content">
                <div class="civ-relation">
                    <div class="civ-icon era-primitive" id="civ1-relation-icon"></div>
                    <div id="civ1-relation-name">Civilization 1</div>
                </div>
                
                <div class="actions">
                    <div class="action-icon action-trade">Trade</div>
                    <div class="action-icon action-war">War</div>
                </div>
                
                <div class="civ-relation">
                    <div id="civ2-relation-name">Civilization 2</div>
                    <div class="civ-icon era-primitive" id="civ2-relation-icon"></div>
                </div>
            </div>
        </div>
        
        <div id="game-over" class="game-over" style="display: none;"></div>
    </div>
    
    <script>
        // Update the game state from the server
        function updateGameState() {
            fetch('/game_state')
                .then(response => response.json())
                .then(data => {
                    if (data.game_ended) {
                        document.getElementById('game-over').textContent = `Game Over! ${data.reason}`;
                        document.getElementById('game-over').style.display = 'block';
                        return;
                    }
                    
                    // Update turn
                    document.getElementById('turn').textContent = data.turn;
                    
                    // Update civilization 1
                    updateCivilization('civ1', data.civ1);
                    
                    // Update civilization 2
                    updateCivilization('civ2', data.civ2);
                    
                    // Update diplomacy icons
                    updateDiplomacyIcons(data.civ1, data.civ2);
                })
                .catch(error => console.error('Error fetching game state:', error));
        }
        
        // Update a civilization's information
        function updateCivilization(prefix, civ) {
            document.getElementById(`${prefix}-name`).textContent = civ.name;
            document.getElementById(`${prefix}-era`).textContent = civ.era;
            
            // Update civilization image based on era
            const image = document.getElementById(`${prefix}-image`);
            image.className = `civ-image era-${civ.era.toLowerCase()}`;
            
            // Update image text based on era
            const eraText = {
                'Primitive': 'Campfire',
                'Ancient': 'Tent',
                'Medieval': 'Wooden Hut',
                'Modern': 'Small Buildings',
                'Future': 'Skyscrapers'
            };
            image.textContent = eraText[civ.era] || civ.era;
            
            // Update resources
            const resourcesDiv = document.getElementById(`${prefix}-resources`);
            resourcesDiv.innerHTML = '';
            
            // Resource definitions with max values for the bar
            const resource_defs = [
                { key: 'resources', name: 'Resources', max: 1000, icon: '💰' },
                { key: 'population', name: 'Population', max: 200, icon: '👥' },
                { key: 'military', name: 'Military', max: 100, icon: '⚔️' },
                { key: 'technology', name: 'Technology', max: 20, icon: '🔬' },
                { key: 'loyalty', name: 'Loyalty', max: 100, icon: '❤️' },
                { key: 'current_action_points', name: 'Action Points', max: civ.action_points, icon: '⚡' }
            ];
            
            resource_defs.forEach(def => {
                const value = def.key === 'current_action_points' ? civ[def.key] : civ[def.key];
                const maxValue = def.max;
                const percentage = Math.min(100, (value / maxValue) * 100);
                
                const resourceDiv = document.createElement('div');
                resourceDiv.className = 'resource';
                resourceDiv.innerHTML = `
                    <div class="resource-name">${def.icon} ${def.name}</div>
                    <div class="resource-bar">
                        <div class="resource-fill ${def.key.toLowerCase()}" style="width: ${percentage}%"></div>
                    </div>
                    <div class="resource-value">${value}/${maxValue}</div>
                `;
                resourcesDiv.appendChild(resourceDiv);
            });
        }
        
        // Update diplomacy icons
        function updateDiplomacyIcons(civ1, civ2) {
            const civ1Icon = document.getElementById('civ1-relation-icon');
            civ1Icon.className = `civ-icon era-${civ1.era.toLowerCase()}`;
            document.getElementById('civ1-relation-name').textContent = civ1.name;
            
            const civ2Icon = document.getElementById('civ2-relation-icon');
            civ2Icon.className = `civ-icon era-${civ2.era.toLowerCase()}`;
            document.getElementById('civ2-relation-name').textContent = civ2.name;
        }
        
        // Update game state every 2 seconds
        setInterval(updateGameState, 2000);
        
        // Initial update
        updateGameState();
    </script>
</body>
</html>
"""

# Custom HTTP request handler
class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global game_state
        
        if self.path == '/':
            # Return the HTML template
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == '/game_state':
            # Return the current game state as JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(game_state).encode('utf-8'))
        else:
            # Handle 404
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')

# Function to start the web server
def start_web_server():
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        print(f"Web GUI running at http://localhost:{PORT}")
        httpd.serve_forever()

# Function to update the game state
def update_game_state():
    global game_state, game
    
    while True:
        if game:
            # Update game state
            game_state["turn"] = game.current_turn
            game_state["civ1"] = game.civ1.to_dict()
            game_state["civ2"] = game.civ2.to_dict()
            game_state["game_ended"] = game.game_ended if hasattr(game, 'game_ended') else False
            game_state["reason"] = game.reason if hasattr(game, 'reason') else ""
        
        time.sleep(1)  # Update game state every second

# Function to run the game in a separate thread
def run_game():
    global game
    game = CivilizationGame()
    
    # Add game ended flag to the game object
    game.game_ended = False
    game.reason = ""
    
    try:
        for game.current_turn in range(1, game.max_turns + 1):
            # Check game end conditions
            game_ended, reason = game.check_game_end()
            if game_ended:
                game.game_ended = True
                game.reason = reason
                break
            
            # Diplomacy phase (trade and war)
            game.handle_diplomacy()
            
            # Civilization 1's turn
            game.handle_civilization_turn(game.civ1, game.civ2, game.ai1)
            time.sleep(1)  # Pause for readability
            
            # Update game state
            game_state["turn"] = game.current_turn
            game_state["civ1"] = game.civ1.to_dict()
            game_state["civ2"] = game.civ2.to_dict()
            
            # Civilization 2's turn
            game.handle_civilization_turn(game.civ2, game.civ1, game.ai2)
            time.sleep(1)  # Pause for readability
            
            # Update game state
            game_state["turn"] = game.current_turn
            game_state["civ1"] = game.civ1.to_dict()
            game_state["civ2"] = game.civ2.to_dict()
            
            # Save game state every 10 turns
            if game.current_turn % 10 == 0:
                game.save_game()
                
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
    finally:
        # Final state
        game.save_game()
        game.print_final_summary()
        
        # Set game ended flag
        game.game_ended = True
        game.reason = "Game completed"

if __name__ == "__main__":
    # Start the web server in a separate thread
    web_server_thread = threading.Thread(target=start_web_server)
    web_server_thread.daemon = True
    web_server_thread.start()
    
    # Start game state update thread
    game_state_thread = threading.Thread(target=update_game_state)
    game_state_thread.daemon = True
    game_state_thread.start()
    
    # Run the game in the main thread
    run_game()
