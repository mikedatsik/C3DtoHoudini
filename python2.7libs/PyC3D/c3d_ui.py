from PyC3D import c3d
import hou, os, tempfile

## UI File template
template = ('file_c3d.gad = FILENAME_FIELD(all) "File":0.35 VALUE(file_c3d.val);',
            'file_chan.gad = FILENAME_FIELD "File":0.35 VALUE(file_chan.val);',
            'savechan.val := 0;',
            'hou_cord.val := 1;',
            'framerate_enabler.val := 0;',
            'framerate.val := 24;',
            'startend_enabler.val := 0;',
            'startend0.val := 1;',
            'startend1.val := 100;',
            'mymenu.val = SELECT_MENU{',
            '"Geometry Set"',
            '"Locator Set"}',
            'dialog.win = DIALOG "C3D Import Option"{',
            'HSTRETCH LOOK(plain) LAYOUT(vertical)',
            'VALUE(open.val)',
            'ROW{',
            'HSTRETCH MARGIN(0.1)',
            'file_c3d.gad MIN_WIDTH(4.55) HSTRETCH;',
            'INFO_BUTTON "By Default .chan file will be seved to the .chan directory. Frame Rate and Start/End reads from file." WIDTH(0.3) HEIGHT(0.3) LOOKFLAT;}{',
            'HSTRETCH HMARGIN(0.1)',
            'LABEL "Import Options";}',
            'SEPARATOR;{',
            'HSTRETCH MARGIN(0.1)',
            'TOGGLE_BUTTON "Set .clip save directory" VALUE(savechan.val);',
            'file_chan.gad MIN_WIDTH(4.55) HSTRETCH;',
            'TOGGLE_BUTTON "Convert to Houdini coordinates" VALUE(hou_cord.val);}',
            'SEPARATOR;{',
            'HSTRETCH MARGIN(0.1)',
            'SELECT_MENU_BUTTON "Import Type: " MENU(mymenu.val);}',
            'ROW{',
            'HSTRETCH MARGIN(0.1)',
            'TOGGLE_BUTTON "Change Frame Rate:" VALUE(framerate_enabler.val);',
            'STRING_FIELD MIN_WIDTH(3.7) HSTRETCH VALUE(framerate.val);}',
            'ROW{',
            'HSTRETCH MARGIN(0.1)',
            'TOGGLE_BUTTON "Change Start/End:" VALUE(startend_enabler.val);',
            'FLOAT_VECTOR_FIELD(2) MIN_WIDTH(0.5) HSTRETCH VALUE(startend0.val,startend1.val);}',
            'SEPARATOR;',
            'ROW{',
            'HSTRETCH MARGIN(0.1) SPACING(0.1)',
            'COL{',
            'HSTRETCH}',
            'ACTION_BUTTON "Import" VALUE(save.val) SENDS(1);',
            'ACTION_BUTTON "Cancel" VALUE(save.val) SENDS(0);}}',
            'DISABLE file_chan.val;',
            'DISABLE framerate.val;',
            'DISABLE startend0.val;',
            'DISABLE startend1.val;')


def C3D_MainCallBackFunction():

    explist = hou.expandString(dialog.value("file_c3d.val")).split(" ; ")

    file_chan = [dialog.value("savechan.val"), dialog.value("file_chan.val")]
    hou_cord = dialog.value("hou_cord.val")
    framerate = [dialog.value("framerate_enabler.val"), dialog.value("framerate.val")]
    start_end = [dialog.value("startend_enabler.val"), dialog.value("startend0.val"), dialog.value("startend1.val")]
    mymenu = dialog.value("mymenu.val")
    
    if str(dialog.value("save.val")) == "1.0":
        if explist[0] == "":
            hou.ui.displayMessage("You must choose file!")
        else:
            check_done = 0
            for expstr in explist:
                if os.path.exists(expstr) and  os.path.splitext(expstr)[1].lower() == ".c3d":
                    cmd = []

                    cmd.append(expstr)

                    cmd.append(mymenu)

                    cmd.append(framerate[0])

                    cmd.append(int(framerate[1]))

                    ### ADD Convert to Houdini coordinates

                    cmd.append(start_end[0])

                    cmd.append(start_end[1])

                    cmd.append(start_end[2])
                    
                    if file_chan[0]:
                        if file_chan[1] != "":
                            cmd.append(file_chan[1])
                        else:
                            hou.ui.displayMessage("You must choose directory to write clip!\n or unselect checkbox to save by Default")
                            return
                    else:
                        cmd.append("")

                    c3d.CreateMarkerSet(*cmd)
                    print cmd
                    check_done=+1
            if check_done != 0:
                pass
                dialog.setValue("open.val", 0)
                dialog.destroy()
                hou.ui.displayMessage("All done!")
            else:
                hou.ui.displayMessage("You must choose .c3d file!")

    else:
        dialog.setValue("open.val", 0)
        dialog.destroy()

def C3D_ChanCallBackFunction():
    if str(dialog.value("savechan.val")) == "1":
        dialog.enableValue("file_chan.val", 1)
    else:
        dialog.enableValue("file_chan.val", 0)

def C3D_FramerateCallBackFunction():
    if str(dialog.value("framerate_enabler.val")) == "1":
        dialog.enableValue("framerate.val", 1)
    else:
        dialog.enableValue("framerate.val", 0)

def C3D_StartendCallBackFunction():
    if str(dialog.value("startend_enabler.val")) == "1":
        dialog.enableValue("startend0.val", 1)
        dialog.enableValue("startend1.val", 1)
    else:
        dialog.enableValue("startend0.val", 0)
        dialog.enableValue("startend1.val", 0)


def C3D_MainWindow():

    global dialog
    
    ui_file_path = os.path.join(tempfile.gettempdir(), "ui_file.ui")
    ui_file = open(ui_file_path, "wb")
    ui_file.write("\n".join(template))
    ui_file.close()

    dialog = hou.ui.createDialog(ui_file_path)

    dialog.addCallback("save.val", C3D_MainCallBackFunction)
    dialog.addCallback("savechan.val", C3D_ChanCallBackFunction)
    dialog.addCallback("framerate_enabler.val", C3D_FramerateCallBackFunction)
    dialog.addCallback("startend_enabler.val", C3D_StartendCallBackFunction)

    dialog.setValue("open.val", 1)