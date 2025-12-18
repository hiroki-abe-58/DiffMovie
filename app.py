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


def create_multi_comparison_html(all_metadata: list, filenames: list) -> str:
    """複数ファイルの比較結果をHTMLテーブルとして生成"""
    if not all_metadata:
        return "<p>データがありません</p>"
    
    num_files = len(all_metadata)
    
    # 全てのキーを収集
    all_keys = []
    for meta_dict in all_metadata:
        for key in meta_dict.keys():
            if key not in all_keys:
                all_keys.append(key)
    
    # ヘッダー作成
    col_width = max(15, 70 // num_files)  # 動的に幅を調整
    
    html = f"""
    <div style="overflow-x: auto;">
    <table style="width: 100%; border-collapse: collapse; font-size: 14px; min-width: {200 + num_files * 150}px;">
        <thead>
            <tr style="background: #EEFF00; color: #000;">
                <th style="padding: 12px; text-align: left; min-width: 180px; position: sticky; left: 0; background: #EEFF00;">項目</th>
    """
    
    for i, filename in enumerate(filenames):
        short_name = os.path.basename(filename) if filename else f"ファイル{i+1}"
        # ファイル名が長い場合は省略
        if len(short_name) > 20:
            short_name = short_name[:17] + "..."
        html += f'<th style="padding: 12px; text-align: left; min-width: 150px;" title="{os.path.basename(filename) if filename else ""}">{short_name}</th>'
    
    html += """
            </tr>
        </thead>
        <tbody>
    """
    
    # 各行を生成
    for key in all_keys:
        values = [meta_dict.get(key, "N/A") for meta_dict in all_metadata]
        
        # 値が全て同じかチェック
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
    
    return html


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
        tuple: (サムネイルHTML, 比較テーブルHTML, 変換サマリーテキスト)
    """
    # 初期値
    thumbnails_html = ""
    comparison_html = "<p style='color: #888;'>動画ファイルをドロップしてください（複数可）</p>"
    summary_text = ""
    
    # 入力チェック
    if not files:
        return thumbnails_html, comparison_html, summary_text
    
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
        return thumbnails_html, comparison_html, summary_text
    
    # サムネイルHTML生成
    thumbnails_html = create_thumbnails_html(filenames, thumbnails)
    
    if len(all_metadata) == 1:
        # 1ファイルのみ
        comparison_html = create_single_video_table(all_metadata[0], filenames[0])
        summary_text = "複数の動画を追加すると変換サマリーが表示されます"
    else:
        # 複数ファイル比較
        comparison_html = create_multi_comparison_html(all_metadata, filenames)
        summary_text = generate_multi_conversion_summary(all_metadata, all_meta_raw, filenames)
    
    return thumbnails_html, comparison_html, summary_text


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
        
        # サムネイル表示エリア
        gr.HTML("<h3 class='section-title'>プレビュー</h3>")
        thumbnails_output = gr.HTML(
            value="",
            elem_classes=["thumbnail-area"]
        )
        
        # 比較結果
        gr.HTML("<h3 class='section-title'>比較結果</h3>")
        comparison_output = gr.HTML(
            value="<p style='color: #888;'>動画ファイルをドロップしてください（複数可）</p>",
            elem_classes=["diff-table"]
        )
        
        # 変換サマリー
        gr.HTML("<h3 class='section-title'>変換サマリー（クリックでコピー）</h3>")
        summary_output = gr.Textbox(
            value="",
            label="",
            lines=15,
            max_lines=30,
            elem_classes=["summary-box"],
            interactive=False
        )
        
        # コピーボタン
        copy_btn = gr.Button(
            "クリップボードにコピー",
            variant="secondary",
            size="sm"
        )
        
        # フッター
        gr.HTML("""
            <div class="app-footer">
                <p>DiffMovie v2.0 - Powered by ffprobe - 複数ファイル対応</p>
            </div>
        """)
        
        # イベントハンドラ
        compare_btn.click(
            fn=analyze_multiple_videos,
            inputs=[video_files],
            outputs=[thumbnails_output, comparison_output, summary_output]
        )
        
        # ファイル変更時も自動比較
        video_files.change(
            fn=analyze_multiple_videos,
            inputs=[video_files],
            outputs=[thumbnails_output, comparison_output, summary_output]
        )
        
        # コピーボタンのJavaScript
        copy_btn.click(
            fn=None,
            inputs=[summary_output],
            outputs=None,
            js="""(text) => {
                if (text) {
                    navigator.clipboard.writeText(text).then(() => {
                        alert('クリップボードにコピーしました');
                    });
                }
                return [];
            }"""
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
