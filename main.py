import ltk
import asyncio  # for file uploading
from weavemaker import *
# File save support
import io
from js import Uint8Array, URL, File

#ltk.window.document.currentScript.terminal.resize(60, 12)

# Allow user to upload a wmd/wmdf file from WeaveMaker
# - Show the colorwyas found and other info,
# - quietly convert the file into a wif representation,
# - allow user to download the wif as a file.


current_wmd = None  # Holds the current wmd file class object

###     
def act_on_file(bytestream, widget, filename):
    """
    Load the wmd file and convert it.
    Update UI:
    - number of colorways,
    - Select widget (colorways),
    - Report section,
    - show colors if we can be bothered...
    Set a global variable for others to reference wmdf.
    """
    global current_wmd
    #print("Processing file")
    data, colors = parse_wmdf(bytestream)
    current_wmd = WMDF(data, colors, filename)
    num_colorways = len(current_wmd.c_mapping)
    #
    widget.colorway_count.text(num_colorways)
    # replace options on Select using jquery
    chooser = ltk.find("#cway_chooser")
    chooser.empty()  # to remove old
    for val in range(num_colorways):
        chooser.append(f"<option>{str(val+1)}</option>").attr("value", str(val+1)).addClass("ltk-select vcenter")
    # Report
        #report_text = "\n".join(current_wmd.report_fstructure())
        report_text = "\n - ".join(current_wmd.report_summary())
    if current_wmd.conversion_notes:
        report_text += "\n"+"\n - ".join(current_wmd.report_conversion_notes())
    if current_wmd.warnings:
        report_text += "\n"+"\n - ".join(current_wmd.report_warning())
    widget.RHS_report.text(report_text)


### Upload the file
async def get_bytes_from_file(file):
    """ Asynchronously fetch the bytes inside the file """
    array_buf = await file.arrayBuffer()
    return array_buf.to_bytes()

async def get_file(first_item, widget):
    """ 
    Asynchronously fetch the file 
    - returns a read-only array of bytes
    """
    #my_bytes: bytes = await get_bytes_from_file(first_item)
    my_bytes = await get_bytes_from_file(first_item)
    act_on_file(my_bytes, widget, first_item.name)

def upload_file(event, widget):
    """ Event to upload a file and act on it """
    file_list = event.target.files
    first_item = file_list.item(0)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(get_file(first_item, widget))
    finally:
        loop.close()

### Download the wif to user
def download_file(event, widget):
    # make the wif
    cway_chooser = ltk.find("#cway_chooser")
    selected_colorway = int(cway_chooser.val())-1
    if current_wmd:
        current_wmd.make_wif(selected_colorway)
        data = current_wmd.wif
        encoded_data = data.encode('utf-8')  # Transform our string of data into bytes
        my_stream = io.BytesIO(encoded_data)  # convert data into bytesIO object
        # Copy of the contents into the JavaScript buffer
        js_array = Uint8Array.new(len(encoded_data))
        js_array.assign(my_stream.getbuffer())
        # File constructor takes a buffer, name, MIME type. (name not used)
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
        file = File.new([js_array], "foo.txt", {type: "text/plain"})
        url = URL.createObjectURL(file)
        hidden_link = ltk.window.document.createElement("a")
        # The second parameter here is the actual name of the file that will appear in the user's file system
        hidden_link.setAttribute("download", current_wmd.wif_filename)
        hidden_link.setAttribute("href", url)
        hidden_link.click()


class WMD_widget(object):
    """
    Top level object that manages loading/converting.
    """
    def __init__(self):
        self.description = "\n".join(["This tool converts wmd or wmdf weaving files from the 'WeaveMaker' software to the wif file format.",
                                      "It has been tested on version 8.6.1. It should work for earlier versions. If the converter does not work or produces incorrect/missing output:",
                                      " - please raise an issue at: https://github.com/Neon22/weavemaker-to-wif. Include the wmd file if possible." ])
        self.privacy = "\n".join(["Privacy note:", " - This webpage and its program are entirely standalone. All processing occurs entirely within this webpage.  No data is sent to a server and the wmd files never leave your machine.",
                                  "I'd like to acknowledge the invaluable help of Dana Cartwright, one of the original WeaveMaker authors, for his help in making this possible."])

    def choose_colorway(self, index, option):
        pass
    
    def create(self):
        self.report_text = "Report:"
        self.RHS_report = ltk.TextArea(self.report_text).addClass("report mytext")
        self.colorway_count = ltk.Text("0").addClass("cway_count vcenter cway_color  mytext")
        self.colorways = ["0"]  # Hold the possible colorways values
        getfile_widget = ltk.File().attr("accept",".wmd, .wmdf").addClass("vcenter mytext").on("input", ltk.proxy(lambda event: upload_file(event, self)))
        download_widget = ltk.Button("Download wif file", ltk.proxy(lambda event: download_file(event, self))).addClass("vcenter mytext")
        self.colorway_chooser = ltk.Select(self.colorways, 0, self.choose_colorway).addClass("vcenter  mytext cway_color").attr("id","cway_chooser")
        #
        LHS_controls = ltk.VBox(
                            ltk.HBox(ltk.Label("1.").addClass("count mytext"),
                                     getfile_widget),
                            ltk.HBox(self.colorway_count,
                                     ltk.Label("Colorways found.").addClass("label  mytext vcenter")),
                            ltk.HBox(ltk.Label("2.").addClass("count"),
                                     ltk.Label("Choose a colorway:").addClass("label vcenter mytext"),
                                     self.colorway_chooser),
                            ltk.HBox(ltk.Label("3.").addClass("count mytext"),
                                     download_widget)
                        ).addClass("stepBox mytext")
        return (
            ltk.VBox(ltk.Text("WeaveMaker to WIF file converter").addClass("title mytext"),
                     ltk.TextArea(self.description).addClass("textbox mytext"),
                     ltk.TextArea(self.privacy).addClass("textbox mytext"),
                     ltk.HBox(LHS_controls, self.RHS_report).addClass("sidebyside mytext")
                    ))
                     


if __name__ == "__main__":
    w = WMD_widget()
    widget = w.create()
    #widget = create()
    widget.appendTo(ltk.window.document.body)