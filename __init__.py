from mycroft import MycroftSkill, intent_file_handler


class Test(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('test.intent')
    def handle_test(self, message):
        self.speak_dialog('test')


def create_skill():
    return Test()

