from flask import Flask, render_template
from flask_socketio import SocketIO
from pynput import mouse
from threading import Thread
import keyboard

app = Flask(__name__)
socketio = SocketIO(app)

class ClickCounter:
    def __init__(self):
        self.click_count = 0
        self.counter_enabled = False  # Counter is initially disabled
        self.app = app

        # Set up mouse listener
        self.mouse_listener = mouse.Listener(on_click=self.on_click)

        # Start a thread to listen for the "p" key
        Thread(target=self.toggle_counter_on_keypress).start()

    def on_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left and self.counter_enabled:
            self.click_count += 20
            self.update_web_page()

    def update_web_page(self):
        socketio.emit('update_click_count', {'click_count': self.click_count}, namespace='/')

    def toggle_counter_on_keypress(self):
        while True:
            if keyboard.is_pressed('p'):
                self.counter_enabled = not self.counter_enabled
                print(f"Counter {'enabled' if self.counter_enabled else 'disabled'}")
                socketio.emit('counter_status', {'enabled': self.counter_enabled}, namespace='/')
                keyboard.wait('p')  # Wait until the key is released to avoid repeated toggling

    def start(self):
        # Start the mouse listener in a separate thread
        thread = Thread(target=self.mouse_listener.start)
        thread.start()
        # Start the Flask-SocketIO app
        socketio.run(self.app, debug=True, use_reloader=False)

    def stop(self):
        # Stop the mouse listener
        self.mouse_listener.stop()
        # Join the listener thread
        self.mouse_listener.join()

if __name__ == "__main__":
    click_counter = ClickCounter()

    @app.route('/')
    def index():
        return render_template('index.html', click_count=click_counter.click_count)

    @socketio.on('connect', namespace='/')
    def handle_connect():
        socketio.emit('update_click_count', {'click_count': click_counter.click_count}, namespace='/')
        socketio.emit('counter_status', {'enabled': click_counter.counter_enabled}, namespace='/')

    click_counter.start()