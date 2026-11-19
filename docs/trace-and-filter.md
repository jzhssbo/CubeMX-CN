# 界面文字记录与缺口筛选

给不常用主流芯片的人用：用你自己的芯片跑一遍界面，导出一份干净的「还需翻译」清单，交给任何 AI 或自己翻。

## 一、为什么需要这个

词库是按作者自己的芯片（F1/F4 等）攒起来的。你用的是 C8T6、RCT6 之外的型号，界面上就会有一部分仍是英文。手工翻界面找漏翻既慢又容易漏。

启动器可以把「界面实际画出来的每一个字符串」记录下来，再筛掉噪声，只留下真正缺的。

## 二、记录（两步）

1. 打开 `CubeMX-CN.exe`，勾选 **「记录界面显示过的文字（用于补充词库，不影响使用）」**，勾选状态会被记住。
2. 点「启动中文版」，**正常使用 CubeMX，把你在意的页面点一遍**，然后**点右上角 × 正常关闭**。

> 必须正常关闭。追踪数据在进程退出时才写盘，用任务管理器强杀会丢这一轮。

每次启动生成一个独立文件，互不覆盖：

```
%LOCALAPPDATA%\CubeMX-CN\logs\trace-<时间戳>.tsv
```

格式为 `命中(0/1)<TAB>原始文本<TAB>译文`。

命令行等价写法：

```bash
python launcher.py --launch D:/STM32CubeMX --trace
```

## 三、筛选（一条命令）

```bash
python tools/filter_trace.py logs/ --dictionary translations/zh_CN.tsv
```

也可以直接指定单个文件，或指定输出位置与格式：

```bash
# 导出为 TSV（英文<TAB>，适合直接追加进词库）
python tools/filter_trace.py logs/ --dictionary translations/zh_CN.tsv \
    --format tsv --output gaps.tsv

# 导出为 Markdown（适合贴给 AI）
python tools/filter_trace.py logs/ --dictionary translations/zh_CN.tsv \
    --format md --output gaps.md
```

`--include-truncated` 会额外列出「已翻译但界面显示被裁切」的条目，它们不是词库缺口。

## 四、会筛掉什么

脚本按类别丢弃噪声，并在结束时打印各类数量：

| 丢弃类别 | 例子 | 理由 |
|---|---|---|
| `skip-part-number` | `STM32C011F4P6` | 型号不译 |
| `skip-pin-row` / `skip-pin-name` | `(23)-PA0-WKUP : Reset_State`、`PH1-OSC_OUT` | 引脚名不译 |
| `skip-measurement` | `72 MHz`、`3400.0 mAh`、`100Mbps (IEEE 1588)` | 数值单位 |
| `skip-clock-fragment` | `* N`、`/ M` | 时钟树分频符号 |
| `skip-cpu-core` | `Arm Cortex-M4` | 内核型号 |
| `skip-spec-row` | `ADC 12-bit (channels)` | 外设规格行 |
| `skip-version` | `BLE 5.2`、`USB 2.0` | 版本号 |
| `skip-acronym` / `skip-known-name` | `ADC`、`SPI`、`FIFO` | 规范保留原文 |
| `skip-code` / `skip-filename` | `int main()`、`launch.py` | 代码与文件名 |
| `skip-already-translated` | `导出 (Export)` | 已是译文（避免重复翻译） |
| `skip-shortcut` | `Ctrl+S` | 快捷键 |

保留下来的是 `gap-phrase`（多词短语）、`gap-word`（单个普通英文词）与 `review-truncated`。

## 五、拿到清单之后

对每一条按词库既有格式补：

```
English original<TAB>中文 (English original)
```

实例名与引脚名不必加英文括注，写成：

```
USB_OTG_FS<TAB>USB_OTG_FS（通用串行总线 OTG 全速）
```

补完直接覆盖 `translations/zh_CN.tsv`，重启 CubeMX 生效。启动日志里
`Dictionary entries=<条数>` 应与文件实际条数一致。

## 六、已知限制

- 只记录**被绘制过**的文字。没点到的页面不会出现，所以要点全。
- 界面按像素裁切的长文本会以省略号形式出现，这类是排版问题，加词条解决不了。
- 筛选基于模式匹配，仍会有少量误判；建议对着清单快速扫一遍再翻。
- 词库键必须与软件内字符串**逐字节一致**（含 ST 的拼写错误与多余空格），否则不生效。
