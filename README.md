# VeighNa框架的MySQL数据库接口

<p align="center">
  <img src ="https://vnpy.oss-cn-shanghai.aliyuncs.com/vnpy-logo.png"/>
</p>

<p align="center">
    <img src ="https://img.shields.io/badge/version-1.1.0-blueviolet.svg"/>
    <img src ="https://img.shields.io/badge/platform-windows|linux|macos-yellow.svg"/>
    <img src ="https://img.shields.io/badge/python-3.10|3.11|3.12|3.13-blue.svg" />
</p>

## 说明

基于peewee开发的MySQL数据库接口。

## 使用

### 全局配置

在VeighNa中使用MySQL时，需要在全局配置中填写以下字段信息：

|名称|含义|必填|举例|
|---------|----|---|---|
|database.name|名称|是|mysql|
|database.host|地址|是|localhost|
|database.port|端口|是|3306|
|database.database|实例|是|vnpy|
|database.user|用户名|是|root|
|database.password|密码|是|123456|

### 创建实例（Schema）

VeighNa不会主动为MySQL数据库创建实例，所以使用前请确保database.database字段中填写的的数据库实例已经创建了。

若实例尚未创建，可以使用【MySQL Workbench】客户端的【new_schema】进行操作。


### 字符串大小写敏感支持

由于peewee的建表功能限制，默认情况下在保存合约代码的【symbol】字段时，无法区分字符串大小写。如果影响使用，可按照以下方式手动修改MySQL数据表来解决：

```
# 用MySQL命令行工具连接数据库

# 选择数据实例
use vnpy;

# 修改四张表symbol字段的BINARY属性
ALTER TABLE `dbbaroverview` MODIFY COLUMN `symbol` VARCHAR(45) BINARY;

ALTER TABLE `dbtickoverview` MODIFY COLUMN `symbol` VARCHAR(45) BINARY;

ALTER TABLE `dbbardata` MODIFY COLUMN `symbol` VARCHAR(45) BINARY;

ALTER TABLE `dbtickdata` MODIFY COLUMN `symbol` VARCHAR(45) BINARY;
```
