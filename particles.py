"""
Particle system for engine trails, explosions, and effects
"""
import pygame
import random

class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def emit(self, x, y, color, count=1):
        """Emit particles at position"""
        for _ in range(count):
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(50, 150)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': random.cos(angle) * speed,
                'vy': random.sin(angle) * speed,
                'color': color,
                'life': 1.0,
                'size': random.randint(2, 5)
            })
            
    def update(self, dt):
        """Update all particles"""
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt * 2  # 0.5 second lifetime
            p['vx'] *= 0.95  # Slow down
            p['vy'] *= 0.95
            
            if p['life'] <= 0:
                self.particles.remove(p)
                
    def draw(self, screen, camera):
        """Draw all particles with camera offset"""
        offset_x, offset_y = camera
        
        for p in self.particles:
            x = int(p['x'] - offset_x)
            y = int(p['y'] - offset_y)
            
            # Only draw if on screen
            if -50 <= x <= screen.get_width() + 50 and -50 <= y <= screen.get_height() + 50:
                alpha = int(p['life'] * 255)
                size = int(p['size'] * p['life'])
                color = p['color']
                
                # Draw with alpha using a surface
                if size > 0:
                    s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*color, alpha), (size, size), size)
                    screen.blit(s, (x - size, y - size))