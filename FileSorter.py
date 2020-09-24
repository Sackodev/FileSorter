import os
import sys
import tkinter.filedialog
from tkinter import messagebox
import tkinter as tk
from PIL import ImageTk, Image
import math
import random
import os
from functools import partial
import threading
import time
import webbrowser

# FEATURES TO ADD
# Back button for when you misclick (up to like 50-100 images?)
# Maybe make directory buttons bigger or aligned better?
# Rename directory?
# Add duplicate scanner as a misc function?
# File type selector?
# Image ending fixer? (.jpg:large and such, maybe check file headers, webp?)
# Make sure files aren't being overwritten - DONE
#     -Give user option to automatically add prefix to file name when needed
# File (MIME) type checker for images? Sometimes, pngs are jpgs, etc
#
# TO FIX
# After moving a GIF, sometimes it stops playing and the image doesn't change like it should
#    -Still picks a new image, just doesn't display it
#    -If you move to a diff folder, it moves that new image
# Some files seem to save wrong
#    -Some pngs saved as jpgs
#    -Infrequent; could be after a gif save?
#    -Name in text box changes too
# GIF colors break occasionally (maybe after a file move?)
# GIFs sometimes prevent the next image from showing up (Not as often as before though!)
# GIFs sometimes play really fast (rare)

# supported file types
supported_types = ["png", "jpg", "gif", "jpeg", "jpg:large", "png:large", "jpg_large", "webp"]
# full path to file
file_path = []
# name of file with extension
file_name = []
# absolute directory file is in
file_dir = []
# file's name without extension
file_name_noext = []
# file's extension
file_ext = []
# immediate directory names
dir_names = []

# stores gif thread for displaying frames in a gif file
gif_thread = ""
# lock for gif thread
gif_lock = threading.Lock()

# gets all files in folder
# add break to not include subdirectories

root_path = ""
#if root_path[-1] != os.path.sep:
#    root_path = root_path + os.path.sep
#    print("NOOO")


num = 0

def img_update():
    global file_path, file_name, file_dir, file_name_noext, file_ext, dir_names
    # set to blank whenever they're updated
    file_path = []
    file_name = []
    file_dir = []
    file_name_noext = []
    file_ext = []

    # gets list of all files in current directory (not including subdirectories)
    # also gets all immediate subdirectory names
    for (dirpath, dirnames, filenames) in os.walk( root_path ):
        file_path.extend(os.path.join(dirpath, filename) for filename in filenames)
        file_name.extend(os.path.join(filename) for filename in filenames)
        file_dir.extend(os.path.join(dirpath) for filename in filenames)

        dir_names = dirnames
        break

    # sorts the immediate directories
    dir_names.sort()

    # gets file name without extension and its extension into separate variables
    # if file has no extension, file_ext value is set to "NO_EXT"
    for item in file_name:
        if '.' in item:
            split_vals = item.rsplit('.', 1)
            file_name_noext.append(split_vals[0])
            file_ext.append(split_vals[1])
        else:
            file_name_noext.append(file_name)
            file_ext.append("NO_EXT")

# resizes image to fit in tkinter's image display box
def img_resizer(side_max):
    #gets image from path
    orig = Image.open(file_path[num])

    # gets width and height for resizing
    width, height = orig.size
    
    # if width greater and is too big for the box, resize to fit based on width
    if width > side_max and width > height:
        ratio = height/width
        width = side_max
        height = math.floor(width * ratio)
    # if height greater and is too big for the box, resize to fit based on height
    elif height > side_max and height > width:
        ratio = width/height
        height = side_max
        width = math.floor(height * ratio)
    # if sides are equal but still too big for the box, resize both to fit box
    elif width == height and width > side_max:
        width, height = side_max, side_max

    #creates image with new dimensions
    resized = orig.resize((width,height),Image.ANTIALIAS)

    # returns pil image
    return resized

# picks a random image
def randimg(fn_old = None):
    global num, gif_frames, play_gif, gif_duration, gif_avg_time, play_gif, gif_thread
    if not isinstance(gif_thread, str):
        play_gif = False
        time.sleep(.1)
        gif_thread = ""
    if fn_old is not None:
        file_name_old = fn_old
    else:
        if num != 0:
            file_name_old = file_name[num]
        else:
            file_name_old = None
    file_count_old = len(file_name)
    img_update()
    dir_update()
    file_exists = False
    for i in file_ext:
        if i in supported_types:
            file_exists = True
            break
    if file_exists:
        # picks a random compatible file that is not the same as the last file, if possible
        while (True):
            # picks random file from list
            num = random.randint(0, len(file_name) - 1)
            # checks if selected file is supported; if it isn't compatible, another number is chosen
            if file_ext[num] in supported_types:
                # prevents selecting the same file twice if it can be avoided
                # len(file_name) used to get size of file list
                if file_name_old == file_name[num] and len(file_name) != 1:
                    continue
                # if selected file gets through all the checks, the file is kept and the loop is ended
                break
        
        # gif handling
        if file_ext[num] == "gif":
            gif_frames = []
            gif_img = Image.open(file_path[num])
            i = 0
            gif_duration = 0
            gif_avg_time = 0
            while True:
                try:
                    gif_img.seek(i)
                    gif_duration += gif_img.info['duration']
                    gif_frames.append(gif_img.copy())
                    # PIL Image object can be resized
                    gif_frames[i] = gif_frame_resize(gif_frames[i], 400)
                    i += 1
                except Exception as e:
                    #print(e)
                    gif_avg_time = (gif_duration/len(gif_frames))/1000
                    play_gif = True
                    gif_player()
                    resized = img_resizer(400)
                    break
        else:
            resized = img_resizer(400)

        if not len(file_name) == 1 and not file_count_old == 1:
            img = ImageTk.PhotoImage(resized)

            panel.configure(image=img)
            panel.image = img

            rename_ext.configure(text="." + file_ext[num])
            rename_ext.text = "." + file_ext[num]

            # clears the textbox
            rename_tbox.delete(0, tk.END)
            # places a default value in the textbox
            rename_tbox.insert(0, file_name_noext[num])
    else:
        info_text_change("No more compatible files to sort!", 1)

# used to resize each image in a gif to fit the tkinter image box; works similarly to img_resizer
# maybe fix later to reduce redundancy
def gif_frame_resize(orig, side_max):
    width, height = orig.size

    if width > side_max and width > height:
        ratio = height/width
        width = side_max
        height = math.floor(width * ratio)
    elif height > side_max and height > width:
        ratio = width/height
        height = side_max
        width = math.floor(height * ratio)
    elif width == height and width > side_max:
        width, height = side_max, side_max

    #creates image with new dimensions
    resized = orig.resize((width,height),Image.ANTIALIAS)

    # returns resized pil image
    return resized

def rename():
    global file_name, file_path, file_name_noext
    new_name = rename_val.get() + "." + file_ext[num]
    new_path = file_dir[num] + new_name
    if not os.path.exists(new_path) and new_name != file_name[num]:
        try:
            os.rename(file_path[num], file_dir[num] + new_name)
            info_text_change("The file name was changed to: " + new_name, 0)
                
            file_name[num] = rename_val.get() + "." + file_ext[num]
            file_path[num] = file_dir[num] + file_name[num]
            file_name_noext[num] = rename_val.get()
        except Exception as e:
            info_text_change("File name change unsuccessful :(", 1)
            print(e)
    elif new_name == file_name[num]:
        info_text_change("New file name wasn't given!", 1)
    else:
        info_text_change("File already exists with that name!", 1)

def info_text_change(msg, type):
    if type == 0:
        info_text.configure(fg="green")
        info_text.fg = "green"
    if type == 1:
        info_text.configure(fg="red")
        info_text.fg = "red"
    info_text.configure(text=msg)
    info_text.text = msg

def info_text_clear():
    info_text.configure(text=" ")
    info_text.text = " "

def move_file(d_name):
    global file_path, file_name, file_dir, file_name_noext, file_ext
    # if the user renamed the file without hitting the rename button first, it renames the file as well as moves the files
    if rename_val.get() != file_name_noext[num]:
        new_path = root_path + d_name + os.path.sep + rename_val.get() + "." + file_ext[num]
    # creates the file's new path without renaming it if the rename value wasn't changed
    else:
        new_path = root_path + d_name + os.path.sep + file_name[num]
    # checks if a file with that name already exists
    if not os.path.exists(new_path):
        # program attempts to move file
        try:
            os.rename(file_path[num], new_path)
        # if fails, throws error
        except Exception as e:
            info_text_change("File move failed :(", 1)
            print(e)
        # if success, notifies the user
        else:
            if rename_val.get() != file_name_noext[num]:
                info_text_change("File '" + rename_val.get() + "." + file_ext[num] + "' was moved to '" + d_name + "' folder!", 0)
            else:
                info_text_change("File '" + file_name[num] + "' was moved to '" + d_name + "' folder!", 0)
            fn_old = file_name[num]
            #del file_path[num], file_name[num], file_dir[num], file_name_noext[num], file_ext[num]
            randimg(fn_old)
    # if file name already exists in selected folder, gives error
    else:
        info_text_change("File name already exists in that folder!", 1)

def make_dir():
    global dir_win
    new_dir = newdir_val.get()
    dir_win.destroy()
    try:
        path = root_path + new_dir
        os.mkdir(path)
    except OSError:
        info_text_change("Failed to create directory: " + new_dir, 1)
    else:
        info_text_change("Successfully created directory: " + new_dir, 0)
        img_update()
        dir_update()

def rand_butt_click():
    info_text_clear()
    randimg()

def make_dir_window():
    global newdir_val
    global dir_win
    global newdir_val

    newdir_val = tk.StringVar()

    dir_win = tk.Toplevel()
    dir_win.geometry("400x100")
    dir_win.title("Create New Directory")
    dir_win.resizable(width=False, height=False)

    margin = tk.Frame(dir_win, height=20)
    margin.pack()
    top_fr = tk.Frame(dir_win)
    top_fr.pack()
    bot_fr = tk.Frame(dir_win)
    bot_fr.pack()
    
    dir_label = tk.Label(top_fr, text="Give a new folder name: ")
    dir_label.pack(side="top")
    dir_textbox = tk.Entry(bot_fr, textvariable = newdir_val)
    dir_textbox.pack(side='left')
    dir_button = tk.Button(bot_fr, text="Create", command=make_dir)
    dir_button.pack(side='left')

def dir_update():
    # creates a button for all directories in the root folder
    global dir_buttons, dir_frame, dir_header
    i = 0
    while i < len(dir_buttons):
        dir_buttons[i].destroy()
        del dir_buttons[i]
    
    i = 0
    for dirs in dir_names:
        if i%3 == 0:
            dir_buttons.append(tk.Button(dir_frame_col1, text=dir_names[i], width=14, command=partial(move_file, dir_names[i])))
        elif i%3 == 1:
            dir_buttons.append(tk.Button(dir_frame_col2, text=dir_names[i], width=14, command=partial(move_file, dir_names[i])))
        elif i%3 == 2:
            dir_buttons.append(tk.Button(dir_frame_col3, text=dir_names[i], width=14, command=partial(move_file, dir_names[i])))
        
        dir_buttons[i].pack(pady = 1, padx = 1)
        i += 1

# brings up the directory selection dialog box and takes care of handling
def choose_directory():
    global root_path
    dir_select.attributes('-topmost', False)
    chosen_dir = tk.filedialog.askdirectory()
    # if a directory was chosen, the main window is created
    # if nothing selected, program exits
    if not chosen_dir:
        sys.exit()
    else:
        root_path = chosen_dir + os.path.sep
        img_update()
        file_exists = False
        for i in file_ext:
            # if file type supported, the main program is started and the directory dialog is closed
            if i in supported_types:
                file_exists = True
                dir_select.destroy()
                main_window()
                break
        # if no files have a compatible type, the program asks for a different directory
        if file_exists == False:
            dir_select.attributes('-topmost', True)
            msg = "Chosen directory doesn't contain compatible file types. Pick a different directory."
            dir_label.configure(text=msg, wraplength=370)

# first window that pops up
# tells the user to select a directory to use the program
def dir_select_window():
    global dir_select, dir_label
    dir_select = tk.Toplevel()
    # forces this dialog box to be on top of the other window
    dir_select.attributes('-topmost', True)
    # makes this dialog box focused
    dir_select.focus_force()
    dir_select.geometry("400x100")
    dir_select.title("Directory Selection")
    dir_select.resizable(width=False, height=False)
    # closes the program if the dialog box is closed
    dir_select.protocol("WM_DELETE_WINDOW", sys.exit)

    margin = tk.Frame(dir_select, height=20)
    margin.pack()
    top_fr = tk.Frame(dir_select)
    top_fr.pack()
    bot_fr = tk.Frame(dir_select)
    bot_fr.pack()
    
    dir_label = tk.Label(top_fr, text="Pick a directory to sort through: ")
    dir_label.pack(side="top")
    # if clicked, dialog box pops up for selecting a folder
    dir_button = tk.Button(bot_fr, text="Select directory...", command=choose_directory)
    dir_button.pack(side='left')

def gif_loop():
    global gif_frame_num, img
    while(True):
        time.sleep(gif_avg_time)
        if play_gif != False:
            gif_lock.acquire()
            gif_frame_num += 1
            if gif_frame_num >= len(gif_frames):
                gif_frame_num = 0

            # turns PIL Image into an ImageTk PhotoImage object
            img = ImageTk.PhotoImage(gif_frames[gif_frame_num])
            panel.configure(image=img)
            panel.image = img
            gif_lock.release()
        else:
            sys.exit()
            print("Exited GIF thread.")

def gif_player():
    global play_gif, gif_thread, gif_frame_num
    play_gif = True
    gif_frame_num = 0
    gif_thread = threading.Thread(target=gif_loop)
    gif_thread.start()

def delete_file():
    global file_path, file_name, file_dir, file_name_noext, file_ext
    MsgBox = messagebox.askquestion('Delete File', 'Are you sure you want to delete this file?', icon='warning')
    if MsgBox == 'yes':
        if os.path.exists(file_path[num]):
            try:
                os.remove(file_path[num])
            except Exception as e:
                info_text_change("File could not be deleted :(", 1)
                print(e)
            else:
                info_text_change("File '" + file_name[num] + "' was deleted!", 0)
                #del file_path[num], file_name[num], file_dir[num], file_name_noext[num], file_ext[num]
                randimg()
        else:
            info_text_change("File could not be deleted :(", 1)

def open_default():
    webbrowser.open(file_path[num])

def main_window():
    global root_path, window, top_frame, bottom_frame, info_frame, img_frame, rename_frame, button_frame, dir_margin, dir_header, dir_frame, create_folder_frame, dir_frame_col1, dir_frame_col2, dir_frame_col3, info_text, panel, rename_butt, rand_butt, rename_val, rename_tbox, rename_ext, newdir_val, dir_buttons, create_folder_butt, resized, img, dir_win

    # updates the lists that allows the program to work
    img_update()

    # program's focus switched to the main window after the user selects a directory
    window.focus_force()

    # top and bottom frames for window organization
    top_frame = tk.Frame(window)
    top_frame.pack()
    bottom_frame = tk.Frame(window)
    bottom_frame.pack(side='bottom')

    # displays notifications on the top of the window to notify the user if an operation succeeded or failed (errors)
    info_frame = tk.Frame(top_frame)
    info_frame.pack(pady=7)
    # displays images
    img_frame = tk.Frame(top_frame, borderwidth=2, relief='solid')
    img_frame.pack(pady=7)

    # frame for textbox for renaming a file
    rename_frame = tk.Frame(bottom_frame)
    rename_frame.pack(pady=4)
    # buttons for file-related operations other than moving files to a different folder
    button_frame = tk.Frame(bottom_frame)
    button_frame.pack(pady=4)
    # separator
    dir_margin = tk.Frame(bottom_frame, height=15)
    dir_margin.pack()
    # directory section's header
    dir_header = tk.Label(bottom_frame, text="Move to folder:")
    dir_header.pack()
    # container for directory's button columns
    dir_frame = tk.Frame(bottom_frame)
    dir_frame.pack(pady=7)
    # container for new folder/directory button
    create_folder_frame = tk.Frame(bottom_frame)
    create_folder_frame.pack(pady=7)

    # columns where directory buttons will be placed
    dir_frame_col1 = tk.Frame(dir_frame)
    dir_frame_col2 = tk.Frame(dir_frame)
    dir_frame_col3 = tk.Frame(dir_frame)
    dir_frame_col1.pack(side="left")
    dir_frame_col2.pack(side="left")
    dir_frame_col3.pack(side="left")

    # sets the notification text's default height, lets the text wrap, and sets the text to blank
    info_text = tk.Label(info_frame, text=" ", wraplength=440, height=3)
    info_text.pack()

    # label where the image is displayed
    panel = tk.Label(img_frame, height = 400, width = 400)
    panel.pack(side='bottom', fill="both", expand="yes")

    # button for rename operation
    rename_butt = tk.Button(button_frame, text="Rename", command=rename)
    rename_butt.pack(side= 'left')
    # button for random file operation
    rand_butt = tk.Button(button_frame, text="Random file", command=rand_butt_click)
    rand_butt.pack(side= 'left')
    # button for opening file in default program
    open_butt = tk.Button(button_frame, text="Open in Default", command=open_default)
    open_butt.pack(side= 'left')
    # button to delete file
    delete_butt = tk.Button(button_frame, text="Delete file", command=delete_file, fg="red")
    delete_butt.pack(side= 'bottom')

    # textbox for renaming the current file
    rename_val = tk.StringVar()
    rename_tbox = tk.Entry(rename_frame, width = 30, textvariable = rename_val)
    rename_tbox.pack(side = 'left', padx=3)
    # displays the file's extension beside the textbox
    rename_ext = tk.Label(rename_frame, text="." + file_ext[num])
    rename_ext.pack(side = 'left')

    dir_buttons = []
    i = 0

    # creates buttons for all directories in the root folder
    dir_update()

    newdir_val = tk.StringVar()
    create_folder_butt = tk.Button(create_folder_frame, text="Create new folder...", command=make_dir_window)
    create_folder_butt.pack(side='bottom')

    # clears the textbox
    rename_tbox.delete(0, tk.END)
    # places a default value in the textbox
    rename_tbox.insert(0, file_name_noext[num])

    resized = ''
    img = ''
    randimg()

    dir_win = 0

    img_update()

# used to keep the parts of the main window global so the functions can access them
window = top_frame = bottom_frame = info_frame = img_frame = rename_frame = button_frame = dir_margin = dir_header = dir_frame = create_folder_frame = dir_frame_col1 = dir_frame_col2 = dir_frame_col3 = info_text = panel = rename_butt = rand_butt = rename_val = rename_tbox = rename_ext = newdir_val = create_folder_butt = resized = img = dir_win = 0

#creates tkinter window with options
window = tk.Tk()
window.title("File Sorter")
window.geometry("450x850")
window.resizable(width=False, height=True)
#window.configure(background='grey')

dir_buttons = []

# gif-related variables
# used to tell when picture is a gif
play_gif = False
# stores each gif image/frame
gif_frames = []
# stores the timer
gif_thread = ""
# gif frame counter
gif_frame_num = 0
# stores entire gif duration
gif_duration = 0
# average time per frame
gif_avg_time = 0

dir_select = ""
dir_label = ""
dir_select_window()

window.mainloop()