import pygame
import sys
import os

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Fonts
FONT_SMALL = pygame.font.Font(None, 20)
FONT_MEDIUM = pygame.font.Font(None, 24)
FONT_LARGE = pygame.font.Font(None, 32)
FONT_XLARGE = pygame.font.Font(None, 48)

# Icons (we'll use colored rectangles as placeholders for now)
RESOURCE_ICONS = {
    "resources": BLUE,
    "population": GREEN,
    "military": RED,
    "technology": YELLOW,
    "loyalty": ORANGE,
    "action_points": PURPLE
}

# Civilization era images (colored rectangles as placeholders)
ERA_IMAGES = {
    "Primitive": (50, 50, 50),      # Dark gray - Campfire
    "Ancient": (139, 69, 19),      # SaddleBrown - Tent
    "Medieval": (165, 42, 42),     # Brown - Wooden Hut
    "Modern": (220, 220, 220),     # LightGray - Small Buildings
    "Future": (135, 206, 235)       # SkyBlue - Skyscrapers
}

# Action icons (colored rectangles as placeholders)
ACTION_ICONS = {
    "trade": (0, 255, 255),         # Cyan - Trade
    "war": (255, 0, 0)              # Red - War
}

class CivilizationGUI:
    def __init__(self, game):
        self.game = game
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AI Civilization Simulation")
        self.clock = pygame.time.Clock()
        self.running = True
        
    def draw_text(self, text, font, color, x, y, center=False):
        """Draw text on the screen."""
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        self.screen.blit(text_surface, text_rect)
        return text_rect
    
    def draw_resource_bar(self, resource_name, value, max_value, x, y, width, height, color):
        """Draw a resource bar with label and value."""
        # Draw background
        pygame.draw.rect(self.screen, LIGHT_GRAY, (x, y, width, height))
        
        # Draw fill
        fill_width = int(width * (value / max_value))
        pygame.draw.rect(self.screen, color, (x, y, fill_width, height))
        
        # Draw border
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        
        # Draw resource icon
        icon_size = height - 4
        pygame.draw.rect(self.screen, color, (x + 2, y + 2, icon_size, icon_size))
        
        # Draw label and value
        text = f"{resource_name}: {value}/{max_value}"
        self.draw_text(text, FONT_SMALL, BLACK, x + height + 5, y + height // 2 - 10)
    
    def draw_civilization(self, civ, x, y, width, height):
        """Draw a civilization panel."""
        # Draw panel background
        pygame.draw.rect(self.screen, GRAY, (x, y, width, height))
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        
        # Draw civilization name and era
        self.draw_text(civ.name, FONT_LARGE, WHITE, x + 10, y + 10)
        self.draw_text(f"Era: {civ.era}", FONT_MEDIUM, WHITE, x + 10, y + 50)
        
        # Draw civilization image based on era
        era_color = ERA_IMAGES.get(civ.era, GRAY)
        image_size = 100
        pygame.draw.rect(self.screen, era_color, (x + width // 2 - image_size // 2, y + 80, image_size, image_size))
        
        # Draw resource bars
        resource_y = y + 200
        resource_spacing = 40
        
        self.draw_resource_bar("Resources", civ.resources, 1000, x + 20, resource_y, width - 40, 30, BLUE)
        resource_y += resource_spacing
        
        self.draw_resource_bar("Population", civ.population, 200, x + 20, resource_y, width - 40, 30, GREEN)
        resource_y += resource_spacing
        
        self.draw_resource_bar("Military", civ.military, 100, x + 20, resource_y, width - 40, 30, RED)
        resource_y += resource_spacing
        
        self.draw_resource_bar("Technology", civ.technology, 20, x + 20, resource_y, width - 40, 30, YELLOW)
        resource_y += resource_spacing
        
        self.draw_resource_bar("Loyalty", civ.loyalty, 100, x + 20, resource_y, width - 40, 30, ORANGE)
        resource_y += resource_spacing
        
        self.draw_resource_bar("Action Points", civ.current_action_points, civ.action_points, x + 20, resource_y, width - 40, 30, PURPLE)
    
    def draw_diplomacy(self, civ1, civ2, x, y, width, height):
        """Draw diplomacy panel."""
        # Draw panel background
        pygame.draw.rect(self.screen, DARK_GRAY, (x, y, width, height))
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        
        # Draw title
        self.draw_text("Diplomacy", FONT_LARGE, WHITE, x + 10, y + 10)
        
        # Draw civilization relationship
        mid_x = x + width // 2
        mid_y = y + height // 2
        
        # Draw civ1 icon
        pygame.draw.rect(self.screen, ERA_IMAGES.get(civ1.era, GRAY), (x + 50, mid_y - 25, 50, 50))
        self.draw_text(civ1.name, FONT_MEDIUM, WHITE, x + 30, mid_y + 40, center=True)
        
        # Draw civ2 icon
        pygame.draw.rect(self.screen, ERA_IMAGES.get(civ2.era, GRAY), (x + width - 100, mid_y - 25, 50, 50))
        self.draw_text(civ2.name, FONT_MEDIUM, WHITE, x + width - 70, mid_y + 40, center=True)
        
        # Draw relationship line
        pygame.draw.line(self.screen, WHITE, (x + 100, mid_y), (x + width - 100, mid_y), 2)
        
        # Draw action icons (trade and war)
        trade_icon = pygame.Rect(mid_x - 60, mid_y - 25, 50, 50)
        war_icon = pygame.Rect(mid_x + 10, mid_y - 25, 50, 50)
        
        pygame.draw.rect(self.screen, ACTION_ICONS["trade"], trade_icon)
        pygame.draw.rect(self.screen, ACTION_ICONS["war"], war_icon)
        
        self.draw_text("Trade", FONT_SMALL, WHITE, mid_x - 35, mid_y + 30, center=True)
        self.draw_text("War", FONT_SMALL, WHITE, mid_x + 35, mid_y + 30, center=True)
    
    def draw_turn_info(self, turn, x, y, width, height):
        """Draw turn information panel."""
        # Draw panel background
        pygame.draw.rect(self.screen, DARK_GRAY, (x, y, width, height))
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        
        # Draw turn number
        self.draw_text(f"Turn {turn}", FONT_XLARGE, WHITE, x + width // 2, y + height // 2, center=True)
    
    def handle_events(self):
        """Handle Pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def draw(self):
        """Draw the entire game screen."""
        # Clear screen
        self.screen.fill(BLACK)
        
        # Calculate panel positions
        civ_width = 450
        civ_height = 500
        diplomacy_width = 900
        diplomacy_height = 200
        turn_width = 900
        turn_height = 80
        
        # Draw civilization panels
        self.draw_civilization(self.game.civ1, 20, 20, civ_width, civ_height)
        self.draw_civilization(self.game.civ2, SCREEN_WIDTH - civ_width - 20, 20, civ_width, civ_height)
        
        # Draw diplomacy panel
        diplomacy_x = (SCREEN_WIDTH - diplomacy_width) // 2
        diplomacy_y = civ_height + 40
        self.draw_diplomacy(self.game.civ1, self.game.civ2, diplomacy_x, diplomacy_y, diplomacy_width, diplomacy_height)
        
        # Draw turn information
        turn_x = (SCREEN_WIDTH - turn_width) // 2
        turn_y = diplomacy_y + diplomacy_height + 20
        self.draw_turn_info(self.game.current_turn, turn_x, turn_y, turn_width, turn_height)
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """Run the GUI loop."""
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

# Main function to test the GUI
if __name__ == "__main__":
    # Import Game class for testing
    from game import CivilizationGame
    
    # Create a game instance
    game = CivilizationGame()
    
    # Create and run the GUI
    gui = CivilizationGUI(game)
    gui.run()