"""
DiffMovie - 動画メタデータ比較アプリ
Gradio 6 + ダークテーマ + ネオンイエロー
複数ファイル対応版
"""

import gradio as gr
from video_analyzer import (
    analyze_video,
    metadata_to_dict
)
import os
import subprocess
import tempfile
import base64
import shutil
from datetime import datetime


# カスタムCSS
CUSTOM_CSS = """
/* 全体のスタイル */
.gradio-container {
    max-width: 1600px !important;
    margin: 0 auto !important;
    padding: 0 2rem !important;
}

/* ヘッダー */
.app-header {
    text-align: center;
    padding: 1rem;
    margin-bottom: 1rem;
    border-bottom: 2px solid #EEFF00;
}

.app-header h1 {
    color: #EEFF00 !important;
    font-size: 2.5rem !important;
    margin: 0 !important;
    text-shadow: 0 0 10px rgba(238, 255, 0, 0.5);
}

.app-header p {
    color: #888 !important;
    margin-top: 0.5rem !important;
}

/* ドロップゾーン */
.drop-zone {
    border: 2px dashed #EEFF00 !important;
    border-radius: 12px !important;
    min-height: 200px !important;
    transition: all 0.3s ease !important;
}

.drop-zone:hover {
    border-color: #FFFF00 !important;
    box-shadow: 0 0 20px rgba(238, 255, 0, 0.3) !important;
}

/* ラベル */
.input-label {
    color: #EEFF00 !important;
    font-size: 1.2rem !important;
    font-weight: bold !important;
    margin-bottom: 0.5rem !important;
}

/* 比較ボタン */
.compare-btn {
    background: linear-gradient(135deg, #EEFF00 0%, #CCDD00 100%) !important;
    color: #000 !important;
    font-weight: bold !important;
    font-size: 1.1rem !important;
    padding: 12px 40px !important;
    border-radius: 8px !important;
    border: none !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}

.compare-btn:hover {
    box-shadow: 0 0 25px rgba(238, 255, 0, 0.6) !important;
    transform: translateY(-2px) !important;
}

/* 結果テーブル */
.diff-table {
    margin-top: 1rem !important;
    overflow-x: auto !important;
}

.diff-table table {
    width: 100% !important;
    border-collapse: collapse !important;
    min-width: 600px !important;
}

.diff-table th {
    background: #EEFF00 !important;
    color: #000 !important;
    padding: 12px !important;
    text-align: left !important;
    font-weight: bold !important;
    position: sticky !important;
    top: 0 !important;
}

.diff-table td {
    padding: 10px 12px !important;
    border-bottom: 1px solid #333 !important;
}

.diff-table tr:hover {
    background: rgba(238, 255, 0, 0.1) !important;
}

/* 変換サマリーボックス */
.summary-box {
    background: #1a1a1a !important;
    border: 1px solid #EEFF00 !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    font-family: 'Courier New', monospace !important;
}

.summary-box textarea {
    background: transparent !important;
    color: #EEFF00 !important;
    border: none !important;
    font-family: 'Courier New', monospace !important;
}

/* セクションタイトル */
.section-title {
    color: #EEFF00 !important;
    font-size: 1.3rem !important;
    border-left: 4px solid #EEFF00 !important;
    padding-left: 12px !important;
    margin: 1.5rem 0 1rem 0 !important;
}

/* コピーボタン */
.copy-btn {
    background: transparent !important;
    border: 1px solid #EEFF00 !important;
    color: #EEFF00 !important;
    padding: 8px 16px !important;
    border-radius: 4px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
}

.copy-btn:hover {
    background: #EEFF00 !important;
    color: #000 !important;
}

/* Footer */
.app-footer {
    text-align: center;
    padding: 1rem;
    margin-top: 2rem;
    border-top: 1px solid #333;
    color: #666;
}

/* ファイル数表示 */
.file-count {
    color: #EEFF00;
    font-size: 1rem;
    margin-top: 0.5rem;
}

/* サムネイルグリッド */
.thumbnail-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1.5rem;
    justify-content: flex-start;
}

.thumbnail-item {
    background: #1a1a1a;
    border: 2px solid #333;
    border-radius: 8px;
    padding: 0.5rem;
    text-align: center;
    transition: all 0.3s ease;
    max-width: 200px;
}

.thumbnail-item:hover {
    border-color: #EEFF00;
    box-shadow: 0 0 10px rgba(238, 255, 0, 0.3);
}

.thumbnail-item img {
    max-width: 180px;
    max-height: 120px;
    border-radius: 4px;
    object-fit: contain;
}

.thumbnail-item p {
    color: #ccc;
    font-size: 0.8rem;
    margin: 0.5rem 0 0 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
"""


# サムネイル用の一時ディレクトリ
THUMBNAIL_DIR = os.path.join(tempfile.gettempdir(), "diffmovie_thumbnails")
os.makedirs(THUMBNAIL_DIR, exist_ok=True)


def generate_thumbnail(video_path: str) -> str:
    """
    動画からサムネイルを生成してBase64エンコードされた画像を返す
    
    Args:
        video_path: 動画ファイルのパス
    
    Returns:
        str: Base64エンコードされた画像データ（data:image/jpeg;base64,...形式）
    """
    if not video_path or not os.path.exists(video_path):
        return ""
    
    # 出力ファイル名を生成
    basename = os.path.basename(video_path)
    thumb_path = os.path.join(THUMBNAIL_DIR, f"{basename}.jpg")
    
    try:
        # ffmpegでサムネイルを生成（1秒目のフレームを取得）
        cmd = [
            'ffmpeg',
            '-y',  # 上書き
            '-i', video_path,
            '-ss', '00:00:01',  # 1秒目
            '-vframes', '1',
            '-vf', 'scale=320:-1',  # 幅320pxに縮小
            '-q:v', '2',  # JPEG品質
            thumb_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # 1秒目が取得できない場合は0秒目を試す
        if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0:
            cmd[5] = '00:00:00'  # 0秒目
            subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
            with open(thumb_path, 'rb') as f:
                img_data = f.read()
            base64_data = base64.b64encode(img_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}"
    except Exception as e:
        print(f"サムネイル生成エラー: {e}")
    
    return ""


def create_thumbnails_html(files: list, thumbnails: list) -> str:
    """サムネイルグリッドのHTMLを生成"""
    if not files or not thumbnails:
        return ""
    
    html = '<div class="thumbnail-grid">'
    
    for i, (file_path, thumb_data) in enumerate(zip(files, thumbnails)):
        filename = os.path.basename(file_path) if file_path else f"ファイル{i+1}"
        short_name = filename[:25] + "..." if len(filename) > 25 else filename
        
        if thumb_data:
            img_tag = f'<img src="{thumb_data}" alt="{filename}">'
        else:
            img_tag = '<div style="width: 180px; height: 120px; background: #333; display: flex; align-items: center; justify-content: center; color: #666; border-radius: 4px;">No Preview</div>'
        
        html += f'''
            <div class="thumbnail-item">
                {img_tag}
                <p title="{filename}">{short_name}</p>
            </div>
        '''
    
    html += '</div>'
    return html


def generate_report_html(thumbnails_html: str, comparison_html: str, summary_text: str) -> str:
    """スタンドアロンのHTMLレポートを生成"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DiffMovie レポート - {timestamp}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #fff;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            padding: 20px;
            border-bottom: 2px solid #EEFF00;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #EEFF00;
            font-size: 2.5rem;
            margin: 0;
            text-shadow: 0 0 10px rgba(238, 255, 0, 0.5);
        }}
        .header p {{
            color: #888;
            margin-top: 10px;
        }}
        .section-title {{
            color: #EEFF00;
            font-size: 1.3rem;
            border-left: 4px solid #EEFF00;
            padding-left: 12px;
            margin: 30px 0 15px 0;
        }}
        .thumbnail-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        .thumbnail-item {{
            background: #1a1a1a;
            border: 2px solid #333;
            border-radius: 8px;
            padding: 0.5rem;
            text-align: center;
            max-width: 200px;
        }}
        .thumbnail-item img {{
            max-width: 180px;
            max-height: 120px;
            border-radius: 4px;
            object-fit: contain;
        }}
        .thumbnail-item p {{
            color: #ccc;
            font-size: 0.8rem;
            margin: 0.5rem 0 0 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        th {{
            background: #EEFF00;
            color: #000;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #333;
        }}
        tr:hover {{
            background: rgba(238, 255, 0, 0.1);
        }}
        .summary-box {{
            background: #1a1a1a;
            border: 1px solid #EEFF00;
            border-radius: 8px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            color: #EEFF00;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            margin-top: 30px;
            border-top: 1px solid #333;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DiffMovie</h1>
            <p>動画メタデータ比較レポート - {timestamp}</p>
        </div>
        
        <h2 class="section-title">プレビュー</h2>
        {thumbnails_html if thumbnails_html else '<p style="color: #666;">サムネイルなし</p>'}
        
        <h2 class="section-title">比較結果</h2>
        {comparison_html}
        
        <h2 class="section-title">変換サマリー</h2>
        <div class="summary-box">{summary_text if summary_text else '変換サマリーなし'}</div>
        
        <div class="footer">
            <p>DiffMovie v2.0 - Generated at {timestamp}</p>
        </div>
    </div>
</body>
</html>'''
    return html


def save_report_as_image(thumbnails_html: str, comparison_html: str, summary_text: str) -> str:
    """レポートを画像として保存（wkhtmltoimageを使用）"""
    # HTMLレポートを生成
    html_content = generate_report_html(thumbnails_html, comparison_html, summary_text)
    
    # 一時ファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 出力ディレクトリを作成
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    html_path = os.path.join(output_dir, f"report_{timestamp}.html")
    png_path = os.path.join(output_dir, f"report_{timestamp}.png")
    
    # HTMLを保存
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # wkhtmltoimageで画像に変換を試みる
    try:
        cmd = [
            'wkhtmltoimage',
            '--width', '1400',
            '--quality', '90',
            '--enable-local-file-access',
            html_path,
            png_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if os.path.exists(png_path) and os.path.getsize(png_path) > 0:
            return png_path
    except FileNotFoundError:
        # wkhtmltoimageがない場合はHTMLパスを返す
        pass
    except Exception as e:
        print(f"画像生成エラー: {e}")
    
    # 画像生成に失敗した場合はHTMLパスを返す
    return html_path


# プリセット定義
PRESETS = {
    "YouTube HD (1080p)": {
        "解像度": "1920x1080",
        "解像度（幅）": "1920",
        "解像度（高さ）": "1080",
        "映像コーデック": "h264",
        "フレームレート（fps）": "30.000",
        "映像ビットレート": "8.00 Mbps",
        "音声コーデック": "aac",
        "サンプルレート": "48000 Hz",
        "チャンネル数": "2",
        "音声ビットレート": "384.00 Kbps",
        "コンテナフォーマット": "mp4",
        "ピクセルフォーマット": "yuv420p",
    },
    "YouTube 4K": {
        "解像度": "3840x2160",
        "解像度（幅）": "3840",
        "解像度（高さ）": "2160",
        "映像コーデック": "h264",
        "フレームレート（fps）": "60.000",
        "映像ビットレート": "35.00 Mbps",
        "音声コーデック": "aac",
        "サンプルレート": "48000 Hz",
        "チャンネル数": "2",
        "音声ビットレート": "384.00 Kbps",
        "コンテナフォーマット": "mp4",
        "ピクセルフォーマット": "yuv420p",
    },
    "Twitter/X": {
        "解像度": "1280x720",
        "解像度（幅）": "1280",
        "解像度（高さ）": "720",
        "映像コーデック": "h264",
        "フレームレート（fps）": "30.000",
        "映像ビットレート": "5.00 Mbps",
        "音声コーデック": "aac",
        "サンプルレート": "44100 Hz",
        "チャンネル数": "2",
        "音声ビットレート": "128.00 Kbps",
        "コンテナフォーマット": "mp4",
        "ピクセルフォーマット": "yuv420p",
    },
    "Instagram Reels": {
        "解像度": "1080x1920",
        "解像度（幅）": "1080",
        "解像度（高さ）": "1920",
        "映像コーデック": "h264",
        "フレームレート（fps）": "30.000",
        "映像ビットレート": "3.50 Mbps",
        "音声コーデック": "aac",
        "サンプルレート": "44100 Hz",
        "チャンネル数": "2",
        "音声ビットレート": "128.00 Kbps",
        "コンテナフォーマット": "mp4",
        "ピクセルフォーマット": "yuv420p",
    },
    "TikTok": {
        "解像度": "1080x1920",
        "解像度（幅）": "1080",
        "解像度（高さ）": "1920",
        "映像コーデック": "h264",
        "フレームレート（fps）": "30.000",
        "映像ビットレート": "4.00 Mbps",
        "音声コーデック": "aac",
        "サンプルレート": "44100 Hz",
        "チャンネル数": "2",
        "音声ビットレート": "128.00 Kbps",
        "コンテナフォーマット": "mp4",
        "ピクセルフォーマット": "yuv420p",
    },
    "Apple ProRes 422": {
        "解像度": "1920x1080",
        "解像度（幅）": "1920",
        "解像度（高さ）": "1080",
        "映像コーデック": "prores",
        "フレームレート（fps）": "29.970",
        "映像ビットレート": "147.00 Mbps",
        "音声コーデック": "pcm_s24le",
        "サンプルレート": "48000 Hz",
        "チャンネル数": "2",
        "音声ビットレート": "2304.00 Kbps",
        "コンテナフォーマット": "mov",
        "ピクセルフォーマット": "yuv422p10le",
    },
}


# グローバル変数で最新の解析結果を保持
_latest_results = {
    'thumbnails_html': '',
    'comparison_html': '',
    'summary_text': '',
    'ffmpeg_commands': '',
    'all_meta_raw': [],
    'all_metadata': [],
    'filenames': [],
    'diff_count': 0,
    'total_count': 0,
    'presets_added': []
}


def generate_ffmpeg_command(source_meta, target_meta, source_path: str, output_path: str = None) -> str:
    """
    ソース動画をターゲット動画の仕様に変換するffmpegコマンドを生成
    
    Args:
        source_meta: ソース動画のメタデータ
        target_meta: ターゲット動画のメタデータ
        source_path: ソース動画のパス
        output_path: 出力パス（省略時は自動生成）
    
    Returns:
        str: ffmpegコマンド
    """
    if not source_meta or not target_meta:
        return ""
    
    if not output_path:
        base, ext = os.path.splitext(os.path.basename(source_path))
        output_path = f"{base}_converted{ext}"
    
    cmd_parts = ['ffmpeg', '-i', f'"{source_path}"']
    
    # 映像設定
    if target_meta.video:
        tv = target_meta.video
        
        # コーデック
        codec_map = {
            'h264': 'libx264',
            'hevc': 'libx265',
            'h265': 'libx265',
            'vp9': 'libvpx-vp9',
            'vp8': 'libvpx',
            'av1': 'libaom-av1',
            'prores': 'prores_ks',
        }
        codec = tv.codec_name.lower() if tv.codec_name != "N/A" else 'h264'
        encoder = codec_map.get(codec, 'libx264')
        cmd_parts.append(f'-c:v {encoder}')
        
        # 解像度
        if tv.width > 0 and tv.height > 0:
            cmd_parts.append(f'-vf "scale={tv.width}:{tv.height}"')
        
        # フレームレート
        if tv.fps != "N/A":
            try:
                fps_val = float(tv.fps)
                cmd_parts.append(f'-r {fps_val:.2f}')
            except ValueError:
                pass
        
        # ビットレート
        if tv.bit_rate != "N/A" and 'Mbps' in tv.bit_rate:
            try:
                br = float(tv.bit_rate.replace(' Mbps', ''))
                cmd_parts.append(f'-b:v {br:.1f}M')
            except ValueError:
                pass
        elif tv.bit_rate != "N/A" and 'Kbps' in tv.bit_rate:
            try:
                br = float(tv.bit_rate.replace(' Kbps', ''))
                cmd_parts.append(f'-b:v {br:.0f}K')
            except ValueError:
                pass
        
        # ピクセルフォーマット
        if tv.pix_fmt != "N/A":
            cmd_parts.append(f'-pix_fmt {tv.pix_fmt}')
    
    # 音声設定
    if target_meta.audio:
        ta = target_meta.audio
        
        # コーデック
        audio_codec_map = {
            'aac': 'aac',
            'mp3': 'libmp3lame',
            'opus': 'libopus',
            'vorbis': 'libvorbis',
            'flac': 'flac',
            'pcm_s16le': 'pcm_s16le',
            'pcm_s24le': 'pcm_s24le',
        }
        acodec = ta.codec_name.lower() if ta.codec_name != "N/A" else 'aac'
        aencoder = audio_codec_map.get(acodec, 'aac')
        cmd_parts.append(f'-c:a {aencoder}')
        
        # サンプルレート
        if ta.sample_rate != "N/A":
            cmd_parts.append(f'-ar {ta.sample_rate}')
        
        # チャンネル数
        if ta.channels > 0:
            cmd_parts.append(f'-ac {ta.channels}')
        
        # ビットレート
        if ta.bit_rate != "N/A" and 'Kbps' in ta.bit_rate:
            try:
                abr = float(ta.bit_rate.replace(' Kbps', ''))
                cmd_parts.append(f'-b:a {abr:.0f}k')
            except ValueError:
                pass
    
    cmd_parts.append(f'"{output_path}"')
    
    return ' \\\n  '.join(cmd_parts)


def generate_all_ffmpeg_commands(all_meta_raw: list, filenames: list, base_index: int = 0) -> str:
    """
    複数ファイルに対するffmpegコマンドを生成
    
    Args:
        all_meta_raw: 全ファイルのメタデータリスト
        filenames: ファイル名リスト
        base_index: 基準ファイルのインデックス
    
    Returns:
        str: 全ffmpegコマンド
    """
    if len(all_meta_raw) < 2:
        return "2つ以上の動画をアップロードするとffmpegコマンドが生成されます"
    
    base_meta = all_meta_raw[base_index]
    base_name = os.path.basename(filenames[base_index])
    
    lines = []
    lines.append("=" * 60)
    lines.append("【ffmpegコマンド】")
    lines.append(f"ターゲット仕様: {base_name}")
    lines.append("=" * 60)
    
    for i, (meta, filepath) in enumerate(zip(all_meta_raw, filenames)):
        if i == base_index:
            continue
        
        filename = os.path.basename(filepath)
        base, ext = os.path.splitext(filename)
        
        # ターゲットのフォーマットに合わせた拡張子
        if base_meta.format_name:
            format_ext_map = {
                'mp4': '.mp4',
                'mov': '.mov',
                'matroska': '.mkv',
                'webm': '.webm',
                'avi': '.avi',
            }
            for fmt, new_ext in format_ext_map.items():
                if fmt in base_meta.format_name.lower():
                    ext = new_ext
                    break
        
        output_name = f"{base}_to_{os.path.splitext(base_name)[0]}{ext}"
        
        lines.append("")
        lines.append(f"# {filename} -> {output_name}")
        lines.append(generate_ffmpeg_command(meta, base_meta, filepath, output_name))
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def create_multi_comparison_html(all_metadata: list, filenames: list, show_diff_only: bool = False) -> tuple:
    """
    複数ファイルの比較結果をHTMLテーブルとして生成
    
    Returns:
        tuple: (HTML文字列, 差分数, 全項目数)
    """
    if not all_metadata:
        return "<p>データがありません</p>", 0, 0
    
    num_files = len(all_metadata)
    
    # 全てのキーを収集
    all_keys = []
    for meta_dict in all_metadata:
        for key in meta_dict.keys():
            if key not in all_keys:
                all_keys.append(key)
    
    # 差分のある項目を事前にカウント
    diff_count = 0
    diff_keys = []
    for key in all_keys:
        values = [meta_dict.get(key, "N/A") for meta_dict in all_metadata]
        unique_values = set(str(v) for v in values)
        if len(unique_values) > 1:
            diff_count += 1
            diff_keys.append(key)
    
    total_count = len(all_keys)
    
    # フィルタリング対象のキー
    display_keys = diff_keys if show_diff_only else all_keys
    
    if not display_keys:
        return "<p style='color: #888;'>差分がある項目はありません</p>", diff_count, total_count
    
    # ヘッダー作成
    html = f"""
    <div style="overflow-x: auto;">
    <table style="width: 100%; border-collapse: collapse; font-size: 14px; min-width: {200 + num_files * 150}px;">
        <thead>
            <tr style="background: #EEFF00; color: #000;">
                <th style="padding: 12px; text-align: left; min-width: 180px; position: sticky; left: 0; background: #EEFF00;">項目</th>
    """
    
    for i, filename in enumerate(filenames):
        short_name = os.path.basename(filename) if filename else f"ファイル{i+1}"
        if len(short_name) > 20:
            short_name = short_name[:17] + "..."
        html += f'<th style="padding: 12px; text-align: left; min-width: 150px;" title="{os.path.basename(filename) if filename else ""}">{short_name}</th>'
    
    html += """
            </tr>
        </thead>
        <tbody>
    """
    
    # 各行を生成
    for key in display_keys:
        values = [meta_dict.get(key, "N/A") for meta_dict in all_metadata]
        unique_values = set(str(v) for v in values)
        is_different = len(unique_values) > 1
        
        row_style = "background: rgba(238, 255, 0, 0.1);" if is_different else ""
        
        html += f"""
            <tr style="{row_style}">
                <td style="padding: 10px 12px; border-bottom: 1px solid #333; color: #ccc; position: sticky; left: 0; background: {'#1a1a0a' if is_different else '#121212'};">{key}</td>
        """
        
        for val in values:
            val_style = "color: #EEFF00; font-weight: bold;" if is_different else "color: #fff;"
            html += f'<td style="padding: 10px 12px; border-bottom: 1px solid #333; {val_style}">{val}</td>'
        
        html += "</tr>"
    
    html += """
        </tbody>
    </table>
    </div>
    """
    
    return html, diff_count, total_count


def create_single_video_table(metadata_dict: dict, filename: str) -> str:
    """単一の動画情報をメインエリア用のHTMLテーブルとして生成"""
    if not metadata_dict:
        return "<p>動画情報がありません</p>"
    
    short_name = os.path.basename(filename) if filename else "動画"
    
    html = f"""
    <div style="margin-bottom: 1rem;">
        <h4 style="color: #EEFF00; margin-bottom: 15px; font-size: 1.2rem;">{short_name} の詳細情報</h4>
        <p style="color: #888; margin-bottom: 15px;">複数の動画を追加すると比較できます</p>
    </div>
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <thead>
            <tr style="background: #EEFF00; color: #000;">
                <th style="padding: 12px; text-align: left; width: 40%;">項目</th>
                <th style="padding: 12px; text-align: left; width: 60%;">値</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for key, value in metadata_dict.items():
        html += f"""
            <tr>
                <td style="padding: 10px 12px; border-bottom: 1px solid #333; color: #ccc;">{key}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #333; color: #fff;">{value}</td>
            </tr>
        """
    
    html += """
        </tbody>
    </table>
    """
    return html


def generate_multi_conversion_summary(all_metadata: list, all_meta_raw: list, filenames: list) -> str:
    """複数ファイルの変換サマリーを生成（最初のファイルを基準）"""
    if len(all_metadata) < 2:
        if len(all_metadata) == 1:
            return "複数の動画を追加すると変換サマリーが表示されます"
        return ""
    
    lines = []
    lines.append("=" * 60)
    lines.append("【変換サマリー】")
    lines.append(f"基準: {os.path.basename(filenames[0])}")
    lines.append("=" * 60)
    
    base_dict = all_metadata[0]
    base_raw = all_meta_raw[0]
    
    for i in range(1, len(all_metadata)):
        target_dict = all_metadata[i]
        target_raw = all_meta_raw[i]
        target_name = os.path.basename(filenames[i])
        
        lines.append("")
        lines.append(f"--- {target_name} との比較 ---")
        
        differences = []
        
        # 主要な項目を比較
        compare_items = [
            ("コンテナフォーマット", "format_name"),
            ("映像コーデック", "video.codec_name"),
            ("解像度", None),  # 特別処理
            ("フレームレート（fps）", "video.fps"),
            ("映像ビットレート", "video.bit_rate"),
            ("音声コーデック", "audio.codec_name"),
            ("サンプルレート", "audio.sample_rate"),
            ("チャンネル数", "audio.channels"),
        ]
        
        for display_name, attr_path in compare_items:
            base_val = base_dict.get(display_name, "N/A")
            target_val = target_dict.get(display_name, "N/A")
            
            if base_val != target_val:
                differences.append(f"[{display_name}] {base_val} -> {target_val}")
        
        # 解像度の特別処理
        if base_raw.video and target_raw.video:
            if base_raw.video.width != target_raw.video.width or base_raw.video.height != target_raw.video.height:
                base_res = f"{base_raw.video.width}x{base_raw.video.height}"
                target_res = f"{target_raw.video.width}x{target_raw.video.height}"
                if base_raw.video.width > 0 and target_raw.video.width > 0:
                    scale_w = target_raw.video.width / base_raw.video.width
                    scale_h = target_raw.video.height / base_raw.video.height
                    differences.append(f"[解像度] {base_res} -> {target_res} (幅{scale_w:.2f}倍, 高さ{scale_h:.2f}倍)")
        
        # ファイルサイズ比較
        if base_raw.file_size > 0 and target_raw.file_size > 0:
            ratio = target_raw.file_size / base_raw.file_size
            differences.append(f"[ファイルサイズ] {base_raw.file_size_human} -> {target_raw.file_size_human} ({ratio:.2f}倍)")
        
        if differences:
            for diff in differences:
                lines.append(diff)
        else:
            lines.append("差分なし（同一仕様）")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def analyze_multiple_videos(files):
    """
    複数の動画を解析して比較する
    
    Args:
        files: ファイルパスのリスト
    
    Returns:
        tuple: (サムネイルHTML, 比較テーブルHTML, 変換サマリーテキスト, ffmpegコマンド)
    """
    # 初期値
    thumbnails_html = ""
    comparison_html = "<p style='color: #888;'>動画ファイルをドロップしてください（複数可）</p>"
    summary_text = ""
    ffmpeg_commands = ""
    diff_info = ""
    
    # 入力チェック
    if not files:
        return thumbnails_html, comparison_html, summary_text, ffmpeg_commands, diff_info, gr.update(choices=[], value=None)
    
    # ファイルリストを正規化
    if isinstance(files, str):
        files = [files]
    
    # 各ファイルを解析
    all_metadata = []
    all_meta_raw = []
    filenames = []
    thumbnails = []
    
    for file_path in files:
        if file_path:
            meta = analyze_video(file_path)
            meta_dict = metadata_to_dict(meta)
            all_metadata.append(meta_dict)
            all_meta_raw.append(meta)
            filenames.append(file_path)
            # サムネイル生成
            thumb = generate_thumbnail(file_path)
            thumbnails.append(thumb)
    
    # 結果を生成
    if len(all_metadata) == 0:
        return thumbnails_html, comparison_html, summary_text, ffmpeg_commands, diff_info, gr.update(choices=[], value=None)
    
    # サムネイルHTML生成
    thumbnails_html = create_thumbnails_html(filenames, thumbnails)
    
    diff_count = 0
    total_count = 0
    diff_info = ""
    
    if len(all_metadata) == 1:
        # 1ファイルのみ
        comparison_html = create_single_video_table(all_metadata[0], filenames[0])
        summary_text = "複数の動画を追加すると変換サマリーが表示されます"
    else:
        # 複数ファイル比較
        comparison_html, diff_count, total_count = create_multi_comparison_html(all_metadata, filenames, False)
        summary_text = generate_multi_conversion_summary(all_metadata, all_meta_raw, filenames)
        diff_info = f"差分: {diff_count}/{total_count}項目"
    
    # ffmpegコマンド生成
    ffmpeg_commands = generate_all_ffmpeg_commands(all_meta_raw, filenames, 0)
    
    # グローバル変数に保存
    _latest_results['thumbnails_html'] = thumbnails_html
    _latest_results['comparison_html'] = comparison_html
    _latest_results['summary_text'] = summary_text
    _latest_results['ffmpeg_commands'] = ffmpeg_commands
    _latest_results['all_meta_raw'] = all_meta_raw
    _latest_results['all_metadata'] = all_metadata
    _latest_results['filenames'] = filenames
    _latest_results['diff_count'] = diff_count
    _latest_results['total_count'] = total_count
    
    # 基準ファイル選択肢を更新
    file_choices = [os.path.basename(f) for f in filenames] if filenames else []
    default_choice = file_choices[0] if file_choices else None
    
    return thumbnails_html, comparison_html, summary_text, ffmpeg_commands, diff_info, gr.update(choices=file_choices, value=default_choice)


def apply_diff_filter(show_diff_only: bool):
    """差分フィルターを適用"""
    all_metadata = _latest_results.get('all_metadata', [])
    filenames = _latest_results.get('filenames', [])
    
    if len(all_metadata) < 2:
        return _latest_results.get('comparison_html', '')
    
    comparison_html, _, _ = create_multi_comparison_html(all_metadata, filenames, show_diff_only)
    return comparison_html


def get_file_choices():
    """基準ファイル選択用の選択肢を取得"""
    filenames = _latest_results.get('filenames', [])
    if not filenames:
        return []
    return [os.path.basename(f) for f in filenames]


def update_base_file(base_file_name: str):
    """基準ファイルを変更してサマリーとffmpegコマンドを更新"""
    all_meta_raw = _latest_results.get('all_meta_raw', [])
    all_metadata = _latest_results.get('all_metadata', [])
    filenames = _latest_results.get('filenames', [])
    
    if len(all_meta_raw) < 2 or not base_file_name:
        return _latest_results.get('summary_text', ''), _latest_results.get('ffmpeg_commands', '')
    
    # 基準ファイルのインデックスを取得
    base_index = 0
    for i, f in enumerate(filenames):
        if os.path.basename(f) == base_file_name:
            base_index = i
            break
    
    # サマリーとffmpegコマンドを再生成
    summary_text = generate_multi_conversion_summary_with_base(all_metadata, all_meta_raw, filenames, base_index)
    ffmpeg_commands = generate_all_ffmpeg_commands(all_meta_raw, filenames, base_index)
    
    return summary_text, ffmpeg_commands


def add_preset_to_comparison(preset_name: str):
    """プリセットを比較対象に追加"""
    if preset_name not in PRESETS:
        return None, None, None, None, None, None
    
    all_metadata = _latest_results.get('all_metadata', []).copy()
    filenames = _latest_results.get('filenames', []).copy()
    presets_added = _latest_results.get('presets_added', []).copy()
    
    # 既に追加済みかチェック
    preset_filename = f"[PRESET] {preset_name}"
    if preset_filename in filenames:
        return None, None, None, None, None, None
    
    # プリセットデータを追加
    preset_data = PRESETS[preset_name].copy()
    preset_data["ファイル名"] = preset_filename
    preset_data["ファイルサイズ"] = "N/A (プリセット)"
    
    all_metadata.append(preset_data)
    filenames.append(preset_filename)
    presets_added.append(preset_name)
    
    # グローバル変数を更新
    _latest_results['all_metadata'] = all_metadata
    _latest_results['filenames'] = filenames
    _latest_results['presets_added'] = presets_added
    
    # 比較結果を再生成
    if len(all_metadata) >= 2:
        comparison_html, diff_count, total_count = create_multi_comparison_html(all_metadata, filenames, False)
        diff_info = f"差分: {diff_count}/{total_count}項目"
        _latest_results['comparison_html'] = comparison_html
        _latest_results['diff_count'] = diff_count
        _latest_results['total_count'] = total_count
    else:
        comparison_html = create_single_video_table(all_metadata[0], filenames[0])
        diff_info = ""
    
    # 基準ファイル選択肢を更新
    file_choices = [os.path.basename(f) if not f.startswith("[PRESET]") else f for f in filenames]
    default_choice = file_choices[0] if file_choices else None
    
    summary_text = ""
    ffmpeg_commands = ""
    
    return (
        _latest_results.get('thumbnails_html', ''),
        comparison_html,
        summary_text,
        ffmpeg_commands,
        diff_info,
        gr.update(choices=file_choices, value=default_choice)
    )


def generate_multi_conversion_summary_with_base(all_metadata: list, all_meta_raw: list, filenames: list, base_index: int = 0) -> str:
    """複数ファイルの変換サマリーを生成（指定した基準ファイル）"""
    if len(all_metadata) < 2:
        if len(all_metadata) == 1:
            return "複数の動画を追加すると変換サマリーが表示されます"
        return ""
    
    lines = []
    lines.append("=" * 60)
    lines.append("【変換サマリー】")
    lines.append(f"基準: {os.path.basename(filenames[base_index])}")
    lines.append("=" * 60)
    
    base_dict = all_metadata[base_index]
    base_raw = all_meta_raw[base_index]
    
    for i in range(len(all_metadata)):
        if i == base_index:
            continue
        
        target_dict = all_metadata[i]
        target_raw = all_meta_raw[i]
        target_name = os.path.basename(filenames[i])
        
        lines.append("")
        lines.append(f"--- {target_name} との比較 ---")
        
        differences = []
        
        compare_items = [
            ("コンテナフォーマット", "format_name"),
            ("映像コーデック", "video.codec_name"),
            ("解像度", None),
            ("フレームレート（fps）", "video.fps"),
            ("映像ビットレート", "video.bit_rate"),
            ("音声コーデック", "audio.codec_name"),
            ("サンプルレート", "audio.sample_rate"),
            ("チャンネル数", "audio.channels"),
        ]
        
        for display_name, attr_path in compare_items:
            base_val = base_dict.get(display_name, "N/A")
            target_val = target_dict.get(display_name, "N/A")
            
            if base_val != target_val:
                differences.append(f"[{display_name}] {target_val} -> {base_val}")
        
        if base_raw.video and target_raw.video:
            if base_raw.video.width != target_raw.video.width or base_raw.video.height != target_raw.video.height:
                base_res = f"{base_raw.video.width}x{base_raw.video.height}"
                target_res = f"{target_raw.video.width}x{target_raw.video.height}"
                if base_raw.video.width > 0 and target_raw.video.width > 0:
                    scale_w = base_raw.video.width / target_raw.video.width
                    scale_h = base_raw.video.height / target_raw.video.height
                    differences.append(f"[解像度] {target_res} -> {base_res} (幅{scale_w:.2f}倍, 高さ{scale_h:.2f}倍)")
        
        if base_raw.file_size > 0 and target_raw.file_size > 0:
            ratio = base_raw.file_size / target_raw.file_size
            differences.append(f"[ファイルサイズ] {target_raw.file_size_human} -> {base_raw.file_size_human} ({ratio:.2f}倍)")
        
        if differences:
            for diff in differences:
                lines.append(diff)
        else:
            lines.append("差分なし（同一仕様）")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def save_report():
    """現在の解析結果をレポートとして保存"""
    thumbnails_html = _latest_results.get('thumbnails_html', '')
    comparison_html = _latest_results.get('comparison_html', '')
    summary_text = _latest_results.get('summary_text', '')
    
    if not comparison_html or '動画ファイルをドロップ' in comparison_html:
        return None, "解析結果がありません。まず動画をアップロードしてください。"
    
    # レポートを保存
    saved_path = save_report_as_image(thumbnails_html, comparison_html, summary_text)
    
    if saved_path:
        filename = os.path.basename(saved_path)
        return saved_path, f"レポートを保存しました: {filename}"
    else:
        return None, "レポートの保存に失敗しました"


# ネオンイエローテーマ
neon_yellow_theme = gr.themes.Base(
    primary_hue=gr.themes.Color(
        c50="#FFFFF0",
        c100="#FFFFE0",
        c200="#FFFFC0",
        c300="#FFFF80",
        c400="#FFFF40",
        c500="#EEFF00",
        c600="#CCDD00",
        c700="#AABB00",
        c800="#889900",
        c900="#667700",
        c950="#445500",
    ),
    secondary_hue="gray",
    neutral_hue="gray",
    font=gr.themes.GoogleFont("Inter"),
).set(
    body_background_fill="#0a0a0a",
    body_background_fill_dark="#0a0a0a",
    block_background_fill="#121212",
    block_background_fill_dark="#121212",
    block_border_color="#333",
    block_border_color_dark="#333",
    block_label_text_color="#EEFF00",
    block_label_text_color_dark="#EEFF00",
    block_title_text_color="#EEFF00",
    block_title_text_color_dark="#EEFF00",
    input_background_fill="#1a1a1a",
    input_background_fill_dark="#1a1a1a",
    input_border_color="#333",
    input_border_color_dark="#333",
    button_primary_background_fill="#EEFF00",
    button_primary_background_fill_dark="#EEFF00",
    button_primary_background_fill_hover="#FFFF40",
    button_primary_background_fill_hover_dark="#FFFF40",
    button_primary_text_color="#000",
    button_primary_text_color_dark="#000",
    checkbox_background_color="#1a1a1a",
    checkbox_background_color_dark="#1a1a1a",
    checkbox_border_color="#EEFF00",
    checkbox_border_color_dark="#EEFF00",
)


def create_app():
    """Gradioアプリを作成 (Gradio 6対応)"""
    
    with gr.Blocks() as app:
        
        # ヘッダー
        gr.HTML("""
            <div class="app-header">
                <h1>DiffMovie</h1>
                <p>動画メタデータ比較ツール - 複数の動画の詳細情報を比較します</p>
            </div>
        """)
        
        # 入力エリア
        gr.HTML("<p class='input-label'>動画ファイルをドロップ（複数選択可）</p>")
        video_files = gr.File(
            label="",
            file_types=["video"],
            type="filepath",
            file_count="multiple",
            elem_classes=["drop-zone"]
        )
        
        # 比較ボタン
        with gr.Row():
            compare_btn = gr.Button(
                "比較する",
                variant="primary",
                elem_classes=["compare-btn"],
                scale=0
            )
        
        # プリセット追加
        gr.HTML("<p class='input-label' style='margin-top: 1rem;'>プリセットと比較</p>")
        with gr.Row():
            preset_dropdown = gr.Dropdown(
                label="プリセット選択",
                choices=list(PRESETS.keys()),
                value=None,
                interactive=True,
                scale=2
            )
            add_preset_btn = gr.Button(
                "プリセットを追加",
                variant="secondary",
                size="sm",
                scale=1
            )
        
        # サムネイル表示エリア
        gr.HTML("<h3 class='section-title'>プレビュー</h3>")
        thumbnails_output = gr.HTML(
            value="",
            elem_classes=["thumbnail-area"]
        )
        
        # 比較結果
        gr.HTML("<h3 class='section-title'>比較結果</h3>")
        
        # フィルタリングオプション
        with gr.Row():
            diff_filter_checkbox = gr.Checkbox(
                label="差分がある項目のみ表示",
                value=False
            )
            diff_info_label = gr.Textbox(
                value="",
                label="",
                interactive=False,
                scale=1,
                max_lines=1
            )
        
        comparison_output = gr.HTML(
            value="<p style='color: #888;'>動画ファイルをドロップしてください（複数可）</p>",
            elem_classes=["diff-table"]
        )
        
        # 変換サマリー
        gr.HTML("<h3 class='section-title'>変換サマリー</h3>")
        
        # 基準ファイル選択
        with gr.Row():
            base_file_dropdown = gr.Dropdown(
                label="基準ファイル（変換先の仕様）",
                choices=[],
                value=None,
                interactive=True,
                scale=2
            )
        
        summary_output = gr.Textbox(
            value="",
            label="",
            lines=10,
            max_lines=20,
            elem_classes=["summary-box"],
            interactive=False
        )
        
        # ボタンエリア（サマリー用）
        with gr.Row():
            copy_summary_btn = gr.Button(
                "サマリーをコピー",
                variant="secondary",
                size="sm"
            )
        
        # ffmpegコマンド
        gr.HTML("<h3 class='section-title'>ffmpegコマンド（クリックでコピー）</h3>")
        ffmpeg_output = gr.Textbox(
            value="",
            label="",
            lines=12,
            max_lines=30,
            elem_classes=["summary-box"],
            interactive=False
        )
        
        # ボタンエリア（ffmpeg用）
        with gr.Row():
            copy_ffmpeg_btn = gr.Button(
                "コマンドをコピー",
                variant="secondary",
                size="sm"
            )
            save_btn = gr.Button(
                "レポートを保存",
                variant="secondary",
                size="sm"
            )
        
        # 保存結果表示
        save_status = gr.Textbox(
            value="",
            label="",
            lines=1,
            interactive=False,
            visible=True
        )
        
        # ダウンロードファイル
        download_file = gr.File(
            label="ダウンロード",
            visible=False
        )
        
        # フッター
        gr.HTML("""
            <div class="app-footer">
                <p>DiffMovie v3.0 - Powered by ffprobe</p>
                <p style="font-size: 0.8rem; color: #555;">ffmpegコマンド生成 / 差分フィルター / 基準ファイル選択 / プリセット比較</p>
            </div>
        """)
        
        # イベントハンドラ
        compare_btn.click(
            fn=analyze_multiple_videos,
            inputs=[video_files],
            outputs=[thumbnails_output, comparison_output, summary_output, ffmpeg_output, diff_info_label, base_file_dropdown]
        )
        
        # ファイル変更時も自動比較
        video_files.change(
            fn=analyze_multiple_videos,
            inputs=[video_files],
            outputs=[thumbnails_output, comparison_output, summary_output, ffmpeg_output, diff_info_label, base_file_dropdown]
        )
        
        # 差分フィルターの適用
        diff_filter_checkbox.change(
            fn=apply_diff_filter,
            inputs=[diff_filter_checkbox],
            outputs=[comparison_output]
        )
        
        # 基準ファイル変更時
        base_file_dropdown.change(
            fn=update_base_file,
            inputs=[base_file_dropdown],
            outputs=[summary_output, ffmpeg_output]
        )
        
        # プリセット追加ボタン
        add_preset_btn.click(
            fn=add_preset_to_comparison,
            inputs=[preset_dropdown],
            outputs=[thumbnails_output, comparison_output, summary_output, ffmpeg_output, diff_info_label, base_file_dropdown]
        )
        
        # サマリーコピーボタンのJavaScript
        copy_summary_btn.click(
            fn=None,
            inputs=[summary_output],
            outputs=None,
            js="""(text) => {
                if (text) {
                    navigator.clipboard.writeText(text).then(() => {
                        alert('サマリーをコピーしました');
                    });
                }
                return [];
            }"""
        )
        
        # ffmpegコマンドコピーボタンのJavaScript
        copy_ffmpeg_btn.click(
            fn=None,
            inputs=[ffmpeg_output],
            outputs=None,
            js="""(text) => {
                if (text) {
                    navigator.clipboard.writeText(text).then(() => {
                        alert('ffmpegコマンドをコピーしました');
                    });
                }
                return [];
            }"""
        )
        
        # レポート保存ボタン
        save_btn.click(
            fn=save_report,
            inputs=[],
            outputs=[download_file, save_status]
        ).then(
            fn=lambda x: gr.update(visible=True) if x else gr.update(visible=False),
            inputs=[download_file],
            outputs=[download_file]
        )
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=False,  # run.commandで開くため
        app_kwargs={
            "title": "DiffMovie - 動画比較ツール"
        },
        theme=neon_yellow_theme,
        css=CUSTOM_CSS
    )
