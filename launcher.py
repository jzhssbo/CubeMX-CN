"""CubeMX-CN desktop launcher. All launch arguments use lists; installation is read-only."""
from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import zipfile
from windows_paths import jvm_path, prepare_agent

APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
BUNDLE = APP_ROOT if (APP_ROOT / "cubemx-cn-agent.jar").exists() else APP_ROOT / "dist/CubeMX-CN"
STATE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "CubeMX-CN"
MAIN_CLASS = "com.st.microxplorer.maingui.STM32CubeMX"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def validate_dictionary(path: Path) -> int:
    entries: dict[str, str] = {}
    for index, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 2 or not all(fields):
            raise ValueError(f"词典第 {index} 行格式错误：需要英文、制表符、中文。")
        key, value = fields
        if key in entries and entries[key] != value:
            raise ValueError(f"词典第 {index} 行与已有词条冲突：{key}")
        entries[key] = value
    if not entries:
        raise ValueError("词典为空。")
    return len(entries)


def inspect_install(folder: Path) -> dict:
    folder = folder.expanduser().resolve()
    executable = folder / "STM32CubeMX.exe"
    java = folder / "jre/bin/java.exe"
    if not executable.is_file() or not java.is_file():
        raise ValueError("请选择传统版 STM32CubeMX 安装目录，需包含 STM32CubeMX.exe 和 jre 文件夹。")
    try:
        with zipfile.ZipFile(executable) as archive:
            manifest = archive.read("META-INF/MANIFEST.MF").decode("utf-8")
            if f"Main-Class: {MAIN_CLASS}" not in manifest:
                raise ValueError("此安装包不是受支持的传统版 STM32CubeMX。")
            properties = archive.read("META-INF/maven/com.st.microxplorer/mcu/pom.properties").decode("utf-8")
    except (zipfile.BadZipFile, KeyError) as error:
        raise ValueError("无法识别此 STM32CubeMX 安装包；请勿选择 CubeMX2。") from error
    version_match = re.search(r"^version=(.+)$", properties, re.M)
    release = (folder / "jre/release").read_text(encoding="utf-8")
    java_match = re.search(r'^JAVA_VERSION="([^"]+)"', release, re.M)
    java_version = java_match.group(1) if java_match else "unknown"
    if java_version.split(".")[0] != "21":
        raise ValueError(f"此版汉化层仅支持 Java 21；当前运行时为 {java_version}。")
    return {"installation": str(folder), "component_version": version_match.group(1).strip() if version_match else "unknown",
            "java_version": java_version, "executable": str(executable), "java": str(java)}


def detect_installations() -> list[Path]:
    candidates: list[Path] = []
    config = STATE / "settings.json"
    try:
        candidates.append(Path(json.loads(config.read_text(encoding="utf-8"))["installation"]))
    except (OSError, ValueError, KeyError):
        pass
    if sys.platform == "win32":
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for root in (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                         r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"):
                try:
                    with winreg.OpenKey(hive, root) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                with winreg.OpenKey(key, winreg.EnumKey(key, i)) as entry:
                                    name = winreg.QueryValueEx(entry, "DisplayName")[0]
                                    if name != "STM32CubeMX":
                                        continue
                                    try:
                                        location = winreg.QueryValueEx(entry, "InstallLocation")[0]
                                        if location:
                                            candidates.append(Path(location))
                                    except OSError:
                                        pass
                                    try:
                                        uninstall = winreg.QueryValueEx(entry, "UninstallString")[0]
                                        match = re.search(r'"([^\"]+)"', uninstall)
                                        path = Path(match.group(1) if match else uninstall)
                                        if path.parent.name.lower() == "uninstaller":
                                            candidates.append(path.parent.parent)
                                    except OSError:
                                        pass
                            except OSError:
                                continue
                except OSError:
                    continue
    candidates.extend([Path("D:/STM32CubeMX"), Path("C:/ST/STM32CubeMX"),
                       Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "STMicroelectronics/STM32Cube/STM32CubeMX"])
    result: list[Path] = []
    for path in candidates:
        path = path.resolve()
        if path not in result and (path / "STM32CubeMX.exe").is_file():
            result.append(path)
    return result


def java_options(folder: Path) -> list[str]:
    ini = folder / "STM32CubeMX.l4j.ini"
    if not ini.exists():
        return []
    options: list[str] = []
    for line in ini.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("--add-exports ", "--add-opens ")):
            flag, value = line.split(None, 1)
            options.extend([flag, value])
        elif line.startswith("-"):
            options.append(line)
        else:
            raise ValueError(f"无法识别原版启动选项：{line}")
    return options


def launch(folder: Path, chinese: bool = True, capture: Path | None = None,
           dictionary: Path | None = None, project: Path | None = None,
           trace: bool = False) -> tuple[subprocess.Popen, Path, dict]:
    info = inspect_install(folder)
    folder = Path(info["installation"])
    STATE.mkdir(parents=True, exist_ok=True)
    logs = STATE / "logs"
    logs.mkdir(exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    log_path = logs / f"cubemx-{stamp}.log"
    command = [info["java"], *java_options(folder)]
    if chinese:
        dictionary = (dictionary or BUNDLE / "translations/zh_CN.tsv").resolve()
        info["dictionary_entries"] = validate_dictionary(dictionary)
        for name in ("cubemx-cn-agent.jar", "cubemx-cn-bootstrap.jar"):
            if not (BUNDLE / name).is_file():
                raise ValueError(f"汉化文件缺失：{BUNDLE / name}。请完整解压发布包。")
        runtime, runtime_dictionary = prepare_agent(BUNDLE, dictionary)
        command.extend([f"-javaagent:{jvm_path(runtime / 'cubemx-cn-agent.jar')}", f"-Dcubemx.cn.dictionary={jvm_path(runtime_dictionary)}"])
        if capture:
            command.append(f"-Dcubemx.cn.capture={capture.resolve()}")
        if trace:
            # One file per session so several days of use do not overwrite each other.
            trace_path = logs / f"trace-{stamp}.tsv"
            command.append(f"-Dcubemx.cn.trace={trace_path}")
            info["trace"] = str(trace_path)
    command.extend(["-jar", info["executable"]])
    if project is not None:
        if project.suffix.lower() != ".ioc" or not project.is_file():
            raise ValueError("工程参数必须指向已存在的 .ioc 文件。")
        command.append(str(project.resolve()))
    with Path(info["executable"]).open("rb") as source:
        info["exe_sha256"] = hashlib.file_digest(source, "sha256").hexdigest()
    info["mode"] = "zh_CN" if chinese else "original"
    info["command"] = command
    metadata = log_path.with_suffix(".json")
    metadata.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    (STATE / "settings.json").write_text(json.dumps({"installation": str(folder)}, ensure_ascii=False), encoding="utf-8")
    # Use only this child process's command line. No installation or system environment writes.
    with log_path.open("wb") as output:
        process = subprocess.Popen(command, cwd=folder, stdout=output, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)
    info["pid"] = process.pid
    try:
        metadata.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass  # The process is already running; never misreport it as a failed launch.
    return process, log_path, info


def wait_ready(process: subprocess.Popen, log: Path, timeout: float = 12) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"STM32CubeMX 启动失败（退出码 {process.returncode}）。\n日志：{log}")
        if "[CubeMX-CN] READY" in log.read_text(encoding="utf-8", errors="replace"):
            return True
        time.sleep(0.2)
    raise RuntimeError(f"尚未确认汉化层加载成功，请检查日志。\n日志：{log}")


def gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    root.title("CubeMX-CN · STM32CubeMX 汉化启动器")
    root.geometry("760x510")
    root.minsize(680, 480)
    root.configure(bg="#f3f6fb")
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background="#f3f6fb")
    style.configure("TLabel", background="#f3f6fb", foreground="#29334b", font=("Microsoft YaHei UI", 10))
    style.configure("Title.TLabel", font=("Microsoft YaHei UI", 24, "bold"), foreground="#172e54")
    style.configure("Sub.TLabel", foreground="#53637e")
    style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(15, 10))
    style.configure("Primary.TButton", background="#1169d3", foreground="white")
    style.map("Primary.TButton", background=[("active", "#0c54ac")])
    # The clam theme draws a cross for "selected", which reads as "off" on Windows.
    # Replace both indicator states with check marks drawn here, so the control looks
    # native and cannot be misread.
    def _indicator(checked: bool) -> tk.PhotoImage:
        size = 16
        image = tk.PhotoImage(width=size, height=size)
        image.put("#ffffff", to=(0, 0, size, size))          # clear canvas
        image.put("#c8d2e0", to=(0, 0, size, 1))              # top border
        image.put("#c8d2e0", to=(0, size - 1, size, size))     # bottom border
        image.put("#c8d2e0", to=(0, 0, 1, size))              # left border
        image.put("#c8d2e0", to=(size - 1, 0, size, size))     # right border
        if checked:
            for x, y in ((3, 8), (4, 9), (5, 10), (6, 9), (7, 8), (8, 7), (9, 6), (10, 5), (11, 4)):
                image.put("#1169d3", to=(x, y, x + 2, y + 2))
        return image
    _checked_icon = _indicator(True)
    _unchecked_icon = _indicator(False)
    style.element_create("CubemxCn.Indicator", "image", _unchecked_icon,
                         ("selected", _checked_icon), sticky="", padding=(2, 2))
    style.layout("CubemxCn.TCheckbutton", [
        ("Checkbutton.padding", {"sticky": "nswe", "children": [
            ("CubemxCn.Indicator", {"side": "left", "sticky": ""}),
            ("Checkbutton.focus", {"side": "left", "sticky": "w", "children": [
                ("Checkbutton.label", {"sticky": "nswe"}),
            ]}),
        ]}),
    ])
    style.configure("CubemxCn.TCheckbutton", background="#f3f6fb",
                    font=("Microsoft YaHei UI", 10), foreground="#29334b")
    body = ttk.Frame(root, padding=30)
    body.pack(fill="both", expand=True)
    ttk.Label(body, text="CubeMX-CN", style="Title.TLabel").pack(anchor="w")
    ttk.Label(body, text="让熟悉的 STM32 开发工具，说中文。", style="Sub.TLabel").pack(anchor="w", pady=(4, 25))
    ttk.Label(body, text="STM32CubeMX 安装位置").pack(anchor="w")
    row = ttk.Frame(body)
    row.pack(fill="x", pady=(8, 8))
    installations = detect_installations()
    path = tk.StringVar(value=str(installations[0]) if installations else "")
    entry = ttk.Entry(row, textvariable=path, font=("Microsoft YaHei UI", 10))
    entry.pack(side="left", fill="x", expand=True, ipady=8)
    def browse() -> None:
        selected = filedialog.askdirectory(title="选择 STM32CubeMX 安装目录", initialdir=path.get() or None)
        if selected:
            path.set(selected)
    ttk.Button(row, text="浏览…", command=browse).pack(side="right", padx=(10, 0))
    ttk.Label(body, text="适用于传统版 STM32CubeMX / Java 21。", style="Sub.TLabel").pack(anchor="w")
    actions = ttk.Frame(body)
    actions.pack(fill="x", pady=(26, 18))
    trace_var = tk.BooleanVar(value=(STATE / "trace.flag").exists())
    trace_box = ttk.Checkbutton(body, text="记录界面显示过的文字（用于补充词库，不影响使用）",
                                variable=trace_var, style="CubemxCn.TCheckbutton")
    trace_box.pack(anchor="w", pady=(0, 6))

    def persist_trace_flag() -> None:
        try:
            STATE.mkdir(parents=True, exist_ok=True)
            flag = STATE / "trace.flag"
            if trace_var.get():
                flag.write_text("1", encoding="utf-8")
            elif flag.exists():
                flag.unlink()
        except OSError:
            pass

    trace_box.configure(command=persist_trace_flag)
    status = tk.StringVar(value="就绪。选择启动语言即可。")
    child: list[subprocess.Popen] = []
    def complete(error: Exception | None, log: Path | None, chinese: bool) -> None:
        cn.configure(state="normal"); en.configure(state="normal")
        if error:
            status.set("启动未完成，请查看错误信息。")
            messagebox.showerror("启动未完成", str(error), parent=root)
        else:
            status.set("汉化层已加载，STM32CubeMX 正在启动。" if chinese else "已启动原版 STM32CubeMX。")
    def start(chinese: bool) -> None:
        if any(p.poll() is None for p in child):
            messagebox.showinfo("STM32CubeMX 已启动", "请先关闭由本启动器打开的 STM32CubeMX，再切换语言。", parent=root)
            return
        selected = Path(path.get())
        cn.configure(state="disabled"); en.configure(state="disabled")
        status.set("正在检查安装并启动，请稍候…")
        def worker() -> None:
            try:
                process, log, info = launch(selected, chinese, trace=trace_var.get())
                child.append(process)
                if chinese:
                    wait_ready(process, log)
                else:
                    time.sleep(1)
                    if process.poll() is not None:
                        raise RuntimeError(f"STM32CubeMX 已退出，请检查日志：{log}")
                root.after(0, complete, None, log, chinese)
            except Exception as error:
                root.after(0, complete, error, None, chinese)
        threading.Thread(target=worker, daemon=True).start()
    cn = ttk.Button(actions, text="启动中文版", style="Primary.TButton", command=lambda: start(True))
    cn.pack(side="left")
    en = ttk.Button(actions, text="启动英文版", command=lambda: start(False))
    en.pack(side="left", padx=12)
    ttk.Separator(body).pack(fill="x", pady=8)
    ttk.Label(body, text="独立启动 · 原版文件保持原样\n关闭后从原版入口打开，即可恢复英文。", style="Sub.TLabel", justify="left").pack(anchor="w", pady=10)
    footer = ttk.Frame(body)
    footer.pack(fill="x", pady=(8, 0))
    def open_path(target: Path) -> None:
        try:
            os.startfile(str(target))
        except OSError as error:
            messagebox.showerror("无法打开", str(error), parent=root)
    def edit_dictionary() -> None:
        try:
            subprocess.Popen(["notepad.exe", str(BUNDLE / "translations/zh_CN.tsv")])
        except OSError as error:
            messagebox.showerror("无法打开词库", str(error), parent=root)
    ttk.Button(footer, text="编辑中文词库", command=edit_dictionary).pack(side="left")
    def open_logs() -> None:
        (STATE / "logs").mkdir(parents=True, exist_ok=True)
        open_path(STATE / "logs")
    ttk.Button(footer, text="查看日志", command=open_logs).pack(side="left", padx=12)

    def export_gaps() -> None:
        """Filter recorded traces into a translation checklist for this user's chip."""
        logs = STATE / "logs"
        traces = sorted(logs.glob("*trace*.tsv")) if logs.is_dir() else []
        if not traces:
            messagebox.showinfo(
                "还没有记录",
                "先勾选「记录界面显示过的文字」，启动中文版并用一遍界面，"
                "正常关闭 CubeMX 后再来导出。",
                parent=root)
            return
        target = filedialog.asksaveasfilename(
            title="保存待翻译清单",
            defaultextension=".md",
            initialfile="待翻译清单.md",
            filetypes=[("Markdown（便于交给 AI 翻译）", "*.md"),
                       ("TSV（可直接追加进词库）", "*.tsv"),
                       ("文本", "*.txt")],
            parent=root)
        if not target:
            return
        destination = Path(target)
        # Under PyInstaller __file__ points into a temp extraction dir, so the tools
        # folder must be resolved from _MEIPASS when frozen.
        if getattr(sys, "frozen", False):
            tools_dir = Path(getattr(sys, "_MEIPASS", APP_ROOT)) / "tools"
        else:
            tools_dir = Path(__file__).resolve().parent / "tools"
        try:
            sys.path.insert(0, str(tools_dir))
            from filter_trace import collect, load_dictionary  # noqa: PLC0415
        except Exception as error:  # pragma: no cover - packaging guard
            messagebox.showerror("筛选组件缺失", f"找不到 filter_trace 模块：{error}", parent=root)
            return
        try:
            entries, translated = load_dictionary(BUNDLE / "translations/zh_CN.tsv")
            gaps, buckets, seen = collect(traces, entries, translated)
            ordered = sorted(gaps.items())
            if destination.suffix.lower() == ".tsv":
                body = "".join(f"{text}\t\n" for text, _ in ordered)
            elif destination.suffix.lower() == ".txt":
                body = "".join(text + "\n" for text, _ in ordered)
            else:
                lines = ["# 待翻译清单", "",
                         f"来源：{len(traces)} 份记录、{seen} 条界面文字。",
                         f"候选：**{len(ordered)}** 条（已滤掉型号、引脚名、数值等噪声）。", "",
                         "按 `中文 (English original)` 格式翻译；实例名与引脚名保留原文，"
                         "写成 `原名（中文注释）`。", ""]
                for text, bucket in ordered:
                    suffix = "　_（界面显示被裁切）_" if bucket == "review-truncated" else ""
                    lines.append(f"- `{text}`{suffix}")
                body = "\n".join(lines) + "\n"
            with destination.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(body)
        except Exception as error:
            messagebox.showerror("导出失败", str(error), parent=root)
            return
        dropped = sum(n for name, n in buckets.items() if name.startswith("skip-"))
        status.set(f"已导出 {len(ordered)} 条待翻译，滤掉 {dropped} 条噪声。")
        try:
            os.startfile(str(destination.parent))
        except OSError:
            pass

    ttk.Button(footer, text="导出待翻译清单", command=export_gaps).pack(side="left", padx=12)
    ttk.Label(body, textvariable=status, style="Sub.TLabel", wraplength=650).pack(anchor="w", pady=(18, 0))
    # Size from the actual DPI-scaled widgets so the footer remains visible at 150%/200%.
    root.update_idletasks()
    width = min(max(760, root.winfo_reqwidth()), root.winfo_screenwidth() - 60)
    height = min(max(510, root.winfo_reqheight()), root.winfo_screenheight() - 80)
    root.geometry(f"{width}x{height}")
    root.minsize(width, height)
    root.mainloop()


def main() -> int:
    parser = argparse.ArgumentParser(description="STM32CubeMX 中文启动器（独立汉化层）")
    parser.add_argument("--inspect", type=Path, help="只读检查安装目录")
    parser.add_argument("--launch", type=Path, help="直接启动指定安装目录")
    parser.add_argument("--english", action="store_true", help="启动原版，不加载汉化层")
    parser.add_argument("--capture", type=Path, help="开发验证：30 秒后抓取此进程窗口，指定输出前缀")
    parser.add_argument("--dictionary", type=Path, help="指定 UTF-8 TSV 词典")
    parser.add_argument("--project", type=Path, help="启动时打开指定 .ioc 文件")
    parser.add_argument("--trace", action="store_true",
                        help="记录界面实际渲染的字符串到 logs/trace-<时间>.tsv，用于发现词库缺口")
    args = parser.parse_args()
    try:
        if args.inspect:
            result = inspect_install(args.inspect)
        elif args.launch:
            process, log, result = launch(args.launch, not args.english, args.capture,
                                          args.dictionary, args.project, args.trace)
            if not args.english:
                wait_ready(process, log)
            result["log"] = str(log)
        else:
            gui()
            return 0
        if sys.stdout:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        if sys.stderr:
            print(str(error), file=sys.stderr)
        else:
            import tkinter.messagebox
            tkinter.messagebox.showerror("CubeMX-CN", str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
