from pynput import keyboard
def what_type(key):

    print("you pressed: ",key)

with keyboard. Listener(on_press = what_type) as listiner:
    listiner.join()
