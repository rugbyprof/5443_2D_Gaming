"""
After we saw how to control each player using event logic,
could we use similar logic to do the same for a multiplayer game?
Instead of directly controlling each player, we could let commands 
comming from a specific player be passed to a "dot" instance to move
it. 

First however, lets get a comms example that will let players wanting
to be added to the same game get added and basically "appear" when they
send a message to the same game queue you are on. 
"""
import pygame
from random import randint
import json
import sys 
from rich import print

# necessary libs for rabbitmq
from comms import CommsListener
from comms import CommsSender

class MessageHandler:
    def __init__(self,**creds):
        self.user = creds["user"]
        self.creds = creds
    

        # create instances of a comms listener and sender
        # to handle message passing.
        self.commsListener = CommsListener(**self.creds)
        self.commsSender = CommsSender(**self.creds)

        # Start the comms listener to listen for incoming messages
        self.commsListener.threadedListen(self.callBack)

    def callBack(self,**kwargs):
        print(kwargs)

    def send(self,**kwargs):
        target = kwargs.get('target','broadcast')
        self.commsSender.threadedSend(
            target=target, sender=self.user,body =json.dumps(kwargs),debug=False
        )

    def setCallback(self,callback):
        self.callBack = callback

class Player:
    def __init__(self,screen,creds):
        self.screen = screen    # copy of screen to display dot on
        self.creds = creds
        self.player = self.creds['user'] 

        self.messages = MessageHandler(**creds,callBack=self.messageCallback)
        
        # set the initial position of the dot
        self.dot_position = pygame.math.Vector2(randint(25,400), randint(25,400))
        self.speed = 1
        self.color = (randint(0,256),randint(0,256),randint(0,256))
        self.ticks = 0


    def messageCallback(self,**kwargs):
        print(kwargs)

    def update(self,keys):
        """ Get the keys from main, then adjust position based
            on keys pressed
        """
        if keys[pygame.K_UP]:
            self.dot_position.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.dot_position.y += self.speed
        if keys[pygame.K_LEFT]:
            self.dot_position.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.dot_position.x += self.speed

    def draw(self):
        # draw the dot
        pygame.draw.circle(self.screen, self.color , self.dot_position, 10)

        # only send a message so many ticks otherwise problems occur!
        if pygame.time.get_ticks() - self.ticks > 100:
            pos = (self.dot_position.x,self.dot_position.y)
            self.messages.send(
                target='broadcast', sender=self.player, player=self.player,dot_position=pos
            )
        self.ticks = pygame.time.get_ticks()

class PlayerManager:
    def __init__(self):
        self.players = {}


    def addPlayer(self,player):
        if not player.player in self.players:
            self.players['user'] = player
    
    def update(self,keys):
        pass


playerManager = PlayerManager()
    # initialize Pygame
pygame.init()
# set the window size
size = (400, 400)

# create the window
screen = pygame.display.set_mode(size)

def main(creds):

    print(creds)

    localplayer = Player(screen,creds)

    playerManager.addPlayer(localplayer)
    
    # set the window title
    pygame.display.set_caption("Move the Player")

    # create list for lookup for keys 0-9
    # The keys 0-9 are ascii 48-57 
    numericKeys = [x for x in range(0,58)]

    # run the game loop
    running = True
    while running:

        screen.fill((255, 255, 255))

        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                # get the keys 0-9 if pressed
                elif event.key in numericKeys:
                    print(f"You pressed: {48-event.key}")
                    # choose current dot by which key pressed
                    currentPlayer = 48 - event.key



        # move the dot based on key input
        keys = pygame.key.get_pressed()
        localplayer.update(keys)

        # clear the screen
        

        localplayer.draw()
        # update the screen
        pygame.display.flip()

    # quit Pygame
    pygame.quit()

if __name__=='__main__':
    if len(sys.argv) < 4:
        print("Need: exchange playerName passWord")
        sys.exit()
    exchange = sys.argv[1]
    playerName = sys.argv[2]
    playerPass = sys.argv[3]
    creds = {
        "exchange": exchange,
        "port": '5672',
        "host": 'terrywgriffin.com',
        "user": playerName,
        "password": playerPass
    }

    main(creds)