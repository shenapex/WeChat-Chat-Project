# WxDat Decrypt

> 一个用于解密微信图片文件的工具
> 
> 本项目仅供学习交流使用，**可能存在封号风险，请勿用于非法用途**，否则后果自负。
> 
> **最近更新**: **wxgf**

## 功能简介

- 将微信缓存的 `.dat` 文件解密为原始图片格式。
- 支持微信 3.x 和 4.x 多种加密版本。

## 特性

- 支持多个微信版本解密：
  - 微信 3.x 加密格式
  - 微信 4.0.0 加密格式
  - 微信 4.0.3+ 新加密格式

- 灵活的密钥管理：
  - 自动识别加密版本
  - 自动查找密钥 (Web API)
  - 模板文件辅助查找密钥 (命令行)
  - 密钥缓存功能 (命令行)

- 两种使用方式：
  - Web API 模式（推荐）
  - 命令行模式

## 安装

从 [Releases](https://github.com/recarto404/reChat/releases) 页面下载预编译的二进制文件。

## 使用方式 (推荐, Web API)

> 使用 `server.py` 文件，或者从 [Releases](https://github.com/recarto404/WxDatDecrypt/releases) 页面下载预编译的二进制文件。

### 启动服务器

```bash
server -d <weixin_dir>
```

### 参数说明

- `-d, --dir`  
  微信文件目录路径（例如：`C:\Users\Admin\Documents\xwechat_files\wxid_pl4c3h0ld3r222_abcd`）

### API 说明

服务器运行在: `http://127.0.0.1:49152`

#### 解密接口

- **端点**: `/decrypt/{file_path:path}`
- **方法**: `GET`
- **参数**: file_path - dat文件相对路径
- **返回**: 解密后的图片文件

### 使用示例

1. 启动服务器: 
```bash
server -d "C:\Users\Admin\Documents\xwechat_files\wxid_pl4c3h0ld3r222_abcd"
```

2. 调用 API: 
```
GET http://127.0.0.1:49152/decrypt/msg/attach/cfcd208495d565ef66e7dff9f98764da/2025-06/Img/cfcd208495d565ef66e7dff9f98764da.dat
```

### 返回说明

- 成功：返回解密后的图片文件
- 失败：返回错误信息

## 使用方法 (旧, 命令行)

> 使用 `dat2img.py` 文件，或者从 [Releases](https://github.com/recarto404/WxDatDecrypt/releases/tag/v0.0.7) 页面下载预编译的二进制文件。

```bash
dat2img -i <input_path> -o <output_path> [-v <version>] [-x <xorKey> -a <aesKey> | -f <template>]
```
`-f` 命令会在同目录下生成 `key.dat` AES 密钥缓存文件，第二次使用时将优先尝试缓存密钥。

### 参数说明

- `-i, --input`  
  输入文件路径（`.dat` 格式）。

- `-o, --output`  
  输出文件路径（如 `output.jpg`、`output.png`）。

- `-v, --version`  
  `.dat` 文件版本（整型）。**可选项，不使用将自动判断文件加密版本**
  - `0`：纯 XOR 解密  
  - `1`：V1 版本，文件头为 `b"\x07\x08V1\x08\x07"`  
  - `2`：V2 版本，文件头为 `b"\x07\x08V2\x08\x07"`

- `-x, --xorKey`  
  异或密钥（整型）。**与 `-f` 参数二选一**。

- `-a, --aesKey`  
  AES 密钥（16位字符串）。**与 `-f` 参数二选一**。

- `-f, --findKey`  
  模板文件路径。用于辅助查找密钥。建议选用 `_t.dat` 结尾的文件作为模板文件。**与 `-x` 和 `-a` 参数二选一**。

### 使用示例

0. **推荐**: 解密微信图片，自动选择加密版本，并使用模板文件查找密钥解密
   ```bash
   dat2img -i wx_image.dat -o wx_image.jpg -f template_t.dat
   ```

1. 解密 V1 版本微信图片，手动指定异或密钥解密
   ```bash
   dat2img -i wx_image.dat -o wx_image.jpg -v 1 -x 101
   ```

2. 解密 V2 版本微信图片，手动指定密钥解密
   ```bash
   dat2img -i wx_image.dat -o wx_image.jpg -v 2 -x 101 -a abcdefgh12345678
   ```

3. 解密 V2 版本微信图片，使用模板文件查找密钥解密
   ```bash
   dat2img -i wx_image.dat -o wx_image.jpg -v 2 -f template_t.dat
   ```

## 常见问题

- **Q:** 解密后图片无法打开？  
  **A:** 请确认 `version`, `xorKey`, `aesKey` 设置正确。如果使用 `-f` 参数，请确保模板文件有效。

- **Q:** 如何选择合适的模板文件？  
  **A:** 建议使用与目标 `.dat` 文件来自同一微信账号的 `_t.dat` 文件。通常，同一个微信账号使用相同的密钥。

- **Q:** 支持批量解密吗？  
  **A:** 当前版本仅支持单文件操作，可通过 shell 脚本或批处理自行循环调用。

- **Q:** 为何设置正确但解密的图片仍无法查看?  
  **A:** 查看文件前四个字节是否为 b"wxgf"，若是，则在计划之中。

## 计划

- [x] 实现对 `wxgf` 格式微信图片的解码支持. **暂时只提供 [Releases](https://github.com/recarto404/WxDatDecrypt/releases) 的分支**

## 贡献

欢迎提交 Issue！

## 许可证

本项目采用 [MIT License](./LICENSE) 开源协议。
