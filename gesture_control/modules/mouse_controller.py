import pyautogui
import numpy as np
from time import time
import screen_brightness_control as sbc
from pynput.keyboard import Key, Controller
import subprocess

class MouseController:
    def __init__(self, smoothing=5, screen_size=(1920, 1080)):
        self.smoothing = smoothing
        self.screen_size = screen_size
        self.prev_positions = []
        self.last_click_time = 0
        pyautogui.FAILSAFE = False
        self.keyboard = Controller()
        self.is_dragging = False
        self.volume_change_time = 0
        self.brightness_change_time = 0

    def move_cursor(self, hand_pos, frame_size):
        x, y = hand_pos
        frame_w, frame_h = frame_size

        # Convert coordinates
        screen_x = np.interp(x, (0, frame_w), (0, self.screen_size[0]))
        screen_y = np.interp(y, (0, frame_h), (0, self.screen_size[1]))

        # Apply smoothing
        self.prev_positions.append((screen_x, screen_y))
        if len(self.prev_positions) > self.smoothing:
            self.prev_positions.pop(0)
        
        avg_x = sum(p[0] for p in self.prev_positions) / len(self.prev_positions)
        avg_y = sum(p[1] for p in self.prev_positions) / len(self.prev_positions)

        pyautogui.moveTo(avg_x, avg_y)

    def perform_action(self, gesture):
        current_time = time()
        
        if gesture == "LEFT_CLICK" and current_time - self.last_click_time > 0.5:
            pyautogui.click()
            self.last_click_time = current_time
        
        elif gesture == "DOUBLE_CLICK":
            pyautogui.doubleClick()
            self.last_click_time = current_time
        
        elif gesture == "RIGHT_CLICK" and current_time - self.last_click_time > 0.5:
            pyautogui.rightClick()
            self.last_click_time = current_time
        
        elif gesture == "SCROLL":
            pyautogui.scroll(10)
        
        elif gesture == "DRAG":
            if not self.is_dragging:
                pyautogui.mouseDown()
                self.is_dragging = True
        else:
            if self.is_dragging:
                pyautogui.mouseUp()
                self.is_dragging = False

        # Volume control
        if gesture == "VOLUME_UP" and current_time - self.volume_change_time > 0.5:
            self.keyboard.press(Key.media_volume_up)
            self.keyboard.release(Key.media_volume_up)
            self.volume_change_time = current_time
        
        elif gesture == "VOLUME_DOWN" and current_time - self.volume_change_time > 0.5:
            self.keyboard.press(Key.media_volume_down)
            self.keyboard.release(Key.media_volume_down)
            self.volume_change_time = current_time

        # Brightness control
        if gesture == "BRIGHTNESS_UP" and current_time - self.brightness_change_time > 0.5:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(min(current + 10, 100))
            self.brightness_change_time = current_time
        
        elif gesture == "BRIGHTNESS_DOWN" and current_time - self.brightness_change_time > 0.5:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(max(current - 10, 0))
            self.brightness_change_time = current_time

        # Screenshot
        elif gesture == "SCREENSHOT":
            pyautogui.screenshot('screenshot.png')
