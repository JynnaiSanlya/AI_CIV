import http.server
import socketserver
import json
import threading
import time
import os
from game import CivilizationGame

# Web server settings
PORT = 8000

# Game state to be sent to the client
game_state = {
    "turn": 0,
    "civ1": None,
    "civ2": None,
    "game_ended": False,
    "reason": "",
    "model_info": {
        "civ1": "",
        "civ2": ""
    },
    "action_history": {
        "civ1": [],
        "civ2": []
    },
    "diplomacy_history": [],
    "era_events": {
        "civ1": [],
        "civ2": []
    }
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
        .resource-fill.culture { background-color: #9b59b6; } /* Purple */
        .resource-fill.loyalty { background-color: #e67e22; } /* Orange */
        .resource-fill.action_points { background-color: #8e44ad; } /* Dark Purple */
        
        /* AI Model Display */
        .ai-model {
            font-size: 14px;
            color: #95a5a6;
            margin-bottom: 15px;
        }
        
        /* Flag Display */
        .civ-flag {
            width: 30px;
            height: 20px;
            margin-right: 10px;
            display: inline-block;
            vertical-align: middle;
            border-radius: 2px;
        }
        
        /* Civ Image Improvements */
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
            background-size: cover;
            background-position: center;
            position: relative;
        }
        
        /* Era-specific images */
        .era-primitive { background-image: url('/assets/images/EraLives/Primitive.jpg'); } /* Primitive */
        .era-classical { background-image: url('/assets/images/EraLives/Classical.jpg'); } /* Classical */
        .era-medieval { background-image: url('/assets/images/EraLives/Medieval.jpg'); } /* Medieval */
        .era-renaissance { background-image: url('/assets/images/EraLives/Renaissance.jpg'); } /* Renaissance */
        .era-industrial { background-image: url('/assets/images/EraLives/Industrial.jpg'); } /* Industrial */
        .era-modern { background-image: url('/assets/images/EraLives/Modern.jpg'); } /* Modern */
        .era-information { background-image: url('/assets/images/EraLives/Information.jpg'); } /* Information */
        .era-future { background-image: url('/assets/images/EraLives/Future.jpg'); } /* Future */
        
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
        
        /* Action History */
        .action-history {
            background-color: #2c2c2c;
            border: 2px solid #444;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .action-history-title {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #4a90e2;
        }
        
        .action-item {
            background-color: #333;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        .action-item .turn {
            color: #f39c12;
            font-weight: bold;
        }
        
        .action-item .action {
            color: #3498db;
        }
        
        /* Diplomacy History */
        .diplomacy-history {
            background-color: #2c2c2c;
            border: 2px solid #444;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .diplomacy-history-title {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #4a90e2;
        }
        
        .diplomacy-item {
            background-color: #333;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        .diplomacy-item .turn {
            color: #f39c12;
            font-weight: bold;
        }
        
        .diplomacy-item.trade {
            border-left: 4px solid #00ffff;
        }
        
        .diplomacy-item.war {
            border-left: 4px solid #ff0000;
        }
        
        .diplomacy-item.war_declaration {
            border-left: 4px solid #e67e22;
        }
        
        /* Era Events */
        .era-events {
            background-color: #2c2c2c;
            border: 2px solid #444;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .era-events-title {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #4a90e2;
        }
        
        .era-event-item {
            background-color: #333;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            font-size: 14px;
            border-left: 4px solid #9b59b6; /* Purple for era events */
        }
        
        .era-event-item .turn {
            color: #f39c12;
            font-weight: bold;
        }
        
        .era-event-item .event-name {
            color: #9b59b6;
            font-weight: bold;
        }
        
        .game-over {
            text-align: center;
            font-size: 36px;
            color: #e74c3c;
            margin-top: 50px;
        }
        
        .final-results {
            background-color: #2c2c2c;
            border: 2px solid #444;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
            text-align: center;
        }
        
        .final-results-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #4a90e2;
        }
        
        .final-scores {
            display: flex;
            justify-content: center;
            gap: 50px;
            margin-bottom: 20px;
        }
        
        .civ-score {
            text-align: center;
        }
        
        .civ-score-name {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .civ-score-value {
            font-size: 36px;
            font-weight: bold;
        }
        
        .winner-announcement {
            font-size: 28px;
            font-weight: bold;
            margin-top: 20px;
            color: #f39c12;
        }
        
        .winning-margin {
            font-size: 18px;
            margin-top: 10px;
            color: #95a5a6;
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
                <div class="civ-name" id="civ1-name"><div class="civ-flag" id="civ1-flag"></div>Civilization 1</div>
                <div class="ai-model" id="civ1-model">AI Model: qwen-flash</div>
                <div class="civ-era" id="civ1-era">Primitive</div>
                <div class="civ-image" id="civ1-image">Campfire</div>
                <div class="resources" id="civ1-resources"></div>
                <div class="action-history">
                    <div class="action-history-title">Recent Actions</div>
                    <div id="civ1-action-history"></div>
                </div>
            </div>
            
            <div class="civ-panel" id="civ2-panel">
                <div class="civ-name" id="civ2-name"><div class="civ-flag" id="civ2-flag"></div>Civilization 2</div>
                <div class="ai-model" id="civ2-model">AI Model: qwen-plus</div>
                <div class="civ-era" id="civ2-era">Primitive</div>
                <div class="civ-image" id="civ2-image">Campfire</div>
                <div class="resources" id="civ2-resources"></div>
                <div class="action-history">
                    <div class="action-history-title">Recent Actions</div>
                    <div id="civ2-action-history"></div>
                </div>
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
        
        <div class="diplomacy-history">
            <div class="diplomacy-history-title">Diplomacy History</div>
            <div id="diplomacy-history-content"></div>
        </div>
        
        <div class="era-events">
            <div class="era-events-title">Era Events</div>
            <div id="era-events-content"></div>
        </div>
        
        <div id="game-over" class="game-over" style="display: none;"></div>
        
        <div id="final-results" class="final-results" style="display: none;">
            <div class="final-results-title">Final Results</div>
            <div class="final-scores" id="final-scores"></div>
            <div class="winner-announcement" id="winner-announcement"></div>
            <div class="winning-margin" id="winning-margin"></div>
        </div>
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
                        
                        // Display final results if available
                        if (data.final_scores && data.winner) {
                            const finalResultsDiv = document.getElementById('final-results');
                            const finalScoresDiv = document.getElementById('final-scores');
                            const winnerAnnouncementDiv = document.getElementById('winner-announcement');
                            const winningMarginDiv = document.getElementById('winning-margin');
                            
                            // Clear existing content
                            finalScoresDiv.innerHTML = '';
                            
                            // Create score display for each civilization
                            for (const civName in data.final_scores) {
                                const civScoreDiv = document.createElement('div');
                                civScoreDiv.className = 'civ-score';
                                
                                civScoreDiv.innerHTML = `
                                    <div class="civ-score-name">${civName}</div>
                                    <div class="civ-score-value">${data.final_scores[civName]}</div>
                                `;
                                
                                finalScoresDiv.appendChild(civScoreDiv);
                            }
                            
                            // Set winner announcement
                            if (data.winner === 'Tie') {
                                winnerAnnouncementDiv.textContent = 'The game ended in a tie!';
                                winningMarginDiv.textContent = '';
                            } else {
                                winnerAnnouncementDiv.textContent = `${data.winner} wins!`;
                                winningMarginDiv.textContent = `Winning Margin: ${data.winning_margin} points`;
                            }
                            
                            // Show final results
                            finalResultsDiv.style.display = 'block';
                        }
                        
                        return;
                    }
                    
                    // Update turn
                    document.getElementById('turn').textContent = data.turn;
                    
                    // Update civilization 1 with model info and action history
                    updateCivilization('civ1', data.civ1, data.model_info.civ1, data.action_history.civ1);
                    
                    // Update civilization 2 with model info and action history
                    updateCivilization('civ2', data.civ2, data.model_info.civ2, data.action_history.civ2);
                    
                    // Update diplomacy icons
                    updateDiplomacyIcons(data.civ1, data.civ2);
                    
                    // Update diplomacy history
                    updateDiplomacyHistory(data.diplomacy_history);
                    
                    // Update era events
                    if (data.era_events) {
                        updateEraEvents(data.era_events);
                    }
                })
                .catch(error => console.error('Error fetching game state:', error));
        }
        
        // Update a civilization's information
        function updateCivilization(prefix, civ, modelName, actionHistory) {
            // Update name with flag
            const nameElement = document.getElementById(`${prefix}-name`);
            nameElement.innerHTML = `<div class="civ-flag" id="${prefix}-flag"></div>${civ.name}`;
            
            // Update AI model
            document.getElementById(`${prefix}-model`).textContent = `AI Model: ${modelName}`;
            
            // Update era
            document.getElementById(`${prefix}-era`).textContent = civ.era;
            
            // Update civilization image based on era
            const image = document.getElementById(`${prefix}-image`);
            image.className = `civ-image era-${civ.era.toLowerCase()}`;
            
            // Update image text based on era (but hide it since we're using background images)
            image.textContent = '';
            
            // Update resources
            const resourcesDiv = document.getElementById(`${prefix}-resources`);
            resourcesDiv.innerHTML = '';
            
            // Resource definitions with max values for the bar
            const resource_defs = [
                { key: 'resources', name: 'Resources', max: 1000, icon: '💰' },
                { key: 'population', name: 'Population', max: 200, icon: '👥' },
                { key: 'military', name: 'Military', max: 100, icon: '⚔️' },
                { key: 'technology', name: 'Technology', max: 20, icon: '🔬' },
                { key: 'culture', name: 'Culture', max: 200, icon: '🎭' },
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
            
            // Update action history
            updateActionHistory(prefix, actionHistory);
            
            // Update flag color
            updateFlag(prefix, civ.color);
        }
        
        // Update civilization flag color
        function updateFlag(prefix, color) {
            const flag = document.getElementById(`${prefix}-flag`);
            flag.style.backgroundColor = color;
        }
        
        // Update action history for a civilization
        function updateActionHistory(prefix, actionHistory) {
            const historyDiv = document.getElementById(`${prefix}-action-history`);
            historyDiv.innerHTML = '';
            
            // Get last 5 turns of actions
            const recentActions = actionHistory.slice(-5).reverse();
            
            recentActions.forEach(turnActions => {
                const turnDiv = document.createElement('div');
                turnDiv.className = 'action-item';
                
                let actionsHTML = `<div class="turn">Turn ${turnActions.turn}</div>`;
                
                turnActions.actions.forEach(action => {
                    actionsHTML += `<div class="action">${action.action} ${action.amount}: ${action.result}</div>`;
                });
                
                turnDiv.innerHTML = actionsHTML;
                historyDiv.appendChild(turnDiv);
            });
        }
        
        // Update diplomacy history
        function updateDiplomacyHistory(diplomacyHistory) {
            const historyDiv = document.getElementById('diplomacy-history-content');
            historyDiv.innerHTML = '';
            
            // Get last 10 diplomacy events
            const recentEvents = diplomacyHistory.slice(-10).reverse();
            
            recentEvents.forEach(event => {
                const eventDiv = document.createElement('div');
                eventDiv.className = `diplomacy-item ${event.type}`;
                
                let eventHTML = `<div class="turn">Turn ${event.turn}</div>`;
                
                if (event.type === 'trade') {
                    eventHTML += `<div>Trade: ${event.proposer} ↔ ${event.responder}</div>`;
                    eventHTML += `<div>Offer: ${event.offer.resources} resources, ${event.offer.population} population, ${event.offer.technology} technology</div>`;
                    eventHTML += `<div>Request: ${event.request.resources} resources, ${event.request.population} population, ${event.request.technology} technology</div>`;
                    eventHTML += `<div>Result: ${event.result}</div>`;
                } else if (event.type === 'war') {
                    eventHTML += `<div>War: ${event.attacker} → ${event.defender}</div>`;
                    eventHTML += `<div>Result: ${event.result}</div>`;
                    eventHTML += `<div>Plunder: ${event.plunder.resources} resources, ${event.plunder.population} population</div>`;
                } else if (event.type === 'war_declaration') {
                    eventHTML += `<div>War Declaration: ${event.attacker} → ${event.defender}</div>`;
                    eventHTML += `<div>Result: ${event.result}</div>`;
                    if (event.reason) {
                        eventHTML += `<div>Reason: ${event.reason}</div>`;
                    }
                }
                
                eventDiv.innerHTML = eventHTML;
                historyDiv.appendChild(eventDiv);
            });
        }
        
        // Update era events
        function updateEraEvents(eraEvents) {
            const eventsDiv = document.getElementById('era-events-content');
            eventsDiv.innerHTML = '';
            
            // Combine events from both civilizations
            const allEvents = [];
            for (const civ in eraEvents) {
                eraEvents[civ].forEach(event => {
                    allEvents.push({
                        ...event,
                        civ: civ
                    });
                });
            }
            
            // Sort events by turn (newest first)
            allEvents.sort((a, b) => b.turn - a.turn);
            
            // Get last 10 events
            const recentEvents = allEvents.slice(0, 10);
            
            recentEvents.forEach(event => {
                const eventDiv = document.createElement('div');
                eventDiv.className = 'era-event-item';
                
                let eventHTML = `<div class="turn">Turn ${event.turn}</div>`;
                eventHTML += `<div class="event-name">${event.civ === 'civ1' ? 'Atlantis' : 'Eldorado'}: ${event.name}</div>`;
                eventHTML += `<div>${event.description}</div>`;
                eventHTML += `<div>Cost: ${JSON.stringify(event.cost)}</div>`;
                eventHTML += `<div>Reward: ${JSON.stringify(event.reward)}</div>`;
                eventHTML += `<div>Result: ${event.result}</div>`;
                
                eventDiv.innerHTML = eventHTML;
                eventsDiv.appendChild(eventDiv);
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
        elif self.path.startswith('/assets/'):
            # Serve static files from assets directory
            # Get the file path without the leading slash
            relative_path = self.path[1:]  # Remove leading slash
            
            # Construct the full path using the current script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(script_dir, relative_path)
            
            if os.path.exists(full_path):
                # Determine content type based on file extension
                ext = os.path.splitext(full_path)[1].lower()
                content_type = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.css': 'text/css',
                    '.js': 'application/javascript'
                }.get(ext, 'application/octet-stream')
                
                # Debug: Print the path being served
                print(f"Serving static file: {full_path}")
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                # Debug: Print missing file path
                print(f"Static file not found: {full_path}")
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'404 Not Found')
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
            
            # Update model information
            if hasattr(game, 'model_info'):
                game_state["model_info"] = game.model_info
            
            # Update action history
            if hasattr(game, 'action_history'):
                game_state["action_history"] = game.action_history
            
            # Update diplomacy history
            if hasattr(game, 'diplomacy_history'):
                game_state["diplomacy_history"] = game.diplomacy_history
            
            # Update era events history
            if hasattr(game, 'era_events_history'):
                # Convert era events history to UI format
                era_events_ui = {
                    "civ1": [],
                    "civ2": []
                }
                for event in game.era_events_history:
                    if event["civ"] == "civ1":
                        era_events_ui["civ1"].append(event)
                    elif event["civ"] == "civ2":
                        era_events_ui["civ2"].append(event)
                game_state["era_events"] = era_events_ui
            
            # Update final results if game ended
            if hasattr(game, 'game_ended') and game.game_ended:
                if hasattr(game, 'winner'):
                    game_state["winner"] = game.winner
                if hasattr(game, 'final_scores'):
                    game_state["final_scores"] = game.final_scores
                if hasattr(game, 'winning_score'):
                    game_state["winning_score"] = game.winning_score
                if hasattr(game, 'losing_score'):
                    game_state["losing_score"] = game.losing_score
                if hasattr(game, 'winning_margin'):
                    game_state["winning_margin"] = game.winning_margin
        
        time.sleep(1)  # Update game state every second

# Function to run the game in a separate thread
def run_game():
    global game
    game = CivilizationGame()
    
    # Add game ended flag to the game object
    game.game_ended = False
    game.reason = ""
    
    # Ensure model_info, action_history, and diplomacy_history are initialized
    if not hasattr(game, 'model_info'):
        game.model_info = {
            "civ1": "qwen-flash",
            "civ2": "qwen-plus"
        }
    
    if not hasattr(game, 'action_history'):
        game.action_history = {
            "civ1": [],
            "civ2": []
        }
    
    if not hasattr(game, 'diplomacy_history'):
        game.diplomacy_history = []
    
    try:
        for game.current_turn in range(1, game.max_turns + 1):
            # Check game end conditions
            game_ended, reason = game.check_game_end()
            if game_ended:
                game.game_ended = True
                game.reason = reason
                break
            
            # Handle era events for both civilizations
            game.handle_era_event(game.civ1, game.ai1, "civ1")
            game.handle_era_event(game.civ2, game.ai2, "civ2")
            
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
            
            # Apply culture influence after both turns
            game.civ1.apply_culture_influence(game.civ2)
            game.civ2.apply_culture_influence(game.civ1)
            
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
        
        # Calculate final scores and winner
        score1 = game.civ1.calculate_score()
        score2 = game.civ2.calculate_score()
        
        if score1 > score2:
            game.winner = game.civ1.name
            game.winning_score = score1
            game.losing_score = score2
            game.winning_margin = score1 - score2
        elif score2 > score1:
            game.winner = game.civ2.name
            game.winning_score = score2
            game.losing_score = score1
            game.winning_margin = score2 - score1
        else:
            game.winner = "Tie"
            game.winning_score = score1
            game.losing_score = score2
            game.winning_margin = 0
        
        # Store final scores for display
        game.final_scores = {
            game.civ1.name: score1,
            game.civ2.name: score2
        }

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
