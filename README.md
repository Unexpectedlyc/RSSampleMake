# RSSampleMake

遥感影像制作深度学习样本的程序，包含样本制作和相对辐射校正功能。

## 功能介绍

1. 📷 **图像裁剪** (clipimage.py)

   - ✂️ 支持将大尺寸遥感影像按指定大小分块裁剪
   - 🖼️ 可输出为 PNG 或 TIFF 格式

2. 🗺️ **矢量数据栅格化** (clipimage.py)

   - 🔄 将 Shapefile 矢量数据转换为与模板影像一致的栅格数据
   - 📊 支持指定属性字段作为栅格值

3. ⚫ **二值化处理** (clipimage.py)

   - 🔁 将矢量数据栅格化后进行二值化处理

4. 📈 **相对辐射校正** (RelativeRadiometricCorrection.py)
   - 📊 基于直方图匹配的相对辐射校正
   - 🎯 可将一幅影像的辐射特征调整为与参考影像一致

## 环境依赖

🔧 安装所需依赖包：

```bash
pip install -r requirements.txt
```

📚 依赖包列表：

- GDAL==3.4.1
- numpy==1.22.3
- opencv_python==4.5.5.64
- osgeo==0.0.1
- tqdm==4.64.0

## 使用说明

### 📷 图像裁剪

```python
from clipimage import clipImg

# 裁剪图像
clipImg(
    srcImgPath="输入图像路径",
    dstFolder="输出文件夹路径",
    blockSize=256,  # 裁剪块大小
    format='png'    # 输出格式，可选 'png' 或 'tif'
)
```

### 🗺️ 矢量数据栅格化

```python
from clipimage import shpToRaster

# 将矢量数据转换为栅格
output_file = shpToRaster(
    imgpath="模板影像路径",
    shapepath="矢量文件路径",
    TableValue="属性字段名"
)
```

### 📈 相对辐射校正

```python
from RelativeRadiometricCorrection import HistSpecify
from clipimage import readTif, writeTiff, OpencvData2GdalData, unit16Touint8

# 读取待校正影像和参考影像
img1Data, im1_geotrans, im1_proj = readTif("参考影像路径", 0, 0, 0, 0)
img2Data, im2_geotrans, im2_proj = readTif("待校正影像路径", 0, 0, 0, 0)

# 执行直方图匹配校正
dst = HistSpecify(img2Data, img1Data)

# 数据格式转换和保存
dst = OpencvData2GdalData(dst)
dst = unit16Touint8(dst)
writeTiff(dst, im1_geotrans, im1_proj, "输出影像路径")
```

## ⚠️ 注意事项

1. 🌍 所有影像处理均保持原始地理信息不变
2. 📏 相对辐射校正要求两幅影像空间分辨率和覆盖范围一致
3. 🌈 程序支持处理多波段遥感影像

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Unexpectedlyc/RSSampleMake&type=Date)](https://www.star-history.com/#Unexpectedlyc/RSSampleMake&Date)
