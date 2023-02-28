import pygame
import neat
import time
import os
import random
pygame.font.init()

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

STAT_FONT = pygame.font.SysFont("comicsans", 35) #score font


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
    
    #collision detection with 2D list
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

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        #offset => how far away the mask are from each other, look up mask in pygame for further info
        top_offset = (self.x - bird.x, self.top - round(bird.y)) 
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        #offset from bird to top mask (2 top left corner) and use mask (list of pixels) and see if they overlap

        b_point = bird_mask.overlap(bottom_mask, bottom_offset) #point of overlap between bird mask and bottom pipe (bottom offset), if not collide return None
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point: #if its not none => collided (bird passed in collided with this pipe or not)
            return True
        return False
    

class Base:
    VEL = 5 #same as pipe
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y): #don't need x cuz it will be moving to left
        self.y =y
        self.x1 = 0 #img1 at 0
        self.x2 = self.WIDTH #img2 right behind img1
    
    def move(self):
        #both img moving at same speed
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        #if img1/img2 is off screen, move it back to cycle it again, forming infinite loop
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))



def draw_window(win, bird, pipes, base, score):
    win.blit(BG_IMG, (0,0)) #position 0,0 (top left)
    for pipe in pipes:  #can have multiple pipes (list of pipes) in screen
        pipe.draw(win)
    
    #creating score
    text = STAT_FONT.render("Score: " + str(score), 1,(255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10)) #no matter how long the score is, will keep moving left to the screen
    base.draw(win)
    bird.draw(win)
    pygame.display.update()


#main loop of game
def main():
    bird = Bird(230, 350)
    base = Base(730) #730 is bottom of screen
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0

    run = True
    while run:
        clock.tick(30) #at most 30 ticks every seconds
        for event in pygame.event.get(): #listening for user event
            if event.type == pygame.QUIT:
                run= False

        #bird.move()
        add_pipe = False
        rem = [] #removing pipes list
        for pipe in pipes:
            #collision test
            if pipe.collide(bird): 
                pass

            #check if pipe is off the screen
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            
            #when bird passes pipe, we set passed = True (defined in bird class), and we need to add another pipe
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            pipe.move()
        if add_pipe:
            score += 1
            pipes.append(Pipe(600))

        #removing pipes off screen
        for r in rem:
            pipes.remove(r)

        #dying condition (when it hits floor)
        if bird.y + bird.img.get_height() >= 730: #730 is the floor/base
            pass

        base.move()
        draw_window(win, bird, pipes, base, score)
    pygame.quit()
    quit()
main()


#load in config file
def run(config_path): 
    #defining all the sub-headings in config file
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, 
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    #population
    p = neat.Population(config) #population depending on what we have in the config file

    #give us detail stats of generation, best finess... in console
    p.add_reporter(neat.StdOutReporter(True)) 
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    #setting fitness function
    winner = p.run(main,50)


if __name__ == "__main__":
    #getting path of configuration file in the way neat recommends
    local_dir = os.path.dirname(__file__) #give us path to directory we are currently in, to load in the config file
    config_path = os.path.join(local_dir, "config-feedforward.txt") #finding the absolute path to config file (by joining the local directory to the name of config file)
    run(config_path)

    
