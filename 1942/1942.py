# 1942 python using pygame Created by Van Seiler for CS 399 spring 2019.
# Game is a vertical scrolling plane fighter game based off the old cabinet arcade game 1942. This version features
# 2 small ship types, silver and green, 1 medium, and 1 large
import pygame, sys, math, random
from pygame.locals import *
from pygameSettings import *

pygame.init()
hSize = 700
vSize = 800

window = pygame.display.set_mode((hSize, vSize), 0, 32)
pygame.display.set_caption("1942")
gameFont = pygame.font.Font('ArcadeFont.ttf', 20)


# Player ship class, defines what happens to the ship
# Movement: gets keyboard input and moves player ship that direction/ allows diagonal movement
# boundary: nothing special, keeps plane inside the screen
# livesleft: decreases players lives when called (by either rockets collision or collision with plane
# collide: exactly same as other classes, will return a true when the object interacts with plane i.e other ai planes
class playerPlane(pygame.sprite.Sprite):

    def __init__(self, imgFile, xStart, yStart, xspeed, yspeed, lives):
        super().__init__()
        self.image = pygame.transform.scale(imgFile, (80, 60))
        self.rect = self.image.get_rect(center=(xStart, yStart))
        self.xStart, self.yStart, self.xspeed, self.yspeed, self.lives = xStart, yStart, xspeed, yspeed, lives

    def movement(self):
        keys = pygame.key.get_pressed()
        if keys[K_a]:
            self.rect.centerx -= 5
        elif keys[K_d]:
            self.rect.centerx += 5
        if keys[K_w]:
            self.rect.centery -= 3
        if keys[K_s]:
            self.rect.centery += 3
        self.boundary()

    def boundary(self):
        if self.rect.left <= 0:
            self.rect.left = 0
        elif self.rect.right >= hSize:
            self.rect.right = hSize
        if self.rect.top <= 0:
            self.rect.top = 0
        elif self.rect.bottom >= vSize:
            self.rect.bottom = vSize

    def livesLeft(self):
        self.lives -= 1

    def collide(self, object):
        collision = pygame.sprite.collide_rect(self, object)
        if collision:
            return True


# Rocket class, defines specific functions for when player rocket is launched
# Launch: Responsible for moving the rockets and will call delete if the rocket leaves top of screen
# Collide: returns a boolean that will determine when a rocket collides with an enemy plane
# Delete: function that will delete the rocket and decrease the number of rockets alive(itr)
class Rockets(pygame.sprite.Sprite):
    def __init__(self, imgFile, xStart, yStart, yspeed):
        super().__init__()
        self.image = pygame.transform.scale(imgFile, (25, 25))
        self.rect = self.image.get_rect(center=(xStart, yStart))
        self.xStart, self.yStart, self.xspeed, self.yspeed = xStart, yStart, 0, yspeed

    # When function called, the only thing changing is the y value of the object
    def launch(self, rocketlist, spriteList):
        global misses  # used to calculate accuacy
        self.rect.centery -= self.yspeed
        # When the rocket hits the top of screen delete it from both rocket list and sprite list
        if self.rect.bottom <= 0:
            self.delete(spriteList, rocketlist)
            misses += 1

    def collide(self, object):
        collision = pygame.sprite.collide_rect(self, object)
        if collision:
            return True

    def delete(self, spriteList, rocketlist):
        global itr
        rocketlist.remove(self)
        spriteList.remove(self)
        itr -= 1


# EnemyRocket class, defines movement of the rockets for the specific plane sizes.
# sLaunch: responsible for moving the small (green) ships rockets, xspeed and yspeed are calculated as the slope between
#          players ship and when the small ship launches it and call delete when it leaves screen
# mLaunch: launches rockets along every x and y axis(4) in a sort of plus shape and call delete once off screen
# collide: like before returns a bool that tells when the rocket collides with something
# delete: responsible for deleting the rocket from sprite list and rocket list
class Enemyrocket(pygame.sprite.Sprite):

    def __init__(self, imgFile, xStart, yStart, xspeed, yspeed, count):
        super().__init__()
        self.image = pygame.transform.scale(imgFile, (32, 32))
        self.rect = self.image.get_rect(center=(xStart, yStart))
        self.xStart, self.yStart, self.xspeed, self.yspeed, self.count = xStart, yStart, xspeed, yspeed, count

    def slaunch(self, spriteList, rl):
        self.rect.centerx += self.xspeed
        self.rect.centery += self.yspeed
        if self.rect.right > hSize or self.rect.bottom > vSize or self.rect.left < 0 or self.rect.top < 0:
            self.delete(spriteList, rl)

    def mlaunch(self, spritelist, rl, dx, dy):
        self.rect.centerx += dx
        self.rect.centery += dy
        if self.rect.left >= hSize or self.rect.right <= 0 or self.rect.top >= vSize or self.rect.bottom <= 0:
            self.delete(spritelist, rl)

    def collide(self, object):
        collision = pygame.sprite.collide_rect(self, object)
        if collision:
            return True

    def delete(self, spriteList, rl):
        spriteList.remove(self)
        rl.remove(self)


# Two types of small planes, Small Green and Small Silver
# Paths: Green will dive towards player and at last second launch a rocket and turn around
#        Silver will dive down towards bottom of screen and thats it. nothing special
#       :flyGreen is responsible for setting behaivor of the diving plane, when the plane gets within a certain distance
#       it will flip around and initiate retreat protocol. Pretty much  just returns a bool value that will tell another
#       function to fire
# Boundary: will remove the plane from both lists involved. Since the green plane only flys towards the top of the
#   screen, only need to check when the bottom of the plane is out of play
# Delete is used when other functions need to delete the ai plane, i.e. player shoots it down
class SmallPlane(pygame.sprite.Sprite):

    def __init__(self, imgFile, xStart, yStart, xspeed, yspeed, retreat, fire, dummy, health):
        super().__init__()
        self.image = pygame.transform.scale(imgFile, (60, 60))
        self.rect = self.image.get_rect(center=(xStart, yStart))
        self.xStart, self.yStart, self.xspeed, self.yspeed, self.retreat, self.fire, self.dummy, self.health =\
            xStart, yStart, xspeed, yspeed, retreat, fire, dummy, health

    # Basic movement for green small green plane, Basic idea is that it will dive towards the player, at the last second
    # it will flip around and launch a bomb towards player plane at one position( no tracking). Use of dummy variable
    # helpes prevent the plane from firing more than once. Basically a dumb counter
    def flyGreen(self, x, sx, sy):
        if x <= 200:
            self.dummy += 1
            self.retreat = True
            self.fire = True

        if self.retreat:
            if self.dummy == 1:
                self.image = pygame.transform.rotate(self.image, 180)
                self.dummy += 1
            self.rect.centerx -= 1
            self.rect.centery -= 5
            if self.fire:
                self.fire = False
                return self.dummy

        # Diving algorithm isn't perfect, path is a little funky, but it does its job
        elif self.retreat == False:
            dx, dy = calculate(self.rect.centerx, self.rect.centery, sx, sy)
            if dx < 2:
                dx *= 2
            if dy < 4:
                dy *= 2
            self.rect.centerx += dx
            self.rect.centery += dy

    def flySilver(self):
        self.rect.centerx += self.xspeed
        self.rect.centery += self.yspeed

    # accounts for both silver and green, so when a ship reaches the edge it is done for, user gets no points
    def boundary(self, spritelist, shiplist):
        if self.rect.bottom < 0:
            self.delete(shiplist, spritelist)
        elif self.rect.top > vSize:
            self.delete(shiplist, spritelist)
        if self.rect.left > hSize:
            self.delete(shiplist, spritelist)
        elif self.rect.right < 0:
            self.delete(shiplist, spritelist)

    def delete(self, shiplist, spriteList):
        shiplist.remove(self)
        spriteList.remove(self)


# Medium plane class, determines the behavior of the flying path, boundry and and delete
# FlyGreen: pathway for the medium green ship, pathway is determined in phases, forms a square shaped path,
#   loop around once and leave through topside opp. it came in. Every phase change, bool fire is changed to fire to
#   return a true value that tells the code below to call the mLaunch for shooting rockets, each if statement changes
#   fire back to false to prevent another missile launch
# Boundary: because ship leaves through top, only need to check if the bottom of ship has left screen
# Delete: remove ship from ship list and sprite list
class MediumPlane(pygame.sprite.Sprite):
    def __init__(self, imgFile, xStart, yStart, xspeed, yspeed, phase, itr, fire, health):
        super().__init__()
        self.image = pygame.transform.scale(imgFile, (90, 90))
        self.rect = self.image.get_rect(center=(xStart, yStart))
        self.xStart, self.yStart, self.xspeed, self.yspeed, self.phase, self.itr, self.fire, self.health = \
            xStart, yStart, xspeed, yspeed, phase, itr, fire, health

    def flyGreen(self):
        if self.itr == 6:
            self.fire = False
            self.phase = 4
            self.fire = True
            self.itr += 1
            return self.fire
        if self.phase == 0:
            self.rect.centery += self.yspeed
            if self.rect.centery >= 3 * vSize // 5:
                self.phase = 1
                self.itr += 1
                self.fire = True
                return self.fire
        elif self.phase == 1:
            self.fire = False
            self.rect.centerx -= self.xspeed
            if self.rect.centerx <= hSize // 4:
                self.phase = 2
                self.itr += 1
                self.fire = True
                return self.fire
        elif self.phase == 2:
            self.fire = False
            self.rect.centery -= self.yspeed
            if self.rect.centery <= vSize // 4:
                self.phase = 3
                self.itr += 1
                self.fire = True
                return self.fire
        elif self.phase == 3:
            self.fire = False
            self.rect.centerx += self.xspeed
            if self.rect.centerx >= 8 * hSize // 10:
                self.phase = 0
                self.itr += 1
                self.fire = True
                return self.fire
        elif self.phase == 4:
            self.fire = False
            self.rect.centery -= self.yspeed

    def boundry(self, spritelist, shiplist):
        if self.rect.bottom < 0:
            self.delete(spritelist, shiplist)

    def delete(self, spriteList, shiplist):
        shiplist.remove(self)
        spriteList.remove(self)


# Class for the large plane determines the planes path and other stuff
# flyGreen: pathway for planes movement, nothing too special, similar to mediumplane, uses system of phases to
#   tell when to change direction. pathway is come into screen from bottom right, go to middle-ish, move left and
#   right and after 7 itrations leave screen to top
# boundary: when bottom of ship leaves top of screen remove it. will only leave through top of screen
# delete: remove ship from shiplist and spritelist when its health is gone
class LargePlane(pygame.sprite.Sprite):
    def __init__(self, imgFile, xStart, yStart, xspeed, yspeed, phase, itr, fire, health):
        super().__init__()
        self.image = pygame.transform.scale(imgFile, (160, 120))
        self.rect = self.image.get_rect(center=(xStart, yStart))
        self.xStart, self.yStart, self.xspeed, self.yspeed, self.phase, self.itr, self.fire, self.health = \
            xStart, yStart, xspeed, yspeed, phase, itr, fire, health

    def flyGreen(self):

        if self.itr == 7:
            self.phase = 3

        if self.phase == 0:
            self.rect.centery -= self.yspeed
            if self.rect.centery <= vSize // 2.5:
                self.phase = 1
                self.itr += 1
        elif self.phase == 1:
            self.rect.centerx += self.xspeed
            if self.rect.centerx >= 4 * hSize // 5:
                self.phase = 2
                self.itr += 1
        elif self.phase == 2:
            self.rect.centerx -= self.xspeed
            if self.rect.centerx <= hSize // 5:
                self.phase = 1
                self.itr += 1
        elif self.phase == 3:
            self.rect.centery -= self.yspeed
            self.rect.centerx += 1

    def boundary(self, shipList, spriteList):
        if self.rect.bottom <= 0:
            self.delete(spriteList, shipList)

    def delete(self, spriteList, shipList):
        shipList.remove(self)
        spriteList.remove(self)


# Class for creating the background sprites, nothing special just creating a screen sized sprite, later functions will
# move it
class Background(pygame.sprite.Sprite):
    def __init__(self, imgFile, xStart, yStart):
        super().__init__()
        self.image = pygame.transform.scale(imgFile, (hSize, vSize))
        self.rect = self.image.get_rect(center=(xStart, yStart))
        self.xStart, self.yStart = xStart, yStart


# https://stackoverflow.com/questions/25221036/pygame-music-pause-unpause-toggle
# For pausing the music, mostly because it is annoying after .1 seconds.
# idea is getting the state of the music track (playing or paused) and will either play or pause it depending on
# whether it's true or false
class Pause(object):
    def __init__(self):
        self.paused = pygame.mixer.music.get_busy()

    def toggle(self):
        if self.paused:
            pygame.mixer.music.unpause()
        if not self.paused:
            pygame.mixer.music.pause()
        self.paused = not self.paused


# function that will create two small green planes, idea is that two diver planes will spawn, not on top of each other
# and dive down towards the player there is no collision between planes so overlapping down the same path is very
# possible
def makeSmallPlane(image, planeList, all_sprites_list):
    x = []
    for i in range(0, 2):
        x.append(random.randint(1, 5))
    while x[0] == x[1]:
        x[1] = random.randint(1, 5)
    for i in range(0, 2):
        GS = SmallPlane(image, hSize // x[i], 0, 0, 0, False, False, 0, 1)
        planeList.append(GS)
        all_sprites_list.add(GS)

    return planeList, all_sprites_list


# create the small silver plane and add it to the lists, spawns in at a random spot on top of screen and will dive down
# to the left or right alternating depending on if alt is negative or positive
def makeSmallSilver(image, planeList, all_sprites_list):
    global alt
    alt *= -1
    x = alt * 1
    GS = SmallPlane(image, hSize // random.randint(1, 5), 0, x, 5, False, False, 0, 1)
    planeList.append(GS)
    all_sprites_list.add(GS)

    return planeList, all_sprites_list


# make the medium planes and give them health
def makeMediumPlane(image, planeList, all_sprites_list):
    gm = MediumPlane(image, 8 * hSize // 10, 0, 3, 3, 0, 0, False, 3)
    planeList.append(gm)
    all_sprites_list.add(gm)


# make the large plane and give it health
def makeLargePlane(image, planeList, all_sprites_list):
    gl = LargePlane(image, 4 * hSize // 5, vSize + vSize // 20, 2, 2, 0, 0, False, 5)
    planeList.append(gl)
    all_sprites_list.add(gl)


# used to calculate "trajectory" of the small green planes, basically it will find the slope between the two, divide
# by 100 to get a smaller value and return the values for later calling. Not perfect, planes will slow down closer
# and closer they get to the player. Its a feature
def calculate(enemyx, enemyy, playerx, playery):
    x = playerx - enemyx
    y = playery - enemyy
    x /= 100
    y /= 100

    return x, y


# This function is responsible for "stitching" the background segments into one large image to imitate scrolling
# Basically, 3 background images are used, an island, ocean and the carrier.
# Carrier: indicates beginning and end of level
# island: decorative
# ocean: fill in space
# all three are stored in an array and called to when they are needed.
# when a new background is created eg. bgi its y location is on top of the previous background image
def bgstitch():
    bg = []  # the total "stitched" image

    # Currently the Three images being used, an Island, the carrier and plain old ocean
    CA = pygame.image.load('CarrierBG.png').convert_alpha()
    OC = pygame.image.load('OceanBG.png').convert_alpha()
    IS = pygame.image.load('IslandBG.png').convert_alpha()

    # Coordinates, make things look cleaner
    x = hSize // 2
    y = vSize
    # Loop for "creating" the large image. What really is happening here is loading each image into a background sprite
    # class and making the coordinates of them right on top of the other. So in the end all images will look like one
    # large picture instead of 7 different ones.
    for i in range(0, 8):
        # Values of i indicate what picture is being used, carrier first and last, two islands, water inbetween
        if i == 0 or i == 6:
            bg.append(Background(CA, x, y // 2 - (i * y)))
        elif i == 1 or i == 3 or i == 5:
            bg.append(Background(OC, x, y // 2 - (i * y)))
        elif i == 2 or i == 4:
            bgi = Background(IS, x, y // 2 - (i * y))
            # To create a little variety, flip the image of one of the islands to make it look "different"
            if i == 4:
                bgi.image = pygame.transform.flip(bgi.image, True, False)
            bg.append(bgi)

    return bg


# Taking in the group of background images put together from bgstich\
# and just moving them yspeed ( 1) to make the background move
def background(group, speed):
    for g in group:
        g.rect.centery += speed
        g.rect.centery += speed


# function that "hold" all the player/ai/rocket sprites, make main a little bit cleaner
# and create the 1942 logo with specific scale
def spriteImages():
    rocketImg = pygame.image.load('Rockets.png').convert_alpha()
    enemyRocket = pygame.image.load('enrocket.png').convert_alpha()

    player = pygame.image.load('PlayerShip.png').convert_alpha()

    greenS = pygame.image.load('SmallGreen.png').convert_alpha()
    silverS = pygame.image.load('SmallSilver.png').convert_alpha()
    greenM = pygame.image.load('MediumGreen.png').convert_alpha()
    greenL = pygame.image.load('LargeGreen.png').convert_alpha()

    logo = pygame.image.load('main.png').convert_alpha()
    logo = pygame.transform.scale(logo, (3 * hSize // 4, vSize // 5))

    return rocketImg, enemyRocket, player, greenS, silverS, greenM, greenL, logo


# starting menu when game first launched, PAUSE is the object responsible for playing/ pausing "music" on press of m
# Space bar will start the game by telling gameOn is true
# two string lines to guide user and of course update the screen to show it
def mainMenu(logo, PAUSE):
    global gameOn
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_m:
                    PAUSE.toggle()
                if event.key == pygame.K_RETURN:
                    gameOn = True
                    return False

        text = gameFont.render("Press Return to Begin", True, WHITE, BLACK)
        textRect = text.get_rect()
        textRect.center = hSize // 2, vSize // 2

        text2 = gameFont.render("Press M to pause music", True, WHITE, BLACK)
        textRect2 = text2.get_rect()
        textRect2.center = hSize // 2, vSize // 2 + vSize // 20

        window.fill(BLACK)
        window.blit(text, textRect)
        window.blit(text2, textRect2)

        window.blit(logo, (hSize // 7, vSize // 4))
        pygame.display.update()


# Updates the value of score in the specific location (top left of screen) as well as tell how many lives are left
# score carriers between leveles, other values do not
def score(lives):
    global totalScore
    totalScore, lives = str(totalScore), str(lives)
    text = gameFont.render("" + totalScore + "    " + lives + " UP", True, WHITE)
    textRect = text.get_rect()
    textRect.left, textRect.top = 50, 20
    window.blit(text, textRect)
    totalScore, lives = int(totalScore), int(lives)


# end level stats, specific to that level.
# will be called on both death and end of level, reset when move to next level
# Enter will continue game dead determines if player will restart on the same level, or go to next
def levelStats(PAUSE, background_group, bg, dead):
    text = []
    textRect = []
    global totalScore, fires, hits, misses, destroyed, gameOn, level

    # will get a divide by 0 error if no shots are fired when computing avg, so make avg 0 if no shots fired
    if fires == 0:
        avg = 0
    elif fires is not 0:
        avg = 100 * (hits / fires)

    avg = math.floor(avg)  # floor value to get percent

    totalScore, fires, hits, misses, destroyed, avg = str(totalScore), str(fires), str(hits), str(misses), \
                                                      str(destroyed), str(avg)
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_m:
                PAUSE.toggle()
            if event.key == pygame.K_RETURN:
                gameOn = True
                reset(background_group, bg)
                level = int(level)
                if dead == 0:
                    level += 1
                dead = 0
                return

    if dead == 1:
        text.append(gameFont.render("Ship destroyed Try again?", True, WHITE))

    level = str(level)

    # Stats
    text.append(gameFont.render("Level " + level + " Stats", True, WHITE))
    text.append(gameFont.render("Score         " + totalScore + "", True, WHITE))
    text.append(gameFont.render("Shots         " + fires + "", True, WHITE))
    text.append(gameFont.render("Hits          " + hits + "", True, WHITE))
    text.append(gameFont.render("Misses        " + misses + "", True, WHITE))
    text.append(gameFont.render("Destroyed     " + destroyed + "", True, WHITE))
    text.append(gameFont.render("Percent hit   " + avg + "", True, WHITE))
    text.append(gameFont.render("Press Enter to continue", True, WHITE))

    # easier to just make an array of all the text lines above
    for i in range(0, len(text)):
        textRect.append(text[i].get_rect())
        textRect[i].center = hSize // 2, vSize // 2 + i * vSize // 20

    background_group.draw(window)  # Background goes first, not moving but will still be where level ended or death spot

    for i in range(0, len(text)):
        window.blit(text[i], textRect[i])
    # return all values to integers to they can be modified
    totalScore, fires, hits, misses, destroyed, avg, level = int(totalScore), int(fires), int(hits), int(misses), \
                                                             int(destroyed), int(avg), int(level)
    pygame.display.update()
    return dead


# on level end/ death these stats need to be reset, and background will need to be recreated, so delete the old one,
# and make a new one
def reset(background_group, bg):
    global fires, hits, misses, destroyed, counter, totalScore
    totalScore, fires, hits, misses, destroyed = int(totalScore), int(fires), int(hits), int(misses), int(destroyed)

    counter, fires, hits, misses, destroyed = 0, 0, 0, 0, 0
    background_group.remove(bg)
    bg = bgstitch()
    background_group.add(bg)


# in case some ships/rockets are still alive on death/level end, they will still be there on return, so safer to just
# delete all of them and restart again. Pretty dumb way to do it though
def resetShips(greenList, silverList, mediumList, largeList, spriteList, mrl, lrl, srl, r):
    for sg in greenList:
        sg.delete(spriteList, greenList)
    for ss in silverList:
        ss.delete(spriteList, silverList)
    for mg in mediumList:
        mg.delete(spriteList, mediumList)
    for lg in largeList:
        lg.delete(spriteList, largeList)
    for m in mrl:
        m.delete(spriteList, mrl)
    for s in srl:
        s.delete(spriteList, srl)
    for l in lrl:
        l.delete(spriteList, lrl)
    for rocket in r:
        rocket.delete(spriteList, r)


# determines how often a plane will launch
def planeSpawn(greenS, greenList,silverS, silverList,greenM ,mediumList, greenL, largeList, all_sprites_list):
    global counter
    if counter % 100 == 1 and counter >= 100 and counter <= 2000:
        greenList, all_sprites_list = makeSmallPlane(greenS, greenList, all_sprites_list)
    if counter % 60 == 0 and counter >= 100 and counter <= 2000:
        silverList, all_sprites_list = makeSmallSilver(silverS, silverList, all_sprites_list)
    if counter == 225 or counter == 725 or counter == 1225:
        makeMediumPlane(greenM, mediumList, all_sprites_list)
    if counter == 350 or counter == 1000:
        makeLargePlane(greenL, largeList, all_sprites_list)


#Responsible for creating the rockets from enemyShips
def planeFire(enemyplane, rocketlist, enemyRocket, all_sprites_list, i):
    rocket = Enemyrocket(enemyRocket, enemyplane.rect.centerx, enemyplane.rect.centery, 0, 0, i)
    rocketlist.append(rocket)
    all_sprites_list.add(rocket)
    return rocketlist


def lgFire(lg, lrl, enemyRocket, all_sprites_list):
    global counter
    if counter % 75 == 0 and lg.rect.centery <= vSize // 2:
        for i in range(1, 4):
            planeFire(lg, lrl, enemyRocket, all_sprites_list, i)


# For getting key presses space and mute
def gameEvents(ship, rocketImg, r, all_sprites_list):
    global fires, itr
    PAUSE = Pause()  # pause/resume music
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:  #
                fires += 1
                cx, cy = ship.rect.centerx, ship.rect.centery - hSize // 13
                r.append(Rockets(rocketImg, cx, cy, 8))
                all_sprites_list.add(r[itr])
                itr += 1
            if event.key == pygame.K_m:
                PAUSE.toggle()




# General Function for detecting collision between planes and user rockets
def collision(r, enemyplane, enemyplanelist, all_sprites_list, pointsvalue):
    global hits, destroyed, totalScore
    for rocket in r:
        if rocket.collide(enemyplane):
            enemyplane.health -= 1
            rocket.delete(r, all_sprites_list)
            hits += 1
            if enemyplane.health == 0:
                destroyed += 1
                enemyplane.delete(enemyplanelist, all_sprites_list)
                totalScore += pointsvalue  # points for score


# Collision with player plane and enemy plane
def playerCollision(playerplane, enemyplane):
    if playerplane.collide(enemyplane):
        playerplane.livesLeft()
        enemyplane.health -= 1


def greenPlaneFires(gs, ship, enemyRocket, all_sprites_list, srl):
    global run
    # Way used to work without dummy, it would fire multiple rockets on retreat due to issues with
    # calculating x so when dummy is 2 it allows ships to fire only once
    if run == 2:
        # dx, dy of rockets
        x, y = calculate(gs.rect.centerx, gs.rect.centery, ship.rect.centerx, ship.rect.centery)
        x *= 2
        y *= 2
        enrock = Enemyrocket(enemyRocket, gs.rect.centerx, gs.rect.centery, x, y, 0)  # enemy rocket
        all_sprites_list.add(enrock)
        srl.append(enrock)


def enemyRocketCollision(enemyrocket, enemyrocketlist, ship, all_sprites_list):
    if enemyrocket.collide(ship):
        enemyrocket.delete(all_sprites_list, enemyrocketlist)
        ship.livesLeft()  # decrease ship lives


def smallPlaneRockets(srl, all_sprites_list, ship):
    for sr in srl:
        sr.slaunch(all_sprites_list, srl)
        enemyRocketCollision(sr, srl, ship, all_sprites_list)


# statements for medium rockets colliding, count is the "identity" for each rocket in the plus shaped launch
# makes it easier to move specific rockets when another one has been deleted without it, moving rockets was
# a nightmare with an identity, they will move along a predetermined path.
def mediumPlaneRockets(mrl, all_sprites_list, ship):
    for mr in mrl:
        if mr.count == 1:
            mr.mlaunch(all_sprites_list, mrl, 4, 0)
        elif mr.count == 2:
            mr.mlaunch(all_sprites_list, mrl, -4, 0)
        elif mr.count == 3:
            mr.mlaunch(all_sprites_list, mrl, 0, 4)
        elif mr.count == 4:
            mr.mlaunch(all_sprites_list, mrl, 0, -4)
        enemyRocketCollision(mr, mrl, ship, all_sprites_list)


def largePlaneRockets(lrl, all_sprites_list, ship):
    # large rockets, only three, but move in two diagonal and one straight down, if they collide delete it
    for lr in lrl:
        if lr.count == 1:
            lr.mlaunch(all_sprites_list, lrl, 0, 4)
        elif lr.count == 2:
            lr.mlaunch(all_sprites_list, lrl, 4, 4)
        elif lr.count == 3:
            lr.mlaunch(all_sprites_list, lrl, -4, 4)
        enemyRocketCollision(lr, lrl, ship, all_sprites_list)


def playerDeath(dead, greenList, silverList, mediumList, largeList, all_sprites_list, \
                mrl, lrl, srl, r, PAUSE, background_group, bg, ship):
    global gameOn
    if ship.lives == 0:
        gameOn = False
        dead = 1
        dead = levelStats(PAUSE, background_group, bg, dead)
        ship.lives = 3
        resetShips(greenList, silverList, mediumList, largeList, all_sprites_list, mrl, lrl, srl, r)
    return dead


# loop through medium planes alive, fire tells when to launch a missile
def mediumPlaneListLooping(mediumList, all_sprites_list, enemyRocket, ship, mrl, r):
    for mg in mediumList:
        fire = mg.flyGreen()
        mg.boundry(mediumList, all_sprites_list)
        if fire:  # Fire four missiles
            for i in range(1, 5):
                mrl = planeFire(mg, mrl, enemyRocket, all_sprites_list, i)
        collision(r, mg, mediumList, all_sprites_list, 500)
        playerCollision(ship, mg)


# loop through large planes,increase hits, score and destroyed too(end level stats)
def largePlaneListLooping(largeList, all_sprites_list, enemyRocket, ship, lrl, r):
    for lg in largeList:
        lg.flyGreen()
        lg.boundary(largeList, all_sprites_list)
        collision(r, lg, largeList, all_sprites_list, 1000)
        lgFire(lg, lrl, enemyRocket, all_sprites_list)
        playerCollision(ship, lg)


# Looping through the small silver plane list
def smallSilverListLooping(silverList, all_sprites_list, ship, r):
    for sl in silverList:
        sl.flySilver()
        sl.boundary(silverList, all_sprites_list)
        collision(r, sl, silverList, all_sprites_list, 100)
        playerCollision(ship, sl)


# Small Green planes
def smallGreenListLooping(greenList, all_sprites_list, enemyRocket, ship, srl, r):
    global run
    for gs in greenList:
        x = math.sqrt(
            math.pow((ship.rect.centerx - gs.rect.centerx), 2) + math.pow((ship.rect.centery - gs.rect.centery),
                                                                          2))
        run = gs.flyGreen(x, ship.rect.centerx, ship.rect.centery)  # dum int used to tell when fire was used
        gs.boundary(all_sprites_list, greenList)
        collision(r, gs, greenList, all_sprites_list, 200)
        greenPlaneFires(gs, ship, enemyRocket, all_sprites_list, srl)
        playerCollision(ship, gs)


# messy function that is in charge of making all ships, rockets, and a bunch of other stuff.
def main():
    global itr, run, alt, gameOn, totalScore, level, fires, hits, misses, destroyed, counter  # bunch of globals
    alt = 1
    timer = pygame.time.Clock()
    run = 0
    r = []  # Rocket list
    srl = []  # small plane  rocket list
    mrl = []  # medium plane rocket list
    lrl = []  # large plane rocket list
    greenList = []
    silverList = []
    mediumList = []
    largeList = []
    level, totalScore = 1, 0
    hits, misses, fires, destroyed = 0, 0, 0, 0  # all global to take keep track of stats, will reset every level
    dead = 0  # alive on 0, dead on 1
    rocketImg, enemyRocket, player, greenS, silverS, greenM, greenL, logo = spriteImages()

    ship = playerPlane(player, hSize // 2, vSize, 0, 0, 3)

    bg = bgstitch()  # Call the function to stitch all images together and get the array into bg
    background_group = pygame.sprite.Group()  # Create another sprite group so no issues with overlapping will happen
    background_group.add(bg)  # Put background images in the group

    all_sprites_list = pygame.sprite.Group()
    all_sprites_list.add(ship)
    counter, itr = 0, 0  # Counter- counts length of level, itr- track of user rockets
    pygame.mixer.music.load('intro.wav')  # terrible game music but authentic
    pygame.mixer.music.set_volume(0.2)  # quiter
    pygame.mixer.music.play(-1)
    gameOn = False  # off by default wait for mainMenu to set it to true

    PAUSE = Pause()  #Pause music object
    mainMenu(logo, PAUSE)  # pass in PAUSE to pause music there too

    while True: # outer while loop for when user dies and wants to continue and prevent program closing
        while gameOn:
            timer.tick(60)
            ship.movement()
            ship.boundary()

            gameEvents(ship, rocketImg, r, all_sprites_list)

            for rocket in r:
                rocket.launch(r, all_sprites_list)

            planeSpawn(greenS, greenList,silverS, silverList,greenM ,mediumList, greenL, largeList, all_sprites_list)

            # looping through all groups of enemy planes
            mediumPlaneListLooping(mediumList, all_sprites_list, enemyRocket, ship, mrl, r)
            largePlaneListLooping(largeList, all_sprites_list, enemyRocket, ship, lrl, r)
            smallSilverListLooping(silverList, all_sprites_list, ship, r)
            smallGreenListLooping(greenList, all_sprites_list, enemyRocket, ship, srl, r)

            # enemy rocket collisions
            smallPlaneRockets(srl, all_sprites_list, ship)
            mediumPlaneRockets(mrl, all_sprites_list, ship)
            largePlaneRockets(lrl, all_sprites_list, ship)

            #behavior when counter gets to certain value
            if counter < vSize * 3:
                background(background_group, 1)
                counter += 1
            elif counter >= vSize * 2.9:
                dead = 0
                gameOn = False

            #check for player health
            dead = playerDeath(dead, greenList, silverList, mediumList, largeList, all_sprites_list, \
                        mrl, lrl, srl, r, PAUSE, background_group, bg, ship)

            background_group.draw(window)
            score(ship.lives)
            all_sprites_list.draw(window)
            pygame.display.update()

        # statement for when the game loop is over( end of level, or death)
        while gameOn == False:
            dead = levelStats(PAUSE, background_group, bg, dead)  # dead is passed returned here to update, and
            resetShips(greenList, silverList, mediumList, largeList, all_sprites_list, mrl, lrl, srl, r)


main()
