#==============================================================================================
# Author:  https://github.com/dogspace
#
# Renames image files with the oldest date found in EXIF metadata and file properties
# Supports recursion of subdirectories and customizable formatting of file names
#=============================================================================================


import os
import sys
import exifread
from datetime import datetime


valid_extensions   = [".jpg", ".jpeg", ".png", ".bmp"]
folder_count = 1
image_count = 0
skip_count = 0

# Returns earliest date found in file properties and EXIF metadata
def get_date(filepath):
    dates = []
    # Get last modified and created dates
    date_modified = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y.%m.%d %H.%M.%S")
    date_created = datetime.fromtimestamp(os.path.getctime(filepath)).strftime("%Y.%m.%d %H.%M.%S")
    dates.append(date_modified)
    dates.append(date_created)
    # Get metadata dates
    image = open(filepath, 'rb')
    tags = exifread.process_file(image, details=False)
    if "EXIF DateTimeDigitized" in tags.keys(): dates.append(str(tags["EXIF DateTimeDigitized"]))
    if "EXIF DateTimeOriginal" in tags.keys():  dates.append(str(tags["EXIF DateTimeOriginal"]))
    if "Image DateTime" in tags.keys():         dates.append(str(tags["Image DateTime"]))
    image.close()

    # Replace invalid chars, filter out invalid dates, sort oldest to newest
    dates = [d.replace(":", ".") for d in dates if "0000" not in d and len(d.strip()) > 0]
    dates.sort()
    # Ensure a valid date was found
    if len(dates) == 0:
        print("\n\n\nERROR: NO DATES FOUND\n\n\n")
        sys.exit()
    elif len(dates[0]) != 19:
        print("\n\n\nERROR: INVALID DATE LENGTH\n\n\n")
        sys.exit()
    # Separate into dictionary for easy formatting
    date_str = dates[0]
    date_values = {
        "YYYY": date_str[0:4],
        "YY":   date_str[2:4],
        "MM":   date_str[5:7],
        "DD":   date_str[8:10],
        "Hh":   date_str[11:13],
        "Mm":   date_str[14:16],
        "Ss":   date_str[17:] }
    return date_values

# Loops through folder, renames and/or moves files
def parse_folder(folder, recurse, formatting):
    global folder_count, image_count, skip_count
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        # Check if folder, recurse if enabled
        if os.path.isdir(filepath) and recurse:
            parse_folder(filepath, recurse, formatting)
        else:
            # Check file extension
            file_ext = os.path.splitext(filename)[1]
            is_image = file_ext.lower() in valid_extensions

            # Rename image files with date
            if is_image:
                image_count = image_count + 1
                # Get earliest date and format it
                date_values = get_date(filepath)
                new_filename = formatting
                for key in date_values.keys():
                    if key in new_filename:
                        new_filename = new_filename.replace(key, date_values[key])
                
                # Append incrementing number if the new filename already exists, exit after 30
                new_filepath = os.path.join(folder, new_filename + file_ext)
                if os.path.exists(new_filepath):
                    dup_count = 1
                    while dup_count <= 30:
                        temp_filename = new_filename + " (" + str(dup_count) + ")"
                        temp_filepath = os.path.join(folder, temp_filename + file_ext)
                        if os.path.exists(temp_filepath):
                            dup_count = dup_count + 1
                        else:
                            new_filename = temp_filename
                            new_filepath = temp_filepath
                            break
                    if dup_count > 30:
                        print("\n\n\nERROR: OVER 20 DUPLICATE DATES\n\n")
                        sys.exit()
                
                # Rename files
                os.rename(filepath, new_filepath)
            else:
                skip_count = skip_count + 1
    return

# Prints help message
def display_help():
    print(f"""
THIS PROGRAM:  Renames image files with the oldest date found in EXIF metadata and file properties\n
    USAGE:
      python RenameImages.py [-r] [-f "formatting"] dir
      -r                :  Recurse into all subdirectories (optional)
      -f "format"       :  Custom formatting of file names (optional)
      dir               :  Folder containing images (required)\n
    FORMATTING:
      Must be contained in quotations ""
      Reserved characters will be ignored  \ / : * ? " < > | 
      Date and time variables (must match case):  YYYY, YY, MM, DD, Hh, Mm, Ss
      * Default formatting:  YYYY-MM-DD Hh-Mm-Ss\n
    EXAMPLES:
      python RenameImages.py E:\Pictures
      python RenameImages.py -r E:\Pictures
      python RenameImages.py -f "YY-MM-DD Hh-Mm" E:\Pictures
      python RenameImages.py -f "YYYY.MM.DD_Hh.Mm.Ss" E:\Pictures
      python RenameImages.py -r -f "Vacation MM DD, YYYY" E:\Pictures\n
    """)

# Processes user input
def main():
    recurse_flag = "-r" in sys.argv
    format_flag = "-f" in sys.argv
    formatting = "YYYY-MM-DD Hh-Mm-Ss"
    folder_path = ""
    
    # Process user input
    if len(sys.argv) >= 2:
        if recurse_flag and format_flag and len(sys.argv) >= 5:
            formatting = "".join(i for i in sys.argv[3] if i not in r'\/:*?"<>|')
            folder_path = "".join(sys.argv[4:])
        elif format_flag and len(sys.argv) >= 4:
            formatting = "".join(i for i in sys.argv[2] if i not in r'\/:*?"<>|')
            folder_path = "".join(sys.argv[3:])
        elif recurse_flag and len(sys.argv) >= 3:
            folder_path = "".join(sys.argv[2:])
        else:
            folder_path = "".join(sys.argv[1:])
    
    # Ensure folder path is valid
    if os.path.isdir(folder_path) and folder_path != "/":
        parse_folder(folder_path, recurse_flag, formatting)
        print(f"\nFolders scanned: {folder_count}   |   Images renamed: {image_count}   |   Files skipped: {skip_count}")
    else:
        display_help()
    return


if __name__ == "__main__": main()