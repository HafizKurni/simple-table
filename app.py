import json
import html
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="List to Table Converter",
    page_icon="📋",
    layout="wide",
)

EXAMPLE_TEXT = """No
Kolom
Deskripsi
Contoh
1
id
ID unik setiap data
001
2
instruction
Perintah atau tugas yang diberikan kepada model
"Jelaskan konsep machine learning."
3
input
Konteks tambahan (opsional)
"Untuk siswa SMA"
4
output
Jawaban yang diharapkan dari model
"Machine learning adalah cabang AI yang memungkinkan komputer belajar dari data..."
5
category
Kategori tugas
Education
6
language
Bahasa yang digunakan
id
7
source
Sumber data
Buku AI Dasar
8
difficulty
Tingkat kesulitan
Easy"""


def tokenize_text(text: str):
    text = text.replace("\\r\
", "\
").replace("\\r", "\
")
    return [line.strip() for line in text.split("\
") if line.strip()]


def build_dataframe(items, columns_per_row, first_row_is_header=True):
    if columns_per_row <= 0:
        return None, [], 0, 0, []

    headers = []
    data_items = items[:]

    if first_row_is_header:
        if len(items) < columns_per_row:
            return None, [], 0, 0, []
        headers = items[:columns_per_row]
        data_items = items[columns_per_row:]
    else:
        headers = [f"Kolom {i + 1}" for i in range(columns_per_row)]

    full_rows = len(data_items) // columns_per_row
    remainder = len(data_items) % columns_per_row

    rows = []
    for i in range(full_rows):
        start = i * columns_per_row
        end = start + columns_per_row
        rows.append(data_items[start:end])

    remainder_items = data_items[full_rows * columns_per_row:]
    df = pd.DataFrame(rows, columns=headers)
    return df, remainder_items, full_rows, remainder, headers


def df_to_markdown(df: pd.DataFrame):
    headers = [str(col) for col in df.columns.tolist()]

    def esc(val):
        return str(val).replace("|", "\\|").replace("\
", "<br>")

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in df.fillna("").astype(str).values.tolist():
        lines.append("| " + " | ".join(esc(v) for v in row) + " |")

    return "\
".join(lines)


def df_to_html_copy(df: pd.DataFrame):
    headers = [html.escape(str(col)) for col in df.columns.tolist()]

    thead = "".join(
        f'<th style="border:1px solid #cbd5e1;padding:8px 10px;background:#f8fafc;text-align:left;font-weight:700;">{col}</th>'
        for col in headers
    )

    tbody_rows = []
    for row in df.fillna("").astype(str).values.tolist():
        tds = "".join(
            f'<td style="border:1px solid #cbd5e1;padding:8px 10px;vertical-align:top;text-align:left;">{html.escape(str(value))}</td>'
            for value in row
        )
        tbody_rows.append(f"<tr>{tds}</tr>")

    tbody = "".join(tbody_rows)

    return (
        '<table style="border-collapse:collapse;width:100%;font-family:Arial, Helvetica, sans-serif;font-size:12px;color:#111827;">'
        f'<thead><tr>{thead}</tr></thead>'
        f'<tbody>{tbody}</tbody>'
        "</table>"
    )


def render_copy_buttons(tsv_text, markdown_text, html_text, plain_table_text):
    payload = json.dumps(
        {
            "tsv": tsv_text,
            "markdown": markdown_text,
            "html": html_text,
            "plain": plain_table_text,
        }
    )

    component_html = f"""
    <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:6px 0 14px 0;">
        <button onclick="copyText('table')" style="padding:10px 14px;border:none;border-radius:8px;background:#059669;color:white;cursor:pointer;font-weight:600;">
            Copy Table
        </button>
        <button onclick="copyText('tsv')" style="padding:10px 14px;border:none;border-radius:8px;background:#0f766e;color:white;cursor:pointer;">
            Copy TSV
        </button>
        <button onclick="copyText('markdown')" style="padding:10px 14px;border:none;border-radius:8px;background:#2563eb;color:white;cursor:pointer;">
            Copy Markdown
        </button>
        <button onclick="copyText('html')" style="padding:10px 14px;border:none;border-radius:8px;background:#7c3aed;color:white;cursor:pointer;">
            Copy HTML
        </button>
        <span id="copy-status" style="font-family:sans-serif;color:#374151;"></span>
    </div>

    <script>
        const payload = {payload};

        function setStatus(msg) {{
            const el = document.getElementById("copy-status");
            el.innerText = msg;
            setTimeout(() => {{
                el.innerText = "";
            }}, 2200);
        }}

        async function copyPlain(text, label) {{
            try {{
                await navigator.clipboard.writeText(text);
                setStatus("Copied: " + label);
            }} catch (e) {{
                setStatus("Copy gagal di browser ini.");
            }}
        }}

        async function copyRichHtml(htmlValue, plainFallback) {{
            try {{
                if (navigator.clipboard && window.ClipboardItem) {{
                    const item = new ClipboardItem({{
                        "text/html": new Blob([htmlValue], {{ type: "text/html" }}),
                        "text/plain": new Blob([plainFallback], {{ type: "text/plain" }})
                    }});
                    await navigator.clipboard.write([item]);
                    setStatus("Copied: TABLE");
                }} else {{
                    await copyPlain(plainFallback, "TABLE (plain text fallback)");
                }}
            }} catch (e) {{
                await copyPlain(plainFallback, "TABLE (plain text fallback)");
            }}
        }}

        async function copyText(kind) {{
            if (kind === "table") {{
                await copyRichHtml(payload.html, payload.plain);
                return;
            }}
            if (kind === "tsv") {{
                await copyPlain(payload.tsv, "TSV");
                return;
            }}
            if (kind === "markdown") {{
                await copyPlain(payload.markdown, "MARKDOWN");
                return;
            }}
            if (kind === "html") {{
                await copyPlain(payload.html, "HTML");
                return;
            }}
        }}
    </script>
    """

    components.html(component_html, height=95)


st.title("📋 List to Table Converter")
st.caption("Paste list vertikal → ubah jadi tabel → copy ke Docs / Word / Spreadsheet")

left, right = st.columns([1.35, 1])

with left:
    st.subheader("Input")
    use_example = st.button("Isi contoh data", use_container_width=True)

    if use_example:
        st.session_state["raw_text"] = EXAMPLE_TEXT

    if "raw_text" not in st.session_state:
        st.session_state["raw_text"] = ""

    st.text_area(
        "Paste list di sini",
        key="raw_text",
        height=430,
        placeholder="Contoh:\
No\
Kolom\
Deskripsi\
Contoh\
1\
id\
ID unik setiap data\
001",
    )

with right:
    st.subheader("Pengaturan")
    columns_per_row = st.number_input(
        "Jumlah kolom per baris",
        min_value=1,
        value=4,
        step=1,
        help="Untuk contoh Anda: 4 kolom (No, Kolom, Deskripsi, Contoh)",
    )

    first_row_is_header = st.checkbox("Baris pertama adalah header", value=True)

    st.info("Jumlah baris data dihitung otomatis dari total item dibagi jumlah kolom.")

items = tokenize_text(st.session_state.get("raw_text", ""))

df, remainder_items, full_rows, remainder, headers = build_dataframe(
    items,
    int(columns_per_row),
    first_row_is_header,
)

st.divider()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total item", len(items))
c2.metric("Kolom", int(columns_per_row))
c3.metric("Baris data", full_rows)
c4.metric("Sisa item", remainder)

if remainder_items:
    st.warning(
        "Ada item tersisa yang tidak membentuk 1 baris penuh: " + " | ".join(remainder_items)
    )

if df is not None and not df.empty:
    st.subheader("Preview tabel")
    st.dataframe(df, use_container_width=True)

    tsv_text = df.to_csv(sep="\\t", index=False)
    csv_text = df.to_csv(index=False)
    markdown_text = df_to_markdown(df)
    html_text = df_to_html_copy(df)
    plain_table_text = df.to_string(index=False)

    st.subheader("Copy cepat")
    render_copy_buttons(tsv_text, markdown_text, html_text, plain_table_text)

    tab1, tab2, tab3 = st.tabs(["TSV", "Markdown", "HTML"])

    with tab1:
        st.caption("Paling cocok untuk Excel atau Google Sheets.")
        st.text_area("TSV output", value=tsv_text, height=220)

    with tab2:
        st.caption("Cocok untuk README atau editor markdown.")
        st.text_area("Markdown output", value=markdown_text, height=220)

    with tab3:
        st.caption("HTML ini dipakai juga oleh tombol Copy Table untuk paste ke Docs atau Word.")
        st.text_area("HTML output", value=html_text, height=220)
        st.markdown("Preview HTML:")
        st.markdown(df.to_html(index=False, escape=False), unsafe_allow_html=True)

    st.download_button(
        "Download CSV",
        data=csv_text,
        file_name="table_output.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("Masukkan data dulu. Untuk contoh Anda, set jumlah kolom = 4.")
