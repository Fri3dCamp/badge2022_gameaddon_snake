# Note that this is very bad 'weekend project'
# Python and is not at all representative
# of how things should be programmed in any
# serious environment.

# This is snake on an ESP8266 with this
# I2C oled (I got it from here https://www.banggood.com/Geekcreit-WiFi-ESP8266-Starter-Kit-IoT-NodeMCU-Wireless-I2C-OLED-Display-DHT11-Temperature-Humidity-Sensor-Module-p-1544116.html)
# and an analog joystick (mine is from here https://www.banggood.com/Geekcreit-37-In-1-Sensor-Module-Board-Set-Starter-Kits-Geekcreit-products-that-work-with-official-Arduino-boards-p-1137051.html)

# Because the ESP8266 only has one analog
# input data pin and I did not implement
# a clock timer to sample from two inputs
# the joystick can only do 'left' and 'up'
# as 'on' and 'off' inputs. For snake this
# is enough to send the snake left and right.

import urandom
import sys

from ucollections import OrderedDict
from machine import Pin, I2C, PWM, sleep

# ESP8266 Pin assignment
import color
from fri3d import BADGE

i2c = I2C(-1, scl=Pin(5), sda=Pin(4))

GAME_ON

joy1 = Pin(12, Pin.IN, Pin.PULL_UP)
joy2 = Pin(13, Pin.IN, Pin.PULL_UP)
joy3 = Pin(15, Pin.IN, Pin.PULL_UP)

mice = dict()
mousecount = 0
score = 0
mouse_amount = 4


# https://forum.micropython.org/viewtopic.php?t=6158
def randint(min, max):
    span = max - min + 1
    div = 0x3fffffff // span
    offset = urandom.getrandbits(30) // div
    val = min + offset
    return val


def read_joystick():
    data = {
        'joy_click': not joy1.value(),
        'joy_left': joy3.value(),
        'joy_up': not joy2.value()
    }
    return data


def beep(beeplen):
    beeper = PWM(Pin(14), freq=440, duty=512)
    sleep(beeplen)
    beeper.deinit()


def draw(y, x):
    BADGE.display().pixel(x, y, color.GREEN)
    BADGE.display().show()


def game_over():
    global score
    beep(1000)
    BADGE.display().fill(color.BLACK)
    BADGE.display().text('Game Over', 0, 20, )
    oled.fill(0)
    oled.text('Game Over', 0, 20)
    oled.text('Click 4 new game', 0, 40)
    oled.show()
    score = 0


def update_score(score):
    for x in range(30):
        for y in range(10):
            oled.pixel(x, y, 0)
    oled.text("{}".format(score), 0, 0)


def draw_mouse(x, y, mousenr, size=4):
    global mice
    global mousecount
    draw_y = y
    for i_y in range(size):
        draw_x = x
        for i_x in range(size):
            mouse_x, mouse_y = draw_x + i_x, draw_y + i_y
            oled.pixel(mouse_x, mouse_y, 1)
            mice[(mouse_x, mouse_y)] = mousenr
    mousecount += 1


def generate_mice(amount=3):
    global mice
    global score
    offset = max(mice.values()) if mice else 0
    for mousenr in range(1, amount):
        if score < 100:
            max_size = 4
        elif score < 250:
            max_size = 6
        elif score < 1000:
            max_size = 8
        elif score < 2000:
            max_size = 10
        else:
            max_size = 12
        size = randint(4, max_size)
        x_rand = randint(size, oled_width - size)
        y_rand = randint(size, oled_height - size)
        draw_mouse(x_rand, y_rand, offset + mousenr, size=size)


def start_game():
    global mice
    global mousecount
    global score
    global mouse_amount
    oled.fill(0)
    grid = OrderedDict()
    snakelen = 15
    y = 32
    x = 64
    direction = 0
    prevscore = -1
    prevdata = read_joystick()
    generate_mice(3)
    while True:
        generate_mice(mouse_amount - mousecount)
        # snake hit itself
        if grid.get((x, y)):
            return

        # hit mouse
        mouse_nr = mice.get((x, y))
        if mouse_nr:
            mouse_blocks = []
            for mousexy, mousenr in mice.items():
                if mousenr == mouse_nr:
                    mouse_blocks.append(mousexy)
            for mousexy in mouse_blocks:
                del mice[mousexy]
                mouse_x, mouse_y = mousexy
                oled.pixel(mouse_x, mouse_y, 0)
                score += 1
            mouse_amount = randint(3, 5)
            mousecount -= 1
            beep(100)
            snakelen += 5

        grid[(x, y)] = 1
        while len(grid) > snakelen:
            snaketail_k, snaketail_v = list(grid.items())[0]
            snaketail_x, snaketail_y = snaketail_k
            oled.pixel(snaketail_x, snaketail_y, 0)
            del grid[(snaketail_x, snaketail_y)]

        draw(y, x)
        data = read_joystick()
        if data['joy_up'] and not prevdata['joy_up']:
            direction += 1
        if data['joy_left'] and not prevdata['joy_left']:
            direction -= 1
        if x > 127:
            x = 1
        if y > 63:
            y = 1
        if x < 1:
            x = 127
        if y < 1:
            y = 63
        if direction >= 4:
            direction = 0
        if direction < 0:
            direction = 3
        if direction == 0:
            x += 1
        if direction == 1:
            y += 1
        if direction == 2:
            x -= 1
        if direction == 3:
            y -= 1
        if score != prevscore:
            update_score(score)
        prevdata = data
        prevscore = score


while True:
    start_game()
    game_over()
    while True:
        data = read_joystick()
        if data['joy_click']:
            break