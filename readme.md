# README

## 项目简介
这是一个部署在 **PythonAnywhere** 上的认证网页项目，用于：
- 登录管理页面
- 添加认证账户
- 生成认证结果页面
- 提供扫码验证成功 / 失败页面
- 管理 MySQL 数据库中的认证信息

---

## 使用方法
1. 登录网站： [maoyifei.pythonanywhere.com](https://maoyifei.pythonanywhere.com)
2. 按照页面流程进行后续操作。
3. **注意：在生成二维码之后请及时登出，以确保网页及数据库安全。**

---

## 管理须知

1. 登录 **PythonAnywhere** 后进入 **Dashboard**。
2. 每三个月内进入 **Web** 页面刷新网站使用时间（会自动往后延三个月）。
3. 可以进入 **Tasks** 页面查看每天 CPU 的使用情况。

---

## 项目文件结构

```text
my_cite/                      # 项目根目录
├── app.py                    # 主应用文件（路由、数据库逻辑）
├── requirements.txt          # 依赖包列表（需安装的库及其版本）
├── static/                   # 静态资源文件夹
│   ├── logo.jpg              # 项目 Logo（把它改成你自己的logo！）
│   └── styles.css            # （目前没有，后续可添加）
└── templates/                # HTML 模板文件夹
    ├── login.html            # 登录页面
    ├── form.html             # 认证表单页面（添加账户）
    ├── success.html          # 认证成功页面
    ├── verify_success.html   # 扫码验证成功页面
    └── verify_fail.html      # 扫码验证失败页面
```

---

## 页面编辑说明
如果想修改扫码验证结果页面，可以直接编辑以下文件：
- `verify_success.html`
- `verify_fail.html`

建议先在本地进行测试。  
如果使用豆包生成 HTML，可以配合豆包的**预览功能**查看效果。

---

## 数据库管理：`certifications`
建议简单学习一下 MySQL 的基本指令。以下加粗部分为常用 MySQL 指令。

### 进入数据库
1. 打开 **Consoles** 页面
2. 进入或打开 **MySQL console**
3. 登录数据库：

```sql
USE maoyifei$rednote;
```

### 查看认证用户信息
```sql
SELECT * FROM certifications;
```

该表中主要字段示例：
- `id`
- `rednote_id`
- `account_name`
- `cert_code`
- `valid_from`
- `valid_to`
- `status`

---

## 修改认证状态

### 将 `status` 从 `active` 改为 `expired`
```sql
UPDATE certifications
SET status='expired'
WHERE rednote_id='...';
```

> 将 `...` 替换为实际的小红书 ID。

### 示例
```sql
UPDATE certifications SET status='expired' WHERE rednote_id='007';
SELECT * FROM certifications;
```

### 将 `status` 改回 `active`
```sql
UPDATE certifications
SET status='active'
WHERE rednote_id='...';
```

---

## 安全提醒
- 生成二维码后请及时退出登录。
- 不要随意暴露数据库账号信息。
- 修改数据库内容前，建议先确认目标 `rednote_id` 是否正确。
- 对线上页面进行修改前，建议先在本地测试。

---

## 后续可扩展内容
后续可以考虑加入：
- `styles.css` 统一页面样式
- 更完善的后台管理页面
- 日志记录功能
- 认证过期自动处理逻辑
- 更友好的异常提示页面
