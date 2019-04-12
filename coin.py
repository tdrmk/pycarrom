from pygame import Vector2
from pygame import Rect
import pygame


class Coin:
    """ General class models a carrom coin or a striker, defines the physics components of the coin """
    def __init__(self, radius, mass, position: Vector2, container: Rect):
        """ Initialized the coin with given parameters and place it at given position inside the container """
        self.radius = radius
        self.mass = mass
        self.position = position
        self.container = container
        """ Update the velocity later on """
        self.velocity = Vector2(0.0, 0.0)

    def update(self, dt, deceleration):
        """ Updates the coin position on the board, and also handles reflection and deceleration of the coin """
        self.position += self.velocity * dt

        """ If over board, then it must be reflected to inside the board, and direction of velocity appropriately 
        changed. Refection with the wall are perfectly elastic. """
        """ If moved outside the board along x direction, then change the direction of x component of velocity """
        if self.position.x + self.radius > self.container.right:
            self.position.x -= 2 * (self.position.x + self.radius - self.container.right)
            self.velocity.x = -self.velocity.x
        elif self.position.x - self.radius < self.container.left:
            self.position.x += 2 * (self.container.left - self.position.x + self.radius)
            self.velocity.x = -self.velocity.x

        """ If moved outside the board along y direction, then change the direction of x component of velocity """
        if self.position.y + self.radius > self.container.bottom:
            self.position.y -= 2 * (self.position.y + self.radius - self.container.bottom)
            self.velocity.y = -self.velocity.y
        elif self.position.y - self.radius < self.container.top:
            self.position.y += 2 * (self.container.top - self.position.y + self.radius)
            self.velocity.y = -self.velocity.y

        """ Now decelerate the coins, which is used to model sliding friction """
        if self.velocity.length() <= deceleration * dt:
            """ If velocity is too small, then set the coin to rest """
            self.velocity = Vector2()
        else:
            """ Reduce the velocity based on deceleration along same direction """
            self.velocity -= self.velocity.normalize() * deceleration * dt

    def check_collision(self, other):
        """ Check if given two coins are colliding """
        if self.position.distance_to(other.position) > self.radius + other.radius:
            """ Collision only can happen if distance between centers is less than sum of radii"""
            return False

        if (self.velocity - other.velocity) * (self.position - other.position) > 0:
            """ Collisions can only happen if they are moving towards each other """
            return False

        """ If coins overlap and are moving towards each other, then they collide """
        return True

    def resultant_collision_velocity(self, other, e):
        """ Return the resultant velocity of current coin on collision with the other coin,
         elasticity of the collision is determined the the co-efficient of restitution 'e'."""
        """ If they overlap fully then no collision, handle division by zero exception  """
        if Vector2.length(self.position - other.position) == 0:
            return self.velocity
        return self.velocity - ((1 + e) * other.mass / (self.mass + other.mass)) * \
            Vector2.dot(self.velocity - other.velocity, self.position - other.position) / \
            Vector2.length_squared(self.position - other.position) * (self.position - other.position)

    def collide(self, other, e):
        """ This function is used to handle collisions between the current coin and the other coin and updates the
        velocity of both the coins, elasticity of the collision is determined the the co-efficient of restitution 'e'"""
        self.velocity, other.velocity = self.resultant_collision_velocity(other, e), \
            other.resultant_collision_velocity(self, e)

    def check_moving(self):
        """ Checks if the current coin is moving or not based on the velocity """
        return self.velocity.length() > 0

    def draw(self, win):
        raise NotImplementedError("draw function not implemented")


class CarromMen(Coin):
    def __init__(self, player, radius, mass, position: Vector2, container: Rect):
        """ Constructs a carrom men coin for a given player """
        assert player in (0, 1)
        self.player = player
        self.color = (255, 255, 255) if player == 0 else (0, 0, 0)
        Coin.__init__(self, radius, mass, position, container)

    def reset(self):
        """ Moving it back to the center """
        self.position = Vector2(self.container.center)
        self.velocity = Vector2()

    def get_player(self):
        return self.player

    def draw(self, win):
        pygame.draw.circle(win, self.color, (int(self.position.x), int(self.position.y)), int(self.radius))


class Queen(Coin):
    def __init__(self, radius, mass, position: Vector2, container: Rect):
        """ Constructs a queen coin """
        Coin.__init__(self, radius, mass, position, container)
        self.color = (255, 0, 0)

    def reset(self):
        """ Moving it back to the center """
        self.position = Vector2(self.container.center)
        self.velocity = Vector2()

    def draw(self, win):
        pygame.draw.circle(win, self.color, (int(self.position.x), int(self.position.y)), int(self.radius))


class Striker(Coin):
    def __init__(self, radius, mass, container: Rect):
        """ Constructs a striker """
        Coin.__init__(self, radius, mass, Vector2(), container)

    def draw(self, win):
        pygame.draw.circle(win, (0, 0, 255), (int(self.position.x), int(self.position.y)), int(self.radius))
