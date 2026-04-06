"""Data Orb - collectible items that the player gathers"""
import pygame
import math
import random

NEON_YELLOW = (255, 255, 0)
NEON_CYAN = (0, 255, 255)
NEON_MAGENTA = (255, 0, 255)
WHITE = (255, 255, 255)
GOLD = (255, 200, 0)

# Neon palette for color cycling
NEON_PALETTE = [
  (255, 255, 0),   # Yellow
  (0, 255, 255),   # Cyan
  (255, 0, 255),   # Magenta
  (255, 200, 0),   # Gold
]


class DataOrb:
  def __init__(self, x, y):
    self.position = pygame.math.Vector2(x, y)
    self.size = 15
    self.pulse_phase = random.uniform(0, math.pi * 2)
    self.rotation = 0
    self.color_index = random.randint(0, len(NEON_PALETTE) - 1)
    self.x = x  # For particle compatibility
    self.y = y  # For particle compatibility

  def update(self, dt):
    """Animate the orb"""
    self.pulse_phase += dt * 3
    self.rotation += dt * 2
    # Cycle through colors slowly
    self.color_index = int(self.pulse_phase / 2) % len(NEON_PALETTE)

  def get_color(self):
    """Get current neon color"""
    return NEON_PALETTE[self.color_index % len(NEON_PALETTE)]

  def draw(self, screen, camera):
    """Draw the glowing data orb with enhanced neon effects"""
    offset_x, offset_y = camera
    x = int(self.position.x - offset_x)
    y = int(self.position.y - offset_y)

    # Skip if off screen with margin
    if x < -50 or x > screen.get_width() + 50 or y < -50 or y > screen.get_height() + 50:
      return

    color = self.get_color()
    
    # Pulse effect
    pulse = math.sin(self.pulse_phase) * 0.3 + 1.0
    radius = int(self.size * pulse)

    # MULTI-LAYER GLOW EFFECT
    # Layer 1: Wide outer glow
    for i in range(5, 0, -1):
      glow_radius = radius + i * 12
      alpha = int(20 / i)
      s = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
      pygame.draw.circle(s, (*color, alpha), (glow_radius, glow_radius), glow_radius - 2)
      screen.blit(s, (x - glow_radius, y - glow_radius))

    # Layer 2: Medium glow
    for i in range(3, 0, -1):
      glow_radius = radius + i * 6
      alpha = int(40 / i)
      s = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
      pygame.draw.circle(s, (*color, alpha), (glow_radius, glow_radius), glow_radius - 1)
      screen.blit(s, (x - glow_radius, y - glow_radius))

    # Layer 3: Inner bright core
    s = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(s, (*WHITE, 180), (radius + 2, radius + 2), radius // 2 + 2)
    pygame.draw.circle(s, (*color, 220), (radius + 2, radius + 2), radius // 2)
    screen.blit(s, (x - radius - 2, y - radius - 2))

    # Outer ring (rotating) with glow
    points = []
    for i in range(6):
      angle = self.rotation + i * math.pi / 3
      points.append((
        x + math.cos(angle) * (radius + 5),
        y + math.sin(angle) * (radius + 5)
      ))
    
    # Draw ring with thick neon line
    pygame.draw.polygon(screen, (*color, 100), points, 1)
    pygame.draw.polygon(screen, color, points, 2)

    # Center symbol (data bit) with glow
    pygame.draw.circle(screen, (*color, 100), (x, y), 8)
    pygame.draw.circle(screen, WHITE, (x, y), 5)
    pygame.draw.circle(screen, color, (x, y), 3)

    # Sparkle effect
    sparkle_offset = self.pulse_phase * 2
    for i in range(4):
      angle = sparkle_offset + i * math.pi / 2
      sparkle_dist = radius + 15 + math.sin(self.pulse_phase * 3 + i) * 5
      sx = x + math.cos(angle) * sparkle_dist
      sy = y + math.sin(angle) * sparkle_dist
      sparkle_alpha = int(150 + math.sin(self.pulse_phase * 4 + i) * 100)
      pygame.draw.circle(screen, (*WHITE, sparkle_alpha), (int(sx), int(sy)), 2)