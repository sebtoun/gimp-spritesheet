#!/usr/bin/env python

from gimpfu import *
from array import array

# redirects to gimp's Error Console
def gprint( text ):
   pdb.gimp_message(text)

# copy a portion of a drawable to another drawable
def gcopy(src, dst, srcpos, w, h, dstpos):
   src_rgn = src.get_pixel_rgn(srcpos[0], srcpos[1], w, h)
   dst_rgn = dst.get_pixel_rgn(dstpos[0], dstpos[1], w, h)
   dst_rgn[:,:] = src_rgn[:,:]

# paste a portion of a drawable to another drawable
def gpaste(src, dst, srcpos, w, h, dstpos):
   src_rgn = src.get_pixel_rgn(srcpos[0], srcpos[1], w, h, False)
   dst_rgn = dst.get_pixel_rgn(dstpos[0], dstpos[1], w, h, True)
   src_pixels = array("B", src_rgn[:,:])
   dst_pixels = array("B", dst_rgn[:,:])
   for i in range(w * h * src_rgn.bpp):
      dst_pixels[i] = src_pixels[i] if src_pixels[i] > 0 else dst_pixels[i]
      #dst_pixels[i] = (src_pixels[i] | dst_pixels[i]) > 0
   dst_rgn[:,:] = dst_pixels.tostring() 

# paste a portion of a drawable to another drawable (it's more like a mask actually)
def gpaste_np(src, dst, srcpos, w, h, dstpos, np):
   src_rgn = src.get_pixel_rgn(srcpos[0], srcpos[1], w, h, False)
   dst_rgn = dst.get_pixel_rgn(dstpos[0], dstpos[1], w, h, True)
   src_pixels = np.fromstring(src_rgn[:,:], dtype=np.uint8)
   dst_pixels = np.fromstring(dst_rgn[:,:], dtype=np.uint8)
   # actually we only need to know if there is a non transparent pixel, not its value
   dst_pixels = (src_pixels | dst_pixels) > 0
   dst_rgn[:,:] = dst_pixels.tostring()
   
# create a new layer
def newLayer(img, w, h, name):
   buff = gimp.Layer(img, name, w, h, RGBA_IMAGE, 100, NORMAL_MODE)
   img.add_layer(buff, 0)
   return buff

IMPL_NUMPY = 1
IMPL_ARRAY = 0

# our script
def script_main(img, drawable, nx, ny, pad, sqr, impl) :
   pasteFun = gpaste
   if impl == IMPL_NUMPY:
      try:
         import numpy as np
         pasteFun = lambda a,b,c,d,e,f : gpaste_np(a,b,c,d,e,f,np)
      except ImportError:
         gprint("numpy module not found, falling back to array implementation")
   
   w = int(drawable.width / nx)
   h = int(drawable.height / ny)
   
   gimp.progress_init("Computing bounds...")
   img.undo_freeze()
   
   # compute bounding box of all tiles superimposed
   unionTile = newLayer(img, w, h, 'union')
   
   for i in range(nx):
      x = i * w
      for j in range(ny):
         y = j * h
         gimp.progress_update(float(i * ny + j) / (nx * ny))
         pasteFun(drawable, unionTile, (x,y), w, h, (0,0))

   # bounds
   pdb.plug_in_autocrop_layer(img, unionTile)
   
   offsetX, offsetY = unionTile.offsets
   tileW = unionTile.width
   tileH = unionTile.height
   
   img.remove_layer(unionTile)
   
   # modify bounds according to options
   if pad > 0:
      padx = offsetX if pad > offsetX else pad
      pady = offsetY if pad > offsetY else pad
      (offsetX, offsetY) = (offsetX - padx, offsetY - pady)
      tileW = min(tileW + pad + padx, w - offsetX)
      tileH = min(tileH + pad + pady, h - offsetY)
      
   if sqr:
      if tileW < tileH:
         tileW = tileH
         if offsetX + tileW > w:
            offsetX = w - tileW
      if tileW > tileH:
         tileH = tileW
         if offsetY + tileH > h:
            offsetY = h - tileH
   
   pdb.gimp_progress_end()
   gimp.progress_init("Trimming tiles...")

   img.undo_thaw()   
   # new layer will contain trimmed tiles
   new_layer = newLayer(img, nx * tileW, ny * tileH, 'trimmed')
   
   img.undo_freeze()
   # fill new layer with trimmed tiles
   for i in range(nx):
      srcX = i * w
      dstX = i * tileW
      for j in range(ny):
         srcY = j * h
         dstY = j * tileH
         gimp.progress_update(float(i * ny + j) / (nx * ny))
         
         gcopy(drawable, new_layer, (srcX + offsetX, srcY + offsetY), tileW, tileH, (dstX, dstY))

   img.undo_thaw()   
   pdb.gimp_progress_end()
   pdb.gimp_displays_flush()
   

# This is the plugin registration function
register(
   "spritesheet_transform_trim",    
   "Trim tiles of a spritesheet",
   "Trim tiles of a spritesheet",
   "Sebastien Andary", 
   "Sebastien Andary", 
   "December 2013",
   "<Image>/SpriteSheet/Trim Tiles", 
   "RGBA", 
   [
     (PF_INT,     "nx",     "n horizontal tiles",    1),
     (PF_INT,     "ny",     "n vertical tiles",       1),
     (PF_INT,     "pad",   "margin padding",    1),
     (PF_TOGGLE,  "sqr",   "keep square tiles", True),
     (PF_RADIO,   "impl",  "interface",         1, (("python array", 0),("numpy array (faster)", 1))),
   ], 
   [],
   script_main,
   )

main()
