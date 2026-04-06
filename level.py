"""
Level class - walls and boundaries
"""
import pygame
import random

NEON_CYAN = (0, 255, 255)
NEON_MAGENTA = (255, 0, 255)
DARK_PURPLE = (30, 10, 50)

class Level:
    def __init__(self):
        self.width = 2000
        self.height = 1500
        
        # Generate some walls
        self.walls = []
        self.checkpoints = []
        self.start_pos = (self.width // 2, self.height // 2)
        self.generate_walls()
        self.generate_checkpoints()

    def generate_walls(self):
        """Create level layout"""
        # Border walls
        self.walls = [
            # Top
            {'x': 0, 'y': 0, 'w': self.width, 'h': 20},
            # Bottom
            {'x': 0, 'y': self.height - 20, 'w': self.width, 'h': 20},
            # Left
            {'x': 0, 'y': 0, 'w': 20, 'h': self.height},
            # Right
            {'x': self.width - 20, 'y': 0, 'w': 20, 'h': self.height},
        ]
        
        # Add some random obstacles
        for _ in range(8):
            w = random.randint(50, 150)
            h = random.randint(50, 150)
            x = random.randint(100, self.width - w - 100)
            y = random.randint(100, self.height - h - 100)
            self.walls.append({'x': x, 'y': y, 'w': w, 'h': h})

    def generate_checkpoints(self):
        """Create checkpoints for time trial mode"""
        margin = 150
        # Checkpoint positions around the level
        self.checkpoints = [
            {'x': margin, 'y': margin, 'w': 80, 'h': 80, 'passed': False, 'order': 0},  # Top-left
            {'x': self.width - margin - 80, 'y': margin, 'w': 80, 'h': 80, 'passed': False, 'order': 1},  # Top-right
            {'x': self.width - margin - 80, 'y': self.height - margin - 80, 'w': 80, 'h': 80, 'passed': False, 'order': 2},  # Bottom-right
            {'x': margin, 'y': self.height - margin - 80, 'w': 80, 'h': 80, 'passed': False, 'order': 3},  # Bottom-left
        ]

    def check_collisions(self, ship):
        """Check and resolve ship collisions with walls"""
        ship_rect = pygame.Rect(
            ship.position.x - ship.size,
            ship.position.y - ship.size,
            ship.size * 2,
            ship.size * 2
        )

        for wall in self.walls:
            wall_rect = pygame.Rect(wall['x'], wall['y'], wall['w'], wall['h'])

            if ship_rect.colliderect(wall_rect):
                # Find closest edge and push out
                # Calculate overlap on each side
                ship_center = ship.position
                wall_center = pygame.math.Vector2(
                    wall['x'] + wall['w'] / 2,
                    wall['y'] + wall['h'] / 2
                )

                dx = ship_center.x - wall_center.x
                dy = ship_center.y - wall_center.y

                overlap_x = (ship.size + wall['w'] / 2) - abs(dx)
                overlap_y = (ship.size + wall['h'] / 2) - abs(dy)

                if overlap_x < overlap_y:
                    # Push horizontally
                    if dx > 0:
                        ship.position.x += overlap_x
                    else:
                        ship.position.x -= overlap_x
                    ship.velocity.x *= -0.5  # Bounce
                else:
                    # Push vertically
                    if dy > 0:
                        ship.position.y += overlap_y
                    else:
                        ship.position.y -= overlap_y
                    ship.velocity.y *= -0.5  # Bounce

    def draw(self, screen, camera):
        """Draw level walls"""
        offset_x, offset_y = camera

        for wall in self.walls:
            x = int(wall['x'] - offset_x)
            y = int(wall['y'] - offset_y)
            w = wall['w']
            h = wall['h']

            # Only draw if visible
            if -w < x < screen.get_width() and -h < y < screen.get_height():
                # Fill
                pygame.draw.rect(screen, DARK_PURPLE, (x, y, w, h))
                # Neon outline
                pygame.draw.rect(screen, NEON_CYAN, (x, y, w, h), 2)
                # Corner accents
                pygame.draw.circle(screen, NEON_MAGENTA, (x, y), 4)
                pygame.draw.circle(screen, NEON_MAGENTA, (x + w, y), 4)
                pygame.draw.circle(screen, NEON_MAGENTA, (x, y + h), 4)
                pygame.draw.circle(screen, NEON_MAGENTA, (x + w, y + h), 4)

    def check_checkpoint(self, ship):
        """Check if ship passed a checkpoint"""
        for cp in self.checkpoints:
            if not cp['passed']:
                cx = cp['x'] + cp['w'] // 2
                cy = cp['y'] + cp['h'] // 2
                dist = ship.position.distance_to(pygame.math.Vector2(cx, cy))
                if dist < 50:
                    cp['passed'] = True
                    return True
        return False

    def reset_checkpoints(self):
        """Reset all checkpoints for new time trial"""
        for cp in self.checkpoints:
            cp['passed'] = False

    def all_checkpoints_passed(self):
        """Check if all checkpoints passed"""
        return all(cp['passed'] for cp in self.checkpoints)

    def draw_checkpoints(self, screen, camera):
        """Draw checkpoints on screen"""
        offset_x, offset_y = camera
        for cp in self.checkpoints:
            x = int(cp['x'] - offset_x)
            y = int(cp['y'] - offset_y)
            w = cp['w']
            h = cp['h']
            
            # Only draw if visible
            if -w < x < screen.get_width() and -h < y < screen.get_height():
                if cp['passed']:
                    color = NEON_MAGENTA  # Passed = magenta
                else:
                    color = NEON_CYAN  # Not passed = cyan
                
                # Pulsing effect
                import math
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 0.5 + 0.5
                
                pygame.draw.rect(screen, color, (x, y, w, h), 2)
                # Draw checkpoint number
                font = pygame.font.Font(None, 24)
                num_text = font.render(str(cp['order'] + 1), True, color)
                screen.blit(num_text, (x + w//2 - 5, y + h//2 - 8))