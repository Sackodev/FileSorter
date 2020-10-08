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
import hashlib

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

# gets all files in folder
# add break to not include subdirectories

root_path = ""
#if root_path[-1] != os.path.sep:
#    root_path = root_path + os.path.sep
#    print("NOOO")

stop_dupe_dialog = False

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
def img_resizer(side_max, f_path = ''):
    #gets image from path
    if f_path == '':
        orig = Image.open(file_path[num])
    else:
        orig = Image.open(f_path)

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
    global num, gif_frames, play_gif, gif_duration, gif_avg_time, play_gif
    if play_gif == True:
        play_gif = False
        time.sleep(.2)
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
                    gif_avg_time = round(gif_duration/len(gif_frames))
                    print(gif_avg_time)
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

dupe_win = ''

def make_dupe_window(fpath_list, progress, dupe_win):
    try:
        dupe_win.grab_set()
    except Exception as e:
        print(e)
    dupe_win.geometry("650x600")
    center_window([650, 600], dupe_win)
    dupe_win.title("Duplicate Checker")
    dupe_win.resizable(width=False, height=False)

    top_fr = tk.Frame(dupe_win)
    top_fr.pack()
    img_frame = tk.Frame(dupe_win)
    img_frame.pack()
    bot_fr = tk.Frame(dupe_win)
    bot_fr.pack(side="bottom")

    top_text = tk.Label(top_fr, text="Choose which duplicates to keep (" + str(progress[0]) + "/" + str(progress[1]) + "): \n(Must choose one)")
    top_text.pack()

    img_list = []
    img_info_list = []
    img_text_list = []
    chk_list = []
    chk_f_num_list = []

    final = False
    if progress[0] == progress[1]:
        final = True

    i = 0
    for img in fpath_list:
        img_info_list.append(tk.Frame(img_frame))
        img_info_list[-1].pack(fill="x")
        img_list.append(tk.Label(img_info_list[-1], height = 100, width = 100, padx=15))
        img_list[-1].pack(side='left', fill="both", expand=False)

        cur_path = img
        cur_dir = cur_path[0:(cur_path.rfind(os.sep))]
        cur_name = cur_path[(cur_path.rfind(os.sep)) + 1:]

        chk_f_num_list.append(tk.IntVar())

        chk_list.append(tk.Checkbutton(img_info_list[-1], variable=chk_f_num_list[-1]))
        chk_list[-1].pack(side="left")

        img_text_string = "File name: " + cur_name + "\nDirectory: " + cur_dir + "\nFile size: " + str(math.floor(os.path.getsize(cur_path)/1024)) + " KB\n"
        img_text_list.append(tk.Label(img_info_list[-1], text=img_text_string, justify=tk.RIGHT, padx=15))
        img_text_list[-1].pack(side='right')
        img_text_list[-1].configure(font=("TkDefaultFont", 10))

        if i == 0:
            chk_list[-1].select()

        resized = img_resizer(100, img)
        
        img = ImageTk.PhotoImage(resized)

        img_list[-1].configure(image=img)
        img_list[-1].image = img

        i += 1

    # if "Stop Checking" button clicked, the duplicate dialog boxes stop, and you're brought back to the main window
    def stop_checking_pressed():
        global stop_dupe_dialog
        stop_dupe_dialog = True
        dupe_win.grab_release()
        dupe_win.destroy()
        randimg()

    # when "Keep Selected..." clicked, keeps files that are selected, and deletes files that are unselected
    def dupe_win_pressed():
        files_keep = []
        files_delete = []
        # checks if any check boxes were selected, and figures out keep/delete files accordingly
        for i in range(len(chk_f_num_list)):
            if chk_f_num_list[i].get():
                files_keep.append(fpath_list[i])
            else:
                files_delete.append(fpath_list[i])
        # does not allow user to leave the dialog box until at least one image is checked
        if len(files_keep) >= 1:
            # deletes all unselected files
            for del_file_path in files_delete:
                if os.path.exists(del_file_path):
                    try:
                        os.remove(del_file_path)
                    except Exception as e:
                        print(e)
            dupe_win.grab_release()
            dupe_win.destroy()
        if final:
            randimg()

    # bottom buttons
    keep_button = tk.Button(bot_fr, padx=10, text="Keep Selected...", command = dupe_win_pressed)
    keep_button.pack(side="left")
    stop_dupe_button = tk.Button(bot_fr, padx=10, text="Stop Checking", command = stop_checking_pressed)
    stop_dupe_button.pack(side="left")
    
def make_dir_window():
    global newdir_val
    global dir_win
    global newdir_val

    newdir_val = tk.StringVar()

    dir_win = tk.Toplevel()
    dir_win.geometry("400x100")
    dir_win.title("Create New Folder")
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
    global root_path, window
    # disables the use of any window besides the directory selection box
    dir_select.grab_set()
    # brings the directory select window to focus
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
                # control is reenabled for all windows
                dir_select.grab_release()
                dir_select.destroy()
                # resets the window if it is already set for a directory change
                if 'window' in globals():
                    try:
                        window.destroy()
                    except Exception as e:
                        print(e)
                    window = tk.Tk()
                    window.title("File Sorter")
                    window.geometry("450x900")
                    center_window([450, 900], window)
                    window.resizable(width=False, height=True)

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
    if play_gif != False:
        # prepares to run next frame once gif's average frame time passes
        window.after(gif_avg_time, gif_loop)
        gif_frame_num += 1
        if gif_frame_num >= len(gif_frames):
            gif_frame_num = 0

        # turns PIL Image into an ImageTk PhotoImage object
        img = ImageTk.PhotoImage(gif_frames[gif_frame_num])
        panel.configure(image=img)
        panel.image = img
    else:
        print("Exited GIF player.")

# starts initial launch of gif file animation
def gif_player():
    global play_gif, gif_thread, gif_frame_num
    # when set to false, gif_loop discontinues
    play_gif = True
    # starts off the first animated frame of the gif
    gif_loop()
    gif_frame_num = 0

# deletes selected file after a warning prompt; triggered by 'Delete file' button
def delete_file():
    global file_path, file_name, file_dir, file_name_noext, file_ext
    
    # Yes/No Prompt to be sure the user wanted to delete the selected file
    MsgBox = messagebox.askquestion('Delete File', 'Are you sure you want to delete this file?', icon='warning')
    # If user selected yes, file gets deleted
    if MsgBox == 'yes':
        if os.path.exists(file_path[num]):
            try:
                os.remove(file_path[num])
            except Exception as e:
                info_text_change("File could not be deleted :(", 1)
                print(e)
            else:
                info_text_change("File '" + file_name[num] + "' was deleted!", 0)
                randimg()
        else:
            info_text_change("File could not be deleted :(", 1)

# opens the file in its default program
def open_default():
    webbrowser.open(file_path[num])

# Checks for image duplicates, either including subdirectory images or not
def duplicate_search():
    # If user hits the button indicating to stop checking duplicates,
    # then this is set to false, closing all future dialogs
    global stop_dupe_dialog

    # updates current directory for if user selects 'No' in Subdirectory prompt
    dir_update()
    
    # stores shrinked and grey scaled thumbnail used for image duplicate comparisons
    grey_scaled = []

    # each grey scaled image gets converted to an md5 according to each pixel's color value/16
    grey_md5 = []

    # if a duplicate is found, this dict will contain them
    # still contains singles, just skipped over
    md5_dict = {}

    files_to_search = []
    files_to_search_ext = []
    MsgBox = tk.messagebox.askquestion("Search in Subdirectory?", "Do you also want to search for duplicates in subdirectories?", icon='question')
    if MsgBox == 'yes':
        for (dirpath, dirnames, filenames) in os.walk( root_path ):
            files_to_search.extend(os.path.join(dirpath, filename) for filename in filenames)
        for item in files_to_search:
            if '.' in item:
                split_vals = item.rsplit('.', 1)
                files_to_search_ext.append(split_vals[1])
            else:
                files_to_search_ext.append("NO_EXT")
    else:
        files_to_search = file_path
        files_to_search_ext = file_ext

    for i in range(len(files_to_search)):
        f = None
        if files_to_search_ext[i] in supported_types:
            f = files_to_search[i]
        else:
            grey_scaled.append('')
            grey_md5.append('')
            continue
        # shrinks the image with antialiasing, then converts it to greyscale
        grey_scaled.append(Image.open(f).resize((16, 16),Image.ANTIALIAS).convert('LA'))
        pixel_val = ''

        # gets current image and loads it to look at each pixel
        px = grey_scaled[-1].load()
        for x in range(16):
            for y in range(16):
                # divide's color value by 16 for easier comparison between files
                color = px[x, y][0]
                pixel_val += str((math.floor(color/16))) + ","
        grey_md5.append(hashlib.md5(pixel_val.encode()).hexdigest())
        if grey_md5[-1] in md5_dict:
            md5_dict[grey_md5[-1]].add(i)
        else:
            md5_dict[grey_md5[-1]] = {i}

    md5_with_dupe = []
    total_to_check = 0
    for md5 in md5_dict:
        if len(md5_dict[md5]) >= 2:
            md5_with_dupe.append(md5)
            total_to_check += 1

    i = 0
    for md5 in md5_with_dupe:
        if len(md5_dict[md5]) >= 2:
            i += 1
            fpath_list = []
            f_num = []
            for fnum in md5_dict[md5]:
                fpath_list.append(files_to_search[fnum])
                f_num.append(fnum)
            dupe_win = tk.Toplevel()
            make_dupe_window(fpath_list, [i, total_to_check], dupe_win)
            window.wait_window(dupe_win)
            if stop_dupe_dialog == True:
                stop_dupe_dialog = False
                break

    if len(md5_with_dupe) <= 0:
        messagebox.showinfo("No Duplicates", "No duplicates were found!")

def center_window(size, w = None):

    if w == None:
        w = window

    window_width = size[0]
    window_height = size[1]

    screen_width = w.winfo_screenwidth()
    screen_height = w.winfo_screenheight()

    x_cordinate = int((screen_width/2) - (window_width/2))
    y_cordinate = int((screen_height/2) - (window_height/2))

    w.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))

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
    create_folder_butt.pack(side='top')
    check_dupes_butt = tk.Button(create_folder_frame, text="Check for duplicates", command=duplicate_search)
    check_dupes_butt.pack(side='top')
    change_folder_butt = tk.Button(create_folder_frame, text="Change working directory...", command=dir_select_window)
    change_folder_butt.pack(side='top')

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
window.geometry("450x900")
center_window([450, 900], window)
window.resizable(width=False, height=True)
#window.configure(background='grey')

dir_buttons = []

# gif-related variables
# used to tell when picture is a gif
play_gif = False
# stores each gif image/frame
gif_frames = []
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