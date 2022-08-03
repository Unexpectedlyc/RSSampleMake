import cv2
import numpy as np
import math
from clipimage import readTif,writeTiff,OpencvData2GdalData,GdalData2OpencvData
from tqdm import tqdm


def unit16Touint8(data):
    c=data.shape[0]
    w=data.shape[1]
    h=data.shape[2]
    dUint8=np.array(data,dtype='uint8')
    dUint8=np.reshape(dUint8,(c*w*h))
    maxP=np.max(data)
    minP=np.min(data)
    data=np.reshape(data,(c*w*h))
    if maxP <= 255:
        for i in tqdm(range(w * h * c)):
            dUint8[i] = data[i]
    else:
        for i in tqdm(range(w*h*c)):
            dUint8[i]=int((data[i]-minP)/(maxP-minP)*255)

    dUint8=np.reshape(dUint8,(c,w,h))
    return dUint8

def calHist(imgdata):
    #输入必须为3通道的数据
    bc,gc,rc=cv2.split(imgdata)
    b = cv2.calcHist([bc],[0],  None, [256],  [0.0, 255.0])
    g = cv2.calcHist([gc], [0], None, [256], [0.0, 255.0])
    r = cv2.calcHist([rc], [0], None, [256], [0.0, 255.0])
    return b,g,r

def HistSpecifyOne(hist1,hist2,img1Size,img2Size,imgOneChannel):
    # 直方图归一化
    hist1Nom = hist1 / img1Size
    hist2Nom = hist2/ img2Size
    # 计算原始直方图和规定直方图的累积概率
    hist1Sum = np.zeros(256)
    hist2Sum = np.zeros(256)
    for i in range(256):
        if i == 0:
            hist1Sum[i] = hist1Nom[i]
            hist2Sum[i] = hist2Nom[i]
        else:
            hist1Sum[i] = hist1Sum[i - 1] + hist1Nom[i]
            hist2Sum[i] = hist2Sum[i - 1] + hist2Nom[i]
    # 累积概率的差值
    diffR = np.zeros((256, 256))
    for i in range(256):
        for j in range(256):
            diffR[i][j] = math.fabs(hist1Sum[i] - hist2Sum[j])
    # 构建单通道映射表
    lutR = np.zeros(256)
    for i in range(256):
        # 查找源灰度级为ｉ的映射灰度
        # 和ｉ的累积概率差值最小的规定化灰度
        min = diffR[i][0]
        index = 0
        for j in range(256):
            if min > diffR[i][j]:
                min = diffR[i][j]
                index = j
        lutR[i] = index

    Res = np.zeros(imgOneChannel.shape)

    cv2.LUT(imgOneChannel, lutR, Res)

    return Res



def HistSpecify(img1data,img2data):
    #第一幅图根据第二幅图来校正

    #将gdaldata转化为opencvdata
    if img1Data.shape[0]==3:
        img1data = GdalData2OpencvData(img1data)
        img2data = GdalData2OpencvData(img2data)


    # 获取直方图
    b1, g1, r1 = calHist(img1data)
    b2, g2, r2 = calHist(img2data)

    # 获取3个通道
    bc1, gc1, rc1 = cv2.split(img1data)
    bc2, gc2, rc2 = cv2.split(img2data)

    #直方图规定化
    bHS=HistSpecifyOne(b1,b2,img1data.shape[0]*img1data.shape[1],img2data.shape[0]*img2data.shape[1],bc1)
    gHS = HistSpecifyOne(g1, g2,img1data[0].size, img2data[0].size,gc1)
    rHS=HistSpecifyOne(r1,r2,img1data[0].size,img2data[0].size,rc1)
    dst=np.zeros(img1data.shape)

    cv2.merge((bHS,gHS,rHS),dst)

    return dst


if __name__ == '__main__':
    #两幅图像大小必须一致
    img1Path = "D:\data\shpimg\\2020.tif"
    img2Path = "D:\data\shpimg\\2021.tif"
    img1Data, im1_geotrans, im1_proj = readTif(img1Path, 0, 0, 0, 0)
    img2Data, im2_geotrans, im2_proj = readTif(img2Path, 0, 0, 0, 0)

    dst=HistSpecify(img2Data,img1Data)
    dst=OpencvData2GdalData(dst)
    dst=unit16Touint8(dst)
    writeTiff(dst,im1_geotrans,im1_proj,"D:\data\shpimg\\2021RE.tif")









