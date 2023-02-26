import pygame
import neat
import time
import os
import random

# dimension of screen, constants
WIN_WIDTH = 500
WIN_HEIGHT = 800

# load imaages, make them 2x size
BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))
]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))


class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25 #max tilt angle
    ROT_VEL = 20    #rotation velocity, how much we will rotate each frame when we move the bird
    ANIMATION_TIME = 5 #how long we gonna show each bird animation

    #constructor
    def __init__(self, x, y):
        #starting position
        self.x = x
        self.y = y
        self.tilt = 0 #how much image is tilted
        self.tick_count = 0 #physics of bird
        self.vel = 0 
        self.height = self.y 
        self.img_count = 0 #which image we are showing currently
        self.img = self.IMGS[0] #pic we would load in with

    def jump(self):
        self.vel = -10.5 #upward -> negative y, downward -> positive
        self.tick_count = 0 #where we last jump (?)
        self.height = self.y #where the bird jump from
    
    def move(self):
        self.tick_count += 1 #1 frame went by
        # -10.5 + 1.5 = -9 (upward pixels)
        d = self.vel*self.tick_count + 1.5*self.tick_count**2
        if d >= 16:
            d = 16 #max drop
        if d < 0:
            d -= 2 #move a little more when jumping
        
        self.y = self.y + d #changing position

        #tilt
        if d < 0 or self.y < self.height + 50: #if bird is going upward or position is still higher than where it jumped from
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else: #moving downward
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win): #win is window
        self.img_count += 1

        #which image to show according to img_count (flapping wings)
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        #if bird is going down, we don't want it to flap wings
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2 #starts at img 1 so it doesn't skip frame
        
        rotated_image = pygame.transform.rotate(self.img, self.tilt) #this will tilt/rotate from top left corner
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center) #rotate image around center
        win.blit(rotated_image, new_rect.topleft) #rotating image
    
    #collision 
    def get_mask(self): 
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200 #gap between pipes
    VEL = 5 #how fast pipe will move

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True) #flip the pipe as pipe on the top
        self.PIPE_BOTTOM = PIPE_IMG 

        self.passed = False  #collision purpose and ai
        self.set_height() 

    #define top and bottom of height and how tall it is in random
    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height() #top left of pipe needs to be calculated
        self.bottom = self.height + self.GAP
    
    def move(self):
        self.x -= self.VEL
    
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    #8:30 min

def draw_window(win, bird):
    win.blit(BG_IMG, (0,0)) #position 0,0 (top left)
    bird.draw(win)
    pygame.display.update()


#main loop of game
def main():
    bird = Bird(200, 200)
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(30) #at most 30 ticks every seconds
        for event in pygame.event.get(): #listening for user event
            if event.type == pygame.QUIT:
                run= False
        bird.move()
        draw_window(win, bird)
    pygame.quit()
    quit()

main()
