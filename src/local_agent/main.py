import time

from src.local_agent.collector.keyboard_collector import Keyboard_collector
from src.local_agent.collector.mouse_collector import Mouse_collector
from src.local_agent.buffer.event_buffer import EventBuffer

def handle_event(event):
    event_buffer.add_event(event)

    # Temporary: print events so we can verify everything works
    print(event)



event_buffer = EventBuffer()

keyboard_collector = Keyboard_collector(handle_event)
mouse_collector = Mouse_collector(handle_event)


keyboard_collector.start()
mouse_collector.start()

print("Sentinel local agent started.")
print("Keyboard and mouse collection active.")
print("Press Ctrl+C to stop.")


try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping Sentinel local agent...")

    keyboard_collector.stop()
    mouse_collector.stop()

    print("Keyboard collector stopped.")
    print("Mouse collector stopped.")
    print(f"Events collected: {event_buffer.size()}")