#!/usr/bin/env python

from gimpfu import *

# create an output function that redirects to gimp's Error Console
def gprint( text ):
   pdb.gimp_message(text)

def gcopy(src, dst, srcpos, w, h, dstpos):
   src_rgn = src.get_pixel_rgn(srcpos[0], srcpos[1], w, h)
   dst_rgn = dst.get_pixel_rgn(dstpos[0], dstpos[1], w, h)
   dst_rgn[:,:] = src_rgn[:,:]

def newLayer(img, w, h, name):
   buff = gimp.Layer(img, name, w, h, RGB_IMAGE, 100, NORMAL_MODE)
   buff.add_alpha()
   buff.fill(TRANSPARENT_FILL)
   img.add_layer(buff, 0)
   return buff

FLIP_H = 0
FLIP_V = 1

# our script
def plugin_main(img, drawable, nx, ny, flip) :
   w = int(drawable.width / nx)
   h = int(drawable.height / ny)
   
   name = 'flipped {0}'.format('horizontally' if flip == FLIP_H else 'vertically')
   new_layer = newLayer(img, img.width, img.height, name)

   img.undo_freeze()
   buff = newLayer(img, w, h, 'temp')
   gimp.progress_init("Flipping tiles...")
   for i in range(nx):
      x = i * w
      for j in range(ny):
         y = j * h
         gimp.progress_update(float(i * ny + j) / (nx * ny))
         
         gcopy(drawable, buff, (x,y), w, h, (0,0))
         buff.transform_flip_simple(flip, 1, 0.5)
         gcopy(buff, new_layer, (0,0), w, h, (x,y))
         
   pdb.gimp_progress_end()
   img.remove_layer(buff)
   img.undo_thaw()
   

# This is the plugin registration function
register(
   "spritesheet_transform_flip",    
   "Flip tiles of a spritesheet",
   "Flip tiles of a spritesheet",
   "Sebastien Andary", 
   "Sebastien Andary", 
   "December 2013",
   "<Image>/SpriteSheet/Flip Tiles", 
   "*", 
   [
     (PF_INT,     "nx",     "n horizontal tiles",  1),
     (PF_INT,     "ny", "n vertical tiles", 1),
     (PF_RADIO,   "flip",  "orientation", 0, (("horizontal", FLIP_H), ("vertical", FLIP_V)))     
   ], 
   [],
   plugin_main,
   )

main()
