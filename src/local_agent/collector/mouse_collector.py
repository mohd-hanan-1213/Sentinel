import time
import math
from pynput import mouse
class Mouse_collector:
    def __init__(self,event_callback):
        self.event_callback=event_callback
        self.last_position=None
        self.last_moveTime=None
        self.click_press_times={}

        self.listener=None

    def on_move(self,x,y):
        timestamp = time.time()
        if self.last_position is None:
            self.last_position=(x,y)
            self.last_moveTime=timestamp
            event = {
                "event_type": "mouse_move",
                "timestamp": timestamp,
                "data": {
                    "x": x,
                    "y": y,
                    "distance":0,
                    "speed":0
                }
            }
            self.event_callback(event)
            return
        last_x,last_y=self.last_position
        dist=math.sqrt(
            (x-last_x)**2+(y-last_y)**2
        )
        timedifference=timestamp-self.last_moveTime
        if timedifference>0:
            speed=dist/timedifference
        else:
            speed=0
        event={
            "event_type":"mouse_move",
            "timestamp":timestamp,
            "data":{
                "x":x,
                "y":y,
                "distance":dist,
                "speed":speed
            }
        }
        self.event_callback(event)
        self.last_position=(x,y)
        self.last_moveTime=timestamp

    def on_click(self,x,y,button,pressed):
        timestamp=time.time()
        button_id=str(button)
        if pressed:
            self.click_press_times[button_id]=time.time()
            event={
                "event_type":"mouse_click_press",
                "timestamp":timestamp,
                "data":{
                    "x":x,
                    "y":y,
                    "button":button_id
                }
            }
            self.event_callback(event)
        else:
            press_time=self.click_press_times.pop(
                button_id,
                None
            )
            click_duration=None
            if press_time is not None:
                click_duration=time.time()-press_time

            event={
                "event_type": "mouse_click_release",
                "timestamp": timestamp,
                "data": {
                    "x": x,
                    "y": y,
                    "button": button_id,
                    "click_duration": click_duration
                }
            }
            self.event_callback(event)

    def on_scroll(self,x,y,dx,dy):
        timestamp=time.time()
        event={
            "event_type":"mouse_scrooll",
            "timestamp":timestamp,
            "data":{
                "dx":dx,
                "dy":dy
            }
        }
        self.event_callback(event)

    def start(self):
        self.listener=mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.listener.start()

    def stop(self):
        if self.listener is not None:
            self.listener.stop()



if __name__ == "__main__":

    def print_event(event):
        print(event)

    collector = Mouse_collector(print_event)

    collector.start()

    print("Mouse collector started. Move, click, or scroll. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        collector.stop()

        print("\nMouse collector stopped.")