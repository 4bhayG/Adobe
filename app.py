import fitz
import pandas as pd
from operator import itemgetter
import re
import json
import os

def pdf_to_dict(path):
    doc = fitz.open(path)
    font_counts, styles = fonts(doc, granularity=True)
    size_tag = font_tags(font_counts, styles, granularity=True)
    elements = headers_para(doc, size_tag) # Pass size_tag here

    final = []
    for ele in elements:
        ele['text'] = ele['text'].strip()
        if len(ele['text']) < 90 and len(ele['text']) > 3 and not re.match('[a-z].*', ele['text']) and re.match('.*[^\d\s].*', ele['text']) and re.match('.*[^.,;({[]\s*$', ele['text']):
          final.append(ele)

    title = find_primary_heading(final)

    # Handle case where no title is found
    title_text = title['text'] if title else ""

    return title_text, final


def relative_borderdistance(list_of_bboxes, x_page, y_page, whole_page=True):  #sort text by y and then x
    list_of_bboxlists = []
    entry_count = 0

    for box in list_of_bboxes:
        x_left = box[0]
        y_top = box[1]
        x_right = box[2]
        y_bottom = box[3]

        # Calculate relative distances from borders
        x_l_distance = round(x_left / x_page, 3)
        x_r_distance = round(x_right / x_page, 3)
        y_t_distance = round(y_top / y_page, 3)
        y_b_distance = round(y_bottom / y_page, 3)

        # Include actual coordinates for sorting
        if whole_page:
            entry = [x_l_distance, y_t_distance, y_b_distance, x_r_distance, entry_count, y_top, x_left]
        else:
            entry = [y_t_distance, x_l_distance, y_b_distance, x_r_distance, entry_count, y_top, x_left]

        entry_count += 1
        list_of_bboxlists.append(entry)

    # Create DataFrame with proper column names
    column_names = ['x_left_rel', 'y_top_rel', 'y_bottom_rel', 'x_right_rel', 'entry_count', 'y_sort', 'x_sort']
    df_bboxes = pd.DataFrame(list_of_bboxlists, columns=column_names)

    # Sort by y-coordinate first, then by x-coordinate
    df_bboxes_sorted = df_bboxes.sort_values(by=['y_sort', 'x_sort'])

    # Get the sorted order
    sorted_entry_counts = df_bboxes_sorted['entry_count'].to_list()

    # For highest/lowest, sort by y only
    df_y_sorted = df_bboxes.sort_values(by=['y_sort'])
    y_highest = df_y_sorted['entry_count'].iloc[0]   # Topmost box
    y_lowest = df_y_sorted['entry_count'].iloc[-1]   # Bottommost box

    return sorted_entry_counts, y_highest, y_lowest


def fonts(doc, granularity):
    styles = {}
    font_counts = {}
    for page in doc:
        blocks = page.get_text("dict", flags=11)["blocks"]
        for b in blocks:
            if b['type'] == 0:
                for l in b["lines"]:
                    for s in l["spans"]:
                        if granularity:
                            identifier = f"{s['size']}_{s['flags']}_{s['font']}_{s['color']}"
                            styles[identifier] = {'size': s['size'], 'flags': s['flags'], 'font': s['font'],
                                                  'color': s['color']}
                        else:
                            identifier = f"{s['size']}"
                            styles[identifier] = {'size': s['size'], 'font': s['font']}

                        font_counts[identifier] = font_counts.get(identifier, 0) + 1
    font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)
    if len(font_counts) < 1:
        raise ValueError("Zero discriminating fonts found!")
    return font_counts, styles


def font_tags(font_counts, styles, granularity):
    p_style = styles[font_counts[0][0]]
    p_size = p_style['size']
    sort_on_size = dict(sorted(styles.items(), key = lambda x: x[1]['size']))
    index_of_p = list(sort_on_size.keys()).index(font_counts[0][0])
    id_upper = 1
    id_lower = 1
    app_tag = {}
    app_tag[font_counts[0][0]] = f"<p>"
    if index_of_p > 0:
        index_of_style = 0
        while index_of_style < index_of_p:
            app_tag[list(sort_on_size.keys())[index_of_style]] = f"<s{id_lower}>"
            id_lower += 1
            index_of_style += 1
    index_of_style = index_of_p + 1
    while index_of_style < len(list(sort_on_size.keys())):
        app_tag[list(sort_on_size.keys())[index_of_style]] = f"<h{id_upper}>"
        id_upper += 1
        index_of_style += 1
    return app_tag


def identify_table_regions(page):
    """Identify potential table regions based on line patterns"""
    tables = []

    # Get all drawing objects (lines, rectangles, etc.)
    drawings = page.get_drawings()

    # Look for horizontal and vertical lines that might indicate tables
    hor_lines = []
    ver_lines = []

    for item in drawings:
        rect = item["rect"]
        width = rect.width
        height = rect.height

        # Consider thin, long lines as table borders
        if width > 50 and height < 5:  # Horizontal lines
            hor_lines.append(rect)
        elif height > 20 and width < 5:  # Vertical lines
            ver_lines.append(rect)

    # Group nearby lines to form table boundaries
    if hor_lines and ver_lines:
        # Create bounding boxes around detected table areas
        if hor_lines and ver_lines:
            min_x = min(line.x0 for line in ver_lines)
            max_x = max(line.x1 for line in ver_lines)
            min_y = min(line.y0 for line in hor_lines)
            max_y = max(line.y1 for line in hor_lines)
            tables.append(fitz.Rect(min_x, min_y, max_x, max_y))

    # print(tables)
    return tables


def headers_para(doc, size_tag):
    initial_elements = headers_para_original(doc, size_tag)
    merged_elements = []
    if not initial_elements:
        return merged_elements

    i = 0
    while i < len(initial_elements):
        current_elem = initial_elements[i]
        j = i + 1
        while j < len(initial_elements):
            next_elem = initial_elements[j]
            if  next_elem['tag'] != current_elem['tag']:
                break
            current_elem['text'] += f" {next_elem['text']}"
            current_elem['p_position_x'] = next_elem['p_position_x']
            current_elem['p_position_y'] = next_elem['p_position_y']
            j += 1

        page = doc[initial_elements[i]['page_num']]
        y = page.rect.height

        if initial_elements[i]['p_position_y'] < 0.05*y or initial_elements[i]['p_position_y'] > 0.9*y:
            i = j
            continue

        cond1 = len(merged_elements) == 0 or initial_elements[i]['p_position_y'] != merged_elements[-1]['p_position_y']
        cond2 = j >= len(initial_elements) or initial_elements[j]['p_position_y'] != initial_elements[j-1]['p_position_y']
        cond3 = re.match('.*[:!\?\-]$', current_elem['text'].strip())

        if cond1 and cond2:
            merged_elements.append(current_elem)
        elif cond1 and cond3:
            merged_elements.append(current_elem)

        i = j

    return merged_elements

def headers_para_original(doc, size_tag):
    header_para = []
    first_span = True
    previous_s = {}
    last_highest_or_lowest = {}
    page_num = 0
    t_point = 30


    for page in doc:
        x_page = page.get_text("dict")['width']
        y_page = page.get_text("dict")['height']
        blocks = page.get_text("dict", flags=11)["blocks"]

        # Identify potential table regions
        table_regions = identify_table_regions(page)

        list_of_bboxes_blocks = [block['bbox'] for block in blocks if block['type'] == 0]

        if len(list_of_bboxes_blocks) > 0:
            bboxes_ordered, y_highest, y_lowest = relative_borderdistance(list_of_bboxes_blocks, x_page, y_page)
            for b_index in bboxes_ordered:
                block = blocks[b_index]
                if block['type'] == 0:
                    block_string = ""
                    list_of_bboxes_spans = []

                    # Check if block is inside any table region

                    for line in block["lines"]:
                        for span in line["spans"]:
                            span_rect = fitz.Rect(span["bbox"])
                            is_in_table = any(span_rect.intersects(table_rect) for table_rect in table_regions)
                            if not is_in_table :
                                list_of_bboxes_spans.append(span['bbox'])


                    if len(list_of_bboxes_spans) > 0:
                        span_bboxes_ordered, _, _ = relative_borderdistance(list_of_bboxes_spans, x_page, y_page, whole_page=False)
                        block_spans = [span for line in block["lines"] for span in line['spans']]
                        for ordered_s_index in span_bboxes_ordered:
                            s = block_spans[ordered_s_index]
                            font_label = f"{s['size']}_{s['flags']}_{s['font']}_{s['color']}"
                            f_tag = size_tag.get(font_label, "<p>")

                            if first_span:
                                previous_s = s
                                first_span = False
                                block_string = {
                                    'tag': f_tag,
                                    'text': s['text'],
                                    'page_num': page_num,
                                    'p_position_x': s['origin'][0],
                                    'p_position_y': s['origin'][1],
                                    'font_size': s['size'],
                                    'font_label': font_label
                                }
                                header_para.append(block_string)
                            else:
                                if header_para:
                                    previous_s_element = header_para[-1]
                                else:
                                    previous_s_element = {}

                                if s['text'].strip() == '':
                                    pass
                                else:
                                    block_string = {
                                        'tag': f_tag,
                                        'text': s['text'],
                                        'page_num': page_num,
                                        'p_position_x': s['origin'][0],
                                        'p_position_y': s['origin'][1],
                                        'font_size': s['size'],
                                        'font_label': font_label
                                    }
                                    header_para.append(block_string)
                                    previous_s = block_string
        page_num += 1
    return header_para


def find_primary_heading(block_strings):
    if not block_strings:
        return None
    page_0_blocks_with_index = [(i, block) for i, block in enumerate(block_strings) if block['page_num'] == 0]

    if not page_0_blocks_with_index:
        # Fallback to first block on any page if page 0 is empty
        if block_strings:
             return block_strings.pop(0)
        return None

    page_0_blocks = [block for _, block in page_0_blocks_with_index]

    heading_tags = ['H1', 'h1', 'Heading1', 'Title', 'title']
    for index, block in page_0_blocks_with_index:
        if block['tag'] in heading_tags:
            heading_block = block_strings.pop(index)
            return heading_block

    max_font_size = max(block['font_size'] for block in page_0_blocks)
    largest_blocks_with_index = [(i, block) for i, block in page_0_blocks_with_index if block['font_size'] == max_font_size]

    if len(largest_blocks_with_index) > 1:
        largest_blocks_with_index.sort(key=lambda x: x[1]['p_position_y'])

    if largest_blocks_with_index:
        index_to_remove = largest_blocks_with_index[0][0]
        heading_block = block_strings.pop(index_to_remove)
        return heading_block

    substantial_blocks_with_index = [(i, block) for i, block in page_0_blocks_with_index if len(block['text'].strip()) > 5]

    if substantial_blocks_with_index:
        substantial_blocks_with_index.sort(key=lambda x: x[1]['p_position_y'])
        index_to_remove = substantial_blocks_with_index[0][0]
        heading_block = block_strings.pop(index_to_remove)
        return heading_block

    # Final fallback: return the first block on page 0 if no other criteria met
    if page_0_blocks_with_index:
        return block_strings.pop(page_0_blocks_with_index[0][0])

    return None


def create_output_json(pdf_path, output_dir):
    """
    Processes a single PDF file and saves its outline as a JSON file in the output directory.
    """
    title, heading_blocks = pdf_to_dict(pdf_path)
    outline = []
    current_level = 1

    for i, block in enumerate(heading_blocks):
        text = block['text'].strip()
        page_num = block['page_num']

        if not text:
            continue

        if i == 0:
            current_level = 1
        else:
            prev_block = heading_blocks[i-1]
            current_font_size = block['font_size']
            prev_font_size = prev_block['font_size']

            if current_font_size > prev_font_size:
                current_level = max(1, current_level - 1)
            elif current_font_size < prev_font_size:
                current_level += 1

        current_level = min(10, max(1, current_level))
        level_label = f"H{current_level}"

        outline.append({
            "level": level_label,
            "text": text,
            "page": page_num
        })

    output_data = {
        "title": title,
        "outline": outline
    }

    # --- Create the correct output path ---
    base_name = os.path.basename(pdf_path)
    file_stem = os.path.splitext(base_name)[0]
    output_filename = f"{file_stem}.json"
    output_filepath = os.path.join(output_dir, output_filename)

    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully processed '{base_name}' -> '{output_filename}'")
    return output_filepath

# --- Main execution block for Docker ---
if __name__ == "__main__":
    INPUT_DIR = "/app/input"
    OUTPUT_DIR = "/app/output"
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.isdir(INPUT_DIR):
        print(f"Error: Input directory {INPUT_DIR} not found or is not a directory.")
        exit(1)

    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in {INPUT_DIR}")
    else:
        print(f"Found {len(pdf_files)} PDF file(s) to process...")
        for pdf_file in pdf_files:
            input_path = os.path.join(INPUT_DIR, pdf_file)
            create_output_json(input_path, OUTPUT_DIR)
            # try:
            #     create_output_json(input_path, OUTPUT_DIR)
            # except Exception as e:
            #     print(f"Error processing file {pdf_file}: {e}")