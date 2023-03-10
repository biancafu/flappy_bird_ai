import pygame
import neat
import time
import os
import random
pygame.font.init()

# dimension of screen, constants
WIN_WIDTH = 500
WIN_HEIGHT = 800

GEN = 0 #generation

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



def draw_window(win, birds, pipes, base, score, gen, alive):
    win.blit(BG_IMG, (0,0)) #position 0,0 (top left)
    for pipe in pipes:  #can have multiple pipes (list of pipes) in screen
        pipe.draw(win)
    
    #creating score
    text = STAT_FONT.render("Score: " + str(score), 1,(255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10)) #no matter how long the score is, will keep moving left to the screen
    
    #creating generation score & # of alive birds
    text = STAT_FONT.render("Gen: " + str(gen), 1,(255,255,255))
    win.blit(text, (10, 10))

    text = STAT_FONT.render("Alive: " + str(alive), 1,(255,255,255))
    win.blit(text, (10, 50))
    
    base.draw(win)
    #to draw all the birds
    for bird in birds:
        bird.draw(win)

    pygame.display.update()


#main loop of game
#this is our fitness function, we need  to take all birds (genomes) and evaluate them
def main(genomes, config): 
    global GEN
    GEN += 1 #every time we run the main loop, our generation increases
    #keep track of neural network that controls the bird to change fitness accordingly after
    nets = []
    ge = [] 
    birds = [] #change to list for multiple birds (ai)

    for _, g in genomes: #we need to do this because genome is actually a tuple with (id, genome object)
        #the genome will have same position in the list for neural network, birds, and genome

        #set up neural network for the genome
        net = neat.nn.FeedForwardNetwork.create(g, config)
        #save this neural network
        nets.append(net)
        #create a bird for the genome and save it
        birds.append(Bird(230, 350))
        #default fitness = 0
        g.fitness = 0
        #save genome in ge list
        ge.append(g)


    base = Base(730) #730 is bottom of screen
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0

    run = True
    while run:
        #run 30 times every seconds
        clock.tick(60) #change this number to make it run faster
        for event in pygame.event.get(): #listening for user event
            if event.type == pygame.QUIT:
                run= False
                pygame.quit()
                quit()

        #need to know which pipe we are looking at if there are more than 1 in the screen
        #for giving the information to the genome as input 

        pipe_ind = 0 #pipe index
        if len(birds) > 0:
            #if we have more than 1 pipe && x position of bird (all have the same) is past the first pipe then we set pipe index to the next one
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        
        else: #if no birds left, quit the game
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            #very small number becuz this for loop runs 30 times a second
            ge[x].fitness += 0.1 #encourages the bird to stay alive and not fly to the top or bottom of screen

            #activate neural network with inputs
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom))) #output of neural network
            if output[0] > 0.5: #0.5 according to our logic
                #output[0] becuase output is a list of all output neurons, but in this case we only have 1 output neuron
                bird.jump()

        add_pipe = False
        rem = [] #removing pipes list
        for pipe in pipes:
            for x, bird in enumerate(birds): #added for loop for multiple birds (ai)
            #collision test
                if pipe.collide(bird): #if collide, we don't wanna keep genome in list anymore, fitness needs to stop as well
                    ge[x].fitness -= 1 #want to make bird who hits the pipe to have less fitness to encourage bird not to hit the pipe (hiehgt fitness for birds who don't hit pipe)
                    #remove this bird(genome) from list
                    birds.pop(x) 
                    nets.pop(x)
                    ge.pop(x)

                #when bird passes pipe, we set passed = True (defined in bird class), and we need to add another pipe
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True
            
            #check if pipe is off the screen
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            #if go through the pipe, fitness adds 5 to encourage bird to go through pipe not just running into them
            for g in ge:
                #remaining genome in the ge list are the ones that are still alive (removed collided ones earlier)
                g.fitness += 5
            pipes.append(Pipe(600))

        #removing pipes off screen
        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds): #added for loop for multiple birds (ai)
            #dying condition (clear bird from the list when it hits when it hits floor or goes above screen)
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0: #730 is the floor/base, 0 is top of screen
                birds.pop(x) 
                nets.pop(x)
                ge.pop(x)

        # threshold score to break out of loop when return to winner, pickle and save and use this neural network
        # to draw only 1 bird on screen instead of 100 and have it run through play the game
        # if score > 50:
        #     break

        base.move()
        alive = len(birds)
        draw_window(win, birds, pipes, base, score, GEN, alive)

#load in config file
def run(config_path): 
    import pickle # to implement best fitness of generation
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
    # save winner object for best fitness of generation (user pickle to save as file)
    # load that file in and use that neural network from that genome to move bird up and down after
    winner = p.run(main, 50) #run fitness function (main here) 50 times/generations


if __name__ == "__main__":
    #getting path of configuration file in the way neat recommends
    local_dir = os.path.dirname(__file__) #give us path to directory we are currently in, to load in the config file
    config_path = os.path.join(local_dir, "config-feedforward.txt") #finding the absolute path to config file (by joining the local directory to the name of config file)
    run(config_path)

    
