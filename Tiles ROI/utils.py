import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image

class MPGrid:
    def __init__(self, dpi:int=120):
        self.dpi = dpi

    def Add(self, image, size=None, intervals=(100, 100), color="black", show_lbls=False):
        assert all(x > 0 for x in intervals), "intervals values should be > 0"
        if type(image) is str:
            try: image = self.read(image, size)
            except:
                print("[ERROR] Could not read the image file:", image)
                return

        self.image = image
        self.shape = shape = image.shape
        self.intervals = intervals
        self.fig = fig = plt.figure(figsize=(shape[1]//self.dpi, shape[0]//self.dpi), dpi=self.dpi)
        ax = fig.add_subplot(111)

        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        
        img_grid = self.add_grid(image, intervals, color)

        ax.imshow(img_grid)
        if show_lbls:
            self._add_gridsquare_labels(ax, intervals)

        ax.format_coord = self.cord_formater
        
        fig.canvas.mpl_connect("button_press_event", lambda x: self.get_grid_square(shape, intervals))
        return fig

    def read(self, src, size=None):
        img = Image.open(src)
        if size:
            img = img.resize(size)
        return np.array(img)

    def _add_gridsquare_labels(self, ax, interval):
    
        nx = abs(int((ax.get_xlim()[1]-ax.get_xlim()[0])/ interval[0]))
        ny = abs(int((ax.get_ylim()[1]-ax.get_ylim()[0])/ interval[1]))
        for j in range(ny):
            y = interval[1] /2 + j * interval[1]
            for i in range(nx):
                x = interval[0] / 2. + i * interval[0]
                ax.text(x,y,'{:d}'.format(i+j*nx),color='w',ha='center',va='center')

    @staticmethod
    def add_grid(img, grid_intervals=(100, 100), color="black"):
        img = img.copy()
        colors = {
            "black" : [0, 0, 0],
            "white" : [255, 255, 255]
        }
        assert color in colors, f"color should be one of {tuple(colors.keys())}"

        color = colors[color]
        gx, gy = grid_intervals
        img[:, ::gx, :] = color
        img[::gy, :, :] = color
        
        return img

    def cord_formater(self, x, y):
        self.mouse_x, self.mouse_y = x, y
        return f"{x:.2f} {y:.2f}"

    def get_grid_square(self, x=None, y=None, intervals=None):
        img_shape = self.shape
        
        xi, yi = self.intervals if intervals is None else intervals
        if x is not None:
            ms_x, ms_y = x, y
        else:
            return
            
        x, y = xi * (ms_x // xi), yi * (ms_y // yi)
        xm, ym = min(x+xi, img_shape[1]), min(y+yi, img_shape[0])
        return tuple(map(int, (x, y, xm, ym)))

def highlight_roi(rois, img_dim):
    img = np.zeros(img_dim)
    for roi in rois:
        x, y, xm, ym = roi
        w, h = xm - x, ym - y
        img[y:ym, x:xm] = np.ones((h, w, 1), dtype=np.float32)
    return plt.imshow(img, alpha=0.3, cmap="jet")

def mpl2tk(plot, parent):
    try:canvas = FigureCanvasTkAgg(plot, master=parent)
    except Exception as e:
        print(e)
        canvas = FigureCanvasTkAgg(plt.figure(), master=parent)
    canvas.draw()
    widget = canvas.get_tk_widget()
    return canvas, widget

class Slider:
    def __init__(self, slides):
        self.slides = slides
        self.size = len(slides)
        self.ind = 0

    def update(self, value):
        self.ind += value
        if 0 <= self.ind < self.size:
            slide = self.slides[self.ind]
            return slide

        else:
            self.ind = 0 if self.ind < 0 else self.size - 1

def pack_all(*widgets, **kwargs):
    for widget in widgets:
        widget.pack(**kwargs)

def get_fname(path, re_dir=False):
    dir, file = os.path.split(path)
    fname = file.rsplit('.')[0]
    if re_dir:
        return dir, fname
    return fname