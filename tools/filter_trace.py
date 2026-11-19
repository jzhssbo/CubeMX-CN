"""Turn a runtime trace into a short list of strings that still need translation.

The launcher can record every string the renderer actually received
(``-Dcubemx.cn.trace=<file>``, or the checkbox in the GUI). A raw trace is mostly
noise: pin names, MCU part numbers, capacities, code fragments. This tool drops
those and keeps only what plausibly belongs in ``translations/zh_CN.tsv``.

Usage:
    python tools/filter_trace.py trace.tsv --dictionary translations/zh_CN.tsv
    python tools/filter_trace.py trace.tsv --format tsv --output gaps.tsv
    python tools/filter_trace.py logs/ --dictionary translations/zh_CN.tsv

Exit codes: 0 found gaps, 1 nothing to add, 2 bad input.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Pin configuration vocabulary. Anything matching stays in the pin section even if it
# looks like an ordinary phrase, because pin labels are the highest-value target.
PIN_CONTEXT = re.compile(
    r"\b(GPIO|Pin|Pins|Signal|Signals|WKUP|NRST|BOOT0?|VBAT|VDD|VSS|VCAP|VDDA|VSSA)\b"
    r"|^(Input|Output|Analog|Alternate)\b"
    r"|\b(pull-up|pull-down|Push Pull|Open Drain|Speed|Mode|Label|Assignment)\b",
    re.I,
)

# Clock-tree vocabulary. Lower priority than pin configuration.
CLOCK_CONTEXT = re.compile(
    r"\b(Prescaler|Mux|Clock|Clocks|PLL|HCLK|PCLK|SYSCLK|AHB|APB|HSE|HSI|LSE|LSI|MSI|"
    r"MCO|Divider|MHz|KHz|VCO|PLLCLK|PLLI2S|CSS)\b",
    re.I,
)

# A trace row is: hit<TAB>original<TAB>translated
CJK = re.compile(r"[\u4e00-\u9fff]")

# Part numbers, order codes, package names: never translated.
CHIP = re.compile(
    r"^(STM32[A-Z0-9][A-Za-z0-9_\-]*"
    r"|FP-[A-Z0-9\-]+|I-CUBE-[A-Za-z0-9\-]+|X-CUBE-[A-Za-z0-9\-]+"
    r"|STM32[0-9A-Za-z]*[A-Z]{2}[0-9A-Z]*)$"
)
# Package / component identifiers that contain hyphens: AIROC-Wi-Fi-Bluetooth-STM32
COMPONENT = re.compile(r"^[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+){2,}$")
# Pin table rows: (23)-PA0-WKUP : Reset_State
PIN_ROW = re.compile(r"^\(\d+\)-(?P<pin>[A-Za-z0-9_\-/]+) ?: ?(?P<state>[A-Za-z_]+)$")
# Bare pin / power names
PIN_NAME = re.compile(r"^(P[A-Z]\d{1,2}([-_][A-Za-z0-9_\-]+)?|V(DD|SS|BAT|CAP|REF|DDA)[A-Z0-9_]*|NRST)$")
# Keyboard shortcuts
SHORTCUT = re.compile(r"^(Ctrl|Alt|Shift|Esc|Del|Tab|F\d{1,2})([-+].*)?$")
# Measurements: 72 MHz, 3400.0 mAh, 25°C / 3.3V, 0.08 %/month, 1 ms / 98.47 °C
MEASURE = re.compile(
    r"^[\d.,]+[\d.,\s]*\s*(MHz|KHz|Hz|GHz|[kKmMgG]?Bytes?|kB|MB|GB|%|mA|µA|uA|nA|V|mV|mAh|"
    r"ms|us|ns|s|°C|dB|bpp|kbps|Mbps|Gbps|DMIPS|%\)?|/month|days?)"
    r"[\d.,\s/°A-Za-z%]*$",
    re.I,
)
# Ranges: 4-26 MHz, 0-1000 KHz
RANGE = re.compile(r"^[\d.]+\s*[-~]\s*[\d.]+\s*[A-Za-z/]*$")
# Code: braces, operators, C keywords, function calls
CODE = re.compile(r"[{};=<>]|\(\*|->|\b(int|void|static|return|define|typedef|struct|sizeof)\b")
# File names
FILENAME = re.compile(r"^[-_.\w/\\]+\.(c|h|java|xml|json|txt|ioc|zip|jar|properties|md|png|svg|pdf)$", re.I)
# Internal identifiers: single token with underscore, camelCase with digits
IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9]*(_[A-Za-z0-9]+)+$")
# Markup noise
HTML_ENTITY = re.compile(r"&[a-z]+;|&#\d+;")
# Placeholders from Java string concatenation
PLACEHOLDER = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]|\\n|\\t|\\r|%[sd]|\{\d+\}")

# Single words that are technical names by policy; keep, do not translate.
KEEP_WORDS = {
    "ADF", "ASK", "AWU", "CAD", "CAN", "CEC", "CRC", "CSE", "ECC", "FPU", "HAL", "HCD",
    "HSE", "HSI", "HSP", "LSE", "LSI", "MDF", "MMC", "NOR", "OOK", "PCC", "PCD", "PWM",
    "RAM", "ROM", "RSA", "RUN", "SIP", "STOP", "SLEEP", "TRNG", "NAND", "SRAM", "SDRAM",
    "EEPROM", "QSPI", "LWIP", "FATFS", "SMBUS", "HMAC", "DMIPS", "ECDSA", "SYSCLK",
    "PLLCLK", "PLLI2S", "LVDS", "CcmRam", "Cordic", "Flash", "ANALOG", "Aliro", "Matter",
    "CMake", "EWARM", "LQFP", "UQFN", "TFBGA", "UFBGA", "VFBGA", "WLCSP", "EWLCSP",
    "LFBGA", "VQFPN", "TSSOP", "NRND", "PLAY", "SHA-1", "SHA-2", "SHA-3", "Bypass",
    "LoRa", "eMMC", "SigFox", "USB", "JTAG", "SWD", "PLL", "ADC", "DAC", "DMA", "RTC",
    "RCC", "GPIO", "SPI", "I2C", "I2S", "SAI", "UART", "USART", "TIM", "LPTIM", "COMP",
    "OPAMP", "ETH", "FMC", "FSMC", "JPEG", "DSI", "LTDC", "DCMI", "PSSI", "MDMA",
    "BDMA", "GPDMA", "HPDMA", "LPDMA", "SDMMC", "SDIO", "RNG", "AES", "DES", "PKA",
    "SAES", "GTZC", "TZSC", "RIF", "HSEM", "IPCC", "DFSDM", "OCTOSPI", "XSPI", "QUADSPI",
    "LPTIM", "USBH", "USB2PHY1", "USB2PHY2",
}

# Words that, on their own, are still worth translating (ordinary English nouns).
COMMON_WORDS = re.compile(
    r"^(Capacity|Duration|Consumption|Generator|Interface|Preview|Proposal|Restricted|"
    r"Obsolete|Commercial|Evaluation|Ambient|Change|Match|Banner|Warning|Error|Help|"
    r"Cancel|Apply|Reset|Search|Filter|Version|Package|Firmware|Component|Software|"
    r"Hardware|Board|Project|Device|Memory|Clock|Power|Mode|Enable|Disable)$"
)


def classify(text: str, translated_values: set[str]) -> str:
    """Return a bucket name for one original string."""
    s = text
    core = s.strip()

    if not core:
        return "skip-blank"
    if PLACEHOLDER.search(s) or "\n" in s or "\t" in s:
        return "skip-multiline"
    if len(core) <= 2:
        return "skip-short"
    if HTML_ENTITY.search(s):
        return "skip-markup"
    if SHORTCUT.match(core):
        return "skip-shortcut"
    if PIN_ROW.match(core):
        return "skip-pin-row"
    if PIN_NAME.match(core):
        return "skip-pin-name"
    if CHIP.match(core):
        return "skip-part-number"
    if MEASURE.match(core) or RANGE.match(core):
        return "skip-measurement"
    if CODE.search(core):
        return "skip-code"
    if FILENAME.match(core):
        return "skip-filename"
    if re.match(r"^Project\s*\d+$", core):
        return "skip-user-name"
    if not re.search(r"[A-Za-z]", core):
        return "skip-no-english"
    if core in translated_values:
        # Already the output of a previous translation pass.
        return "skip-already-translated"
    if CJK.search(core):
        return "review-truncated" if ("..." in core or "\u2026" in core) else "skip-mixed-cjk-only"

    # --- noise patterns seen in real traces ---
    # Clock-tree arithmetic fragments: "* N", "/ M", "x 2"
    if re.fullmatch(r"[*/+\-x]\s*[A-Za-z0-9]+", core):
        return "skip-clock-fragment"
    # Bare clock/MCO label fragments: "(MHz) MCO1"
    if re.match(r"^\((MHz|KHz|Hz)\)", core):
        return "skip-clock-label"
    # Numbered instruction steps: "1/ Press", "2/ See Chapter..."
    if re.match(r"^\d+\s*/", core):
        return "skip-step-fragment"
    # CPU core designators: Arm Cortex-M4, Cortex-A35
    if re.match(r"^(Arm\s+)?Cortex-[A-Z]\d{1,2}(\+|\+M\d)?$", core):
        return "skip-cpu-core"
    # Peripheral capability rows: "ADC Total (converters)", "ADC 12-bit (channels)"
    if re.match(r"^[A-Z][A-Za-z0-9]*\s+(Total|[\d]+-bit)\b.*\((channels|converters)\)$", core):
        return "skip-spec-row"
    # Bus/throughput figures: "100Mbps (IEEE 1588)"
    if re.match(r"^[\d.]+(Mbps|Gbps|kbps)\b", core):
        return "skip-measurement"
    # Standards/version tags: "BLE 5.2", "PCIe Gen2", "USB 2.0"
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9\-]*\s+(Gen)?[\d.]{1,4}", core):
        return "skip-version"

    if re.fullmatch(r"[A-Z0-9_\-/.]{1,8}", core):
        return "skip-acronym"
    if IDENTIFIER.match(core):
        return "skip-identifier"
    if COMPONENT.match(core):
        return "skip-component"
    if core in KEEP_WORDS:
        return "skip-known-name"
    # Sentence fragments that start with punctuation only make sense inside a paragraph.
    if core[0] in ":,;)]":
        return "skip-fragment"

    words = core.split()
    if len(words) >= 2:
        # Multi-word: mostly UI phrases, but drop pure spec rows like "ADC 12-bit (channels)".
        if re.fullmatch(r"[A-Za-z0-9]+[\s\-]?[\d]+-?bit.*", core):
            return "skip-spec-row"
        # Instruction sentences that describe a whole paragraph are poor translation targets
        # and usually belong to clipped help text.
        if len(core) > 140:
            return "skip-long-prose"
        return "gap-phrase"
    if COMMON_WORDS.match(core):
        return "gap-word"
    if re.fullmatch(r"[A-Za-z]{2,}", core):
        return "gap-word"
    return "skip-other"


def read_trace(path: Path) -> list[tuple[str, str, str, str]]:
    """Rows are hit / original / translated, with an optional widget-kind column."""
    rows = []
    with path.open(encoding="utf-8") as handle:
        header = handle.readline()
        if "hit" not in header or "original" not in header:
            raise ValueError(f"{path.name} does not look like a trace file (missing header)")
        has_kind = "kind" in header
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3:
                kind = parts[3] if (has_kind and len(parts) >= 4) else "unknown"
                rows.append((parts[0], parts[1], parts[2], kind))
    return rows


def load_dictionary(path: Path | None) -> tuple[dict[str, str], set[str]]:
    entries: dict[str, str] = {}
    if path is not None and path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.replace("\ufeff", "")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) == 2 and parts[0] and parts[1]:
                entries[parts[0]] = parts[1]
    translated = set(entries.values())
    translated |= {value.strip() for value in entries.values()}
    return entries, translated


def collect(paths: list[Path], entries: dict[str, str], translated: set[str]):
    """Group gaps into the three areas that must never be dropped, plus the rest.

    Pin configuration outranks the clock tree: a pin-table row such as
    ``(10)-VLXSMPS : Power`` carries a translatable state word, so the row is
    split and only the state is checked instead of discarding the whole line.
    """
    groups: dict[str, dict[str, str]] = {
        "pin": {}, "clock": {}, "combo": {}, "other": {},
    }
    buckets: dict[str, int] = {}
    seen = 0

    for path in paths:
        for hit, original, _translated, kind in read_trace(path):
            seen += 1
            if hit == "1":
                continue
            if original in entries:
                continue

            # A pin-table row: keep the state word, drop the pin name.
            row = PIN_ROW.match(original.strip())
            if row:
                state = row.group("state").strip()
                buckets["pin-row-split"] = buckets.get("pin-row-split", 0) + 1
                if state in entries or state in translated:
                    continue
                bucket = classify(state, translated)
                buckets[bucket] = buckets.get(bucket, 0) + 1
                if bucket in ("gap-phrase", "gap-word", "review-truncated"):
                    groups["pin"].setdefault(state, bucket)
                continue

            bucket = classify(original, translated)
            buckets[bucket] = buckets.get(bucket, 0) + 1
            if bucket not in ("gap-phrase", "gap-word", "review-truncated"):
                continue

            area = area_of(original, kind)
            groups[area].setdefault(original.strip(), bucket)

    return groups, buckets, seen


def area_of(text: str, kind: str) -> str:
    """Decide which of the four output sections a string belongs to."""
    core = text.strip()
    # A long sentence is prose, not a pin label, even when it mentions pins in passing.
    if len(core) > 60:
        return "other"
    if PIN_CONTEXT.search(core):
        return "pin"
    if CLOCK_CONTEXT.search(core):
        return "clock"
    if kind in ("combo", "list"):
        return "combo"
    return "other"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("trace", type=Path, nargs="+", help="trace .tsv file(s) or a directory")
    parser.add_argument("--dictionary", type=Path, help="current translations/zh_CN.tsv")
    parser.add_argument("--format", choices=("text", "tsv", "md"), default="text",
                        help="text: read-only list, tsv: English<TAB>Chinese placeholder, md: markdown")
    parser.add_argument("--output", type=Path, help="write to this file instead of stdout")
    parser.add_argument("--include-truncated", action="store_true",
                        help="also list entries whose Chinese is already translated but clipped")
    args = parser.parse_args()

    paths: list[Path] = []
    for item in args.trace:
        if item.is_dir():
            paths.extend(sorted(item.glob("*trace*.tsv")))
        elif item.is_file():
            paths.append(item)
        else:
            print(f"not found: {item}", file=sys.stderr)
            return 2
    if not paths:
        print("no trace files", file=sys.stderr)
        return 2

    entries, translated = load_dictionary(args.dictionary)
    groups, buckets, seen = collect(paths, entries, translated)

    if not args.include_truncated:
        for name in groups:
            groups[name] = {k: v for k, v in groups[name].items() if v != "review-truncated"}

    sections = [
        ("pin", "一、引脚配置（优先，全部保留）"),
        ("clock", "二、时钟树"),
        ("combo", "三、下拉/列表选项"),
        ("other", "四、其余界面文案"),
    ]
    total = sum(len(groups[name]) for name, _ in sections)

    def entry_lines(name: str) -> list[str]:
        out = []
        for text, bucket in sorted(groups[name].items()):
            clipped = bucket == "review-truncated"
            if args.format == "md":
                out.append(f"- `{text}`" + ("　_（界面显示被裁切）_" if clipped else ""))
            elif args.format == "tsv":
                out.append(f"{text}\t")
            else:
                out.append(text + ("  [clipped]" if clipped else ""))
        return out

    lines: list[str] = []
    if args.format == "md":
        lines.append("# 待翻译清单")
        lines.append("")
        lines.append(f"来源：{len(paths)} 份记录、{seen} 条界面文字。候选合计 **{total}** 条。")
        lines.append("")
        lines.append("按 `中文 (English original)` 格式翻译；实例名与引脚名保留原文，")
        lines.append("写成 `原名（中文注释）`。引脚配置优先级最高，请优先处理。")
        lines.append("")
        for name, title in sections:
            items = entry_lines(name)
            if not items:
                continue
            lines.append(f"## {title}（{len(items)} 条）")
            lines.append("")
            lines.extend(items)
            lines.append("")
    else:
        for name, title in sections:
            items = entry_lines(name)
            if not items:
                continue
            if args.format == "text":
                lines.append(f"### {title}（{len(items)} 条）")
            lines.extend(items)

    body = "\n".join(lines) + ("\n" if lines else "")
    if args.output:
        # Explicit LF: the dictionary and trace files must stay LF on Windows too.
        with args.output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
        print(f"wrote {total} entries to {args.output}", file=sys.stderr)
        for name, _ in sections:
            print(f"  {name:<8} {len(groups[name])}", file=sys.stderr)
    else:
        # Avoid CRLF translation on Windows consoles and in redirected files.
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
        sys.stdout.write(body)

    skipped = {k: v for k, v in buckets.items() if k.startswith("skip-")}
    if skipped:
        print("\n--- filtered out ---", file=sys.stderr)
        for name, count in sorted(skipped.items(), key=lambda kv: -kv[1]):
            print(f"  {name:<28} {count}", file=sys.stderr)

    return 0 if ordered else 1


if __name__ == "__main__":
    raise SystemExit(main())
