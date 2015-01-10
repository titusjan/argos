#!/opt/local/bin/python
# -*- coding: utf-8 -*-

""" Reads SVG files and replaces the colors to produce different colored icons
"""
import sys, os
import logging

logger = logging.getLogger(__name__)

SNIP_BLUE0 = '#008BFF'
SNIP_BLUE1 = '#00AAFF'

OLD_COLORS = [SNIP_BLUE0, SNIP_BLUE1] 
SNIP_ICONS_DIR = 'snipicons'
OUTPUT_DIR = 'icons'
    
    
def createIcon(newColor, baseNameOut, baseNameIn):
    """ Creates a single icon file by replacing the snipicon colors with the newColor 
        in the baseNameIn file. Write new icon in the icons directory as baseNameOut.svg
    """
    fileNameIn = os.path.join(SNIP_ICONS_DIR, baseNameIn)
    logger.debug("Opening: {}".format(fileNameIn))
    with open(fileNameIn) as fileInput:
        
        _fileIn, extension = os.path.splitext(os.path.basename(fileNameIn))
        fileNameOut = os.path.join(OUTPUT_DIR, '{}{}'.format(baseNameOut, extension))
        logger.info("Creating: {}".format(fileNameOut))
        
        with open(fileNameOut, 'w') as fileOut:
            for line in fileInput:
                for oldColor in OLD_COLORS:
                    line = line.replace(oldColor, newColor) 
                fileOut.write(line)

def main():
    """ Creates all icons """
    
    errColor = '#FF0000'
    createIcon(errColor, 'err.warning',     'warning-sign.svg')
    #createIcon(errColor, 'err.exclamation', 'exclamation-sign.svg') # not used
    
    memColor = '#8800FF' 
    createIcon(memColor, 'memory.scalar',        'asterisk.svg')
    createIcon(memColor, 'memory.array',         'th-large.svg')
    createIcon(memColor, 'memory.sequence',      'align-left.svg')
    createIcon(memColor, 'memory.folder-open',   'folder-open.svg')
    createIcon(memColor, 'memory.folder-closed', 'folder-close.svg')
            
    fsColor = '#999999' 
    createIcon(fsColor, 'fs.file-open',        'file.svg')
    createIcon(fsColor, 'fs.file-closed',      'file-inverse.svg')
    createIcon(fsColor, 'fs.directory-open',   'folder-open.svg')
    createIcon(fsColor, 'fs.directory-closed', 'folder-close.svg')

    ncdfColor = '#0088FF' 
    createIcon(ncdfColor, 'ncdf.variable',     'th-large.svg')
    createIcon(ncdfColor, 'ncdf.group-open',   'folder-open.svg')
    createIcon(ncdfColor, 'ncdf.group-closed', 'folder-close.svg')
    createIcon(ncdfColor, 'ncdf.file-open',    'file.svg')
    createIcon(ncdfColor, 'ncdf.file-closed',  'file-inverse.svg')
    
    nptxtColor = '#00FF88' 
    createIcon(nptxtColor, 'nptxt.column',     'th-large.svg')
    createIcon(nptxtColor, 'nptxt.file-open',  'file.svg')
    createIcon(nptxtColor, 'nptxt.file-closed','file-inverse.svg')



if __name__ == "__main__":
    logging.basicConfig(format="%(filename)25s:%(lineno)-4d: %(levelname)-7s: %(message)s", 
                        level='INFO', stream=sys.stderr)
    main()
    
