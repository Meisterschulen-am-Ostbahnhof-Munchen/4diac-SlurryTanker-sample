from argparse import ArgumentParser
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

def getPaths():
    script_path = os.path.dirname(os.path.abspath(__file__))
    parser = ArgumentParser()
    parser.add_argument("-o", "--oldfile", dest="old_file", required=True)
    parser.add_argument("-n", "--newfile", dest="new_file", required=True)
    parser.add_argument("-p", "--newfolder", dest="new_folder", required=True)
    args = parser.parse_args()

    # Create the absolute paths using os.path.join
    new_path = os.path.join(os.path.dirname(script_path), args.new_folder)
    old_path = os.path.join(os.path.dirname(script_path), args.old_file)

    filepaths = [old_path, new_path, args.new_file]
    return filepaths

def printPaths(filepaths):
    print('')
    print('')
    print(f"Old File:     {filepaths[0]}")
    print(f"New File:     {filepaths[1]}")
    print(f"New File:     {filepaths[2]}")

def checkPath(path):
    if os.path.exists(path):
        print(f'Path exists : {path}')
    else:
        raise FileNotFoundError(f"The new file '{path}' does not exist.")

def readIOPH(filepaths):
    oldfilepath   = filepaths[0]
    newfilepath   = filepaths[1]

    print("Oldfilepath")
    checkPath(oldfilepath)
    print("Newfilepath")
    checkPath(newfilepath)

    pattern = re.compile(r'#define\s+(\w+)\s+(\S+)')
    with open(oldfilepath, 'r') as file:
    # Initialize a dictionary to store the name and corresponding number
        definitions = {}

        # Iterate through each line in the file
        for line in file:
            # Use the regular expression pattern to match lines with #define
            match = pattern.match(line)
            if match:
                # Extract the name and number from the matched groups
                name, number = match.groups()
                
                # Save the information in the dictionary
                definitions[name] = number

    return definitions

def writeGCFfile(data, filepaths):
    newfilepath = os.path.join(filepaths[1], filepaths[2]+'.gcf')

    root = ET.Element("GlobalConstants", Name=filepaths[2], Comment="Global constants")

    # Create the GlobalConstants element
    global_constants = ET.SubElement(root, "GlobalConstants")

    # Iterate over the data and create VarDeclaration elements
    for name, value in data.items():
        var_declaration = ET.SubElement(global_constants, "VarDeclaration", Name=name, Type="UINT", Comment="", InitialValue=value)

        # If the name is 'ISO_VERSION_LABEL', set the type attribute to '       '
        if name == 'ISO_VERSION_LABEL':
            var_declaration.set('Type', 'STRING')
            var_declaration.set('InitialValue', ''       '')

    # Create an ElementTree object and write it to a file
    tree = ET.ElementTree(root)

    # Create a string with indentation
    xml_str = ET.tostring(root, encoding='utf-8').decode()
    xml_str = minidom.parseString(xml_str).toprettyxml(indent="    ")

    # Adding UTF8-encoding
    xml_str = xml_str[:19] + ' ' + 'encoding="UTF-8"' + xml_str[20:]

    # Write the formatted XML to a file
    with open(newfilepath, "w") as file:
        file.write(xml_str)


if __name__ == "__main__":

    # Gets filepaths and saves it in a variable
    filepaths = getPaths()

    # Prints filepaths
    printPaths(filepaths)
    file_data = readIOPH(filepaths)
    writeGCFfile(file_data, filepaths)


__author__ = "Lorenz Bauer"
__version__ = "0.1"
__description__ = "Searches for an .iop.h file and converts it in an .gcp file"

