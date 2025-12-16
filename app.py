"""
DiffMovie - 動画メタデータ比較アプリ
Gradio 6 + ダークテーマ + ネオンイエロー
"""

import gradio as gr
from video_analyzer import (
    analyze_video,
    compare_metadata,
    generate_conversion_summary,
    metadata_to_dict
)


# カスタムCSS
CUSTOM_CSS = """
/* 全体のスタイル */
.gradio-container {
    max-width: 1400px !important;
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

/* 入力エリアを横並びに強制 */
.input-row {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 1rem !important;
}

.input-row > div {
    flex: 1 !important;
    min-width: 0 !important;
}

/* ドロップゾーン */
.drop-zone {
    border: 2px dashed #EEFF00 !important;
    border-radius: 12px !important;
    min-height: 150px !important;
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
}

.diff-table table {
    width: 100% !important;
    border-collapse: collapse !important;
}

.diff-table th {
    background: #EEFF00 !important;
    color: #000 !important;
    padding: 12px !important;
    text-align: left !important;
    font-weight: bold !important;
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

/* 情報カード */
.info-card {
    background: #1a1a1a !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    margin-bottom: 1rem !important;
}

/* 差分ハイライト */
.diff-different {
    background: rgba(238, 255, 0, 0.15) !important;
    color: #EEFF00 !important;
}

.diff-same {
    color: #666 !important;
}

/* プログレスバー */
.progress {
    background: #333 !important;
}

.progress-bar {
    background: linear-gradient(90deg, #EEFF00, #CCDD00) !important;
}

/* Accordion */
.accordion {
    border: 1px solid #333 !important;
    border-radius: 8px !important;
}

.accordion-header {
    background: #1a1a1a !important;
    color: #EEFF00 !important;
}

/* Footer */
.app-footer {
    text-align: center;
    padding: 1rem;
    margin-top: 2rem;
    border-top: 1px solid #333;
    color: #666;
}
"""


def create_comparison_html(comparison_data: list) -> str:
    """比較結果をHTMLテーブルとして生成"""
    if not comparison_data:
        return "<p>データがありません</p>"
    
    html = """
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <thead>
            <tr style="background: #EEFF00; color: #000;">
                <th style="padding: 12px; text-align: left; width: 25%;">項目</th>
                <th style="padding: 12px; text-align: left; width: 25%;">入力A</th>
                <th style="padding: 12px; text-align: left; width: 25%;">入力B</th>
                <th style="padding: 12px; text-align: left; width: 25%;">差分</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for row in comparison_data:
        item, val_a, val_b, diff = row
        
        # 差分がある行をハイライト
        if diff != "同じ":
            row_style = "background: rgba(238, 255, 0, 0.1);"
            diff_style = "color: #EEFF00; font-weight: bold;"
        else:
            row_style = ""
            diff_style = "color: #666;"
        
        html += f"""
            <tr style="{row_style}">
                <td style="padding: 10px 12px; border-bottom: 1px solid #333; color: #ccc;">{item}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #333; color: #fff;">{val_a}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #333; color: #fff;">{val_b}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #333; {diff_style}">{diff}</td>
            </tr>
        """
    
    html += """
        </tbody>
    </table>
    """
    
    return html


def create_single_info_html(metadata_dict: dict, label: str) -> str:
    """単一の動画情報をHTMLテーブルとして生成"""
    if not metadata_dict:
        return f"<p>{label}の情報がありません</p>"
    
    html = f"""
    <h4 style="color: #EEFF00; margin-bottom: 10px;">{label}</h4>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
    """
    
    for key, value in metadata_dict.items():
        html += f"""
            <tr>
                <td style="padding: 6px 10px; border-bottom: 1px solid #333; color: #888; width: 40%;">{key}</td>
                <td style="padding: 6px 10px; border-bottom: 1px solid #333; color: #fff;">{value}</td>
            </tr>
        """
    
    html += "</table>"
    return html


def analyze_and_compare(video_a, video_b):
    """
    2つの動画を解析して比較する
    
    Args:
        video_a: 動画Aのファイルパス
        video_b: 動画Bのファイルパス
    
    Returns:
        tuple: (比較テーブルHTML, 変換サマリーテキスト, 入力A情報HTML, 入力B情報HTML)
    """
    # 初期値
    comparison_html = "<p style='color: #888;'>動画を2つ入力して「比較する」ボタンをクリックしてください</p>"
    summary_text = ""
    info_a_html = ""
    info_b_html = ""
    
    # 入力チェック
    if not video_a and not video_b:
        return comparison_html, summary_text, info_a_html, info_b_html
    
    # 動画Aを解析
    if video_a:
        meta_a = analyze_video(video_a)
        dict_a = metadata_to_dict(meta_a)
        info_a_html = create_single_info_html(dict_a, "入力A")
    else:
        meta_a = None
        info_a_html = "<p style='color: #666;'>入力Aが未選択です</p>"
    
    # 動画Bを解析
    if video_b:
        meta_b = analyze_video(video_b)
        dict_b = metadata_to_dict(meta_b)
        info_b_html = create_single_info_html(dict_b, "入力B")
    else:
        meta_b = None
        info_b_html = "<p style='color: #666;'>入力Bが未選択です</p>"
    
    # 両方ある場合は比較
    if meta_a and meta_b:
        comparison_data = compare_metadata(meta_a, meta_b)
        comparison_html = create_comparison_html(comparison_data)
        summary_text = generate_conversion_summary(meta_a, meta_b)
    elif meta_a:
        comparison_html = "<p style='color: #EEFF00;'>入力Bを追加すると比較できます</p>"
    elif meta_b:
        comparison_html = "<p style='color: #EEFF00;'>入力Aを追加すると比較できます</p>"
    
    return comparison_html, summary_text, info_a_html, info_b_html


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
                <p>動画メタデータ比較ツール - 2つの動画の詳細情報を比較します</p>
            </div>
        """)
        
        # 入力エリア
        with gr.Row(elem_classes=["input-row"]):
            with gr.Column(scale=1, min_width=300):
                gr.HTML("<p class='input-label'>入力A（変換元）</p>")
                video_a = gr.File(
                    label="",
                    file_types=["video"],
                    type="filepath",
                    elem_classes=["drop-zone"]
                )
            
            with gr.Column(scale=1, min_width=300):
                gr.HTML("<p class='input-label'>入力B（変換先）</p>")
                video_b = gr.File(
                    label="",
                    file_types=["video"],
                    type="filepath",
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
        
        # 個別情報表示（アコーディオン）
        with gr.Accordion("個別情報", open=False):
            with gr.Row():
                with gr.Column(scale=1):
                    info_a_output = gr.HTML(
                        value="<p style='color: #666;'>入力Aを選択してください</p>",
                        label="入力A 詳細"
                    )
                with gr.Column(scale=1):
                    info_b_output = gr.HTML(
                        value="<p style='color: #666;'>入力Bを選択してください</p>",
                        label="入力B 詳細"
                    )
        
        # 比較結果
        gr.HTML("<h3 class='section-title'>比較結果</h3>")
        comparison_output = gr.HTML(
            value="<p style='color: #888;'>動画を2つ入力して「比較する」ボタンをクリックしてください</p>",
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
                <p>DiffMovie v1.0 - Powered by ffprobe</p>
            </div>
        """)
        
        # イベントハンドラ
        compare_btn.click(
            fn=analyze_and_compare,
            inputs=[video_a, video_b],
            outputs=[comparison_output, summary_output, info_a_output, info_b_output]
        )
        
        # ファイル変更時も自動比較（オプション）
        video_a.change(
            fn=analyze_and_compare,
            inputs=[video_a, video_b],
            outputs=[comparison_output, summary_output, info_a_output, info_b_output]
        )
        
        video_b.change(
            fn=analyze_and_compare,
            inputs=[video_a, video_b],
            outputs=[comparison_output, summary_output, info_a_output, info_b_output]
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

