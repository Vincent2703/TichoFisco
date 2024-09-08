from threading import Thread
from time import sleep
from tkinter import DoubleVar, StringVar, Label
from tkinter.ttk import Progressbar


class ProgressBarManager:
    def __init__(self, parentView):
        self.view = parentView

        self.progressValue = DoubleVar()
        self.labelValue = StringVar()

        self.progressBar = Progressbar(self.view, variable=self.progressValue)
        self.progressLabel = Label(self.view, textvariable=self.labelValue)

        self.visible = False

        self.currentStep = 0
        self.progressPercent = 0
        self.nbSteps = 0

    def setNbSteps(self, nbSteps):
        self.nbSteps = nbSteps

    def incrementProgress(self, incrSteps=1, labelTxt='', showStep=False, hideAfterFinish=True):
        self.currentStep += incrSteps
        self.progressPercent = self.currentStep/self.nbSteps * 100

        self.progressLabel.config(text='')
        if showStep:
            labelTxt += f" : {self.currentStep}/{self.nbSteps}"
        self.labelValue.set(labelTxt)
        self.progressValue.set(min(self.progressPercent, 99.9))  # Mise à jour de la variable liée à la barre de progression. Bloque à 99.9% pour ne pas rendre la barre vide
        if self.currentStep == self.nbSteps:
            self.currentStep = 0
            if hideAfterFinish:
                self._startHideTimer()
        elif not self.visible:
            self._show()
        self.view.update_idletasks()  # Forcer la mise à jour de l'interface graphique

    def resetProgress(self):
        self.currentStep = 0
        self.progressPercent = 0

        self.progressLabel.config(text='')
        self.progressValue.set(0)  # Reset la barre de progression
        self.view.update_idletasks()  # Forcer la mise à jour de l'interface graphique

    def pack(self):
        if self.visible:
            self.progressBar.pack()
            self.progressLabel.pack()

    def _hide(self):
        self.progressBar.pack_forget()
        self.progressLabel.pack_forget()
        self.visible = False

    def _show(self):
        self.visible = True
        self.pack()

    def _hideTimer(self, seconds):
        self.view.after(int(seconds * 1000), self._hide)

    def _startHideTimer(self):
        self._hideTimer(2.5)
