> **📘 增强词库版说明**
>
> 本 fork 在原作者基础上**扩充词库，并增加了运行时记录与缺口筛选能力**。
> 词条由原作者的 **1,122 条**扩充到 **18,283 条**，覆盖常用菜单、首页、工程管理、
> 代码生成选项、引脚配置、时钟树、各外设面板与悬浮说明，侧重点在
> F1 / F4 / G0 / G4 / H5 / H7 / L 等常用系列。
>
> **相对原作者改动的内容**（共 6 个文件）：
>
> | 文件 | 性质 | 说明 |
> |---|---|---|
> | `translations/zh_CN.tsv` | 数据 | 词库 1,122 → 18,283 条 |
> | `agent/bootstrap/cubemx/cn/bootstrap/Translator.java` | **源码** | 界面文字记录、空白压缩匹配、引脚行拆分、未命中诊断 |
> | `launcher.py` | **源码** | 增加「记录界面文字」开关与「导出待翻译清单」按钮 |
> | `tools/filter_trace.py` | **新增** | 把运行记录筛成五段待翻译清单 |
> | `docs/trace-and-filter.md` | **新增** | 记录与筛选的完整流程说明 |
> | `README.md` | 文档 | 本说明 |
>
> 汉化机制本身（测量/绘制路径挂钩、不替换控件文本）沿用原作者实现，未作改动。
>
> **安装方法**：本 fork 改动了启动器，**不能只替换词库文件**。
> 请使用本仓库构建的完整发布包（`dist/CubeMX-CN/`），或按「从源码构建」自行打包。
> 若沿用原作者的启动器，则只能获得词库扩充效果，记录与导出功能不可用。
> 验证：启动日志中出现 `Dictionary entries=18283`。
>
> 非官方汉化，与 STMicroelectronics 无关。
>
> **关于质量**：词库由 AI 辅助生成、人工审读修订，**并非逐条对照真实软件界面验证过**。
> 已知可能存在的问题：
> ① 某些界面文案尚未收录，运行时仍显示英文；
> ② 个别词条译法生硬或术语不统一；
> ③ 本应保留英文的内容（型号、寄存器名、协议名）被误译；
> ④ 少量键名与软件内字符串不完全一致，导致该条不生效。
>
> 若某个型号或外设的翻译不合你的用途，**请自行修改 `translations/zh_CN.tsv` 对应部分**——
> 删除不需要的词条、或改写成你要的译法都可以，改动只影响你自己的副本。
> 下文的「自己补充词库」一节说明了如何针对你自己的芯片定位还缺哪些文案。

---

## 📗 自己补充词库（用你自己的芯片）

词库是按 STM32 常用系列攒起来的。你用别的型号，界面上难免还有英文。
启动器可以记录界面文字并导出成待翻译清单，交给任何 AI 翻译后追加进词库：

1. 打开启动器，勾选「记录界面显示过的文字」
2. 启动中文版，**正常使用 CubeMX**，然后**点右上角 × 正常关闭**
3. 回到启动器，点「导出待翻译清单」，保存为 `.md`

清单会自动分成五段：

| 段 | 内容 | 优先级 |
|---|---|---|
| 一、引脚配置 | 引脚位号与状态 | 最高，全部保留 |
| 二、时钟树 | 时钟信号名与频率标签 | 高 |
| 三、下拉/列表选项 | 下拉框、列表里的可选值 | 中 |
| 四、外设说明 | 鼠标悬停才出现的说明文字 | 中 |
| 五、其余界面文案 | 其他标签、按钮、提示 | 低 |

### ⚠️ 要点一：必须手动操作过的文字才会被记录

有三类需要你主动触发：

| 类型 | 怎么触发 | 例子 |
|---|---|---|
| **下拉选项** | 点开下拉框，让选项显示出来 | `Input mode`、`Trigger Source` |
| **引脚功能菜单** | 在引脚图上点引脚 | `GPIO_Input`、`EVENTOUT` |
| **悬浮提示（tooltip）** | **鼠标停在外设名上 1~2 秒** | 悬停 `WWDG1` 显示 `System Window WatchDoG` |

没触发过的，导出的清单里不会有它的文字——被动看着屏幕不动，只能抓到当前可见的那一层。

**tooltip 尤其容易被漏掉**：Swing 的提示有约 750 毫秒延迟，鼠标划过去就移开不会触发，
且它只在鼠标停留期间渲染。想把某个外设的说明收进词库，必须真的把指针停在名字上等它弹出来。

### ⚠️ 要点二：必须正常关闭 CubeMX

记录在进程退出时才写入磁盘，用任务管理器强制结束会丢失这一轮。

### ⚠️ 要点三：每次启动生成独立记录文件

位于 `%LOCALAPPDATA%\CubeMX-CN\logs\trace-<时间戳>.tsv`，多次使用互不覆盖，
导出时会合并全部记录。

### ⚠️ 要点四：已经翻译过的内容不会出现在清单里

记录时就会标出命中状态，导出时直接跳过；型号、引脚名、容量数值、版本号、
代码片段等噪声也会被滤掉。清单末尾会打印每一类被滤掉的数量，便于核对。

---

## 📕 译文写法约定

界面文案统一写成 `中文 (English 原文)`，有三类例外：

| 场合 | 写法 | 原因 |
|---|---|---|
| 一般标签、菜单、按钮、提示 | `中文 (English)` | 方便对照英文界面与官方文档 |
| 实例名、引脚名 | `原名（中文注释）`，如 `ADC1（模数转换器）` | 原名对应数据手册与 HAL 宏，译了就对不上 |
| **外设悬浮说明正文** | **只写中文，不附英文** | 说明面板宽度约 100 字符，附上英文会导致每行折行、面板高度超出而被裁切 |

第三条之所以例外：这些说明是**按行渲染**的，一行一个词条。若每行都追加英文原句，
三行内容会撑成六行，面板上下都被截断，中文也看不全。目前有 40 条正文属于这一类。

**英文原文并没有丢**：这三段外设说明（DMA / WWDG / IWDG）的完整原文保留在
`translations/zh_CN.tsv` 中部的注释块里（搜索 `# ── 外设说明英文原文`），
以 `# [DMA] …`、`# [WWDG] …`、`# [IWDG] …` 分组。
注释行以 `#` 开头，加载时会被跳过，不影响运行。

**缩写要展开**：`MMC` 写成 `MMC 多媒体卡`、`SD` 写成 `SD 安全数字卡`、
`SDIO` 写成 `SDIO 安全数字 I/O`、`PVD` 写成 `可编程电压检测器 (PVD)`。
只保留字母的写法（如 `MMC 1 位模式`）读者无法判断 MMC 是什么。

---

## 🔧 这些译文是怎么做出来的（供后续维护参考）

### 1. 词条从哪来

不是照着界面截图一条条抄，而是从运行中的 CubeMX 里抓：

1. 启动器勾选「记录界面显示过的文字」，用它启动；
2. 把要覆盖的页面点一遍（下拉框要展开、引脚要点击、外设名要悬停）；
3. 正常关闭，记录写到 `%LOCALAPPDATA%\CubeMX-CN\logs\trace-<时间>.tsv`；
4. 点「导出待翻译清单」，得到按键位去噪后的待翻译列表。

这样拿到的键**和程序实际传给渲染层的字符串逐字节一致**，
不会出现"看着一样却匹配不上"的情况。

### 2. 键必须逐字节一致

匹配是精确查找，以下差异都会导致不生效，且界面上完全看不出来：

| 差异 | 例子 |
|---|---|
| 前导/尾随空格 | `Datasheet \n    ` 与 `Datasheet` |
| 中间夹着换行 | `List \n    of Peripheral DMA Requests` |
| **换行是真字符还是字面量** | 记录文件里写 `\n`（反斜杠加 n），运行时传入的却是真换行 `0x0A` |
| 项目符号被转义 | 圆点 `•` 在 tooltip 里变成双引号 `"` |
| ST 的拼写错误 | `Channell 22`、`Controler`、`converfsion` —— **照抄，不要纠正** |

启动器已做三层容错：

1. `strip()` 去首尾空白；
2. `squash()` 把内部连续空白（含字面 `\n` 与真换行）压成一个空格；
3. 为带换行前缀的键额外存一份压缩形式的别名。

仍匹配不到时，会在日志目录写出 `trace-*-miss.txt`，记录该文本的长度、
strip/squash 后是否命中、以及前 60 个字符的十六进制码位——**十六进制是唯一能看出
不可见字符差异的手段**，本项目里多个疑难问题都是靠它定位的。

### 3. tooltip 为什么按行拆开翻

Swing 的 `JToolTip` 把一段说明按宽度拆成多行渲染，**每一行是独立的一次翻译调用**。
所以同一段话要在词库里占多条键，每条只译自己那一行：

```
The DMA allows data transfers to take place in the background, without the intervention of
  → DMA 允许数据传输在后台进行，无需
the Cortex-Mx processor. During this operation, the main processor DMA execute other tasks
  → Cortex-Mx 处理器介入。在此操作期间，主处理器 DMA 可执行其他任务
and it is only interrupted when a whole data block is available for processing.
  → 并且只有当整个数据块可供处理时才产生中断
```

若为了"通顺"把整段中文塞进第一行，界面会把整段重复渲染三遍。

### 4. 引脚表格行只翻译状态词

引脚表的一行形如 `(28)-PB2 : Reset_State`。用整行做键需要为每个引脚各存一份，
几千种组合无法穷举。`Translator` 里做了拆分：保留引脚名，只把状态词换成中文，
即 `(28)-PB2 : Reset_State（复位状态）`。

### 5. 术语与实例名的处理

- 外设实例名保留原文：`ADC1`、`USART2`、`TIM3` —— 对应 HAL 宏与数据手册
- 引脚名保留原文：`PA0`、`PH1-OSC_OUT`、`SYS_JTMS-SWDIO`
- 复用功能号保留原文：`AF7`、`AF8`
- 外设全称译出：`Analog to digital converter` → 模数转换器
- 统一术语：ADC=模数转换器、I2C=集成电路互连总线、I2S=集成电路内置音频总线、
  DFSDM=Sigma-Delta 数字滤波器、UCPD=通用串行总线 Type-C 电力传输、Break=刹车、
  Wide bus=宽总线模式（不是"位宽总线"）
- 数字与单位之间留空格：`12 Mbit/s`、`72 MHz`

### 6. 改完必须校验

词库是纯文本，但一行写错就会静默失效。每次提交前跑一遍：

| 检查项 | 要求 |
|---|---|
| BOM | 无 |
| CRLF | 0（必须是纯 LF） |
| 控制字符 | 0 |
| 字段数异常 | 0（每行恰好一个 Tab、两列） |
| 重复键 | 0 |
| 键值同文 | 0 |
| 中文重复双写 | 0 |
| 括号不配平 | 0（用括号深度判断，避免键名自带括号造成误报） |

---


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
| 词库 | 18,283 条，含常用菜单、首页、工程管理、代码生成选项、引脚/时钟、各外设面板与悬浮说明 |
| 相对原作者的改动 | 6 个文件：词库、`Translator.java`、`launcher.py`、`tools/filter_trace.py`（新增）、`docs/trace-and-filter.md`（新增）、`README.md` |

这是独立的非官方项目，并非完整官方中文语言包。图片、在线内容、系统窗口、未收录动态文字及部分自定义绘制仍可能显示英文。编辑框和文件选择器内容保留原文；固定尺寸控件可能截断长译文。

汉化包位于中文路径时，启动器将两个 JAR 和词库复制到 `%TEMP%/CubeMX-CN/runtime` 的内容哈希缓存中，以兼容 Java 原生加载器。词库修改后自动使用新缓存。如果系统临时目录本身也有中文，请将汉化包和词库放到纯英文目录。缓存可在关闭 CubeMX 后删除。

已验证首页及代表性控件渲染，**尚未完成全部外设页面、完整工程保存和代码生成的回归测试**。其他 CubeMX 版本未逐一验证。详见 [验证记录](docs/verification.md)。

## 自定义翻译

点击“编辑中文词库”，用记事本修改 `translations/zh_CN.tsv`。使用 UTF-8，每行由英文原文、一个 Tab 制表符、中文译文组成，`#` 开头为注释：

```text
File	文件
Save	保存
```

保存后重启中文版生效。启动器会检查空译文、字段数和冲突词条。

匹配规则（知道这些能少踩坑）：

- 普通文字按**完整文本**匹配，键必须与程序传入的字符串逐字节一致
- 兼容首尾空白（自动 strip）、末尾冒号/省略号
- 兼容内部连续空白与换行（自动压成单空格），并对带换行前缀的键预存了压缩别名
- HTML 按文本节点匹配，不会替换标签与 URL

**不要把代码标识符当成文案翻译**（`ADC1`、`PA0`、`AF7`、`SYSCLK` 这类要保留原文），
也不要在译文中添加 HTML 标记。缩写请展开，例如 `MMC` 写成 `MMC 多媒体卡`。

词库末尾/中部有若干 `# ──` 开头的注释块用于分组，删改词条时保留它们不会影响加载。

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
agent/                    Java agent、bootstrap 翻译器与诊断功能
translations/             UTF-8 中文词库（18,283 条）
tools/                    JDK 定位、构建、验证、打包、字符串提取
tools/filter_trace.py     运行时记录 → 待翻译清单的筛选工具
docs/                     实现说明、验证范围与脱敏截图
docs/trace-and-filter.md  记录与筛选的完整流程说明
launcher.py               图形启动器与 CLI
VERSION                   发布版本
```

实现细节见 [架构说明](docs/architecture.md)。工具在测量/绘制路径进行翻译，不替换原控件文本与按钮命令；搜索、复制和无障碍接口仍可能使用英文，快捷键沿用原版键位。

`tools/filter_trace.py` 可单独使用：

```powershell
python tools/filter_trace.py "%LOCALAPPDATA%/CubeMX-CN/logs" \
    --dictionary translations/zh_CN.tsv --format md --output 待翻译清单.md
```

它把记录筛成五段清单，滤掉型号、引脚名、数值单位、代码片段、已是译文的条目等噪声，
并在末尾打印每一类被滤掉的数量。

仓库与发布包不包含 ST 的可执行文件、插件、数据库或 JRE。STM32CubeMX 是 STMicroelectronics 的产品，本项目与其没有隶属或背书关系。
