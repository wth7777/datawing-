"""Enemy class - chasers that hunt the player"""
import pygame
import math
import random

NEON_RED = (255, 50, 50)
NEON_ORANGE = (255, 100, 0)
WHITE = (255, 255, 255)

class Enemy:
    def __init__(self, x, y):
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.angle = 0
        self.size = 15
        self.speed = 200
        self.max_speed = 300
        
    def update(self, dt, player_pos):
        """Update enemy AI - chase the player"""
        # Calculate direction to player
        direction = player_pos - self.position
        distance = direction.length()
        
        if distance > 0:
            direction = direction.normalize()
            self.angle = math.atan2(direction.y, direction.x)
        
        # Move toward player
        self.velocity = direction * self.speed
        self.position += self.velocity * dt
        
        # Clamp speed
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed
    
    def check_collision(self, ship):
        """Check collision with ship - game over"""
        dist = self.position.distance_to(ship.position)
        return dist < (self.size + ship.size)
    
    def draw(self, screen, camera):
        """Draw enemy"""
        offset_x, offset_y = camera
        sx = int(self.position.x - offset_x)
        sy = int(self.position.y - offset_y)
        
        # Skip if off screen
        if sx < -50 or sx > screen.get_width() + 50 or sy < -50 or sy > screen.get_height() + 50:
            return
        
        # Draw as diamond shape
        points = []
        for i in range(4):
            a = self.angle + i * (math.pi / 2)
            points.append((
                sx + math.cos(a) * self.size,
                sy + math.sin(a) * self.size
            ))
        
        pygame.draw.polygon(screen, NEON_RED, points)
        pygame.draw.polygon(screen, WHITE, points, 2)
        
        # Inner glow
        pygame.draw.circle(screen, NEON_ORANGE, (sx, sy), 5)