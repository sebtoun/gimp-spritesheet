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

ROT_CW = 0
ROT_CCW = 2

# our script
def plugin_main(img, drawable, nx, ny, rot) :
   w = int(drawable.width / nx)
   h = int(drawable.height / ny)
   
   name = 'rotated {0}'.format('CW' if rot == ROT_CW else 'CCW')
   new_layer = newLayer(img, img.width, img.height, name)

   img.undo_freeze()
   
   buff = newLayer(img, w, h, 'temp')
   gimp.progress_init("Rotating tiles...")
   
   for i in range(nx):
      x = i * w
      for j in range(ny):
         y = j * h
         gimp.progress_update(float(i * ny + j) / (nx * ny))
         
         gcopy(drawable, buff, (x,y), w, h, (0,0))
         buff.transform_rotate_simple(rot, 1, w / 2, h / 2)
         gcopy(buff, new_layer, (0,0), w, h, (x,y))
         
   pdb.gimp_progress_end()
   img.remove_layer(buff)
   img.undo_thaw()
         
# This is the plugin registration function
register(
   "spritesheet_transform_rotate",    
   "Rotates tiles of a spritesheet",
   "Rotates tiles of a spritesheet",
   "Sebastien Andary", 
   "Sebastien Andary", 
   "December 2013",
   "<Image>/SpriteSheet/Rotate Tiles", 
   "*", 
   [
     (PF_INT,     "nx",    "n horizontal tiles",  1),
     (PF_INT,     "ny",    "n vertical tiles", 1),
     (PF_RADIO,   "rot",   "rotation:",   0, (("CW", ROT_CW),("CCW", ROT_CCW)))
   ], 
   [],
   plugin_main,
   )

main()
