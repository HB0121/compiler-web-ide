from pathlib import Path
import subprocess
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
AUDIO = Path(r"D:/Users/28197/Downloads/编译原理课设.m4a")
FFMPEG = Path(
    r"C:/Users/28197/AppData/Local/Microsoft/WinGet/Packages/"
    r"Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/"
    r"ffmpeg-8.1.1-full_build/bin/ffmpeg.exe"
)
FFPROBE = FFMPEG.with_name("ffprobe.exe")
OUT_DIR = ROOT / "outputs" / "share_video"
FRAME_DIR = OUT_DIR / "frames"
OUT_MP4 = OUT_DIR / "编译原理课设申优分享.mp4"

W, H = 1920, 1080
FONT = Path(r"C:/Windows/Fonts/msyh.ttc")
BOLD_FONT = Path(r"C:/Windows/Fonts/msyhbd.ttc")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD_FONT if bold else FONT), size)


def audio_duration() -> float:
    result = subprocess.run(
        [
            str(FFPROBE),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(AUDIO),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def fit_image(img: Image.Image, box: tuple[int, int]) -> Image.Image:
    img = img.convert("RGB")
    bw, bh = box
    scale = min(bw / img.width, bh / img.height)
    size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
    return img.resize(size, Image.Resampling.LANCZOS)


def draw_wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], fnt, fill, width: int, line_gap: int = 12):
    lines = []
    for para in text.split("\n"):
        current = ""
        for ch in para:
            trial = current + ch
            if draw.textlength(trial, font=fnt) <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap


def base_canvas() -> Image.Image:
    img = Image.new("RGB", (W, H), "#f4f6fb")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 14), fill="#1f6feb")
    draw.rectangle((0, H - 12, W, H), fill="#24a148")
    return img


def add_header(draw: ImageDraw.ImageDraw, title: str, subtitle: str):
    draw.text((96, 58), title, font=font(54, True), fill="#172033")
    if subtitle:
        draw.text((100, 128), subtitle, font=font(28), fill="#546179")


def title_card(path: Path):
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw.text((128, 270), "编译原理课程设计申优分享", font=font(76, True), fill="#172033")
    draw.text((132, 380), "C-like 编译系统 · GUI 可视化 · 优化与自动机扩展", font=font(38), fill="#40506a")
    bullets = ["完整编译流程", "实时错误诊断", "LLVM IR 与目标代码", "CFG/DAG 优化", "日志正则 NFA/DFA"]
    x = 132
    y = 510
    for item in bullets:
        draw.rounded_rectangle((x, y, x + 360, y + 74), radius=18, fill="#ffffff", outline="#d7deea", width=2)
        draw.text((x + 30, y + 18), item, font=font(30, True), fill="#172033")
        y += 94
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def image_slide(path: Path, title: str, subtitle: str, image_path: Path):
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    add_header(draw, title, subtitle)

    panel = (90, 190, W - 90, H - 78)
    draw.rounded_rectangle(panel, radius=22, fill="#ffffff", outline="#d9e1ee", width=2)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((panel[0] + 10, panel[1] + 10, panel[2] + 10, panel[3] + 10), radius=22, fill=(20, 30, 50, 24))
    img = Image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)), img.convert("RGBA")).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(panel, radius=22, fill="#ffffff", outline="#d9e1ee", width=2)

    src = Image.open(image_path)
    fitted = fit_image(src, (panel[2] - panel[0] - 80, panel[3] - panel[1] - 80))
    x = panel[0] + (panel[2] - panel[0] - fitted.width) // 2
    y = panel[1] + (panel[3] - panel[1] - fitted.height) // 2
    img.paste(fitted, (x, y))
    img.save(path)


def end_card(path: Path):
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    draw.text((150, 330), "完整流程 · 可视化展示 · 扩展实现 · 测试覆盖", font=font(58, True), fill="#172033")
    draw_wrapped(
        draw,
        "项目把课程中的编译流程、错误诊断、优化、LLVM IR 和自动机应用整合成一个可演示的系统。",
        (154, 450),
        font(38),
        "#40506a",
        1360,
        18,
    )
    draw.text((154, 650), "谢谢大家", font=font(72, True), fill="#1f6feb")
    img.save(path)


def main():
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    assets = ROOT / "项目介绍"
    # Timings are aligned to the recorded narration's major pauses and the
    # compressed script structure: intro, overview, interface, pipeline,
    # diagnostics, optimization, extensions, tests, closing.
    slides = [
        ("title", "title", "", None, 13.1),
        ("structure", "项目结构与完整性", "编译器核心模块、GUI、示例、测试和输出文件形成完整工程", assets / "课程设计结构图.png", 14.9),
        ("product", "整体界面", "左侧编辑代码，右侧查看各阶段输出，底部显示实时诊断", assets / "项目成品介绍图.png", 12.5),
        ("flow", "完整编译流程", "词法、语法、语义、中间代码、解释执行与后端输出", assets / "编译流程图.png", 11.5),
        ("gui", "阶段结果可视化", "Tokens、AST、符号表、四元式和解释执行结果集中展示", assets / "GUI 界面功能标注图.png", 13.0),
        ("diagnostics", "错误诊断", "错误行标记与 Diagnostics 面板用于定位词法、语法和语义问题", assets / "GUI 界面功能标注图.png", 17.0),
        ("opt", "优化前后对比", "对比原始四元式、优化四元式和优化后的目标代码", assets / "CFG_DAG优化流程图.png", 21.0),
        ("llvm", "LLVM IR 扩展", "将中间表示转换为 LLVM IR 风格文本，贴近现代编译器后端", assets / "LLVM_IR生成流程图.png", 13.0),
        ("log", "日志正则自动机", "从日志中提取关键词，并展示 NFA 和 DFA 构造结果", assets / "日志关键词识别流程图.png", 14.0),
        ("tests", "系统测试覆盖", "覆盖词法、语法、语义、解释执行、优化、LLVM、日志和 GUI", assets / "系统测试用例表.png", 12.0),
        ("end", "end", "", None, 12.346667),
    ]

    duration = audio_duration()
    total_weight = sum(item[4] for item in slides)
    rendered = []
    for i, (name, title, subtitle, image_path, weight) in enumerate(slides, start=1):
        frame = FRAME_DIR / f"{i:02d}_{name}.png"
        if name == "title":
            title_card(frame)
        elif name == "end":
            end_card(frame)
        else:
            image_slide(frame, title, subtitle, image_path)
        rendered.append((frame, duration * weight / total_weight))

    concat = OUT_DIR / "slides.ffconcat"
    with concat.open("w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n")
        for frame, dur in rendered:
            f.write(f"file '{frame.as_posix()}'\n")
            f.write(f"duration {dur:.6f}\n")
        f.write(f"file '{rendered[-1][0].as_posix()}'\n")

    subprocess.run(
        [
            str(FFMPEG),
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-i",
            str(AUDIO),
            "-vf",
            "fps=30,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            f"{duration:.6f}",
            "-shortest",
            str(OUT_MP4),
        ],
        check=True,
    )
    print(OUT_MP4)


if __name__ == "__main__":
    main()
