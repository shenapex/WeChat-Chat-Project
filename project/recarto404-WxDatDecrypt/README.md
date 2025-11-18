# 微信图片查看器

> 一个用于查看和解密微信图片文件的工具
> 
> 本项目仅供学习交流使用，**可能存在封号风险，请勿用于非法用途**，否则后果自负。

## 功能简介

![程序界面预览](img/home.png)

- 图形化界面，操作简单直观
- 将微信缓存的 `.dat` 文件解密为原始图片格式。
- 支持微信 3.x 和 4.x 多种加密版本。
- 实时预览解密后的图片
- 自动检测和保存解密密钥

## 特性

- 支持微信 3/4 版本加密图片解密
- 支持微信 WxAM (wxgf) 格式解码

## 系统要求

- Windows 11
- Python 3.12

## 使用方法

1. 从 [Releases](https://github.com/recarto404/WxDatDecrypt/releases) 页面下载预编译的二进制文件，或使用源代码文件。

2. 首次使用前，需要先获取解密密钥：
   - 运行 `tool.exe`（或 `tool.py`）
   - 选择对应的微信版本
   - 按提示输入微信缓存目录 (例如：`C:\Users\Admin\Documents\xwechat_files\wxid_pl4c3h0ld3r222_abcd`)
   - 程序会查找密钥, 保存至 `config.json` 文件

3. 获取密钥后：
   - 运行 `app.exe`（或 `app.py`）
   - 在程序界面中点击选择文件夹按钮，选择微信的图片缓存目录
   - 程序会自动扫描目录并显示所有可用的图片文件
   - 点击左侧目录树可以浏览不同文件夹

## 许可证

本项目采用 [MIT License](./LICENSE) 开源协议。

## 技术支持

如有问题或建议，请提交 Issue。

## 感谢

- [Fluent Emoji](https://github.com/microsoft/fluentui-emoji)
- [Fluent UI Web Components](https://github.com/microsoft/fluentui/tree/master/packages/web-components)