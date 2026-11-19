> **📘 增强词库版说明**
> 本 fork 仅扩充 `translations/zh_CN.tsv`：1,122 → **17,825 条**，
> 主要补充引脚信号名、模式下拉、外设面板参数、时钟树标签等界面文案，
> 侧重点在 F1 / F4 / G0 / G4 / H5 / H7 / L 等常用系列。
>
> **安装方法**：先按原作者说明下载 Release 启动器并完整解压，
> 再用本仓库的 `translations/zh_CN.tsv` 覆盖解压目录中的同名文件。
> 验证：启动日志中 `dictionary_entries = 17825`。
>
> 非官方汉化，与 STMicroelectronics 无关；不改原项目任何代码。
>
> **关于质量**：本词库由 AI 辅助生成、人工审读修订，**并非逐条对照真实软件界面验证过**。
> 因此可能存在三类问题：
> ① **遗漏**——某些界面文案尚未收录，运行时仍显示英文；
> ② **不当翻译**——个别词条译法生硬、术语不统一，或本应保留英文（如型号、寄存器名、协议名）却被译出；
> ③ **少量键名与软件内字符串不完全一致**，导致该条不生效。
>
> **使用建议**：以上都属于已知风险，本词库不适合替代原版直接分发使用。
> 若某个型号或外设的翻译不合你的用途，**请自行修改 `translations/zh_CN.tsv` 中对应部分后使用**——
> 删除不需要的词条、或改写成你要的译法都可以，改动只影响你自己的副本。
>
> **📗 自己补充词库（用你自己的芯片）**
> 词库是按 STM32 常用系列攒起来的。你用别的型号，界面上难免还有英文。
> 启动器可以记录界面文字并导出成待翻译清单，交给任何 AI 翻译后追加进词库：
>
> 1. 打开启动器，勾选「记录界面显示过的文字」
> 2. 启动中文版，**正常使用 CubeMX**，然后**点右上角 × 正常关闭**
> 3. 回到启动器，点「导出待翻译清单」，保存为 `.md`
>
> 清单会自动分成四段：引脚配置 / 时钟树 / 下拉选项 / 其余文案。
>
> ⚠️ **要点一：必须手动操作过的界面文字才会被记录。**
> 有三类需要你主动触发：
>
> | 类型 | 怎么触发 | 例子 |
> |---|---|---|
> | **下拉选项** | 点开下拉框，让选项显示出来 | `Input mode`、`Trigger Source`、`Internal VRef` |
> | **引脚功能菜单** | 在引脚图上点引脚 | `GPIO_Input`、`EVENTOUT`、`RCC_OSC32_IN` |
> | **悬浮提示（tooltip）** | **鼠标停在外设名上 1~2 秒** | 悬停 `WWDG1` 显示 `System Window WatchDoG` |
>
> 没触发过的，导出的清单里不会有它的文字——被动看着屏幕不动，
> 只能抓到当前可见的那一层。
>
> **tooltip 尤其容易被漏掉**：Swing 的提示有约 750 毫秒延迟，鼠标划过去就移开不会触发，
> 且它只在鼠标停留期间渲染。想把某个外设的说明收进词库，必须真的把指针停在名字上等它弹出来。
>
> ⚠️ **要点二：必须正常关闭 CubeMX。** 记录在进程退出时才写入磁盘，
> 用任务管理器强制结束会丢失这一轮。
>
> ⚠️ **要点三：每次启动生成独立记录文件**，位于
> `%LOCALAPPDATA%\CubeMX-CN\logs\trace-<时间戳>.tsv`，多次使用互不覆盖，导出时会合并全部记录。
>
> ⚠️ **要点四：已经翻译过的内容不会出现在清单里。** 记录时就会标出命中状态，
> 导出时直接跳过；型号、引脚名、容量数值、版本号、代码片段等噪声也会被滤掉。
> 清单末尾会打印每一类被滤掉的数量，便于核对。

# CubeMX-CN

[![Windows build and tests](https://github.com/NingZiXi/CubeMX-CN/actions/workflows/build.yml/badge.svg)](https://github.com/NingZiXi/CubeMX-CN/actions/workflows/build.yml)

传统版 **STM32CubeMX** 的独立中文启动器。通过进程内显示层汉化，让常用菜单和页面显示中文，保留原安装文件与程序内部参数。

**[下载网站](https://ningzixi.github.io/CubeMX-CN/)** · **[Gitee 下载](https://gitee.com/nzxhg/CubeMX-CN/releases/tag/v0.1.0)** · [GitHub 备用下载](https://github.com/NingZiXi/CubeMX-CN/releases/latest) · [更新记录](CHANGELOG.md) · [参与改进](CONTRIBUTING.md)

![实际 CubeMX 首页汉化效果，工程列表已隐藏](docs/images/home.png)

## 使用方法

1. 从 [Gitee 发行版](https://gitee.com/nzxhg/CubeMX-CN/releases/tag/v0.1.0) 或 [GitHub 发行版](https://github.com/NingZiXi/CubeMX-CN/releases/latest) 下载 `CubeMX-CN-v版本号-windows-x64.zip`，**完整解压**。
2. 双击 `CubeMX-CN.exe`，检查自动找到的 CubeMX 安装目录，也可以点击“浏览”选择。
3. 保存并关闭已经打开的 CubeMX，点击 **启动中文版**。
4. 切换英文时，关闭 CubeMX，再点击 **启动英文版**，或者使用原来的 CubeMX 快捷方式。

以后想用中文，都从汉化启动器进入。可以为 EXE 创建快捷方式，但不要只移动 EXE：两个 JAR 文件和 `translations` 文件夹需要保留在旁边。

发布包不需要另装 Python，使用 CubeMX 自带的 Java。工具不覆盖 EXE、插件、数据库、`.ioc` 或原版启动配置，不需要打补丁或恢复备份。删除汉化文件夹即可停止使用；工具自身的设置和日志位于 `%LOCALAPPDATA%/CubeMX-CN`。CubeMX 启动时仍会正常更新它自己的用户设置和软件包索引。

请下载名称包含 `windows-x64` 的便携 ZIP，不要将自动生成的源码 ZIP/TAR 当作安装包。Gitee 如要求登录，可登录后下载，或选择 GitHub 备用入口。两个平台的 v0.1.0 便携包一致，SHA-256 为：

```text
ee6134b320b3a738cd2ded95b527425429ac7b406778ac977c85423a3a9d3493
```

## 兼容性与边界

| 项目 | 当前支持 |
| --- | --- |
| 系统 | Windows x64 |
| 软件 | 传统版 STM32CubeMX，**不支持 CubeMX2** |
| 运行时 | CubeMX 内置 Java 21 |
| 已验证版本 | Java 21.0.10 / CubeMX 内部组件 6.18.1-RC2 |
| 词库 | 1,122 条，含常用菜单、首页、工程管理、代码生成选项、引脚/时钟及部分外设选项 |

这是独立的非官方项目，并非完整官方中文语言包。图片、在线内容、系统窗口、未收录动态文字及部分自定义绘制仍可能显示英文。编辑框和文件选择器内容保留原文；固定尺寸控件可能截断长译文。

汉化包位于中文路径时，启动器将两个 JAR 和词库复制到 `%TEMP%/CubeMX-CN/runtime` 的内容哈希缓存中，以兼容 Java 原生加载器。词库修改后自动使用新缓存。如果系统临时目录本身也有中文，请将汉化包和词库放到纯英文目录。缓存可在关闭 CubeMX 后删除。

已验证首页及代表性控件渲染，**尚未完成全部外设页面、完整工程保存和代码生成的回归测试**。其他 CubeMX 版本未逐一验证。详见 [验证记录](docs/verification.md)。

## 自定义翻译

点击“编辑中文词库”，用记事本修改 `translations/zh_CN.tsv`。使用 UTF-8，每行由英文原文、一个 Tab 制表符、中文译文组成，`#` 开头为注释：

```text
File	文件
Save	保存
```

保存后重启中文版生效。启动器会检查空译文、字段数和冲突词条。普通文字按完整文本匹配，并兼容首尾空白、末尾冒号/省略号；HTML 按文本节点匹配。不要把代码标识符当成文案翻译，也不要在译文中添加 HTML 标记。

## 从源码构建

需要 **Windows、Python 3.11+、JDK 21**。Java 构建没有外部依赖，EXE 使用 PyInstaller 打包。测试使用独立样本和 Swing，不需要安装 CubeMX。

```powershell
git clone https://github.com/NingZiXi/CubeMX-CN.git
cd CubeMX-CN
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'

python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-build.txt

# 从 JAVA_HOME 或 PATH 查找 JDK 21
.venv/Scripts/python.exe tools/build.py
.venv/Scripts/python.exe tools/verify.py
.venv/Scripts/python.exe tools/package.py
```

也可显式指定 JDK，例如安装目录内确实包含 `javac.exe` 时：

```powershell
python tools/build.py --jdk D:/STM32CubeMX/jre
python tools/verify.py --jdk D:/STM32CubeMX/jre
```

产物位于 `dist/CubeMX-CN/`，完整 ZIP 和 SHA-256 校验文件位于 `dist/`。版本号统一读取根目录 `VERSION`。CI 自动完成 Windows 构建、测试和打包。

## 开发命令

```powershell
python launcher.py
python launcher.py --inspect D:/STM32CubeMX
python launcher.py --launch D:/STM32CubeMX
python launcher.py --launch D:/STM32CubeMX --english
python launcher.py --launch D:/STM32CubeMX --capture ./reports/runtime-home
python tools/extract_strings.py D:/STM32CubeMX --output reports/strings.json
```

`--inspect` 只读检查安装；`--capture` 在 30 秒后将本次 JVM 自身窗口绘制为 PNG，并输出控件原文清单。`--project` 可传入 `.ioc` 文件，建议用工程副本验证。日志和提取结果可能含本地路径，默认留在本机并排除在 Git 之外。

## 项目结构

```text
agent/          Java agent、bootstrap 翻译器与诊断功能
translations/   UTF-8 中文词库
tools/          JDK 定位、构建、验证、打包和字符串提取
tests/          启动器测试和 Java 渲染验证
docs/           实现说明、验证范围与脱敏截图
launcher.py     图形启动器与 CLI
VERSION         发布版本
```

实现细节见 [架构说明](docs/architecture.md)。工具在测量/绘制路径进行翻译，不替换原控件文本与按钮命令；搜索、复制和无障碍接口仍可能使用英文，快捷键沿用原版键位。

仓库与发布包不包含 ST 的可执行文件、插件、数据库或 JRE。STM32CubeMX 是 STMicroelectronics 的产品，本项目与其没有隶属或背书关系。
