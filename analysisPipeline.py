from email.charset import QP
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QPushButton, \
    QWidget, QStyle, QSlider, QFileDialog, QInputDialog, QMessageBox, QComboBox, QLabel
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl
import numpy as np
import pandas as pd
import cv2
import sys
import os

def sOut(ms):
    s = ms/1000
    return s

def fOut(ms, fps):
    s = ms/1000
    currentFrame = s*fps
    return currentFrame

class Window(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Touch Analysis Player")
        self.setGeometry(250,100,1200,800) #position on screen (x, y) followed by LxW of the window (1000, 800 because 720x480 videos)
        
        p = self.palette()
        p.setColor(QPalette.Window, Qt.darkCyan)
        self.setPalette(p)
        self.create_player()  
        self.setStyleSheet("QLabel{font-size: 18pt; color: white;}")

        #create initialized global variables
        global frame, startFrames, endFrames, oldPos, x1, x2, y1, y2, abs_meas, speed, startEnd, efPath, sfPath, efStart
        global whichType, whichFinger, whichLoc, typeLabels, locLabels, fingerLabels, fingerTracking, typeTracking, labStart, labEnd
        frame = 0
        startFrames = []
        endFrames = []
        oldPos = 0
        x1 = 9999
        x2 = 9999
        y1 = 9999
        y2 = 9999
        speed = 0
        efStart = 0
        abs_meas = 0
        startEnd = 0 #most recent label was a start = 0, end = 1
        typeLabels = []
        locLabels = []
        fingerLabels = []
        fingerTracking = ["0",'1']
        whichFinger = "thumbR"
        whichType = "Stroke"
        whichLoc = "Head"
        labStart = 1
        labEnd = 1
       

    
    def create_player(self):
        global fingerTracking

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        
        videowidget = QVideoWidget()
        
        self.openBtn = QPushButton('Open New Video')
        self.openBtn.clicked.connect(self.open_file)
        self.openBtn.setStyleSheet("background-color : darkRed; color: white")

        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)

        self.measureBtn = QPushButton('Measure')
        self.measureBtn.hide()
        self.measureBtn.clicked.connect(self.meas_frame)
                                                                    #add a "return to previous start/stop"

        self.prevBtn = QPushButton('<')
        self.prevBtn.hide()
        self.prevBtn.clicked.connect(self.prev_frame)

        self.nextBtn = QPushButton('>')
        self.nextBtn.hide()
        self.nextBtn.clicked.connect(self.next_frame)

        self.prev10Btn = QPushButton('<<')
        self.prev10Btn.hide()
        self.prev10Btn.clicked.connect(self.prev_10frame)

        self.next10Btn = QPushButton('>>')
        self.next10Btn.hide()
        self.next10Btn.clicked.connect(self.next_10frame)

        self.returnBtn = QPushButton('Most Recent')
        self.returnBtn.hide()
        self.returnBtn.clicked.connect(self.returnLabel)

        self.strokeStartBtn = QPushButton("Label Start")
        self.strokeStartBtn.hide()
        self.strokeStartBtn.clicked.connect(self.recStart)

        self.strokeEndBtn = QPushButton("Label End")
        self.strokeEndBtn.hide()
        self.strokeEndBtn.clicked.connect(self.recEnd)

        self.undoRecButton = QPushButton("Undo Label")
        self.undoRecButton.hide()
        self.undoRecButton.clicked.connect(self.undoRec)


        self.analyzeBtn = QPushButton('Analyze')
        self.analyzeBtn.hide()
        self.analyzeBtn.clicked.connect(self.analyze_data)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0,0)
        self.slider.sliderMoved.connect(self.set_position)
        
        self.playbackCtrl = QComboBox()
        self.playbackCtrl.hide()
        self.playbackCtrl.addItems(['1x speed','1.5x speed','2x speed','2.5x speed','3x speed','5x speed'])
        self.playbackCtrl.currentIndexChanged.connect(self.currentPlayback)
        

        self.finger = QComboBox()
        self.finger.hide()
        self.finger.activated.connect(self.labelFinger)

        self.fingerL = QLabel()
        self.fingerL.hide()
        self.fingerL.setText("Which Finger?")
        
        self.touchType = QComboBox()
        self.touchType.hide()
        self.touchType.addItems(['Stroke','Static/Resting','No Contact','Self touch','Other'])
        self.touchType.activated.connect(self.labelType)

        self.touchTypeL = QLabel()
        self.touchTypeL.hide()
        self.touchTypeL.setText("Type of touch:")

        self.touchlocL = QLabel()
        self.touchlocL.hide()
        self.touchlocL.setText("Location of touch:")
        
        self.touchloc = QComboBox()
        self.touchloc.hide()
        self.touchloc.addItems(['Head','Arms','Torso','Legs','Other'])
        self.touchloc.activated.connect(self.labelLoc)

        #frame controls 
        frameBox = QHBoxLayout()
        frameBox.setContentsMargins(0,0,0,0)
        frameBox.addWidget(self.prev10Btn)
        frameBox.addWidget(self.prevBtn)
        frameBox.addWidget(self.nextBtn)
        frameBox.addWidget(self.next10Btn)

        fingerBox = QVBoxLayout()
        fingerBox.addWidget(self.fingerL)
        fingerBox.addWidget(self.finger)
        fingerH = QWidget()
        fingerH.setLayout(fingerBox)
        fingerH.setFixedHeight(80)

        typeBox = QVBoxLayout()
        typeBox.addWidget(self.touchTypeL)
        typeBox.addWidget(self.touchType)
        typeH = QWidget()
        typeH.setLayout(typeBox)
        typeH.setFixedHeight(80)

        locBox = QVBoxLayout()
        locBox.addWidget(self.touchlocL)
        locBox.addWidget(self.touchloc)
        locH = QWidget()
        locH.setLayout(locBox)
        locH.setFixedHeight(80)

        #touch characteristics selection
        touchBox = QVBoxLayout()
        touchBox.setContentsMargins(10,0,10,0)
        touchBox.addWidget(fingerH)
        touchBox.addWidget(typeH)
        touchBox.addWidget(locH)
        touchBox.addWidget(self.strokeStartBtn)
        touchBox.addWidget(self.strokeEndBtn)
        touchBox.addWidget(self.undoRecButton)
        touchW = QWidget()
        touchW.setLayout(touchBox)
        touchW.setFixedWidth(200)
               
        topBox = QHBoxLayout()
        topBox.setContentsMargins(0,0,0,0)
        topBox.addWidget(videowidget)
        topBox.addWidget(touchW)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)
        hbox.addWidget(self.openBtn)
        hbox.addWidget(self.playBtn)
        hbox.addWidget(self.slider)
        hbox.addLayout(frameBox)

        hbox1 = QHBoxLayout()
        hbox1.setContentsMargins(0,0,0,0)
        hbox1.addWidget(self.playbackCtrl)
        hbox1.addWidget(self.measureBtn)
        hbox1.addWidget(self.analyzeBtn)
        hbox1.addWidget(self.returnBtn)
        # hbox1.addWidget(self.prevBtn)
        # hbox1.addWidget(self.nextBtn)

        
       
        vbox = QVBoxLayout()
        vbox.addLayout(topBox)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox1)
        

        self.mediaPlayer.setVideoOutput(videowidget)
        self.mediaPlayer.setNotifyInterval(33)
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)
        
        self.setLayout(vbox)
        
    def open_file(self):
        global filename, file_dir,new_path, fps,csvn, data, fingerTracking, startFrames, endFrames, abs_meas
        global startEnd, typeLabels, locLabels,fingerLabels, efStart, sfPath, efPath
        filename, _= QFileDialog.getOpenFileName(self, "Select Video")
        vid = cv2.VideoCapture(filename)
        file_dir = os.path.dirname(filename)
        
        fps = int(vid.get(cv2.CAP_PROP_FPS))
        startFrames = []
        endFrames = []
        abs_meas = 0
        startEnd = 0 #most recent label was a start = 0, end = 1
        typeLabels = []
        locLabels = []
        fingerLabels = []

        #print(file_dir)

        if filename != '':
            new_dir = (filename+"_analysis")
            new_path = os.path.join(file_dir,new_dir)
            exists = os.path.exists(new_path)
            if not exists:
                os.mkdir(new_path)
            
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile((filename))))
            self.playBtn.setEnabled(True)
            #self.strokeEndBtn.show()
            self.strokeEndBtn.setEnabled(False)
            self.strokeEndBtn.show()
            self.strokeStartBtn.show()
            self.measureBtn.show()
            self.nextBtn.show()
            self.prevBtn.show()
            self.next10Btn.show()
            self.prev10Btn.show()
            self.returnBtn.show()
            self.analyzeBtn.show()
            self.touchloc.show()
            self.touchlocL.show()
            self.touchType.show()
            self.touchTypeL.show()
            self.finger.show()
            self.fingerL.show()
            self.playbackCtrl.show()
            self.undoRecButton.show()
            self.undoRecButton.setEnabled(False)
            csvn, _= QFileDialog.getOpenFileName(self, "Select CSV")
            csvData = pd.read_csv(csvn, header=None)
            trackedPoints = int((len(csvData.columns)-1)/3)
            j = []
            for i in range (1,trackedPoints+1):
                i = i*3
                j.append(i)
            data = csvData.drop(csvData.columns[j], axis=1) 
            fingerTracking = data.iloc[[1]]
            fingerTracking = (fingerTracking.values.tolist())
            fingerTracking = fingerTracking[0]
            del fingerTracking[0::2]
            print(fingerTracking)
            self.finger.addItems(fingerTracking)
            os.chdir(new_path)
            sfPath = os.path.join(new_path,"startFrames.csv")
            efPath = os.path.join(new_path,"endFrames.csv")
            locPath = os.path.join(new_path,"locations.csv")
            fingerPath = os.path.join(new_path,"fingers.csv")
            typePath = os.path.join(new_path,"type.csv")
            if os.path.exists(sfPath):
                startFrames = pd.read_csv(sfPath)
                endFrames = pd.read_csv(efPath)
                locLabels= pd.read_csv(locPath)
                fingerLabels= pd.read_csv(fingerPath)
                typeLabels= pd.read_csv(typePath)
                startFrames.iloc[:,0].tolist()
                endFrames.iloc[:,0].tolist()
                locLabels.iloc[:,0].tolist()
                fingerLabels.iloc[:,0].tolist()
                typeLabels.iloc[:,0].tolist()
                efStart = 1
                print("path exists")
                print(endFrames)
                len(endFrames)
                
            

    def play_video(self):
        global efStart
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        # elif efStart == 1: 
        #     self.mediaPlayer.play()
        #     self.mediaPlayer.setPosition((endFrames[len(endFrames)-1]))
        #     self.mediaPlayer.pause()
            efStart = 0
        else:
            self.mediaPlayer.play()

    def mediastate_changed(self,state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
    
    def currentPlayback(self, speed):
        speed = self.playbackCtrl.currentIndex()
        if speed == 0: 
            self.mediaPlayer.setPlaybackRate(1.0)
        elif speed == 1: 
            self.mediaPlayer.setPlaybackRate(1.5)
        elif speed == 2: 
            self.mediaPlayer.setPlaybackRate(2.0)
        elif speed == 3: 
            self.mediaPlayer.setPlaybackRate(2.5)
        elif speed == 4: 
            self.mediaPlayer.setPlaybackRate(3)
        elif speed == 5: 
            self.mediaPlayer.setPlaybackRate(5)


    def position_changed(self,position):
        self.slider.setValue(position)        
        global frame, oldPos
        frame = round(position*fps/1000)
        oldPos = position + 0

    def duration_changed(self,duration):
        self.slider.setRange(0,duration)
        
        
    def set_position(self, position):
        self.mediaPlayer.setPosition(position)
        print(sOut(position))
    
    def next_frame(self,speed):
        self.mediaPlayer.setPlaybackRate(1.0)
        self.mediaPlayer.play()
        newPos = oldPos + fps
        self.mediaPlayer.setPosition((newPos))        
        self.mediaPlayer.pause()
        self.currentPlayback(speed)
        
   
    def next_10frame(self,speed):
        self.mediaPlayer.setPlaybackRate(1.0)
        self.mediaPlayer.play()
        newPos = oldPos + 10*fps
        self.mediaPlayer.setPosition((newPos))        
        self.mediaPlayer.pause()
        self.currentPlayback(speed)

    def prev_frame(self,speed):
        self.mediaPlayer.setPlaybackRate(1.0)
        self.mediaPlayer.play()
        newPos = oldPos - fps
        self.mediaPlayer.setPosition((newPos))        
        self.mediaPlayer.pause()
        self.currentPlayback(speed)
 
    def prev_10frame(self,speed):
        self.mediaPlayer.setPlaybackRate(1.0)
        self.mediaPlayer.play()
        newPos = oldPos - 10*fps
        self.mediaPlayer.setPosition((newPos))        
        self.mediaPlayer.pause()
        self.currentPlayback(speed)
    
    def returnLabel(self):
        global endFrames, startFrames
        self.mediaPlayer.setPlaybackRate(1.0)
        self.mediaPlayer.play()
        sizeE = np.size(endFrames)
        sizeS = np.size(startFrames)
        if sizeE == sizeS:
            endFrames = np.append(endFrames, 0)
            endFrames = np.delete(endFrames, sizeE)
            newPos = endFrames[sizeE-1]
            newPos = newPos*1000/fps
        else:
            startFrames = np.append(startFrames, 0)
            startFrames = np.delete(startFrames, sizeS)
            newPos = startFrames[sizeS-1]
            newPos = newPos*1000/fps
        #print(newPos)
        self.mediaPlayer.setPosition((int(newPos)))
        self.mediaPlayer.pause()
        self.currentPlayback(speed)

    def labelFinger(self):
        global whichFinger
        whichFinger = self.finger.currentText()
        

    def labelType(self):
        global whichType
        whichType = self.touchType.currentText()

    def labelLoc(self):
        global whichLoc
        whichLoc = self.touchloc.currentText()
        

    def recStart(self):
        global startFrames, endFrames, startEnd, fingerLabels, typeLabels, locLabels, whichFinger, whichType, whichLoc,sfPath, labStart
        startFrames = np.append(startFrames, frame)
        dfSF = pd.DataFrame(startFrames)
        dfSF.to_csv(sfPath, index=False)
        self.strokeEndBtn.setEnabled(True)
        self.strokeStartBtn.setEnabled(False)
        startEnd = 0 
        self.undoRecButton.setEnabled(True)
        print("Stroke starts frame " + str(frame))
        print("array of start frames: ")
        print(startFrames)
        locLabels = np.append(locLabels,whichLoc)
        locPath = os.path.join(new_path,"locations.csv")
        dfLoc = pd.DataFrame(locLabels)
        dfLoc.to_csv(locPath, index=False)
        fingerLabels = np.append(fingerLabels, whichFinger)
        fingerPath = os.path.join(new_path,"fingers.csv")
        dfFinger = pd.DataFrame(fingerLabels)
        dfFinger.to_csv(fingerPath, index=False)
        typeLabels = np.append(typeLabels,whichType)
        typePath = os.path.join(new_path,"type.csv")
        dfType = pd.DataFrame(typeLabels)
        dfType.to_csv(typePath, index=False)
        endFrames = endFrames
        labStart = 0


    def recEnd(self):
        global endFrames, startEnd, efPath, labEnd
        endFrames = np.append(endFrames, frame)
        dfEF = pd.DataFrame(endFrames)
        dfEF.to_csv(efPath, index=False)
        self.strokeEndBtn.setEnabled(False)
        self.strokeStartBtn.setEnabled(True)
        startEnd = 1
        print("Stroke end frame " + str(frame))
        print("array of end frames: ")
        print(endFrames)
        labEnd = 0

    def undoRec(self): 
        global startFrames, endFrames, fingerLabels, locLabels,typeLabels, startEnd
        if startEnd == 0: 
            size = np.size(startFrames)-1
            startFrames = np.delete(startFrames,size,None)
            fingerLabels = np.delete(fingerLabels,size,None)
            locLabels = np.delete(locLabels,size,None)
            typeLabels = np.delete(typeLabels,size,None)
            endFrames = endFrames
            dfSF = pd.DataFrame(startFrames)
            dfSF.to_csv(sfPath, index=False)
            self.strokeEndBtn.setEnabled(False)
            self.strokeStartBtn.setEnabled(True)
            startEnd = 1
            print("array of start frames: ")
            print(startFrames)
            locPath = os.path.join(new_path,"locations.csv")
            dfLoc = pd.DataFrame(locLabels)
            dfLoc.to_csv(locPath, index=False)
            fingerPath = os.path.join(new_path,"fingers.csv")
            dfFinger = pd.DataFrame(fingerLabels)
            dfFinger.to_csv(fingerPath, index=False)
            typePath = os.path.join(new_path,"type.csv")
            dfType = pd.DataFrame(typeLabels)
            dfType.to_csv(typePath, index=False)
            startFrames.tolist()
            locLabels.tolist()
            fingerLabels.tolist()
            typeLabels.tolist()
            
        elif startEnd == 1: 
            size = np.size(endFrames)-1
            endFrames = np.delete(endFrames,size,None)
            print("array of end frames: ")
            print(endFrames)
            self.strokeEndBtn.setEnabled(True)
            self.strokeStartBtn.setEnabled(False)
            startEnd = 0 
            dfEF = pd.DataFrame(endFrames)
            dfEF.to_csv(efPath, index=False)
            self.strokeEndBtn.setEnabled(False)
            self.strokeStartBtn.setEnabled(True)
            endFrames.tolist()

    def click(self, event, x, y, flags, param):
        global img, x1, y1, x2, y2
        imgDup = cv2.imread(impath,1)
        # checking for left mouse clicks
        if event == cv2.EVENT_LBUTTONDOWN:
            font = cv2.FONT_HERSHEY_SIMPLEX
            img = imgDup
            # displaying the coordinates
            # on the image window
            if x2 == 9999 or y2 == 9999:
                cv2.putText(img, str(x) + ',' +
                            str(y), (x,y), font,
                            1, (255, 20, 20), 2)
                cv2.imshow('image', img)
            else:
                cv2.putText(img, str(x) + ',' +
                            str(y), (x,y), font,
                            1, (255, 20, 20), 2)
                cv2.putText(img, str(x2) + ',' +
                            str(y2), (x2,y2), font,
                            1, (20, 255, 20), 2)
                cv2.line(img, (x, y), (x2, y2), (20,20,255), 7)
                cv2.imshow('image', img)
            #set the start of stroke values
            x1 = x
            y1 = y
    
        # checking for right mouse clicks    
        if event==cv2.EVENT_RBUTTONDOWN:
            font = cv2.FONT_HERSHEY_SIMPLEX
            img = imgDup
            # displaying the coordinates
            # on the image window
            if x1 == 9999 or y1 == 9999:
                cv2.putText(img, str(x) + ',' +
                            str(y), (x,y), font,
                            1, (20, 255, 20), 2)
                cv2.imshow('image', img)
            else:
                cv2.putText(img, str(x) + ',' +
                            str(y), (x,y), font,
                            1, (20, 255, 20), 2)
                cv2.putText(img, str(x1) + ',' +
                            str(y1), (x1,y1), font,
                            1, (255, 20, 20), 2)
                cv2.line(img, (x1, y1), (x, y), (20,20,255), 7)
                cv2.imshow('image', img)
            #set the end of stroke value
            x2 = x
            y2 = y
            
    
    def meas_frame(self):
        global img, x1, x2, y1, y2, impath, abs_meas
        vidcap = cv2.VideoCapture(filename)
        vidcap.set(cv2.CAP_PROP_POS_MSEC, oldPos)
        valid, image = vidcap.read()
        if valid:
            imname = "frame" + str(frame) + ".jpg"
            impath = os.path.join(file_dir, imname)
            print(impath)
            cv2.imwrite(impath, image)     # save frame as JPG file
        # reading the image
        img = cv2.imread(impath, 1)

        # displaying the image
        cv2.imshow('image', img)

        #instruction window
        instWindow = QMessageBox()
        instWindow.setWindowTitle('Absolute Measurement Instructions')
        instWindow.setText("To make an absolute distance measurement:\n\nLEFT CLICK the start of your measurement, then RIGHT CLICK the end of the measurement. \n\nHit any key to continue")
        instWindow.exec_()
    
        # setting mouse handler for the image
        # and calling the click_event() function
        cv2.setMouseCallback('image', self.click)
    
        # wait for a key to be pressed to exit
        cv2.waitKey(0)
        print("Start location: x, y")
        print(x1, y1)
        print("End location: x, y")
        print(x2, y2)
        
        
        meas = 0
        ok = bool(False) 

        while not ok or meas == 0: 
            meas, ok = QInputDialog.getInt(self,"Absolute Measurement", "What is the known measurement you traced? (mm)" )
        
        abs_meas = meas
        print("Known distance: ")
        print(str(abs_meas))
  
        #self.analyze_data()
        # close the window
        cv2.destroyAllWindows()

    def analyze_data(self):
        global csvn, data, startFrames, endFrames, locLabels, fingerLabels,typeLabels, labStart, labEnd
        efStroke = []
        sfStroke = []
        efRest = []
        sfRest = []
        efNo = []
        sfNo = []
        efSelf = []
        sfSelf = []
        efOther = []
        sfOther = []
        finStroke = []
        finRest = []
        finNo = []
        finSelf = []
        finOther = []
        locStroke = []
        locRest = []
        locNo = []
        locSelf = []
        locOther = []
        if labEnd == 1: 
            endFrames = endFrames.iloc[:,0].tolist()
        if labStart == 1:
            startFrames = startFrames.iloc[:,0].tolist()
            locLabels = locLabels.iloc[:,0].tolist()
            fingerLabels = fingerLabels.iloc[:,0].tolist()
            typeLabels = typeLabels.iloc[:,0].tolist()
        
 
        if int(abs_meas) > 0:
            dpix = np.sqrt((x2-x1)**2+(y2-y1)**2)
            csvData = pd.read_csv(csvn, header=None)
            csvData = csvData.iloc[3:]
            csv_dir = os.path.dirname(csvn)
            csvname = os.path.basename(csvn)
            trackedPoints = int((len(csvData.columns)-1)/3)
            print(trackedPoints)
            j = []
            for i in range (1,trackedPoints+1):
                i = i*3
                j.append(i)
            print("cols to delete "+str(j))
            data = csvData.drop(csvData.columns[j], axis=1) 
            print(data)
       
            
            for b in range(0,len(typeLabels)):
                if typeLabels[b] == 'Stroke':
                    sfStroke.append(startFrames[b])
                    efStroke.append(endFrames[b])
                    finStroke.append(fingerLabels[b])
                    locStroke.append(locLabels[b])
                    
                elif typeLabels[b] == 'Static/Resting':
                    sfRest.append(startFrames[b])
                    efRest.append(endFrames[b])
                    finRest.append(fingerLabels[b])
                    locRest.append(locLabels[b])
                    
                elif typeLabels[b] == 'No Contact':
                    sfNo.append(startFrames[b])
                    efNo.append(endFrames[b])
                    finNo.append(fingerLabels[b])
                    locNo.append(locLabels[b])

                elif typeLabels[b] == 'Self Touch':
                    sfSelf.append(startFrames[b])
                    efSelf.append(endFrames[b])
                    finSelf.append(fingerLabels[b])
                    locSelf.append(locLabels[b])
                    
                elif typeLabels[b] == 'Other':
                    sfOther.append(startFrames[b])
                    efOther.append(endFrames[b])
                    finOther.append(fingerLabels[b])
                    locOther.append(locLabels[b])
       

            #newData = data.iloc[[1]].to_numpy()
            
            allData = ['Count #', 'Type', 'Finger', 'Location','Velocity','Displacement', 'Duration', 'Start Frame #', 'End Frame #']
            strokeData = ['Count #', 'Finger', 'Location','Velocity','Displacement', 'Duration', 'Start Frame #', 'End Frame #']
            restData = ['Count #', 'Finger', 'Location','Duration', 'Start Frame #', 'End Frame #']
            noData = ['Count #', 'Duration', 'Start Frame #', 'End Frame #']
            selfData = ['Count #', 'Duration', 'Start Frame #', 'End Frame #']
            otherData = ['Count #', 'Finger', 'Location','Velocity','Displacement', 'Duration', 'Start Frame #', 'End Frame #']

            f = 0
            # all data
            for x in range(0,len(startFrames)):
                for n in range(0,len(fingerTracking)):
                    if fingerLabels[x] == fingerTracking[n]:
                        f = n
                newData = []
                # if startFrames[x] <<3: 
                #     startFrames[x]=3
                startData = data.iloc[[startFrames[x]]].to_numpy()
                startData = startData.astype(float)
                endData = data.iloc[[endFrames[x]]].to_numpy()
                endData = endData.astype(float)
                startVal = startData[:,0]
                endVal = endData[:,0]
                xValS = startData[:,(f*2+1)]
                yValS = startData[:,(f*2+2)]
                xValE = endData[:,(f*2+1)]
                yValE = endData[:,(f*2+2)]
                fin = fingerTracking[f]
                xDiff = xValE-xValS
                yDiff = yValE-yValS
                disp = np.sqrt((xDiff**2)+(yDiff**2))*abs_meas/dpix
                dur = (endVal - startVal)/fps
                vel = disp/dur
                vel = str(vel)
                vel=vel.replace("[","")
                vel=vel.replace("]","")
                disp = str(disp)
                disp=disp.replace("[","")
                disp=disp.replace("]","")
                dur = str(dur)
                dur=dur.replace("[","")
                dur=dur.replace("]","")
                startVal = str(startVal)
                startVal=startVal.replace("[","")
                startVal=startVal.replace("]","")
                endVal = str(endVal)
                endVal=endVal.replace("[","")
                endVal=endVal.replace("]","")
                newData.append([x, typeLabels[x], fingerLabels[x],locLabels[x], vel, disp, dur, startVal, endVal])
                allData = np.vstack((allData,newData))
            
            #stroke data
            for x in range(0,len(sfStroke)):
                for n in range(0,len(fingerTracking)):
                    if finStroke[x] == fingerTracking[n]:
                        f = n
                newDataS = []
                startData = data.iloc[[sfStroke[x]]].to_numpy()
                startData = startData.astype(float)
                endData = data.iloc[[efStroke[x]]].to_numpy()
                endData = endData.astype(float)
                startVal = startData[:,0]
                endVal = endData[:,0]
                xValS = startData[:,(f*2+1)]
                yValS = startData[:,(f*2+2)]
                xValE = endData[:,(f*2+1)]
                yValE = endData[:,(f*2+2)]
                xDiff = xValE-xValS
                yDiff = yValE-yValS
                disp = np.sqrt((xDiff**2)+(yDiff**2))*abs_meas/dpix
                dur = (endVal - startVal)/fps
                vel = disp/dur
                vel = str(vel)
                vel=vel.replace("[","")
                vel=vel.replace("]","")
                disp = str(disp)
                disp=disp.replace("[","")
                disp=disp.replace("]","")
                dur = str(dur)
                dur=dur.replace("[","")
                dur=dur.replace("]","")
                startVal = str(startVal)
                startVal=startVal.replace("[","")
                startVal=startVal.replace("]","")
                endVal = str(endVal)
                endVal=endVal.replace("[","")
                endVal=endVal.replace("]","")
                newDataS.append([x, fingerLabels[x],locLabels[x], vel, disp, dur, startVal, endVal])
                strokeData = np.vstack((strokeData,newDataS)) 

            #resting data
            for x in range(0,len(sfRest)):
                for n in range(0,len(fingerTracking)):
                    if finRest[x] == fingerTracking[n]:
                        f = n
                newDataR = []
                startData = data.iloc[[sfRest[x]]].to_numpy()
                startData = startData.astype(float)
                endData = data.iloc[[efRest[x]]].to_numpy()
                endData = endData.astype(float)
                startVal = startData[:,0]
                endVal = endData[:,0]
                dur = (endVal - startVal)/fps
                disp = str(disp)
                disp=disp.replace("[","")
                disp=disp.replace("]","")
                dur = str(dur)
                dur=dur.replace("[","")
                dur=dur.replace("]","")
                startVal = str(startVal)
                startVal=startVal.replace("[","")
                startVal=startVal.replace("]","")
                endVal = str(endVal)
                endVal=endVal.replace("[","")
                endVal=endVal.replace("]","")
                newDataR.append([x, finRest[x],locRest[x], dur, startVal, endVal])
                restData = np.vstack((restData,newDataR)) 

            #no contact data
            for x in range(0,len(sfNo)):
                
                newDataNo = []
                startData = data.iloc[[sfNo[x]]].to_numpy()
                startData = startData.astype(float)
                endData = data.iloc[[efNo[x]]].to_numpy()
                endData = endData.astype(float)
                startVal = startData[:,0]
                endVal = endData[:,0]
                dur = (endVal - startVal)/fps
                dur = str(dur)
                dur=dur.replace("[","")
                dur=dur.replace("]","")
                startVal = str(startVal)
                startVal=startVal.replace("[","")
                startVal=startVal.replace("]","")
                endVal = str(endVal)
                endVal=endVal.replace("[","")
                endVal=endVal.replace("]","")
                newDataNo.append([x, dur, startVal, endVal])
                noData = np.vstack((noData,newDataNo))

            #self touch data
            for x in range(0,len(sfSelf)):
                
                newDataSelf = []
                startData = data.iloc[[sfSelf[x]]].to_numpy()
                startData = startData.astype(float)
                endData = data.iloc[[efSelf[x]]].to_numpy()
                endData = endData.astype(float)
                startVal = startData[:,0]
                endVal = endData[:,0]
                dur = (endVal - startVal)/fps
                dur = str(dur)
                dur=dur.replace("[","")
                dur=dur.replace("]","")
                startVal = str(startVal)
                startVal=startVal.replace("[","")
                startVal=startVal.replace("]","")
                endVal = str(endVal)
                endVal=endVal.replace("[","")
                endVal=endVal.replace("]","")
                newDataSelf.append([x,dur, startVal, endVal])
                selfData = np.vstack((selfData,newDataSelf))

            #other data
            for x in range(0,len(sfOther)):
                for n in range(0,len(fingerTracking)):
                    if finOther[x] == fingerTracking[n]:
                        f = n
                newDataO = []
                startData = data.iloc[[sfOther[x]]].to_numpy()
                startData = startData.astype(float)
                endData = data.iloc[[efOther[x]]].to_numpy()
                endData = endData.astype(float)
                startVal = startData[:,0]
                endVal = endData[:,0]
                xValS = startData[:,(f*2+1)]
                yValS = startData[:,(f*2+2)]
                xValE = endData[:,(f*2+1)]
                yValE = endData[:,(f*2+2)]
                xDiff = xValE-xValS
                yDiff = yValE-yValS
                disp = np.sqrt((xDiff**2)+(yDiff**2))*abs_meas/dpix
                dur = (endVal - startVal)/fps
                vel = disp/dur
                vel = str(vel)
                vel=vel.replace("[","")
                vel=vel.replace("]","")
                disp = str(disp)
                disp=disp.replace("[","")
                disp=disp.replace("]","")
                dur = str(dur)
                dur=dur.replace("[","")
                dur=dur.replace("]","")
                startVal = str(startVal)
                startVal=startVal.replace("[","")
                startVal=startVal.replace("]","")
                endVal = str(endVal)
                endVal=endVal.replace("[","")
                endVal=endVal.replace("]","")
                newDataO.append([x, fingerLabels[x],locLabels[x], vel, disp, dur, startVal, endVal])
                otherData = np.vstack((otherData,newDataO)) 
        
            dfAll = pd.DataFrame(allData)
            dfAll.to_csv("all.csv", index=False, header=False)

            dfStroke = pd.DataFrame(strokeData)
            dfStroke.to_csv("stroke.csv", index=False, header=False)

            dfRest = pd.DataFrame(restData)
            dfRest.to_csv("resting.csv", index=False, header=False)

            dfSelf = pd.DataFrame(selfData)
            dfSelf.to_csv("selfTouch.csv", index=False, header=False)

            dfNo = pd.DataFrame(noData)
            dfNo.to_csv("noContact.csv", index=False, header=False)

            dfOther = pd.DataFrame(otherData)
            dfOther.to_csv("other.csv", index=False, header=False)
            #print(newPath)
            #newData.tofile(newPath, sep = ',')
            #newData.to_csv('analyzed-'+csvname, sep=',', index=False, encoding='utf-8')
        else:
            #instruction window
            instWindow = QMessageBox()
            instWindow.setWindowTitle('Warning: No absolute measurement provided')
            instWindow.setText("Please click 'Measure' and follow all steps before continuing.  \n\nHit any key to continue")
            instWindow.exec_()

        # csv_input = pd.read_csv(csvData)  
        # print(startFrames)  
        # csv_input['strokeStart'] = [1, 2, 3, 4, 4, 4]
        # # csv_input['strokeEnd'] = endFrames
        # csv_input.to_csv(file_dir+"/newone.csv", index=False)        
       
        
app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec_())