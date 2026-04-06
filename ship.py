"""
Ship class - momentum-based movement with drift physics
Inspired by Data Wing and RainbowDrift
"""
import pygame
import math

# Colors
NEON_CYAN = (0, 255, 255)
NEON_MAGENTA = (255, 0, 255)
WHITE = (255, 255, 255)
ORANGE = (255, 150, 0)

class Ship:
    def __init__(self, x, y):
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.angle = 0  # Current facing angle (radians)
        self.target_angle = 0  # Where we want to face
        
        # Physics constants - tuned for good drift feel
        self.thrust_power = 800  # Acceleration when thrusting
        self.max_speed = 600  # Maximum speed
        self.friction = 0.98  # Natural slowdown (air resistance)
        self.turn_speed = 5  # How fast we rotate toward target
        self.drift_factor = 0.92  # How much velocity aligns with facing direction
        
        # Visual
        self.thrusting = False
        self.size = 20
        self.engine_glow = 0
        
        # Trail for visual effect
        self.trail = []
        
    def update(self, dt):
        """Update ship physics - the core drift mechanics"""
        
        # Smoothly rotate toward target angle
        angle_diff = self.target_angle - self.angle
        # Normalize angle difference to -pi to pi
        while angle_diff > math.pi:
            angle_diff -= math.pi * 2
        while angle_diff < -math.pi:
            angle_diff += math.pi * 2
            
        # Apply rotation (with some lag for drift feel)
        self.angle += angle_diff * self.turn_speed * dt
        
        # Calculate thrust direction (where ship is facing)
        thrust_dir = pygame.math.Vector2(math.cos(self.angle), math.sin(self.angle))
        
        # Apply thrust if mouse is held
        if self.thrusting:
            self.velocity += thrust_dir * self.thrust_power * dt
            self.engine_glow = min(1.0, self.engine_glow + 5 * dt)
        else:
            self.engine_glow = max(0, self.engine_glow - 3 * dt)
            
        # DRIFT MECHANIC: 
        # The key to drift is that velocity doesn't immediately align with facing direction
        # We blend the current velocity toward the thrust direction
        if self.thrusting:
            # Get velocity magnitude
            speed = self.velocity.length()
            if speed > 1:
                # Blend velocity toward facing direction (drift recovery)
                current_dir = self.velocity.normalize()
                blended = current_dir.lerp(thrust_dir, 1 - self.drift_factor)
                if blended.length() > 0:
                    self.velocity = blended * speed
        
        # Apply friction (air resistance)
        self.velocity *= self.friction
        
        # Clamp to max speed
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed
            
        # Update position
        self.position += self.velocity * dt
        
        # Add to trail
        speed = self.velocity.length()
        if speed > 50:
            self.trail.append({
                'pos': pygame.math.Vector2(self.position),
                'alpha': min(255, speed * 2),
                'age': 0
            })
            
        # Age and remove old trail points
        for point in self.trail[:]:
            point['age'] += dt
            point['alpha'] -= 200 * dt
            if point['alpha'] <= 0:
                self.trail.remove(point)
                
        # Keep trail reasonable size
        if len(self.trail) > 30:
            self.trail = self.trail[-30:]
            
    def check_collision(self, orb):
        """Check if ship collected an orb"""
        dist = self.position.distance_to(orb.position)
        return dist < (self.size + orb.size)
        
    def draw(self, screen, camera, particles):
        """Draw the ship with neon effects"""
        offset_x, offset_y = camera
        
        # Draw engine trail
        for point in self.trail:
            x = int(point['pos'].x - offset_x)
            y = int(point['pos'].y - offset_y)
            alpha = int(point['alpha'])
            if 0 <= x < screen.get_width() and 0 <= y < screen.get_height():
                # Draw trail as small circles
                radius = max(2, int(alpha / 50))
                color = (*ORANGE, min(255, alpha))
                pygame.draw.circle(screen, ORANGE, (x, y), radius)
        
        # Calculate screen position
        sx = int(self.position.x - offset_x)
        sy = int(self.position.y - offset_y)
        
        # Draw engine glow when thrusting
        if self.engine_glow > 0:
            glow_radius = int(30 * self.engine_glow)
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            
            # Gradient glow
            for r in range(glow_radius, 0, -2):
                alpha = int((1 - r / glow_radius) * 150 * self.engine_glow)
                pygame.draw.circle(glow_surf, (*ORANGE, alpha), (glow_radius, glow_radius), r)
                
            screen.blit(glow_surf, (sx - glow_radius, sy - glow_radius))
            
        # Draw ship as a triangle pointing in direction of movement or facing
        # Use velocity direction if moving fast, otherwise use facing angle
        if self.velocity.length() > 50:
            draw_angle = math.atan2(self.velocity.y, self.velocity.x)
        else:
            draw_angle = self.angle
            
        # Ship vertices (triangle)
        points = []
        for i in range(3):
            if i == 0:  # Nose
                a = draw_angle
                d = self.size
            else:  # Wings
                a = draw_angle + (math.pi if i == 1 else 0) + (0.5 if i == 1 else -0.5)
                d = self.size * 0.7
            points.append((
                sx + math.cos(a) * d,
                sy + math.sin(a) * d
            ))
            
        # Draw filled ship
        pygame.draw.polygon(screen, NEON_CYAN, points)
        
        # Draw neon outline
        pygame.draw.polygon(screen, WHITE, points, 2)
        
        # Draw cockpit glow
        cockpit_pos = (
            sx + math.cos(draw_angle) * self.size * 0.3,
            sy + math.sin(draw_angle) * self.size * 0.3
        )
        pygame.draw.circle(screen, NEON_MAGENTA, (int(cockpit_pos[0]), int(cockpit_pos[1])), 4)
        
        # Emit particles when thrusting
        if self.thrusting and particles:
            particles.emit(
                sx - math.cos(draw_angle) * self.size,
                sy - math.sin(draw_angle) * self.size,
                ORANGE, 1
            )