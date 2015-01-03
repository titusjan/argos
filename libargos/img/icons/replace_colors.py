#!/opt/local/bin/python
# -*- coding: utf-8 -*-

""" Reads SVG files and replaces the colors to produce different colored iconds
"""
import sys, os


def main():
    snipIconBlue0 = '#008BFF'
    snipIconBlue1 = '#00AAFF'
    
    newColors = ['#FF0000', '#00FF00', '#0000FF', '#FF00FF', '#FFFF00', '#00FFFF', 
                 '#666666']
        
    fileOut = None
    for newColor in newColors:
        
        for fileNameIn in sys.argv[1:]:
            with open(fileNameIn) as fileInput:
                fileIn, extension = os.path.splitext(os.path.basename(fileNameIn))
                fileNameOut = '{}.{}{}'.format(fileIn, newColor[1:], extension)
                sys.stderr.write("Writing to: {}\n".format(fileNameOut))
                with open(fileNameOut, 'w') as fileOut:
                    for lineIn in fileInput:
                        lineOut = lineIn.replace(snipIconBlue0, newColor) \
                                        .replace(snipIconBlue1, newColor)
                        fileOut.write(lineOut)
                        #print(lineOut)


if __name__ == "__main__":
    main()
    
