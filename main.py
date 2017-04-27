################################################
#              Paint on a Panel                #
#                                              #
#              By Geoff Samuel                 #
#            www.GeoffSamuel.com               #
#            Info@GeoffSamuel.com              #
################################################
#!!!!!! PLEASE DO NOT REMOVE THIS NOTICE !!!!!!#
################################################

# about license: https://www.codeproject.com/info/cpol10.aspx

import sys
from PyQt5 import QtGui, QtCore, uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import keras
from keras.models import model_from_json

from pprint import pprint
from PIL import Image
import itertools as it
import numpy as np

form, base = uic.loadUiType('layout.ui')

model = model_from_json(open("model.json").read())
model.load_weights("weights.h5")
model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adadelta(),
              metrics=['accuracy'])


class Colour3:
    R = 0
    G = 0
    B = 0

    def __init__(self):
        self.R = 0
        self.G = 0
        self.B = 0

    def __init__(self, nR, nG, nB):
        self.R = nR
        self.G = nG
        self.B = nB


class Point:
    X = 0
    Y = 0

    def __init__(self):
        self.X = 0
        self.Y = 0

    def __init__(self, nX, nY):
        self.X = nX
        self.Y = nY

    def Set(self, nX, nY):
        self.X = nX
        self.Y = nY


class Shape:
    Location = Point(0, 0)
    Width = 0.0
    Colour = Colour3(0, 0, 0)
    ShapeNumber = 0

    def __init__(self, L, W, C, S):
        self.Location = L
        self.Width = W
        self.Colour = C
        self.ShapeNumber = S


class Shapes:
    __Shapes = []

    def __init__(self):
        self.__Shapes = []

    def NumberOfShapes(self):
        return len(self.__Shapes)

    def NewShape(self, L, W, C, S):
        Sh = Shape(L, W, C, S)
        self.__Shapes.append(Sh)

    def GetShape(self, Index):
        return self.__Shapes[Index]

    def GetList(self):
        return [(P.Location.X, P.Location.Y) for P in self.__Shapes]

    def RemoveShape(self, L, threshold):

        i = 0
        while True:
            if (i == len(self.__Shapes)):
                break

            if ((abs(L.X - self.__Shapes[i].Location.X) < threshold) and (
                        abs(L.Y - self.__Shapes[i].Location.Y) < threshold)):

                del self.__Shapes[i]
                for n in range(len(self.__Shapes) - i):
                    self.__Shapes[n + i].ShapeNumber += 1
                i -= 1
            i += 1


class Painter(QWidget):
    ParentLink = 0
    MouseLoc = Point(0, 0)
    LastPos = Point(0, 0)

    def __init__(self, parent):
        super(Painter, self).__init__()
        self.ParentLink = parent
        self.MouseLoc = Point(0, 0)
        self.LastPos = Point(0, 0)
        # Mouse down event

    def mousePressEvent(self, event):
        if (self.ParentLink.Brush == True):
            self.ParentLink.IsPainting = True
            self.ParentLink.ShapeNum += 1
            self.LastPos = Point(0, 0)
        else:
            self.ParentLink.IsEraseing = True

    def mouseMoveEvent(self, event):
        if (self.ParentLink.IsPainting == True):
            self.MouseLoc = Point(event.x(), event.y())
            if ((self.LastPos.X != self.MouseLoc.X) and (self.LastPos.Y != self.MouseLoc.Y)) and (
                                0 <= event.x() < 420 and 0 <= event.y() < 420):
                self.LastPos = Point(event.x(), event.y())
                self.ParentLink.DrawingShapes.NewShape(self.LastPos, self.ParentLink.CurrentWidth,
                                                       self.ParentLink.CurrentColour, self.ParentLink.ShapeNum)
            self.repaint()
        if (self.ParentLink.IsEraseing == True):
            self.MouseLoc = Point(event.x(), event.y())
            self.ParentLink.DrawingShapes.RemoveShape(self.MouseLoc, 10)
            self.repaint()

    def mouseReleaseEvent(self, event):
        if (self.ParentLink.IsPainting == True):
            self.ParentLink.IsPainting = False
        if (self.ParentLink.IsEraseing == True):
            self.ParentLink.IsEraseing = False

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        self.drawLines(event, painter)
        painter.end()

    def drawLines(self, event, painter):
        painter.setRenderHint(QtGui.QPainter.Antialiasing);

        for i in range(self.ParentLink.DrawingShapes.NumberOfShapes() - 1):

            T = self.ParentLink.DrawingShapes.GetShape(i)
            T1 = self.ParentLink.DrawingShapes.GetShape(i + 1)

            if (T.ShapeNumber == T1.ShapeNumber):
                pen = QtGui.QPen(QtGui.QColor(T.Colour.R, T.Colour.G, T.Colour.B), T.Width / 2, QtCore.Qt.SolidLine)
                painter.setPen(pen)
                painter.drawLine(T.Location.X, T.Location.Y, T1.Location.X, T1.Location.Y)


class CreateUI(base, form):
    Brush = True
    DrawingShapes = Shapes()
    IsPainting = False
    IsEraseing = False

    CurrentColour = Colour3(0, 0, 0)
    CurrentWidth = 30
    ShapeNum = 0
    IsMouseing = False
    PaintPanel = 0

    def __init__(self):
        super(base, self).__init__()
        self.setupUi(self)
        self.setObjectName('Rig Helper')
        self.PaintPanel = Painter(self)
        self.PaintPanel.close()
        self.DrawingFrame.insertWidget(0, self.PaintPanel)
        self.DrawingFrame.setCurrentWidget(self.PaintPanel)
        self.Establish_Connections()

    def Predict(self):

        M = [[0 for i in range(420)] for j in range(420)]
        Mm = [[0 for i in range(28)] for j in range(28)]

        def test(y, x):
            s = 0
            for i in range(15):
                for j in range(15):
                    s += M[y * 15 + i][x * 15 + j]
            return s / 15 * 15

        def expand(r, ratio):
            for px, py in self.DrawingShapes.GetList():
                for x, y in it.permutations(range(r + 1), 2):
                    if x ** 2 + y ** 2 <= r ** 2 and 0 <= py + y < 420 and 0 <= px + x < 420:
                        M[py + y][px + x] = ratio

        expand(40, 0.7)
        expand(35, 1)

        for y in range(28):
            for x in range(28):
                Mm[y][x] = test(y, x)

        Mma = np.array(Mm) / np.max(Mm) * 255
        Mma = Mma.astype(np.uint32)

        im = Image.fromarray(np.uint8(Mma))
        im.show()

        test = np.array([[Mma]]).transpose(0, 2, 3, 1)
        result = model.predict(np.array(test))[0]

        print("you wrote", result.argmax())

    def ClearSlate(self):
        self.DrawingShapes = Shapes()
        self.PaintPanel.repaint()

    def Establish_Connections(self):
        self.Pre_Button.clicked.connect(self.Predict)
        self.Clear_Button.clicked.connect(self.ClearSlate)


def main():
    global PyForm
    app = QApplication(sys.argv)
    PyForm = CreateUI()
    PyForm.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
