###
# Playing with circular orbits and things moving between them
# Use the 1, 2 and 3 keys to tell the spacecraft (green) to move
# go into orbit with planets 1, 2 and 3 respectively.
#
# Todo:
# - Implement intercepts (i.e. so the spacecraft actually hits the planet)
# - 

import pygame
import math
import random

dt = .01  # Time gap for calculating impulse and stuff e.g. (dp = F * dt)
G = .01  # Gravitational constant


class MassiveObject():
    """
    Represents any object that exists in space.
    Includes: planets, stars, asteroids, ships and possibly missiles. 
    """    
    def __init__(self, x, y, mass, radius, color=0x000000):
        self.x, self.y = x, y
        self.mass = mass
        self.radius = radius
        self.color = color

    def draw(self, surface, reference_frame=None, zoom=1):
        """
        Draw the object on the surface

        Parameters:
        surface - an instance of pygame.surface.Surface that this will be drawn on
        reference_frame - something with x and y. This will be drawn with that in the middle.
        zoom - the system will be drawn with everything multiplied by zoom. 
        """
        if reference_frame is None:
            x = surface.get_width() / 2 + self.x * zoom
            y = surface.get_height() / 2 + self.y * zoom
        else:
            x = surface.get_width() / 2 + (self.x - reference_frame.x) * zoom
            y = surface.get_height() / 2 + (self.y - reference_frame.y) * zoom
        
        pygame.draw.circle(surface, self.color, (int(x), int(y)), int(self.radius * zoom ** 0.5))

class FixedObject(MassiveObject):
    """
    Represents the fixed object that defines the reference frame
    e.g. the sun
    """
    pass

class OrbitingObject(MassiveObject):
    """
    Base class for objects that are affected by gravity
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.vel_x, self.vel_y = 0, 0

    def get_acceleration(self, massive_objects):
        """
        Return the acceleration of this object when put into the gravity field of all items in massive_objects.

        Parameters
        massive_objects - iterable of MassiveObject and FixedObject. If self is in MassiveObject, ignores it.

        return - acceleration as a x,y pair. 
        """
        accel_x, accel_y = 0, 0
        
        for obj in massive_objects:
            dist_x = obj.x - self.x
            dist_y = obj.y - self.y

            dist_squared = dist_x*dist_x + dist_y*dist_y
            dist_squared_sqrt = math.sqrt(dist_squared)

            if dist_squared < 0.0001:
                continue  #Operating on self or very close. Ignore these objecs or it creates errors
            #elif dist_squared < self.radius + obj.radius: collision

            accel_x += G * obj.mass / dist_squared * dist_x / dist_squared_sqrt
            accel_y += G * obj.mass / dist_squared * dist_y / dist_squared_sqrt
            
        return accel_x, accel_y

    def update(self, acceleration):
        """
        Updates the position and speed of the object

        Parameters
        acceleration - a 2-tuple of the x and y components of acceleration. 
        """
        self.vel_x += acceleration[0] * dt
        self.vel_y += acceleration[1] * dt

        self.x += self.vel_x * dt  # I could use more complicated behavior taking into account acceleration,
        self.y += self.vel_y * dt  # but it's probably not worth it.

    def set_circular_orbit(self, central_mass, clockwise=True):
        """
        Puts the object into a circular orbit around central_mass. Modifies vel_x, vel_y

        Parameters
        central_mass - an instance of a MassiveObject
        clockwise - the direction of the orbit
        """
        import math
        dx = self.x - central_mass.x
        dy = self.y - central_mass.y
        radius = math.sqrt(dx * dx + dy * dy)

        if clockwise:
            self.vel_y = dx / radius * math.sqrt(G * central_mass.mass / radius)
            self.vel_x = -dy / radius * math.sqrt(G * central_mass.mass / radius)
        else:
            self.vel_y = -dx / radius * math.sqrt(G * central_mass.mass / radius)
            self.vel_x = dy / radius * math.sqrt(G * central_mass.mass / radius)

        try:
            self.vel_y += central_mass.vel_y
            self.vel_x += central_mass.vel_x
        except AttributeError:
            pass

    def get_orbit_direction(self, centre):
        """Returns True if orbiting clockwise, False otherwise"""
        #Return whether the z component of (self - centre) cross velocity is positive
        dx = self.x - centre.x
        dy = self.y - centre.y
        return dx * self.vel_y - dy * self.vel_x > 0

class Spacecraft(OrbitingObject):
    import math
    
    class Burn():
        def __init__(self, delta_vx, delta_vy, time):
            """
            Represents a thrust to be applied at some time (used for scheduling thrusts)
            """
            self.delta_vx = delta_vx
            self.delta_vy = delta_vy
            self.time = time

            if time < 0:
                print("Warning: You have a negative time")
        def __repr__(self):
            return "This burn will change the velocity by {},{}. It is scheduled for {} updates from now".format(
                self.delta_vx, self.delta_vy, self.time)

    # STATES
    TRANSFERRING = "<spacecraft state:transferring>"  # when a Spacecraft is moving between orbits.
    STABLE = "<spacecraft state:transferring>"  #when a Spacecraft is in a stable circular orbit
        
    
    def __init__(self, source, radius, color, mass=0.00001):
        """
        Create a spacecraft at source. It inherits source's velocity, so it
        should probably orbit around the same thing as source does. 

        Parameters:
        source - where the planet will start. must have properties x and y.
        """
        super().__init__(source.x, source.y, mass, radius, color)
        try:
            self.vel_x = source.vel_x
            self.vel_y = source.vel_y
        except AttributeError:
            pass  # orbiting around a fixed object.
        self.radius = radius
        self.color = color
        
        self.scheduled_burns = []

    def launch_to_orbit(self, centre, target):
        """
        Launch an orbiter to orbit in the same orbit as the target_planet
        Only works on circular orbits because of how the radius is calculated.
        Clears all other scheduled burns. 
        
        TODO: Make it time correctly to actually hit target planet

        Parameters:
        centre - what the Spacecraft and the target are orbiting. 
        target - the orbiter will be launched at a target planet. Must have x, y, x_vel, y_vel
        """
        self.set_circular_orbit(centre, self.get_orbit_direction(centre))
        
        dx_s = self.x - centre.x  # x-distance to the source
        dy_s = self.y - centre.y  # y-distance
        dx_t = target.x - centre.x  # x-distance to the target
        dy_t = target.y - centre.y
        
        r1 = math.sqrt(dx_s * dx_s + dy_s * dy_s)
        r2 = math.sqrt(dx_t * dx_t + dy_t * dy_t)

        #Applying the Hohmann transfer orbit: http://en.wikipedia.org/wiki/Hohmann_transfer_orbit
        delta_v1 = math.sqrt(G * centre.mass / r1) * (math.sqrt(2 * r2 / (r1 + r2)) - 1)
        delta_v2 = math.sqrt(G * centre.mass / r2) * (1 - math.sqrt(2 * r1 / (r1 + r2)))

        self.vel_x += -dy_s / r1 * delta_v1
        self.vel_y += dx_s / r1 * delta_v1

        self.scheduled_burns = [Spacecraft.Burn(dy_s / r1 * delta_v2, -dx_s / r1 * delta_v2,
                                         math.pi * math.sqrt((r1 + r2) ** 3 / (8 * centre.mass * G)) / dt)]
        print(self.scheduled_burns[0].time, self.scheduled_burns[0].delta_vx, self.scheduled_burns[0].delta_vy)

    def launch_to_orbital_target(self, centre, target):
        """
        Launch itself to actually hit target.
        TODO: implement this. 
        """
        pass 

    def update(self, acceleration):
        super().update(acceleration)
        
        #which order do these parts go in?
        for burn in self.scheduled_burns:
            burn.time -= 1
            if burn.time < 0:
                self.vel_x += burn.delta_vx
                self.vel_y += burn.delta_vy

        #Remove all burns with time < 0.         
        self.scheduled_burns = list(filter(lambda burn:burn.time > 0, self.scheduled_burns))
        

class Particle():
    """
    Base class for objects that do not have gravity of their own.
    """
    pass
    
pygame.init()
window = pygame.display.set_mode ((600, 400))
main_surface = pygame.Surface ((600, 400))
clock = pygame.time.Clock()

sun = FixedObject(300, 200, 30000, 5, 0xffff00)
#orbited planet is the first one
planets = [OrbitingObject(100, 200, 10, 3, 0xfa8072), OrbitingObject(200, 200, 1, 2, 0xfe4b03), OrbitingObject(115, 300, 3, 2, 0x4a0000), OrbitingObject(140, 250, 4, 2, 0x008080)]

for p in planets:
    p.set_circular_orbit(sun, True)

#x, y, mass, radius, color
moon = OrbitingObject(101, 200, .1, 1, 0xFF0000)
moon.set_circular_orbit(planets[0])

spaceship_one = Spacecraft(planets[1], 2, 0x00FF00)

def render(reference_frame, zoom):
    #main_surface.fill(0x000000)
    sun.draw(main_surface, reference_frame, zoom)
    for p in planets:
        p.draw(main_surface, reference_frame, zoom)
    moon.draw(main_surface, reference_frame, zoom)
    spaceship_one.draw(main_surface, reference_frame, zoom)

spaceship_one.launch_to_orbit(sun, planets[2])

while (True):
    for i in range(100):    
        for p in planets:
            a = p.get_acceleration([sun])
            p.update(a)

        a = moon.get_acceleration([sun, planets[0]])
        moon.update(a)

        a = spaceship_one.get_acceleration([sun])
        spaceship_one.update(a)
        
    render(sun, .5)
    
    window.blit(main_surface, (0, 0))
    pygame.display.flip()

    clock.tick(60)

    for event in pygame.event.get(pygame.KEYDOWN):
        if event.key == pygame.K_1:
            spaceship_one.launch_to_orbit(sun, planets[1])
        elif event.key == pygame.K_2:
            spaceship_one.launch_to_orbit(sun, planets[2])
        elif event.key == pygame.K_3:   
            spaceship_one.launch_to_orbit(sun, planets[3])
    pygame.event.pump()
