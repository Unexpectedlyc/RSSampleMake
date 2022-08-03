from osgeo import gdal, gdalconst,ogr,osr
import os
import cv2
from tqdm import tqdm
import numpy as np
import math

#读取tif数据集
def readTif(fileName, xoff=0, yoff=0, data_width=0, data_height=0):
    dataset = gdal.Open(fileName)


    if data_width ==0:
        data_width=dataset.RasterXSize
    if data_height ==0:
        data_height=dataset.RasterYSize
    data=dataset.ReadAsArray(xoff,yoff,data_width,data_height)

    #获取仿射矩阵信息,投影信息
    geotrans=dataset.GetGeoTransform()
    proj=dataset.GetProjection()
    return data, geotrans,proj


#保存tif文件函数
def writeTiff(im_data,im_geotrans,im_proj,path):
    if 'int8' in im_data.dtype.name:
        datatype=gdal.GDT_Byte
    elif  'int16'in im_data.dtype.name:
        datatype=gdal.GDT_UInt16
    else:
        datatype=gdal.GDT_Float32
    if len(im_data.shape)==2:
        im_data=np.array([im_data])
    im_bands,im_height,im_width=im_data.shape

    #创建文件
    driver=gdal.GetDriverByName("GTiff")
    dataset=driver.Create(path,im_width,im_height,im_bands,datatype)
    if(dataset is not None):
        dataset.SetGeoTransform(im_geotrans)#写入仿射变换参数
        dataset.SetProjection(im_proj)#写入投影
    for i in range(im_bands):
        dataset.GetRasterBand(i+ 1).WriteArray(im_data[i])
    del dataset



def shp2Raster(shp,templatePic,output,field,nodata):
    """
    shp:字符串，一个矢量，从0开始计数，整数
    templatePic:字符串，模板栅格，一个tif，地理变换信息从这里读，栅格大小与该栅格一致
    output:字符串，输出栅格，一个tif
    field:字符串，栅格值的字段
    nodata:整型或浮点型，矢量空白区转换后的值
    """
    ndsm = templatePic
    data = gdal.Open(ndsm, gdalconst.GA_ReadOnly)
    geo_transform = data.GetGeoTransform()
    proj=data.GetProjection()
    #source_layer = data.GetLayer()
    x_min = geo_transform[0]
    y_max = geo_transform[3]
    x_max = x_min + geo_transform[1] * data.RasterXSize
    y_min = y_max + geo_transform[5] * data.RasterYSize
    x_res = data.RasterXSize
    y_res = data.RasterYSize
    mb_v = ogr.Open(shp)
    mb_l = mb_v.GetLayer()
    pixel_width = geo_transform[1]
    #输出影像为16位整型
    target_ds = gdal.GetDriverByName('GTiff').Create(output, x_res, y_res, 1, gdal.GDT_Byte)

    target_ds.SetGeoTransform(geo_transform)
    target_ds.SetProjection(proj)
    band = target_ds.GetRasterBand(1)
    NoData_value = nodata
    band.SetNoDataValue(NoData_value)
    band.FlushCache()
    gdal.RasterizeLayer(target_ds, [1], mb_l, options=["ATTRIBUTE=%s"%field,'ALL_TOUCHED=TRUE'])

    target_ds = None

def shpToRaster(imgpath,shapepath,TableValue):

    img = os.path.split(imgpath)[-1].split('.')[0]
    outputfile = f'{img}_shp.tif'
    shp2Raster(shapepath, imgpath, outputfile, TableValue, 0)
    return outputfile



def Binarization(imgpath,shapepath,TableValue):
    fileName=shpToRaster(imgpath,shapepath,TableValue)
    im_data, im_geotrans, im_proj = readTif(fileName, 0, 0, 0, 0)

    im_data=np.where(im_data==0,0,255)
    im_data=unit16Touint8(im_data)
    writeTiff(im_data, im_geotrans, im_proj, fileName)



# opencv数据转gdal
def OpencvData2GdalData(OpencvImg_data):
  # 若为二维，格式相同
  if (len(OpencvImg_data.shape) == 2):
    GdalImg_data = OpencvImg_data
  else:
    if 'int8' in OpencvImg_data.dtype.name:
      GdalImg_data = np.zeros((OpencvImg_data.shape[2], OpencvImg_data.shape[0], OpencvImg_data.shape[1]), np.uint8)
    elif 'int16' in OpencvImg_data.dtype.name:
      GdalImg_data = np.zeros((OpencvImg_data.shape[2], OpencvImg_data.shape[0], OpencvImg_data.shape[1]), np.uint16)
    else:
      GdalImg_data = np.zeros((OpencvImg_data.shape[2], OpencvImg_data.shape[0], OpencvImg_data.shape[1]), np.float32)
    for i in range(OpencvImg_data.shape[2]):
      # 注意，opencv为BGR
      data = OpencvImg_data[:, :, OpencvImg_data.shape[2] - i - 1]
      data = np.reshape(data, (OpencvImg_data.shape[0], OpencvImg_data.shape[1]))
      GdalImg_data[i] = data
  return GdalImg_data


# opencv数据转gdal
def GdalData2OpencvData(GdalImg_data):
  if 'int8' in GdalImg_data.dtype.name:
    OpencvImg_data = np.zeros((GdalImg_data.shape[1], GdalImg_data.shape[2], GdalImg_data.shape[0]), np.uint8)
  elif 'int16' in GdalImg_data.dtype.name:
    OpencvImg_data = np.zeros((GdalImg_data.shape[1], GdalImg_data.shape[2], GdalImg_data.shape[0]), np.uint16)
  else:
    OpencvImg_data = np.zeros((GdalImg_data.shape[1], GdalImg_data.shape[2], GdalImg_data.shape[0]), np.float32)
  for i in range(GdalImg_data.shape[0]):
    OpencvImg_data[:, :, i] = GdalImg_data[GdalImg_data.shape[0] - i - 1, :, :]
  return OpencvImg_data

def clipImg(srcImgPath,dstFolder,blockSize,format='png'):
    #blockSize剪裁的每一块的大小，如果blockSize=256，则每一块为256x256大小
    #format文件格式，默认生成png图片，还可以生成tif,设置format='tif'
    _, name = os.path.split(srcImgPath)
    name, _ = name.split('.')
    data, geo, proj = readTif(srcImgPath, 0, 0, 0, 0)
    if len(data.shape)==2:
        data=np.reshape(data,(1,data.shape[0],data.shape[1]))

    size = max(data.shape[1], data.shape[2])
    size = math.ceil(size / blockSize) * blockSize
    #n = int(size / blockSize)
    n=size // blockSize
    gdalData = np.full((data.shape[0], size, size), 0, dtype=np.uint8)  # 生成一个值全为0的矩阵
    gdalData[0:data.shape[0], 0:data.shape[1], 0:data.shape[2]] = data
    matData = GdalData2OpencvData(gdalData)
    #matData=unit16Touint8(matData)
    #matData=np.zeros_like(matData,dtype='uint8')
    for i in tqdm(range(n)):
        for j in range(n):
            block = matData[i * blockSize:(i + 1) * blockSize, j * blockSize:(j + 1) * blockSize]
            if format!='tif':
                cv2.imwrite(dstFolder+f'\\{name}_{i}_{j}.'+format, block)
            else:
                writeTiff(gdalData,geo,proj,dstFolder+f'\\{name}_{i}_{j}.'+format)



def unit16Touint8(data):
    ibands=data.shape[0]
    if ibands==4:
        ibands=3
    for i in range(ibands):
        maxP = np.max(data[i])
        minP = np.min(data[i])
        data[i]= (data[i] - minP) / (maxP - minP+0.5) * 255
    dUint8=data.astype('uint8')
    return dUint8




if __name__ == '__main__':
    pass
    #clipImg()用来剪裁栅格影像
    #shpToRaster(imgpath,shapepath,TableValue)将shp文件栅格化，tablevalue是shp表格中的字段，string形
























