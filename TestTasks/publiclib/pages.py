__author__ = 'Xuxh'


class BasePage(object):

    def __init__(self, driver):
        self.driver = driver


class SettingSecurity(BasePage):

    def unlock_magazine(self):
        driver = super(SettingSecurity,self).driver
        pass

    def lock_magazine(self):
        pass
