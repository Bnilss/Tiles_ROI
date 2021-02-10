import os
import tkinter as tk
import warnings
import json
from tkinter import ttk, messagebox, filedialog
from utils import *

warnings.filterwarnings('ignore')


class LabelWidget(ttk.LabelFrame):
    def __init__(self, master, widget, text="", **kwargs):
        super().__init__(master, text=text)
        self.widget = widget(self, **kwargs)
        self.widget.pack(expand=True, fill="both")

class LabelPopUp(tk.Toplevel):
    def __init__(self, master, params, **kwargs):
        super().__init__(master, **kwargs)
        self.params = params
        self.geometry('200x120')
        self.title('Labeler')
        self.lbl = LabelWidget(self, ttk.Entry, text="Enter roi label:")
        btn = ttk.Button(self, text="Save", command=self.save)
        pack_all(self.lbl, btn, expand=True, fill="x", pady=10)

    def save(self):
        path = self.params['path']
        lbl = self.lbl.widget.get()
        self.params['label'] = lbl
        if os.path.exists(path):
            prv_lbl = json.load(open(path))['label']
            if prv_lbl != lbl:
                print("[INFO] found file with same name but different labels, saving it to a different name!")
                path, fname = get_fname(path, re_dir=True)
                fname = f"{fname}_{lbl}.json"
                path = os.path.join(path, fname)
            elif messagebox.askquestion(message="File Already exists. continue?") == "no":
                self.destroy()
                return
        del self.params["path"]
        
        json.dump(self.params, open(path, "w"), indent=2)
        messagebox.showinfo(message="Label saved!")
        self.destroy()



class App(tk.Tk):
    def __init__(self, dpi=150):
        super().__init__()
        self.title('Tiles ROI Segmenter')
        self.geometry("600x600")
        self.init_style()

        self.current_img = None
        self.slider = None
        self.save_dir = "./"
        self.dpi = dpi
        self.grid = MPGrid(dpi)
        self.rois = set()

        self.display_opt = {
            "color":"black",
            "intervals":(100, 100),
            "size":None
        }

        self.init_ui()

        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.mainloop()

    def init_style(self):
        self.style = ttk.Style()
        try: self.style.theme_use('vista')
        except: pass

    def init_ui(self):
        NAV = ttk.Frame(self)
        NAV.place(relheight=0.1, relwidth=1)
        self.main = MAIN = ttk.Frame(self)
        MAIN.place(rely=0.1, relheight=0.8, relwidth=1)
        BTN = ttk.Frame(self)
        BTN.place(rely=0.9, relheight=0.1, relwidth=1)

        fold_btn = ttk.Button(NAV, text="Select an image folder", command=self.select_folder)
        save_dir = ttk.Button(NAV, text="Select a saving directory", command=self.select_savedir)
        back_btn = ttk.Button(NAV, text="Back", command=lambda : self.to(-1))
        next_btn = ttk.Button(NAV, text="Next" , command=lambda : self.to(1))
        reset = ttk.Button(NAV, text="Reset", command=lambda : self.display(reset=True))
        pack_all(fold_btn, save_dir, back_btn, next_btn, reset, side="left", expand=True)

        frame_0 = ttk.Frame(BTN)
        frame_1 = ttk.Frame(BTN)

        pack_all(frame_0, frame_1, expand=True, fill="both", side="left")

        grid_inter = LabelWidget(frame_0, ttk.Entry, text="Grid Intervals: (x,y)", width=20)
        grid_cl = LabelWidget(frame_0, ttk.Combobox, text="Grid Color", 
            values=['black', "white"])
        img_resize = LabelWidget(frame_0, ttk.Entry, text="Image Size: (width, height)")

        pack_all(grid_inter, grid_cl, img_resize, 
                expand=True, side="left")

        def set_opt():
            def process(x, default):
                try:
                    x = tuple(map(int, [i.strip() for i in x.split(",")]))
                except:
                    x = default
                return x

            intervals = process(grid_inter.widget.get(), self.display_opt['intervals'])
            size = process(img_resize.widget.get(), None)
            
            cl = grid_cl.widget.get()
            cl = cl if cl else self.display_opt['color']
            opt = {"intervals":intervals, "size":size, "color":cl}
            self.display_opt.update(opt)
            self.display()


        commit_cfg = ttk.Button(frame_1, text="Commit Changes", command=set_opt)
        save = ttk.Button(frame_1, text="Save Label", command=self.label)
        pack_all(save, commit_cfg, expand=True, fill="both")
        

    def display(self, rois=None, reset=False):
        if self.current_img is None:
            return
        for child in self.main.winfo_children():
            child.destroy()
        if reset: self.rois = set()
        img = self.grid.Add(self.current_img, **self.display_opt)
        self.canv, img_widget = mpl2tk(img, self.main)
        img_widget.pack(expand=True, fill="both")
        self.canv.mpl_connect('button_press_event', self.extract_roi)
        if rois:
            img.add_subplot(111)
            highlight_roi(rois, self.grid.shape)


    def extract_roi(self, event):
        roi = self.grid.get_grid_square(event.xdata, event.ydata, 
                self.display_opt['intervals']) # xmin, ymin, xmax, ymax
        if roi not in self.rois:
            self.rois.add(roi)
            self.display(self.rois)
        else:
            self.rois.remove(roi)
            self.display(self.rois)
            

    def exit(self):
        self.quit()
        self.destroy()

    def select_folder(self):
        dir = filedialog.askdirectory(initialdir="./", title="Select an Image Folder")
        if not dir:
            return
        files = [os.path.join(dir, file) for file in os.listdir(dir)]
        self.slider = Slider(files)
        self.current_img = self.slider.update(0)
        self.display()

    def to(self, value):
        if self.slider is not None:
            self.rois = set()
            self.current_img = self.slider.update(value)
            self.display()

    def select_savedir(self):
        self.save_dir = filedialog.askdirectory(initialdir="./", 
                title="Select a Saving directory")

    def label(self):
        if not self.current_img:
            return
        fname = get_fname(self.current_img)+".json"
        path = os.path.join(os.path.abspath(self.save_dir), fname)
        params = {
                "image_path":os.path.abspath(self.current_img),
                "path":path, "roi":list(self.rois), 
                "image_size":self.grid.shape[:2]
                }
        LabelPopUp(self, params)

if __name__ == "__main__":
    App()
