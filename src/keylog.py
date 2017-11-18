""" This module enables logging of keyboard inputs sent to the Dolphin emulator. """

import enum
import logging
import json
import threading
import os
from pynput import keyboard
from src import dolphinscreenshot, helper

logger = logging.getLogger(__name__)


@enum.unique
class Keyboard(enum.Enum):
    """ Default Dolphin keyboard map """
    none = 0  # Neutral controller state
    x = 1  # PRESS A
    z = 2  # PRESS B
    c = 3  # PRESS X
    s = 4  # PRESS Y
    d = 5  # PRESS Z
    left = 6  # PRESS LEFT
    right = 7  # PRESS RIGHT
    up = 8  # PRESS UP
    down = 9  # PRESS DOWN
    enter = 10  # PRESS ENTER


class KeyLog():
    """ Class allowing user to listen for, record, and save keyboard inputs. """

    def __init__(self, logging_delay=0.3):
        """ Create KeyLog instance.

        Args:
            logging_delay: Amount of time to wait before checking keyboard state again in
                seconds.
        """
        self.state = dict((el.name, False) for el in Keyboard)
        self.count = 1
        self.log = {"data": []}
        self.finish = False
        self.logging_freq = logging_delay

    # Collect events until released
    def start(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            self.record()
            listener.join()
            logger.info("Key logging session finished.")

    def on_press(self, key):
        try:
            value = self._get_key_value(key)
            if not self.state[Keyboard[value].name]:
                self.state[Keyboard[value].name] = True
                logger.debug('key {} pressed {}'.format(value, self.state[Keyboard[value].name]))
        except KeyError:
            logger.warning("Pressed key not defined within allowable controller inputs.")

    def on_release(self, key):
        try:
            value = self._get_key_value(key)
            if self.state[Keyboard[value].name]:
                self.state[Keyboard[value].name] = False
                logger.debug('{} released {}'.format(value, self.state[Keyboard[value].name]))
        except KeyError:
            if key == keyboard.Key.esc:
                self.finish = True
                # save_dolphin_state key press log
                self.save_to_file()
                # Stop listener
                return False

    def record(self):
        if self.finish: return
        threading.Timer(self.logging_freq, self.record).start()
        dolphinscreenshot.take_screenshot()
        self.log['data'].append({
            "count": self.count,
            "presses": dict(self.state)
        })
        self.count += 1

    def save_to_file(self, file_name="log.json"):
        output_dir = helper.get_output_folder()
        with open(os.path.join(output_dir, file_name), 'w') as f:
            json.dump(self.log, f)

    @staticmethod
    def _get_key_value(key):
        try:
            # regular key
            return key.char
        except AttributeError:
            # special key
            return key.name
