import random
from os.path import dirname, join

from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.skills.audioservice import AudioService
from mycroft.audio import wait_while_speaking
from mycroft.util.parse import extract_datetime
from mycroft.util.time import now_local


class WhitenoiseSkill(MycroftSkill):
    def __init__(self):
        super(WhitenoiseSkill, self).__init__(name="WhitenoiseSkill")
        self.process = None
        self.start_time = 0
        self.last_index = 24  # index of last pixel in countdowns
        self.settings["duration"] = -1  # default = unknown

        self.play_list_all = {
            0: join(dirname(__file__), "popey-whitenoise.mp3"),
            1: join(dirname(__file__), "popey-whitenoiseocean.mp3"),
            2: join(dirname(__file__), "popey-whitenoiserain.mp3"),
            3: join(dirname(__file__), "popey-whitenoisewave.mp3"),
        }
        self.play_list_ocean = {
            0: join(dirname(__file__), "popey-whitenoiseocean.mp3"),
        }
        self.play_list_rain = {
            0: join(dirname(__file__), "popey-whitenoiserain.mp3"),
        }
        self.play_list_wave = {
            0: join(dirname(__file__), "popey-whitenoisewave.mp3"),
        }

    def initialize(self):
        self.audioservice = AudioService(self.bus)
        self.add_event("mycroft.whitenoise", self.whitenoise, False)

    def whitenoise(self, message):
        self.process = play_mp3(self.play_list_all[0])

    @staticmethod
    def stop_process(process):
        if process.poll() is None:  # None means still running
            process.terminate()
            # No good reason to wait, plus it interferes with
            # how stop button on the Mark 1 operates.
            # process.wait()
            return True
        else:
            return False

    # Show a countdown using the eyes
    def render_countdown(self, r_fore, g_fore, b_fore):
        display_owner = self.enclosure.display_manager.get_active()
        if display_owner == "":
            # Initialization, first time we take ownership
            self.enclosure.mouth_reset()  # clear any leftover bits
            self.enclosure.eyes_color(r_fore, g_fore, b_fore)  # foreground
            self.last_index = 24

        if display_owner == "AudioRecordSkill":
            remaining_pct = self.remaining_time() / self.settings["duration"]
            fill_to_index = int(24 * remaining_pct)
            while self.last_index > fill_to_index:
                if self.last_index < 24 and self.last_index > -1:
                    # fill background with gray
                    self.enclosure.eyes_setpixel(self.last_index, 64, 64, 64)
                self.last_index -= 1

    @intent_handler(IntentBuilder('').require('Whitenoise'))
    def handle_whitenoise(self, message):
        path = random.choice(self.play_list)
        try:
            self.speak_dialog('whitenoise.response')
            wait_while_speaking()
            self.audioservice.play(path)
        except Exception as e:
            self.log.error("Error: {0}".format(e))

    @intent_handler(IntentBuilder('').require('whitenoise.time.intent'))
    def handle_whitenoise_time(self, message):
        utterance = message.data.get('utterance')

        # Calculate how long to record
        self.start_time = now_local()
        stop_time, _ = extract_datetime(utterance, lang=self.lang)
        self.settings["duration"] = (stop_time -
                                     self.start_time).total_seconds()
        if self.settings["duration"] <= 0:
            self.settings["duration"] = 60  # default recording duration

        # Initiate white noise
        path = random.choice(self.play_list_all)
        try:
            time_for = nice_duration(self, self.settings["duration"],
                                       lang=self.lang)
            self.speak_dialog('whitenoise.response.time', {'duration': time_for})
            wait_while_speaking()
            self.audioservice.play(path)
            # self.process = play_mp3(self.play_list_all[0])

            self.enclosure.eyes_color(255, 0, 0)  # set color red
            self.last_index = 24
            self.schedule_repeating_event(self.recording_feedback, None, 1,
                                          name='RecordingFeedback')

        except Exception as e:
            self.log.error("Error: {0}".format(e))

    def recording_feedback(self, message):
        if not self.process:
            self.end_whitenoise()
            return

        # Show recording countdown
        self.render_countdown(255, 0, 0)

    def end_whitenoise(self):

        if self.process:
            # Stop recording
            self.stop_process(self.process)
            self.process = None
            # Calc actual recording duration
            self.settings["duration"] = (now_local() -
                                         self.start_time).total_seconds()

    def stop(self):
        if self.process and self.process.poll() is None:
            self.speak_dialog('whitenoise.stop')
            self.process.terminate()
            self.process.wait()


def create_skill():
    return WhitenoiseSkill()


##########################################################################
# TODO: Move to mycroft.util.format
from mycroft.util.format import pronounce_number


def nice_duration(self, duration, lang="en-us", speech=True):
    """ Convert duration in seconds to a nice spoken timespan

    Examples:
       duration = 60  ->  "1:00" or "one minute"
       duration = 163  ->  "2:43" or "two minutes forty three seconds"

    Args:
        duration: time, in seconds
        speech (bool): format for speech (True) or display (False)
    Returns:
        str: timespan as a string
    """

    # Do traditional rounding: 2.5->3, 3.5->4, plus this
    # helps in a few cases of where calculations generate
    # times like 2:59:59.9 instead of 3:00.
    duration += 0.5

    days = int(duration // 86400)
    hours = int(duration // 3600 % 24)
    minutes = int(duration // 60 % 60)
    seconds = int(duration % 60)

    if speech:
        out = ""
        if days > 0:
            out += pronounce_number(days, lang) + " "
            if days == 1:
                out += self.translate("day")
            else:
                out += self.translate("days")
            out += " "
        if hours > 0:
            if out:
                out += " "
            out += pronounce_number(hours, lang) + " "
            if hours == 1:
                out += self.translate("hour")
            else:
                out += self.translate("hours")
        if minutes > 0:
            if out:
                out += " "
            out += pronounce_number(minutes, lang) + " "
            if minutes == 1:
                out += self.translate("minute")
            else:
                out += self.translate("minutes")
        if seconds > 0:
            if out:
                out += " "
            out += pronounce_number(seconds, lang) + " "
            if seconds == 1:
                out += self.translate("second")
            else:
                out += self.translate("seconds")
    else:
        # M:SS, MM:SS, H:MM:SS, Dd H:MM:SS format
        out = ""
        if days > 0:
            out = str(days) + "d "
        if hours > 0 or days > 0:
            out += str(hours) + ":"
        if minutes < 10 and (hours > 0 or days > 0):
            out += "0"
        out += str(minutes)+":"
        if seconds < 10:
            out += "0"
        out += str(seconds)

    return out
