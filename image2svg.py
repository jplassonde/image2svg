#------------------------------------------------------------------------
# Name: image2svg.py
# 
# Description:
# Convert an image file to a 6-shades svg "line art" file to 
# be printed on an XY Plotter
#
# An aliased & upscaled bitmap (~1600x1000) is preferable
# for optimal results.
#
# To be drawn on a XY plotter with no optimization, vectors 
# coords start from left to right, then right to left
# every other line.
#
# Version 3 - Use PIL Image instead of the now depreciated
#             scipy imread + major cleanup
#     Todo: investigate why PIL antialias/degrade jpg (open? convert?)
#           automate upscaling
#-------------------------------------------------------------------------

from PIL import Image
import numpy as np
import codecs, sys


# Set visible to True to display the vector lines on screen (for testing)
# False to prevent G-Code generator from double-stroking each line (but produce invisible output on SVG viewers)

visible = True

# Shades thresholds. May require tweaking for better results on darker/lighter images
# Pixels values are reduced (darkened) to the nearest
# C64 palette vals: 0, 87, 96, 111, 114, 132, 158, 164, 173, 174, 212, 213, 230, 238, 255

shade1 = 0      # Black
shade2 = 50            
shade3 = 100         
shade4 = 158             
shade5 = 212
shade6 = 240

#------ Functions definition ------#

def needLineX(val, rowIndex):   # Determine if a segment must be drawn depending on its shade & row number
    if rowIndex % 2 == 0 and val <= shade1:
        return True
    elif rowIndex % 4 == 0 and val <= shade3:
        return True
    elif rowIndex % 8 == 0 and val <= shade5:
        return True
    else:
        return False
    
def needLineY(val, rowIndex):
    if rowIndex % 2 == 0 and val <= shade1:
        return False    # Only draw horizontal lines
    elif rowIndex % 4 == 0 and val <= shade2:
        return True
    elif rowIndex % 4 == 0 and val <= shade3:
        return False    # Only draw horizontal lines
    elif rowIndex % 8 == 0 and val <= shade4:
        return True
    else:
        return False

def svgPrint(start, stop, rowNum, invert, axes, axisDimension): 
    svgFile.write('<line '+ axes[0] + '1="'
                  + str(axisDimension-start if invert == True else start)
                  + '" ' + axes[1] + '1="' + str(rowNum)
                  + '" ' + axes[0] + '2="'
                  + str(axisDimension-stop if invert == True else stop)
                  + '" ' + axes[1] + '2="' + str(rowNum) + '"/>\n')

def generateVectors(img, needLine, axes, axisDimension):
    invert = False
    
    for rowIndex, row in enumerate(img):            # Go through each row
        rowDrawn = False
        firstEndpoint = 0
        
        if invert == True:      # Invert every other line where something is drawn on a row
            row = np.flipud(row)
        
        for index, pixel in enumerate(row):             # Go through each column  
            if index > 0 and pixel != row[index-1]:     # If the pixel color is different from the last
                if needLine(row[index-1], rowIndex):    # Check if this last segment must be "printed"
                    svgPrint(firstEndpoint, index, rowIndex, invert, axes, axisDimension)
                    rowDrawn = True
                firstEndpoint = index       # Store the first endpoint of the next line segment        
        
        if needLine(row[index], rowIndex):  # Test/Print last segment at the end of each line
            svgPrint(firstEndpoint, index, rowIndex, invert, axes, axisDimension)
            rowDrawn = True

        if rowDrawn == True:  
            invert = not invert

def main(inputFile):
    image = Image.open(inputFile).convert('L', dither=False) 
    width, height = image.size

    # Reduce color to 6 shades
    image = Image.eval(image, lambda px: shade1 if px < shade2 else
                                        (shade2 if px < shade3 else
                                        (shade3 if px < shade4 else
                                        (shade4 if px < shade5 else
                                        (shade5 if px < shade6 else 255)))))


    # Convert image to array
    image = np.asarray(image)

    # Create SVG file + header
    global svgFile
    svgFile = codecs.open("output.svg", "w+")
    svgFile.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
    svgFile.write('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
    svgFile.write('<svg width="'+ str(width)+ 'pt" height="'+str(height)+'pt" viewBox="0 0 '
                  + str(width)+ " " +str(height)+'" version="1.1" xmlns="http://www.w3.org/2000/svg">\n')

    # Stroke lines if option is set
    if visible == True:
        svgFile.write('<g stroke="black" stroke-width="1">\n')
 
    # Create X axis segments
    generateVectors(image, needLineX, ['x', 'y'], width)

    # Create Y axis segments
    image = np.swapaxes(image, 0, 1)
    generateVectors(image, needLineY, ['y', 'x'], height)

    # Close SVG file
    if visible == True:
        svgFile.write('</g>')
    svgFile.write('</svg>')
    svgFile.close()
# End Main

if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except IndexError:
        print("No input file specified.")
        wait = input("Press enter to continue...")
        sys.exit(1)
    except FileNotFoundError:
        print("Input file not found.")
        wait = input("Press enter to continue...")
        sys.exit(1)
    except OSError:
        print("Image file not recognized.")
        wait = input("Press enter to continue...")
        sys.exit(1)
