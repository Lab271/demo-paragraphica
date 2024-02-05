from gpiozero import RotaryEncoder, PWMLED, Button
from gpiozero.tools import scaled_half
from signal import pause

style = ["Photo", "Painting", "Monet", "SciFi", "Anime"]
def print_style(r):
    print("Style: " + style[int((r.value+1)/2*4)-1])

focal = ["0", "1", "3", "5", "10", "25", "50", "100", "inf"]
def print_focal_length(r):
   print("Focal length: {}".format(focal[9-int((r.value+1)/2*8)-1]))


def print_focus(r):
    print("Focus: {:3.1f}%".format((1-(r.value+1)/2)*100.0))

def print_but(col, but):
    print("{} Button pressed".format(col))

if __name__ == '__main__':
    rot1 = RotaryEncoder(5, 6, wrap=True, max_steps=2)
    rot2 = RotaryEncoder(16, 17, wrap=True, max_steps=4)
    rot3 = RotaryEncoder(18, 19, wrap=True, max_steps=7)
    but1 = Button(22)
    but2 = Button(23)
    led = PWMLED(24)
    led.source = scaled_half(rot3.values)
    rot1.when_rotated = print_style
    rot2.when_rotated = print_focal_length
    rot3.when_rotated = print_focus
    but1.when_pressed = curry(print_but, "Red")
    but2.when_pressed = curry(print_but, "Green")

    pause()