"""Data Wing-style top-down neon spaceship game
Momentum-based flying with drifting controls
Touch controls: Virtual joystick left, thrust button right
"""
import pygame
import math
import random
from ship import Ship
from level import Level
from particles import ParticleSystem
from data_orb import DataOrb

# Colors
BLACK = (5, 5, 15)
NEON_CYAN = (0, 255, 255)
NEON_MAGENTA = (255, 0, 255)
NEON_YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
ORANGE = (255, 150, 0)
DARK_GRAY = (40, 40, 50)

# Color cycling for neon effects
NEON_PALETTE = [
  (0, 255, 255),   # Cyan
  (255, 0, 255),   # Magenta
  (255, 255, 0),   # Yellow
  (0, 255, 150),   # Mint
  (255, 100, 200), # Pink
]

def get_neon_color(time_offset=0, index=0):
  """Get a cycling neon color based on time"""
  t = pygame.time.get_ticks() / 1000.0 + time_offset
  cycle = int(t * 2) % len(NEON_PALETTE)
  return NEON_PALETTE[(cycle + index) % len(NEON_PALETTE)]


class ScorePopup:
  """Floating score popup with neon effect"""
  def __init__(self, x, y, score, color):
    self.x = x
    self.y = y
    self.score = score
    self.color = color
    self.life = 1.0
    self.vy = -80  # Float upward

  def update(self, dt):
    self.y += self.vy * dt
    self.life -= dt * 1.5
    return self.life > 0

  def draw(self, screen, camera):
    x = int(self.x - camera[0])
    y = int(self.y - camera[1])
    if 0 <= x <= screen.get_width() and 0 <= y <= screen.get_height():
      alpha = int(self.life * 255)
      font = pygame.font.Font(None, 56)
      text = font.render(f"+{self.score}", True, self.color)
      text.set_alpha(alpha)
      # Draw glow
      glow_surf = pygame.Surface((text.get_width() + 20, text.get_height() + 20), pygame.SRCALPHA)
      pygame.draw.rect(glow_surf, (*self.color, alpha // 3), glow_surf.get_rect(), border_radius=10)
      screen.blit(glow_surf, (x - 10, y - 10))
      screen.blit(text, (x, y))


class Game:
  def __init__(self):
    pygame.init()
    pygame.display.set_caption("NEON DRIFT")

    # Enable touch inputs
    pygame.event.set_allowed(pygame.FINGERDOWN)
    pygame.event.set_allowed(pygame.FINGERUP)
    pygame.event.set_allowed(pygame.FINGERMOTION)

    self.width = 1280
    self.height = 720
    self.screen = pygame.display.set_mode((self.width, self.height))
    self.clock = pygame.time.Clock()
    self.ticks = 60
    self.running = True

    # Game objects
    self.ship = Ship(self.width // 2, self.height // 2)
    self.particles = ParticleSystem()
    self.level = Level()
    self.orbs = []

    # Generate initial orbs
    for _ in range(8):
      self.spawn_orb()

    # Camera offset
    self.camera = [0, 0]
    self.score = 0

    # Font
    self.font = pygame.font.Font(None, 48)
    self.small_font = pygame.font.Font(None, 24)

    # Touch controls
    self.touch_points = {}  # finger_id -> position
    self.is_using_touch = False
    self.joystick_active = False
    self.thrust_active = False

    # Touch zones
    self.touch_steer_center = (self.width * 0.25, self.height * 0.7)
    self.touch_steer_radius = 100
    self.thrust_button_pos = (self.width * 0.8, self.height * 0.7)
    self.thrust_button_radius = 80

    # Mouse fallback
    self.mouse_pos = (self.width // 2, self.height // 2)
    self.mouse_thrusting = False

    # Time trial
    self.time_trial_mode = False
    self.time_trial_time = 0
    self.best_time = None
    self.checkpoints_passed = 0

    # Enemies
    self.enemies = []
    self.enemy_spawn_timer = 0
    self.enemies_active = False

    # Score popups
    self.score_popups = []

  def spawn_orb(self):
    """Spawn a data orb at random position"""
    x = random.randint(100, self.width - 100)
    y = random.randint(100, self.height - 100)
    self.orbs.append(DataOrb(x, y))

  def spawn_enemy(self):
    """Spawn an enemy (for future enemy system)"""
    from enemy import Enemy
    side = random.choice(['top', 'bottom', 'left', 'right'])
    if side == 'top':
      x, y = random.randint(0, self.width), -50
    elif side == 'bottom':
      x, y = random.randint(0, self.width), self.height + 50
    elif side == 'left':
      x, y = -50, random.randint(0, self.height)
    else:
      x, y = self.width + 50, random.randint(0, self.height)
    return Enemy(x, y)

  def handle_input(self):
    """Handle user input - mouse and touch"""
    # Reset touch state each frame
    self.joystick_active = False
    self.thrust_active = False

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        self.running = False

      # Touch events
      elif event.type == pygame.FINGERDOWN:
        self.is_using_touch = True
        finger_id = event.finger_id
        x = event.x * self.width
        y = event.y * self.height
        self.touch_points[finger_id] = (x, y)

      elif event.type == pygame.FINGERUP:
        finger_id = event.finger_id
        if finger_id in self.touch_points:
          del self.touch_points[finger_id]
        if not self.touch_points:
          self.is_using_touch = False

      elif event.type == pygame.FINGERMOTION:
        finger_id = event.finger_id
        if finger_id in self.touch_points:
          x = event.x * self.width
          y = event.y * self.height
          self.touch_points[finger_id] = (x, y)

    # Process touch inputs
    if self.is_using_touch and self.touch_points:
      for finger_id, pos in self.touch_points.items():
        # Check if in joystick area (left side)
        jx, jy = self.touch_steer_center
        dist_to_joystick = math.sqrt((pos[0] - jx)**2 + (pos[1] - jy)**2)
        if dist_to_joystick < self.touch_steer_radius * 1.5:
          # Virtual joystick - steer
          self.joystick_active = True
          # Calculate angle from joystick center
          if dist_to_joystick > 10:
            joystick_angle = math.atan2(pos[1] - jy, pos[0] - jx)
            self.ship.target_angle = joystick_angle

        # Check if in thrust area (right side) OR right half of screen
        if pos[0] > self.width * 0.5 or pos[1] > self.height * 0.5:
          # Right half or bottom area = thrust
          self.thrust_active = True

    # Mouse/keyboard fallback
    if not self.is_using_touch:
      self.mouse_pos = pygame.mouse.get_pos()
      mouse_buttons = pygame.mouse.get_pressed()
      self.mouse_thrusting = mouse_buttons[0]

      # Mouse steering
      if self.mouse_thrusting:
        self.ship.target_angle = math.atan2(
          self.mouse_pos[1] - self.ship.position.y,
          self.mouse_pos[0] - self.ship.position.x
        )

  def update(self, dt):
    """Update game logic"""
    # Apply input to ship
    if self.is_using_touch:
      self.ship.thrusting = self.thrust_active
    else:
      self.ship.thrusting = self.mouse_thrusting

    # Update ship physics
    self.ship.update(dt)

    # Update particles
    self.particles.update(dt)

    # Update score popups
    self.score_popups = [p for p in self.score_popups if p.update(dt)]

    # Camera follows ship (smooth lerp)
    target_cam_x = self.ship.position.x - self.width // 2
    target_cam_y = self.ship.position.y - self.height // 2
    self.camera[0] += (target_cam_x - self.camera[0]) * 3 * dt
    self.camera[1] += (target_cam_y - self.camera[1]) * 3 * dt

    # Check orb collection
    for orb in self.orbs[:]:
      if self.ship.check_collision(orb):
        self.orbs.remove(orb)
        self.score += 100
        # Spark particles
        self.particles.emit(orb.x, orb.y, NEON_YELLOW, 20)
        self.particles.emit(orb.x, orb.y, WHITE, 15)
        # Score popup
        color_cycle = get_neon_color(index=int(self.score / 100) % 5)
        self.score_popups.append(ScorePopup(orb.x, orb.y, 100, color_cycle))
        self.spawn_orb()

    # Check wall collisions
    self.level.check_collisions(self.ship)

    # Time trial mode
    if self.time_trial_mode:
      self.time_trial_time += dt

  def draw(self):
    """Render the game"""
    self.screen.fill(BLACK)

    # Draw grid background (parallax) with color cycling
    self.draw_grid()

    # Draw level
    self.level.draw(self.screen, self.camera)

    # Draw orbs with pulsing glow
    for orb in self.orbs:
      orb.draw(self.screen, self.camera)

    # Draw particles with glow
    self.particles.draw(self.screen, self.camera)

    # Draw ship with glow effects
    self.ship.draw(self.screen, self.camera, self.particles)

    # Draw score popups
    for popup in self.score_popups:
      popup.draw(self.screen, self.camera)

    # Draw touch controls (if using touch)
    if self.is_using_touch:
      self.draw_touch_controls()

    # Draw UI with neon styling
    self.draw_ui()

    pygame.display.flip()

  def draw_ui(self):
    """Draw UI elements with neon effects"""
    # Score with cycling color
    score_color = get_neon_color(index=0)
    score_text = self.font.render(f"DATA: {self.score}", True, score_color)
    # Glow effect behind score
    glow_surf = pygame.Surface((score_text.get_width() + 20, score_text.get_height() + 10), pygame.SRCALPHA)
    pygame.draw.rect(glow_surf, (*score_color, 50), glow_surf.get_rect(), border_radius=8)
    self.screen.blit(glow_surf, (15, 15))
    self.screen.blit(score_text, (20, 20))

    # Controls hint
    if self.is_using_touch:
      hint = self.small_font.render(
        "LEFT: Joystick to steer | RIGHT: Tap to thrust",
        True, (100, 100, 100)
      )
    else:
      hint = self.small_font.render(
        "Hold LEFT CLICK to thrust | Mouse to steer",
        True, (100, 100, 100)
      )
    self.screen.blit(hint, (self.width // 2 - 200, self.height - 40))

    # Time trial display
    if self.time_trial_mode:
      time_text = self.font.render(f"TIME: {self.time_trial_time:.1f}", True, NEON_MAGENTA)
      self.screen.blit(time_text, (self.width // 2 - 60, 20))
      if self.best_time:
        best_text = self.small_font.render(f"BEST: {self.best_time:.1f}", True, NEON_YELLOW)
        self.screen.blit(best_text, (self.width // 2 - 40, 60))

  def draw_touch_controls(self):
    """Draw virtual joystick and thrust button"""
    # Draw joystick area with cycling color
    jx, jy = self.touch_steer_center
    joystick_color = get_neon_color(index=1)
    pygame.draw.circle(self.screen, (*DARK_GRAY, 100), (int(jx), int(jy)), self.touch_steer_radius, 2)
    pygame.draw.circle(self.screen, (*joystick_color, 50), (int(jx), int(jy)), int(self.touch_steer_radius * 0.3))

    # Draw joystick knob based on touch position
    for finger_id, pos in self.touch_points.items():
      dist = math.sqrt((pos[0] - jx)**2 + (pos[1] - jy)**2)
      if dist < self.touch_steer_radius * 1.5:
        # Clamp to joystick radius
        if dist > self.touch_steer_radius:
          angle = math.atan2(pos[1] - jy, pos[0] - jx)
          knob_x = jx + math.cos(angle) * self.touch_steer_radius
          knob_y = jy + math.sin(angle) * self.touch_steer_radius
        else:
          knob_x, knob_y = pos
        pygame.draw.circle(self.screen, joystick_color, (int(knob_x), int(knob_y)), 20)

    # Draw thrust button
    tx, ty = self.thrust_button_pos
    thrust_color = ORANGE if self.thrust_active else (*DARK_GRAY, 100)
    pygame.draw.circle(self.screen, thrust_color, (int(tx), int(ty)), self.thrust_button_radius, 3)
    # Thrust icon (arrow)
    pygame.draw.polygon(self.screen, NEON_YELLOW if self.thrust_active else (100, 100, 100), [
      (tx, ty - 25),
      (tx - 15, ty + 10),
      (tx + 15, ty + 10)
    ])

    # Labels
    steer_label = self.small_font.render("STEER", True, (80, 80, 90))
    thrust_label = self.small_font.render("THRUST", True, (80, 80, 90))
    self.screen.blit(steer_label, (jx - 25, jy + self.touch_steer_radius + 10))
    self.screen.blit(thrust_label, (tx - 30, ty + self.thrust_button_radius + 10))

  def draw_grid(self):
    """Draw scrolling neon grid with color cycling"""
    grid_size = 80
    offset_x = -int(self.camera[0]) % grid_size
    offset_y = -int(self.camera[1]) % grid_size
    
    # Cycle colors based on position
    cycle = int(pygame.time.get_ticks() / 2000) % len(NEON_PALETTE)
    next_cycle = (cycle + 1) % len(NEON_PALETTE)
    color1 = NEON_PALETTE[cycle]
    color2 = NEON_PALETTE[next_cycle]
    
    for i, x in enumerate(range(offset_x, self.width, grid_size)):
      # Alternate colors for grid lines
      line_color = color1 if i % 2 == 0 else color2
      pygame.draw.line(self.screen, (*line_color, 30), (x, 0), (x, self.height), 1)
    
    for i, y in enumerate(range(offset_y, self.height, grid_size)):
      line_color = color2 if i % 2 == 0 else color1
      pygame.draw.line(self.screen, (*line_color, 30), (0, y), (self.width, y), 1)

  def run(self):
    """Main game loop"""
    while self.running:
      dt = self.clock.get_time() / 1000
      self.handle_input()
      self.update(dt)
      self.draw()
      self.clock.tick(self.ticks)

    pygame.quit()


if __name__ == '__main__':
  game = Game()
  game.run()