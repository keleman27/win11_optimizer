import sys
sys.path.insert(0, r"c:\Users\kiril\Music\win11_optimizer")
from main import App

class TestApp(App):
    def _start_sync_engine(self):
        pass  # disable sync engine for test

app = TestApp()
app.after(8000, app.destroy)
app.mainloop()
