"""
動画解析モジュール
ffprobeを使用して動画のメタデータを取得する
"""

import json
import subprocess
import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class VideoStreamInfo:
    """映像ストリーム情報"""
    codec_name: str = "N/A"
    codec_long_name: str = "N/A"
    profile: str = "N/A"
    level: str = "N/A"
    width: int = 0
    height: int = 0
    display_aspect_ratio: str = "N/A"
    sample_aspect_ratio: str = "N/A"
    fps: str = "N/A"
    avg_frame_rate: str = "N/A"
    bit_rate: str = "N/A"
    pix_fmt: str = "N/A"
    color_space: str = "N/A"
    color_primaries: str = "N/A"
    color_transfer: str = "N/A"
    color_range: str = "N/A"
    hdr_format: str = "N/A"
    bits_per_raw_sample: str = "N/A"


@dataclass
class AudioStreamInfo:
    """音声ストリーム情報"""
    codec_name: str = "N/A"
    codec_long_name: str = "N/A"
    profile: str = "N/A"
    sample_rate: str = "N/A"
    channels: int = 0
    channel_layout: str = "N/A"
    bit_rate: str = "N/A"
    bits_per_sample: int = 0
    sample_fmt: str = "N/A"


@dataclass
class VideoMetadata:
    """動画メタデータ全体"""
    # 基本情報
    filename: str = "N/A"
    file_size: int = 0
    file_size_human: str = "N/A"
    format_name: str = "N/A"
    format_long_name: str = "N/A"
    duration: float = 0.0
    duration_human: str = "N/A"
    bit_rate: str = "N/A"
    nb_streams: int = 0
    
    # ストリーム情報
    video: Optional[VideoStreamInfo] = None
    audio: Optional[AudioStreamInfo] = None
    
    # エラー情報
    error: Optional[str] = None


def format_file_size(size_bytes: int) -> str:
    """ファイルサイズを人間が読みやすい形式に変換"""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """秒数を HH:MM:SS.ms 形式に変換"""
    if seconds <= 0:
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    else:
        return f"{minutes:02d}:{secs:06.3f}"


def format_bitrate(bitrate_str: str) -> str:
    """ビットレートを人間が読みやすい形式に変換"""
    if bitrate_str == "N/A" or not bitrate_str:
        return "N/A"
    
    try:
        bitrate = int(bitrate_str)
        if bitrate >= 1_000_000:
            return f"{bitrate / 1_000_000:.2f} Mbps"
        elif bitrate >= 1_000:
            return f"{bitrate / 1_000:.2f} Kbps"
        else:
            return f"{bitrate} bps"
    except (ValueError, TypeError):
        return bitrate_str


def calculate_fps(frame_rate_str: str) -> str:
    """フレームレート文字列をfps値に変換"""
    if not frame_rate_str or frame_rate_str == "N/A" or frame_rate_str == "0/0":
        return "N/A"
    
    try:
        if '/' in frame_rate_str:
            num, den = frame_rate_str.split('/')
            if int(den) == 0:
                return "N/A"
            fps = float(num) / float(den)
            return f"{fps:.3f}"
        else:
            return f"{float(frame_rate_str):.3f}"
    except (ValueError, ZeroDivisionError):
        return frame_rate_str


def analyze_video(file_path: str) -> VideoMetadata:
    """
    ffprobeを使用して動画ファイルを解析する
    
    Args:
        file_path: 動画ファイルのパス
        
    Returns:
        VideoMetadata: 解析結果
    """
    metadata = VideoMetadata()
    
    if not file_path or not os.path.exists(file_path):
        metadata.error = "ファイルが見つかりません"
        return metadata
    
    # ファイル名とサイズを取得
    metadata.filename = os.path.basename(file_path)
    metadata.file_size = os.path.getsize(file_path)
    metadata.file_size_human = format_file_size(metadata.file_size)
    
    # ffprobeコマンドを実行
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        file_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            metadata.error = f"ffprobeエラー: {result.stderr}"
            return metadata
        
        data = json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        metadata.error = "解析がタイムアウトしました"
        return metadata
    except json.JSONDecodeError:
        metadata.error = "ffprobeの出力を解析できませんでした"
        return metadata
    except FileNotFoundError:
        metadata.error = "ffprobeが見つかりません。ffmpegをインストールしてください。"
        return metadata
    except Exception as e:
        metadata.error = f"予期しないエラー: {str(e)}"
        return metadata
    
    # フォーマット情報を取得
    format_info = data.get('format', {})
    metadata.format_name = format_info.get('format_name', 'N/A')
    metadata.format_long_name = format_info.get('format_long_name', 'N/A')
    metadata.duration = float(format_info.get('duration', 0))
    metadata.duration_human = format_duration(metadata.duration)
    metadata.bit_rate = format_bitrate(format_info.get('bit_rate', 'N/A'))
    metadata.nb_streams = int(format_info.get('nb_streams', 0))
    
    # ストリーム情報を取得
    streams = data.get('streams', [])
    
    for stream in streams:
        codec_type = stream.get('codec_type', '')
        
        if codec_type == 'video' and metadata.video is None:
            video_info = VideoStreamInfo()
            video_info.codec_name = stream.get('codec_name', 'N/A')
            video_info.codec_long_name = stream.get('codec_long_name', 'N/A')
            video_info.profile = stream.get('profile', 'N/A')
            video_info.level = str(stream.get('level', 'N/A'))
            video_info.width = int(stream.get('width', 0))
            video_info.height = int(stream.get('height', 0))
            video_info.display_aspect_ratio = stream.get('display_aspect_ratio', 'N/A')
            video_info.sample_aspect_ratio = stream.get('sample_aspect_ratio', 'N/A')
            
            # FPS計算
            r_frame_rate = stream.get('r_frame_rate', 'N/A')
            avg_frame_rate = stream.get('avg_frame_rate', 'N/A')
            video_info.fps = calculate_fps(r_frame_rate)
            video_info.avg_frame_rate = calculate_fps(avg_frame_rate)
            
            video_info.bit_rate = format_bitrate(stream.get('bit_rate', 'N/A'))
            video_info.pix_fmt = stream.get('pix_fmt', 'N/A')
            video_info.color_space = stream.get('color_space', 'N/A')
            video_info.color_primaries = stream.get('color_primaries', 'N/A')
            video_info.color_transfer = stream.get('color_transfer', 'N/A')
            video_info.color_range = stream.get('color_range', 'N/A')
            video_info.bits_per_raw_sample = stream.get('bits_per_raw_sample', 'N/A')
            
            # HDR判定
            if video_info.color_transfer in ['smpte2084', 'arib-std-b67']:
                if video_info.color_transfer == 'smpte2084':
                    video_info.hdr_format = "HDR10/HDR10+"
                else:
                    video_info.hdr_format = "HLG"
            elif video_info.color_primaries == 'bt2020':
                video_info.hdr_format = "Wide Color Gamut"
            else:
                video_info.hdr_format = "SDR"
            
            metadata.video = video_info
            
        elif codec_type == 'audio' and metadata.audio is None:
            audio_info = AudioStreamInfo()
            audio_info.codec_name = stream.get('codec_name', 'N/A')
            audio_info.codec_long_name = stream.get('codec_long_name', 'N/A')
            audio_info.profile = stream.get('profile', 'N/A')
            audio_info.sample_rate = stream.get('sample_rate', 'N/A')
            audio_info.channels = int(stream.get('channels', 0))
            audio_info.channel_layout = stream.get('channel_layout', 'N/A')
            audio_info.bit_rate = format_bitrate(stream.get('bit_rate', 'N/A'))
            audio_info.bits_per_sample = int(stream.get('bits_per_sample', 0))
            audio_info.sample_fmt = stream.get('sample_fmt', 'N/A')
            
            metadata.audio = audio_info
    
    return metadata


def metadata_to_dict(metadata: VideoMetadata) -> dict:
    """
    VideoMetadataを辞書形式に変換（表示用）
    
    Returns:
        dict: キーが項目名、値がメタデータ値の辞書
    """
    result = {}
    
    if metadata.error:
        result["エラー"] = metadata.error
        return result
    
    # 基本情報
    result["ファイル名"] = metadata.filename
    result["ファイルサイズ"] = metadata.file_size_human
    result["コンテナフォーマット"] = metadata.format_name
    result["フォーマット詳細"] = metadata.format_long_name
    result["総尺"] = metadata.duration_human
    result["総尺（秒）"] = f"{metadata.duration:.3f}"
    result["総ビットレート"] = metadata.bit_rate
    result["ストリーム数"] = str(metadata.nb_streams)
    
    # 映像情報
    if metadata.video:
        v = metadata.video
        result["映像コーデック"] = v.codec_name
        result["映像コーデック詳細"] = v.codec_long_name
        result["映像プロファイル"] = v.profile
        result["映像レベル"] = v.level
        result["解像度"] = f"{v.width}x{v.height}" if v.width > 0 else "N/A"
        result["解像度（幅）"] = str(v.width)
        result["解像度（高さ）"] = str(v.height)
        result["アスペクト比（DAR）"] = v.display_aspect_ratio
        result["アスペクト比（SAR）"] = v.sample_aspect_ratio
        result["フレームレート（fps）"] = v.fps
        result["平均フレームレート"] = v.avg_frame_rate
        result["映像ビットレート"] = v.bit_rate
        result["ピクセルフォーマット"] = v.pix_fmt
        result["カラースペース"] = v.color_space
        result["色域（Primaries）"] = v.color_primaries
        result["ガンマ/転送特性"] = v.color_transfer
        result["カラーレンジ"] = v.color_range
        result["HDR形式"] = v.hdr_format
        result["ビット深度（映像）"] = v.bits_per_raw_sample
    else:
        result["映像ストリーム"] = "なし"
    
    # 音声情報
    if metadata.audio:
        a = metadata.audio
        result["音声コーデック"] = a.codec_name
        result["音声コーデック詳細"] = a.codec_long_name
        result["音声プロファイル"] = a.profile
        result["サンプルレート"] = f"{a.sample_rate} Hz" if a.sample_rate != "N/A" else "N/A"
        result["チャンネル数"] = str(a.channels)
        result["チャンネルレイアウト"] = a.channel_layout
        result["音声ビットレート"] = a.bit_rate
        result["ビット深度（音声）"] = str(a.bits_per_sample) if a.bits_per_sample > 0 else "N/A"
        result["サンプルフォーマット"] = a.sample_fmt
    else:
        result["音声ストリーム"] = "なし"
    
    return result


def compare_metadata(meta_a: VideoMetadata, meta_b: VideoMetadata) -> list:
    """
    2つの動画メタデータを比較する
    
    Args:
        meta_a: 動画Aのメタデータ
        meta_b: 動画Bのメタデータ
        
    Returns:
        list: [項目名, 値A, 値B, 差分/変化] のリスト
    """
    dict_a = metadata_to_dict(meta_a)
    dict_b = metadata_to_dict(meta_b)
    
    # すべてのキーを収集
    all_keys = list(dict_a.keys())
    for key in dict_b.keys():
        if key not in all_keys:
            all_keys.append(key)
    
    results = []
    
    for key in all_keys:
        val_a = dict_a.get(key, "N/A")
        val_b = dict_b.get(key, "N/A")
        
        # 差分を計算
        diff = calculate_diff(key, val_a, val_b)
        
        results.append([key, val_a, val_b, diff])
    
    return results


def calculate_diff(key: str, val_a: str, val_b: str) -> str:
    """
    2つの値の差分を計算する
    
    Args:
        key: 項目名
        val_a: 値A
        val_b: 値B
        
    Returns:
        str: 差分の説明
    """
    if val_a == val_b:
        return "同じ"
    
    if val_a == "N/A" or val_b == "N/A":
        return "異なる"
    
    # 数値比較が可能な項目
    numeric_keys = [
        "総尺（秒）", "解像度（幅）", "解像度（高さ）",
        "フレームレート（fps）", "平均フレームレート",
        "チャンネル数", "ストリーム数"
    ]
    
    if key in numeric_keys:
        try:
            num_a = float(val_a)
            num_b = float(val_b)
            if num_a > 0:
                ratio = num_b / num_a
                diff_val = num_b - num_a
                if ratio >= 1:
                    return f"+{diff_val:.2f} ({ratio:.2f}倍)"
                else:
                    return f"{diff_val:.2f} ({ratio:.2f}倍)"
        except (ValueError, ZeroDivisionError):
            pass
    
    # ファイルサイズの比較
    if key == "ファイルサイズ":
        try:
            # サイズ文字列からバイト数を推定
            size_a = parse_size_string(val_a)
            size_b = parse_size_string(val_b)
            if size_a > 0:
                ratio = size_b / size_a
                return f"{ratio:.2f}倍"
        except:
            pass
    
    # ビットレートの比較
    if "ビットレート" in key:
        try:
            br_a = parse_bitrate_string(val_a)
            br_b = parse_bitrate_string(val_b)
            if br_a > 0:
                ratio = br_b / br_a
                return f"{ratio:.2f}倍"
        except:
            pass
    
    return f"{val_a} → {val_b}"


def parse_size_string(size_str: str) -> float:
    """サイズ文字列をバイト数に変換"""
    units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    parts = size_str.split()
    if len(parts) == 2:
        value = float(parts[0])
        unit = parts[1].upper()
        return value * units.get(unit, 1)
    return 0


def parse_bitrate_string(br_str: str) -> float:
    """ビットレート文字列をbpsに変換"""
    if 'Mbps' in br_str:
        return float(br_str.replace(' Mbps', '')) * 1_000_000
    elif 'Kbps' in br_str:
        return float(br_str.replace(' Kbps', '')) * 1_000
    elif 'bps' in br_str:
        return float(br_str.replace(' bps', ''))
    return 0


def generate_conversion_summary(meta_a: VideoMetadata, meta_b: VideoMetadata) -> str:
    """
    AをBに変換するための要約テキストを生成
    
    Args:
        meta_a: 変換元のメタデータ
        meta_b: 変換先のメタデータ
        
    Returns:
        str: 変換に必要な手順の要約
    """
    if meta_a.error or meta_b.error:
        return "エラーがあるため変換サマリーを生成できません"
    
    lines = []
    lines.append("=" * 50)
    lines.append("【変換サマリー】入力A → 入力B")
    lines.append("=" * 50)
    lines.append("")
    
    # コンテナフォーマット
    if meta_a.format_name != meta_b.format_name:
        lines.append(f"[コンテナ] {meta_a.format_name} → {meta_b.format_name}")
    
    # 映像関連
    if meta_a.video and meta_b.video:
        va, vb = meta_a.video, meta_b.video
        
        # 映像コーデック
        if va.codec_name != vb.codec_name:
            lines.append(f"[映像コーデック] {va.codec_name} → {vb.codec_name}")
        
        # 解像度
        if va.width != vb.width or va.height != vb.height:
            if va.width > 0 and vb.width > 0:
                scale_w = vb.width / va.width
                scale_h = vb.height / va.height
                lines.append(f"[解像度] {va.width}x{va.height} → {vb.width}x{vb.height} (幅{scale_w:.2f}倍, 高さ{scale_h:.2f}倍)")
        
        # FPS
        if va.fps != vb.fps and va.fps != "N/A" and vb.fps != "N/A":
            try:
                fps_a = float(va.fps)
                fps_b = float(vb.fps)
                ratio = fps_b / fps_a
                lines.append(f"[フレームレート] {va.fps} fps → {vb.fps} fps ({ratio:.2f}倍)")
            except ValueError:
                lines.append(f"[フレームレート] {va.fps} fps → {vb.fps} fps")
        
        # ビットレート
        if va.bit_rate != vb.bit_rate and va.bit_rate != "N/A" and vb.bit_rate != "N/A":
            lines.append(f"[映像ビットレート] {va.bit_rate} → {vb.bit_rate}")
        
        # ピクセルフォーマット
        if va.pix_fmt != vb.pix_fmt:
            lines.append(f"[ピクセルフォーマット] {va.pix_fmt} → {vb.pix_fmt}")
        
        # HDR
        if va.hdr_format != vb.hdr_format:
            lines.append(f"[HDR形式] {va.hdr_format} → {vb.hdr_format}")
    
    # 音声関連
    if meta_a.audio and meta_b.audio:
        aa, ab = meta_a.audio, meta_b.audio
        
        # 音声コーデック
        if aa.codec_name != ab.codec_name:
            lines.append(f"[音声コーデック] {aa.codec_name} → {ab.codec_name}")
        
        # サンプルレート
        if aa.sample_rate != ab.sample_rate:
            lines.append(f"[サンプルレート] {aa.sample_rate} Hz → {ab.sample_rate} Hz")
        
        # チャンネル数
        if aa.channels != ab.channels:
            lines.append(f"[チャンネル数] {aa.channels}ch → {ab.channels}ch")
        
        # 音声ビットレート
        if aa.bit_rate != ab.bit_rate and aa.bit_rate != "N/A" and ab.bit_rate != "N/A":
            lines.append(f"[音声ビットレート] {aa.bit_rate} → {ab.bit_rate}")
    
    # ファイルサイズ
    if meta_a.file_size > 0 and meta_b.file_size > 0:
        ratio = meta_b.file_size / meta_a.file_size
        lines.append(f"[ファイルサイズ] {meta_a.file_size_human} → {meta_b.file_size_human} ({ratio:.2f}倍)")
    
    # 総尺
    if abs(meta_a.duration - meta_b.duration) > 0.1:
        ratio = meta_b.duration / meta_a.duration if meta_a.duration > 0 else 0
        lines.append(f"[総尺] {meta_a.duration_human} → {meta_b.duration_human} ({ratio:.2f}倍)")
    
    if len(lines) == 4:  # ヘッダーのみ
        lines.append("変換の必要な項目はありません（同一仕様）")
    
    lines.append("")
    lines.append("=" * 50)
    
    return "\n".join(lines)


if __name__ == "__main__":
    # テスト用
    import sys
    if len(sys.argv) > 1:
        meta = analyze_video(sys.argv[1])
        info = metadata_to_dict(meta)
        for k, v in info.items():
            print(f"{k}: {v}")


