import random
from os.path import dirname, join

from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.skills.audioservice import AudioService
from mycroft.audio import wait_while_speaking


class WhitenoiseSkill(MycroftSkill):
    def __init__(self):
        super(WhitenoiseSkill, self).__init__(name="WhitenoiseSkill")
        self.process = None
        self.play_list = {
            0: join(dirname(__file__), "popey-whitenoise.mp3"),
            1: join(dirname(__file__), "popey-whitenoiseocean.mp3"),
            2: join(dirname(__file__), "popey-whitenoiserain.mp3"),
            3: join(dirname(__file__), "popey-whitenoisewave.mp3"),
        }

    def initialize(self):
        self.audioservice = AudioService(self.bus)
        self.add_event("mycroft.whitenoise", self.whitenoise, False)

    def whitenoise(self, message):
        self.process = play_mp3(self.play_list[0])

    @intent_handler(IntentBuilder('').require('Whitenoise'))
    def handle_whitenoise(self, message):
        path = random.choice(self.play_list)
        try:
            self.speak_dialog('singing')
            wait_while_speaking()
            self.audioservice.play(path)
        except Exception as e:
            self.log.error("Error: {0}".format(e))

    def stop(self):
        if self.process and self.process.poll() is None:
            self.speak_dialog('whitenoise.stop')
            self.process.terminate()
            self.process.wait()


def create_skill():
    return WhitenoiseSkill()
