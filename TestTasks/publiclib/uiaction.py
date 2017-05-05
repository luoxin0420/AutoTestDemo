__author__ = 'Xuxh'


from selenium.webdriver.common.by import By
from appium.webdriver.common.touch_action import TouchAction


class UIAction(object):

    def __init__(self, uid, driver):

        self.uid = uid
        self.driver = driver

    def find_element(self,element):

        if element['GroupFlag'] != 1:

            els={
                1: lambda: self.driver.find_element(By.ID, element['Value']),
                2: lambda: self.driver.find_element(By.CLASS_NAME, element['Value']),
                3: lambda: self.driver.find_element(By.NAME, element['Value']),
                4: lambda: self.driver.find_element(By.XPATH, element['Value'])
           }[element['LOCATE_TYPE_id']]()

        elif element['GroupFlag'] == 1 and element['index'] !=999:

            els={
                1: lambda: self.driver.find_elements(By.ID, element['Value'])[element['index']],
                2: lambda: self.driver.find_elements(By.CLASS_NAME, element['Value'])[element['index']],
                3: lambda: self.driver.find_elements(By.NAME, element['Value'])[element['index']],
                4: lambda: self.driver.find_elements(By.XPATH, element['Value'])[element['index']]
            }[element['LOCATE_TYPE_id']]()

        else:
            els={
                1: lambda: self.driver.find_elements(By.ID, element['Value']),
                2: lambda: self.driver.find_elements(By.CLASS_NAME, element['Value']),
                3: lambda: self.driver.find_elements(By.NAME, element['Value']),
                4: lambda: self.driver.find_elements(By.XPATH, element['Value'])
           }[element['LOCATE_TYPE_id']]()

        return els

    def clear_element_attribute(self,element):

        try:
            element = self.find_element(element)
            length = len(element.get_attribute("name"))
            i = 0
            while i < length:
                self.driver.press_keycode(22) #KEYCODE_DPAD_RIGHT
                i += 1
            while i >= 0:
                self.driver.press_keycode(67) #KEYCODE_DEL
                i -= 1
        except Exception, ex:
            print ex

    def get_element_attributes(self, element, attr_name):

        value = ''

        try:
            element = self.find_element(element)
            value = element.get_attribute(attr_name)
        except Exception, ex:
            print ex

        return value

    def get_element_center_location(self,element):

        try:
            element = self.find_element(element)
            x = element.location['x']
            y = element.location['y']
            width = element.size['width']
            height = element.size['height']
            x1 = x + width/2
            y1 = y + height/2
            return x1, y1
        except Exception,ex:
            return ex

    def get_screen_center_location(self):

        height = 0
        width = 0

        try:
            height = self.driver.get_window_size()['height']/2
            width = self.driver.get_window_size()['width']/2

        except Exception,ex:
            print ex

        return height, width

    def long_press_element(self, element):

        el = self.find_element(element)
        action = TouchAction(self.driver)
        action.long_press(el).wait(1000).perform()

        # the other method
        # action2 = TouchAction(self.driver)
        # el = self.driver.find_element_by_id('XXXXX2')
        # action2.moveTo(el).release().perform()

    def swipe_screen(self,value):


        x1,y1,x2,y2 = value.split(',')

        self.driver.swipe(int(x1),int(y1),int(x2),int(y2),500)

    def click_keycode(self, value):

        self.driver.press_keycode(value)


if __name__ == '__main__':

    pass