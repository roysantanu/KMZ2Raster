#Functions to create geo-reference raster from KML
#This functions can extract embaded raster from KMZ
#@Santanu Roy--roysantanu.rs@gmail.com
from zipfile import ZipFile
from pathlib import Path
from PIL import Image
Image.MAX_IMAGE_PIXELS = 9000000000
import os
from pykml import parser
import rasterio
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
import shutil

# specifying the zip file name
#file_name = "/content/01.kmz"

def getAfineParameter(kml_file,AW,AH):
  with open(kml_file) as f:
    doc = parser.parse(f).getroot()
  North=doc.Document.Folder.Region.LatLonAltBox.north
  West=doc.Document.Folder.Region.LatLonAltBox.west
  South=doc.Document.Folder.Region.LatLonAltBox.south
  East=doc.Document.Folder.Region.LatLonAltBox.east
  Ht=abs(North-South)
  Wd=abs(West-East)
  X=Wd/AW
  Y=Ht/AH
  afine=rasterio.Affine(float(X),0.0,West,0.0,-(Y),North)
  return afine

#Georeferenced the predicted mask
#######################################
def georef(unrectMask,kml_f,AW,AH):
  newafine=getAfineParameter(kml_f,AW,AH)
  #print (newafine)
  img=rasterio.open(unrectMask)
  #Deifne coficients matrix for transformation
  #afn=img.transform
  #New Afine transfomation matix
  #newafine=img.transform
  #Open and geo-refernced the image
  #name=unrectMask
  #output=Path(file_name).name
  with rasterio.open(unrectMask) as dataset:
    img_p=dataset.read(
        out_shape=(3, img.shape[0], img.shape[1])
    )
    dataset.close()
  img.close()
  with rasterio.open(
    unrectMask,'w',driver='JPEG',
    height=img_p.shape[1],width=img_p.shape[2],count=3,
    dtype=img_p.dtype,crs='EPSG:4326',transform=newafine,
    resampling=Resampling.bilinear) as dst:
    dst.write(img_p)
  return unrectMask

def KMZextractor(file_name):
  # opening the zip file in READ mode
  with ZipFile(file_name, 'r') as zip:
    parentDir=Path(file_name).parent
    dir_name=os.path.join(parentDir,(Path(file_name).name).replace('.kmz',''))
    if not os.path.isdir(dir_name):
      os.makedirs(dir_name)
    # printing all the contents of the zip file
    #zip.printdir()

    # extracting all the files
    #print('Extracting all the files now...')
    zip.extractall(dir_name)
    #print('Done!')
    return dir_name

#The raster extraction function, where input is KMZ
def MergeImageGeoref(file_name):
  dir_name=KMZextractor(file_name)
  parentDir=Path(file_name).parent
  #parentDir=os.path.join(parentDir,'output')
  #checkDir=os.path.isdir(parentDir)
  #while True:
    #os.makedirs(parentDir)
  #if not os.path.isdir(parentDir):
    #os.makedirs(parentDir)
  outfullImage=os.path.join(parentDir,(Path(file_name).name).replace('.kmz','.JPEG'))
  #Get filename with Level, max Rows and columns
  #def getFilenameWithLRC(dir_name):
  file_list=[]
  maxL=[]
  maxRow=[]
  maxCol=[]
  for f in os.listdir(dir_name):
    if f.endswith('.png') or f.endswith('.PNG'):
      i=f.replace('.png','').split('_L')
      L=i[1].split('_')[0]
      R=i[1].split('_')[1]
      C=i[1].split('_')[2]
      file_list.append(f)
      maxL.append(int(L))
      maxRow.append(int(R))
      maxCol.append(int(C))
  #return file_list,max(maxL),max(maxRow),max(maxCol)
  filename_filter=[]
  for f in sorted(file_list):
    if 'L'+str(max(maxL)) in f:
      filename_filter.append(os.path.join(dir_name,f))
  width=[]
  height=[]
  for i in filename_filter:
    im = Image.open(i)
    w, h = im.size
    if w not in width:
      width.append(w)
    if h not in height:
      height.append(h)
    #width =width+w
    #height =height+h
  AW,AH=width[0]*(max(maxCol))+width[1],height[0]*(max(maxRow))+height[1]
  W,H =width[0],height[0] #1024,1024 #width[0],height[1]
  WIDTH,HEIGHT=1024*(max(maxCol)+1),1024*(max(maxRow)+1) #width[0]*(max(maxCol))+width[1],height[0]*(max(maxRow))+height[1]
  print (WIDTH,HEIGHT)
  new_im = Image.new('RGB', (WIDTH,HEIGHT))
  #outfullImage='/content/aft_2020_037706000_01.jpg'
  #new_im = Image.new('L', (width, height))
  #print (f,W,H)
  c = 0
  for i in range(0, HEIGHT, H):
    for j in range(0, WIDTH, W):

        #box = (j, i, j + W, i + H)
        #cropimg = img[i:i + H, j:j + W]
        #prd = prediction(cropimg)
        #prd = Image.fromarray(img)
      if c < len(filename_filter):
        #print (c, j, i)
        #print (filename_filter[c],j,i, 'count ',c)
        img =  Image.open(filename_filter[c])
        new_im.paste(img, (j, i))
        img.close()
      c += 1
  cropimg =new_im.crop((0, 0, AW, AH)) #new_im[0:0, AW:AH]
  cropimg.save(outfullImage)
  georef(outfullImage,os.path.join(dir_name,'doc.kml'),AW,AH)
  try:
    shutil.rmtree(dir_name)
  except:
    next
  return outfullImage
