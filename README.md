# vn.py框架的MySQL数据库接口

<p align="center">
  <img src ="https://vnpy.oss-cn-shanghai.aliyuncs.com/vnpy-logo.png"/>
</p>

<p align="center">
    <img src ="https://img.shields.io/badge/version-1.0.0-blueviolet.svg"/>
    <img src ="https://img.shields.io/badge/platform-windows|linux|macos-yellow.svg"/>
    <img src ="https://img.shields.io/badge/python-3.7-blue.svg" />
</p>

## 说明

基于peewee开发的Mysql数据库接口。

由于peewee对mysql的限制，目前存在以下问题时。如不影响使用可以忽略，当影响使用时，可按照以下方式手动修改mysql数据库表来解决。

- 保存tick数据时，保存数据的时间精确度只能精确到秒

```
# 首先进入mysql数据库
# 选择vnpy数据库
use vnpy;
# 修改dbtickdata表datetime列的数据格式
ALTER TABLE `dbtickdata` MODIFY COLUMN `datetime` DATETIME(3);
```

- 部分系统对大小写不明敏感

```
# 首先进入mysql数据库
# 选择vnpy数据库
use vnpy;
# 修改三张表symbol字段BINARY属性
ALTER TABLE `dbbaroverview` MODIFY COLUMN `symbol` VARCHAR(45) BINARY;

ALTER TABLE `dbbardata` MODIFY COLUMN `symbol` VARCHAR(45) BINARY;

ALTER TABLE `dbtickdata` MODIFY COLUMN `symbol` VARCHAR(45) BINARY;
```
