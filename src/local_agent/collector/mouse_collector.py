import time
from pynput import mouse
class Mouse_collector:
    def __init__(self,event_callback):
        self.event_callback=event_callback
        self.listener=None

    def on_move(self,x,y):
        timestamp = time.time()
        event = {
            "event_type": "mouse_move",
            "timestamp": timestamp,
            "data": {
                "x": x,
                "y": y
            }
        }
        self.event_callback(event)
    def on_click(self,x,y,button,pressed):
        timestamp=time.time()
        event_type=(
            "mouse_click_press"
            if pressed
            else "mouse_click_release"
        )
        event={
            "event_type":event_type,
            "timestamp":timestamp,
            "data":{
                "x":x,
                "y":y,
                "button":str(button)
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