import cv2, glob, os, math
import numpy as np

from PyQt5.QtWidgets import \
    QApplication, QMainWindow, QLabel, QPushButton,\
    QHBoxLayout, QVBoxLayout, QGridLayout, QWidget,\
    QLineEdit, QSizePolicy, QFileDialog, QDialog,\
    QSpacerItem, QCheckBox, QGroupBox, QRadioButton
    
from PyQt5.QtGui import \
    QPainter, QPen, QBrush, QPixmap, QColor, QFont, \
    QImage, QFontDatabase, QFontMetrics, QIntValidator, \
    QDesktopServices, QPolygon
    
from PyQt5.QtCore import Qt, QTimer, QUrl, QPoint
from PyQt5 import QtTest

def cv2pixmap(cvImg):
    height, width, channel = cvImg.shape
    bytesPerLine = 3 * width
    qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format_RGB888)
    return QPixmap(qImg)

def pixmap2cv(pixmap):
    qImg = QImage(pixmap)
    qImg = qImg.convertToFormat(4)

    width = qImg.width()
    height = qImg.height()
    ptr = qImg.bits()
    ptr.setsize(qImg.byteCount())
    arr = np.array(ptr).reshape(height, width, 4)  #  Copies the data
    return arr

def get_intersection_area(poly1, poly2, w, h):
    blank = np.zeros((h, w))
    
    mask1 = cv2.fillPoly(blank.copy(), pts=[np.array(poly1)], color=(1))
    mask2 = cv2.fillPoly(blank.copy(), pts=[np.array(poly2)], color=(1))
    
    intersection = cv2.bitwise_and(mask1, mask2)
    
    return np.sum(intersection)

def draw_mask(img, poly):
    return cv2.fillPoly(img.copy(), pts=[np.array(poly)], color=(1))

def get_area(box):
    return (box[2]-box[0]) * (box[3]-box[1])

def get_point_distance(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def get_image_paths(directory):
    img_exts = ['bmp', 'jpg', 'jpeg', 'png']
    
    image_paths = []
    for img_ext in img_exts:
        image_paths += glob.glob(os.path.join(directory, "*."+img_ext))
    
    return image_paths


class Canvas(QLabel):
    def __init__(self, width, height):
        super().__init__()
        
        self.width = width
        self.height = height
        
        self.iw = 0
        self.ih = 0
        
        self.pw = 0
        self.ph = 0
        
        self.img_path = None
        self.label_path = None
        self.pixmap = None
        
        self.drawing = False
        self.x1, self.y1 = 0, 0
        
        self.mode = 'poly'
        # [x1, y1], [x2, y2], [x3, y3] ...
        self.anns = []
        self.drawing_ann = []
        
        self.setMouseTracking(True)
    
    def SetImage(self, img_path, label_path):
        self.img_path = img_path
        self.label_path = label_path
        
        pixmap = QPixmap(img_path)
        
        self.iw = pixmap.width()
        self.ih = pixmap.height()
        
        if self.iw / self.ih > 1:
            self.pixmap = pixmap.scaledToWidth(self.width)
        else:
            self.pixmap = pixmap.scaledToHeight(self.height)
        
        self.pw = self.pixmap.width()
        self.ph = self.pixmap.height()
        
        self.setFixedSize(self.pixmap.width(), self.pixmap.height())
        
        self.anns = self.loadAnns()
        
        self.drawAnns()
    
    def mousePressEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            if len(self.drawing_ann) == 0:
                self.drawing_ann = [[e.x(), e.y()], [e.x(), e.y()]]
            else:
                if get_point_distance(self.drawing_ann[0], [e.x(), e.y()]) < 5:
                    self.anns.append(self.drawing_ann[:-1])
                    self.drawing_ann = []
                    
                    self.saveAnns()
                else:
                    self.drawing_ann += [[e.x(), e.y()]]
        
        elif e.buttons() & Qt.RightButton:
            if self.drawing_ann == []:
                if len(self.anns) > 0:
                    self.anns.pop()
                    self.saveAnns()
            else:
                self.drawing_ann.pop()
                if len(self.drawing_ann) != 1:
                    self.drawing_ann[-1] = [e.x(), e.y()]
                else:
                    self.drawing_ann = []
        
        self.drawAnns()
    
    def mouseMoveEvent(self, e):
        if len(self.drawing_ann) > 0:
            self.drawing_ann[-1] = [e.x(), e.y()]
            self.drawAnns()
    
    def mouseReleaseEvent(self, e):
        pass
    
    def drawAnns(self, draw=True):
        pixmap = self.pixmap.copy()
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        
        for ann in self.anns:
            poly_points = ann + [ann[0]]
            for i in range(len(poly_points) - 1):
                painter.drawLine(*poly_points[i], *poly_points[i+1])
                painter.drawEllipse(QPoint(*poly_points[i]), 4, 4)
        
        if self.drawing_ann != []:
            poly_points = self.drawing_ann
            for i in range(len(poly_points) - 1):
                painter.drawLine(*poly_points[i], *poly_points[i+1])
                painter.drawEllipse(QPoint(*poly_points[i]), 4, 4)
        
        if draw:
            painter.end()
            self.setPixmap(pixmap)
        else:
            return painter, pixmap
    
    def getAnns(self):
        res = []
        for ann in self.anns:
            float_ann = []
            for i in range(len(ann)):
                float_ann.append([ann[i][0] / self.pw, ann[i][1] / self.ph])
            res.append(float_ann)
        return res
    
    def saveAnns(self):
        with open(self.label_path, "w") as f:
            anns = self.getAnns()
            
            str_anns = []
            for ann in anns:
                float_ann = sum(ann, [])
                str_ann = list(map(str, float_ann))
                str_anns.append(','.join(str_ann))
                
            f.write('\n'.join(str_anns))
    
    def loadAnns(self):
        if os.path.isfile(self.label_path):
            with open(self.label_path, "r") as f:
                anns = f.readlines()
            anns1d = [ann.strip('\n').split(',') for ann in anns]
            anns1d = [list(map(float, ann)) for ann in anns1d]
            
            anns = []
            for ann1d in anns1d:
                ann = []
                for i in range(len(ann1d)//2):
                    ann.append([int(ann1d[2*i]*self.pw), int(ann1d[2*i+1]*self.ph)])
                ann += [ann[0]]
                anns.append(ann)
                
            return anns
        else:
            return []
    
    def show_example(self, crop_size, stride):
        painter, pixmap = self.drawAnns(draw=False)
        painter.setPen(QPen(QColor(0, 255, 0), 3))
        painter.setBrush(Qt.NoBrush)
        
        draw_crop_size = int(crop_size / self.iw * self.pw)
        painter.drawRect(3, 3, draw_crop_size, draw_crop_size)
        
        painter.setPen(QPen(QColor(0, 0, 255), 3))
        painter.drawRect(int(stride/self.iw*self.pw+3), 3, draw_crop_size, draw_crop_size)
        
        painter.end()
        
        self.setPixmap(pixmap)
        
        QTimer.singleShot(1500, self.drawAnns)
        
    def change_mode(self, mode):
        self.mode = mode

        
class SettingDialog(QDialog):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Welcome")
        self.setStyleSheet("font-size: 20px; font-weight: bold; font-family: Arial")
        
        title = QLabel("Abnormal Area Auto Cropping")
        title.setStyleSheet("font-size: 40px; font-weight: bold; font-family: Arial")
        
        subtitle = QLabel("github.com/ZeroAct")
        subtitle.setStyleSheet("font-size: 15px; font-family: Arial; font-color: blue")
        
        self.directory = QLineEdit('./')
        self.directory.setReadOnly(True)
        self.directory.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.directory.setFixedWidth(540)
        
        browse_btn = QPushButton("Load Directory")
        browse_btn.clicked.connect(self.browse_directory)
        browse_btn.setFixedWidth(160)
        
        self.canvas_width = QLineEdit("1280")
        self.canvas_width.setValidator(QIntValidator())
        self.canvas_height = QLineEdit("720")
        self.canvas_height.setValidator(QIntValidator())
        
        self.start_btn = QPushButton("Start Cropping!")
        self.start_btn.clicked.connect(self.close)
        self.start_btn.setFixedWidth(160)
        self.start_btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        n = len(get_image_paths('./'))
        if n == 0:
            self.start_btn.setEnabled(False)
        
        self.status = QLabel(f"{n} images detected")
        self.status.setStyleSheet("font-size: 20px; font-family: Arial; font-color: blue")
        
        ml = QVBoxLayout()
        ml.addWidget(title, alignment=Qt.AlignCenter)
        ml.addWidget(subtitle, alignment=Qt.AlignRight)
        
        s = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        ml.addItem(s)
        
        ml.addWidget(QLabel("Directory Setting"))
        fl = QHBoxLayout()
        fl.addWidget(self.directory, alignment=Qt.AlignLeft)
        fl.addWidget(browse_btn, alignment=Qt.AlignRight)
        ml.addItem(fl)
        
        ml.addItem(s)
        ml.addWidget(QLabel("Canvas Size Setting"))
        
        cl = QGridLayout()
        cl.setSpacing(4)
        cl.addWidget(QLabel("Width  : "), 0, 0, 1, 1)
        cl.addWidget(self.canvas_width, 0, 1, 1, 1)
        cl.addWidget(QLabel("Height : "), 1, 0, 1, 1)
        cl.addWidget(self.canvas_height, 1, 1, 1, 1)
        cl.addWidget(self.start_btn, 0, 2, 2, 1)
        ml.addItem(cl)
        
        ml.addWidget(self.status, alignment=Qt.AlignRight)
        
        self.setLayout(ml)
        self.show()
        self.setFixedSize(self.size())
    
    def browse_directory(self):
        directory = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        
        if directory == '':
            directory = './'
        
        n = len(get_image_paths(directory))
        if n == 0:
            self.start_btn.setEnabled(False)
        else:
            self.start_btn.setEnabled(True)
        self.status.setText(f"{n} images detected")
        self.directory.setText(directory)

def GetSetting():
    f = SettingDialog()
    f.exec_()
    
    return {"img_dir": f.directory.text(),
            "canvas_width": int(f.canvas_width.text()),
            "canvas_height": int(f.canvas_height.text())}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        setting_values = GetSetting()
        self.img_dir = setting_values["img_dir"]
        self.img_paths = get_image_paths(self.img_dir)
        
        self.result_path = os.path.join("results", os.path.split(self.img_dir)[-1])
        os.makedirs(self.result_path, exist_ok=True)
        
        self.positive_path = os.path.join(self.result_path, "positive")
        os.makedirs(self.positive_path, exist_ok=True)
        
        self.negative_path = os.path.join(self.result_path, "negative")
        os.makedirs(self.negative_path, exist_ok=True)
        
        self.mask_path = os.path.join(self.result_path, "mask")
        os.makedirs(self.mask_path, exist_ok=True)
        
        self.negative_mask_path = os.path.join(self.result_path, "neg_mask")
        os.makedirs(self.negative_mask_path, exist_ok=True)
        
        self.label_path = os.path.join(self.result_path, "annotations")
        os.makedirs(self.label_path, exist_ok=True)
        
        # Define widgets
        self.canvas = Canvas(width=setting_values["canvas_width"], height=setting_values["canvas_height"])
        self.canvas.setWindowFlags(Qt.FramelessWindowHint)
        
        self.label_index = 0
        self.label_index_w = QLabel(f"{self.label_index + 1} / {len(self.img_paths)}")
        
        self.before_btn = QPushButton("◀")
        self.next_btn = QPushButton("▶")
        self.crop_btn = QPushButton("Go!")
        
        self.crop_size = QLineEdit("500")
        self.stride = QLineEdit("100")
        self.example_btn = QPushButton("Example")
        self.example_btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        
        self.poly_radio = QRadioButton('polygon')
        self.poly_radio.setChecked(True)
        self.box_radio = QRadioButton('bbox')
        self.box_radio.setDisabled(True)
        
        # Set events
        self.before_btn.clicked.connect(lambda : self.move_index(-1))
        self.next_btn.clicked.connect(lambda : self.move_index(+1))
        self.crop_btn.clicked.connect(self.crop_image)
        
        self.crop_size.setValidator(QIntValidator())
        self.stride.setValidator(QIntValidator())
        self.example_btn.clicked.connect(self.show_example)
        
        self.poly_radio.toggled.connect(self.change_ann_mode)
        self.box_radio.toggled.connect(self.change_ann_mode)
        
        # Layout
        self.setStyleSheet("font-size: 20px; font-weight: bold; font-family: Arial")
        
        w = QWidget()
        
        gl = QVBoxLayout()
        
        il = QHBoxLayout()
        il.addWidget(self.label_index_w)
        il.addWidget(self.before_btn)
        il.addWidget(self.next_btn)
        gl.addItem(il)
        
        # setting layout
        sl = QGridLayout()
        sl.setSpacing(4)
        sl.addWidget(QLabel("Crop Size"), 0, 0, 1, 1)
        sl.addWidget(self.crop_size, 0, 1, 1, 2)
        
        sl.addWidget(QLabel("Stride"), 1, 0, 1, 1)
        sl.addWidget(self.stride, 1, 1, 1, 2)
        
        sl.addWidget(self.example_btn, 0, 3, 2, 1)
        
        gl.addItem(sl)
        
        mode_chbx_group = QGroupBox("Annotation Mode")
        chl = QHBoxLayout()
        chl.addWidget(self.poly_radio)
        chl.addWidget(self.box_radio)
        mode_chbx_group.setLayout(chl)
        
        gl.addWidget(mode_chbx_group)
        
        gl.addWidget(self.crop_btn)
        
        w.setLayout(gl)
        self.setCentralWidget(w)
        
        img_name = os.path.splitext(os.path.split(self.img_paths[self.label_index])[-1])[0]
        self.canvas.SetImage(self.img_paths[self.label_index], os.path.join(self.label_path, img_name+".txt"))
        
        self.show()
        self.move(30, 30)
        self.canvas.move(self.x()+self.width()+15, self.y())
        self.canvas.show()
    
    def move_index(self, x):
        self.label_index = (self.label_index + len(self.img_paths) + x) % len(self.img_paths)
        self.label_index_w.setText(f"{self.label_index + 1} / {len(self.img_paths)}")
        
        img_name = os.path.splitext(os.path.split(self.img_paths[self.label_index])[-1])[0]
        self.canvas.SetImage(self.img_paths[self.label_index], os.path.join(self.label_path, img_name+".txt"))
    
    def change_ann_mode(self):
        if self.poly_radio.isChecked():
            self.canvas.change_mode('poly')
        else:
            self.canvas.change_mode('box')
    
    def crop_image(self):
        self.crop_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.before_btn.setEnabled(False)
        
        img = cv2.imread(self.img_paths[self.label_index])
        height, width = img.shape[:2]
        
        img_name = os.path.splitext(os.path.split(self.img_paths[self.label_index])[-1])[0]
        
        # load negative annotation
        polys = self.canvas.getAnns().copy()
        
        for i, poly in enumerate(polys):
            for j, point in enumerate(poly):
                polys[i][j] = [int(point[0]*width), int(point[1]*height)]
        
        # draw mask
        mask_img = np.zeros((height, width), dtype=np.uint8)
        for poly in polys:
            mask_img = draw_mask(mask_img, poly)
        
        # save mask img (whole)
        cv2.imwrite(os.path.join(self.mask_path, img_name+".png"), mask_img*255)
        
        # crop img
        crop_size = int(self.crop_size.text())
        crop_area = crop_size**2
        stride = int(self.stride.text())
        
        start_xs = list(range(0, width-crop_size, stride))
        start_ys = list(range(0, height-crop_size, stride))
        
        positive_index = 0
        negative_index = 0
        
        total_step = len(start_xs) * len(start_ys)
        progress_idx = 0
        for x1 in start_xs:
            for y1 in start_ys:
                x2 = x1 + crop_size
                y2 = y1 + crop_size
                
                inter_area = np.sum(mask_img[y1:y2, x1:x2])
                
                if inter_area == 0:
                    cv2.imwrite(os.path.join(self.positive_path, f"{img_name}_{positive_index}.png"), img[y1:y2, x1:x2, :])
                    positive_index += 1
                elif inter_area >= crop_area * 0.01:
                    cv2.imwrite(os.path.join(self.negative_path, f"{img_name}_{negative_index}.png"), img[y1:y2, x1:x2, :])
                    cv2.imwrite(os.path.join(self.negative_mask_path, f"{img_name}_{negative_index}.png"), mask_img[y1:y2, x1:x2]*255)
                    negative_index += 1
                
                progress_idx += 1
                self.crop_btn.setText(f"{int(progress_idx/total_step*100)} %")
                QtTest.QTest.qWait(1)
        
        self.crop_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        self.before_btn.setEnabled(True)
        self.crop_btn.setText("Go!")
    
    def show_example(self):
        self.canvas.show_example(int(self.crop_size.text()), int(self.stride.text()))
    
    def closeEvent(self, e):
        self.canvas.close()
    
    def moveEvent(self, e):
        self.canvas.move(self.x()+self.width()+15, self.y())

if __name__ == "__main__":
    app = QApplication([])
    w = MainWindow()
    app.exec_()

