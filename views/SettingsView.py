from tkinter import Frame, BOTH, YES, Text, Button, filedialog, END
from tkinter.ttk import Notebook, Style


class SettingsView(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.createWidgets()
        self.displayWidgets()

    def createWidgets(self):
        def cbPathBtn(source):
            path, widget, askFor = None, None, None

            if source == "thunderbirdPath":
                widget = self.thunderbirdPathTxt
                askFor = "directory"

            if askFor == "directory":
                path = filedialog.askdirectory()
            elif askFor == "file":
                path = filedialog.askopenfile()

            if len(path) > 0:
                widget.delete(1.0, END)
                widget.insert(END, path)

        _style = Style()
        _style.configure("vertical.TNotebook", tabposition="wn")

        self.settingsNtbk = Notebook(self, style="vertical.TNotebook")

        self.thunderbird = Frame(self.settingsNtbk)
        self.receipts = Frame(self.settingsNtbk)
        self.settingsNtbk.add(self.thunderbird, text="Thunderbird")
        self.settingsNtbk.add(self.receipts, text="Reçus fiscaux")


        # Thunderbird :
        self.thunderbirdPathTxt = Text(self.thunderbird, height=1, width=40)
        self.thunderbirdPathBtn = Button(self.thunderbird, text="Choisir", command=lambda: cbPathBtn("thunderbirdPath"))


    def displayWidgets(self):
        self.settingsNtbk.pack(fill=BOTH, expand=YES)
        self.thunderbirdPathTxt.pack()
        self.thunderbirdPathBtn.pack()
