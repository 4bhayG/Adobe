
# 📄 Adobe 1A - PDF Heading Extraction

This project provides a **containerized Python solution** to extract structured outlines (title, headings, subheadings) from PDF documents without relying on unreliable built-in metadata.

The script analyzes **stylistic (font size, style)** and **positional (layout)** properties of text in PDFs to generate a structured **JSON output** representing the document’s heading hierarchy.

---

## 🚀 Features

- Detects and tags headings (`<h1>`, `<h2>`, etc.) based on font properties.
- Filters out irrelevant content like footers, headers, and table text.
- Builds a hierarchical structure based on relative font sizes.
- Completely self-contained using Docker.

---

## 🔍 How It Works

### 1. **Font Profiling**
- Scans all text to identify unique font styles (name, size, color, weight).
- Determines the most common style, assumed to be paragraph text (`<p>`).

### 2. **Semantic Tagging**
- Tags text **larger than `<p>`** as potential headings (`<h1>`, `<h2>`, etc.).
- Tags smaller text as `<s>` (small).

### 3. **Content Parsing**
- Reads text **page by page** in natural reading order (top-to-bottom, left-to-right).
- **Ignores**:
  - Text inside tables (detected using lines).
  - Headers and footers (top 5%, bottom 10% of page height).

### 4. **Heading Identification**
- Applies heuristics:
  - Less than 90 characters  
  - Starts with an uppercase letter  
  - Includes non-numeric characters  
  - Avoids ending punctuation like commas, semicolons

### 5. **Hierarchy Generation**
- Determines heading levels:
  - Larger font → higher level (e.g., `<h1>`)
  - Smaller font → subheading (e.g., `<h2>`, `<h3>`)

---

## 📦 Requirements

- **Docker** (only external requirement)

### Python Dependencies (within container):
- `PyMuPDF`: PDF parsing  
- `pandas`: Text sorting and manipulation

---

## 🛠️ Project Structure

```
your_project_folder/
├── input/
│   └── your_document.pdf          # Place your PDF files here
├── output/                        # JSON output will appear here
├── app.py                         # Main script
├── Dockerfile                     # Docker setup
└── requirements.txt               # Python dependencies
```

---

## 🐳 How to Run (with Docker)

### 1. Install Docker

Make sure Docker Desktop is installed and running on your machine:  
👉 https://www.docker.com/products/docker-desktop

---

### 2. Place Your PDFs

Copy all the PDF files you want to process into the `input/` directory.

---

### 3. Build the Docker Image

Run the following command in your project root (where `Dockerfile` is located):

```bash
docker build --platform linux/amd64 -t pdf-parser .
```

---

### 4. Run the Container

This will process all PDFs inside `input/` and save JSONs to `output/`:

```bash
docker run --rm \
  -v "$(pwd)/input:/app/input" \
  -v "$(pwd)/output:/app/output" \
  --network none \
  pdf-parser
```

---

### 5. View Output

Each `.pdf` will generate a corresponding `.json` in the `output/` folder.

---

## 📁 Sample Output (JSON)

```json
[
  {
    "level": "H1",
    "text": "Introduction"
  },
  {
    "level": "H2",
    "text": "Background and Motivation"
  },
  {
    "level": "H2",
    "text": "Approach"
  }
]
```

---

## 📬 Contact

Feel free to reach out if you have questions or suggestions!

---

## 📝 License

This project is licensed under the **MIT License**.
