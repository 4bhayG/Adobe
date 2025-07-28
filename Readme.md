Adobe 1A - PDF Heading Extraction
This project provides a containerized solution for extracting a structured outline, including a title and hierarchical headings, from PDF documents. It analyzes the stylistic and positional properties of text within a PDF to generate a JSON output.

How It Works: Heading Extraction Logic 🔎
The script identifies headings without relying on a PDF's built-in metadata, which is often missing or incorrect. The process is a multi-step analysis:

Font Profiling: The script first performs a full scan of the document to identify all unique font styles (combinations of font name, size, color, and weight). It counts the occurrences of each style to determine that the most frequently used font style is the primary paragraph text (<p>).

Semantic Tagging: With the baseline paragraph style established, the script assigns semantic tags to all other font styles.

Text with a larger font size than the paragraph text is tagged as a potential heading (<h1>, <h2>, etc.).

Text with a smaller font size is tagged as small text (<s>).

Content Parsing and Filtering: The script reads the text content page by page, in natural reading order (top-to-bottom, left-to-right). During this process, it:

Detects and ignores text within tables by identifying horizontal and vertical lines.

Filters out common headers and footers by ignoring text in the top 5% and bottom 10% of each page.

Heading Identification: The list of potential headings is further refined using a set of heuristics to distinguish them from other text:

The text is typically short (less than 90 characters).

It does not start with a lowercase letter.

It contains non-numeric characters.

It does not end with standard punctuation like commas or semicolons.

Hierarchy Generation: Finally, the script constructs the hierarchical outline for the JSON output. It determines the level of each heading (e.g., H1, H2) by comparing its font size to that of the preceding heading. A larger font indicates a higher level in the hierarchy (e.g., moving from an H2 to an H1), and a smaller font indicates a lower level.

Requirements 📋
The project is designed to be run inside a Docker container, so the only direct requirement is Docker Desktop.

The Python environment inside the container uses the following key libraries:

PyMuPDF: For parsing PDF files.

pandas: For data manipulation during text block sorting.

How to Run with Docker 🐳
Follow these steps to process your PDF files.

Prerequisites
Ensure you have Docker installed and running on your system.

File Structure
Your project folder should be organized as follows:

your_project_folder/
├── input/
│   └── your_document.pdf
├── output/
├── app.py
├── Dockerfile
└── requirements.txt
Step 1: Place Your PDFs
Copy all the PDF files you want to process into the input directory.

Step 2: Build the Docker Image
Open a terminal in your project's root directory (the one containing the Dockerfile) and run the following command. This will build the image for a standard Linux environment and tag it as pdf-parser.

Bash

docker build --platform linux/amd64 -t pdf-parser .
Step 3: Run the Container
Once the build is complete, run the following command. It will process all PDFs in the input folder and place the results in the output folder.

Bash

docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none pdf-parser
Step 4: Check the Output
The script will generate a corresponding .json file for each processed PDF in your local output folder.