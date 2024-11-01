#! /usr/bin/python3
# type: ignore

import csv
import hashlib
import json
import numbers
import os
import re

import reportlab.graphics.shapes as shapes
from reportlab.lib import utils
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from yattag import Doc, indent

CANDIDATE_DETAILS = "candidate_details"
CONF_HTML_TABLE = "html_table"
CONF_HTML_COLOR = "color_matches"
CONF_HTML_TITLES = "title_overrides"

# A quick style to justify paragraph text
JUSTIFY_STYLE = ParagraphStyle("justify")
JUSTIFY_STYLE.alignment = TA_JUSTIFY

# A quick style to justify paragraph text
BODY_STYLE = ParagraphStyle("body")
BODY_STYLE.alignment = TA_LEFT

ANSWER_STYLE = ParagraphStyle("body")
ANSWER_STYLE.alignment = TA_LEFT
ANSWER_STYLE.firstLineIndent = 0
ANSWER_STYLE.leftIndent = 12

# A quick style to center paragraph text
CENTER_STYLE = ParagraphStyle("justify")
CENTER_STYLE.alignment = TA_CENTER

doc, tag, text = Doc().tagtext()


# Some convience functions for hrule spacing
def spacer(elems):
    elems.append(Spacer(1, 0.1 * inch))


def big_spacer(elems):
    elems.append(Spacer(1, 0.25 * inch))


def small_spacer(elems):
    elems.append(Spacer(1, 0.05 * inch))


def short_hash(s):
    h = hashlib.md5()
    h.update(s.encode())
    return "C" + h.hexdigest()[0:4]


# Generate a pathname with the format:
#    County/City (or County again if county-wide)/Contested Office/Candidate.pdf
# Each path is prefixed with a folder called pdfs/ to keep things clean.
# Note the paths are using unix style delimeters. This should be made
# cross-platform.
def generate_filename(candidate, conf):
    path = conf["output_directory"]
    for elem in conf["file_structure"]:
        path = "%s/%s" % (path, candidate[elem].replace("/", "-"))
    path = "%s.pdf" % path

    return path


def get_candidate_details(questionnaire, conf):
    candidate = {}
    for prop in conf[CANDIDATE_DETAILS]:
        candidate[prop] = questionnaire[prop].strip()

    return candidate


def get_prompt(question, conf):
    # print("Override '%s'?" % question)
    if question in conf["question_overrides"]:
        # print("Yes: '%s'" % conf["question_overrides"][question])
        return conf["question_overrides"][question]
    # print("No")

    return question


# Print the first section of the document, which details who the candidate is.
def print_candidate_details(d, candidate, conf):
    for elem in conf["candidate_details"]:
        d.append(Paragraph("<b>%s</b>: %s" % (get_prompt(elem, conf), candidate[elem])))
        spacer(d)


# Print a single paragraph of a candidate answer.
def print_answer_subpart(d, part):
    # if part == "":
    # d.append(Paragraph("<i>Not answered.</i>", ANSWER_STYLE))
    # else:
    d.append(Paragraph("%s" % part.strip(), ANSWER_STYLE))


# Print candidate answer to a single question.
def print_answer(d, answer):
    for _, para in enumerate(answer.split("\n")):
        if para != "\n":
            print_answer_subpart(d, para)
            small_spacer(d)


def print_question_subpart(d, part, header=""):
    d.append(Paragraph("<b>%s%s</b>" % (header, part.strip()), BODY_STYLE))


# Print out a bolded copy of a question.
def print_question(d, question, num):
    for i, para in enumerate(question.split("\n")):
        if para != "\n":
            if i == 0:
                print_question_subpart(d, para, header="%s. " % num)
            else:
                print_question_subpart(d, para)
            small_spacer(d)


# Print all questions and answer for a single questionnare.
def print_answers(d, questionnare, conf):
    spacer(d)

    conditional_fields = {}
    if conf.get("conditional_sections"):
        for condition_field, conditions in conf["conditional_sections"].items():
            for condition in conditions:
                for field in condition["fields"]:
                    conditional_fields[field] = {
                        "compare_field": condition_field,
                        "compare_value": condition["value"],
                    }

    i = 1
    for _, t in enumerate(questionnare.items()):
        q, a = t[0], t[1]

        # skip these columns; they are handled elsewhere or not printed at all
        if q in conf["ignored_fields"] or q in conf["candidate_details"]:
            continue

        if q in conditional_fields:
            compare_field = conditional_fields[q]["compare_field"]
            compare_value = conditional_fields[q]["compare_value"]

            if questionnare[compare_field] != compare_value:
                continue

        print_question(d, get_prompt(q, conf), i)
        spacer(d)
        print_answer(d, a)
        spacer(d)
        i = i + 1


def get_default_image_size(img, largest_dim):
    iw, ih = img.getSize()
    width, height = 0, 0

    if iw >= ih:
        width = largest_dim
        height = ih * (width / float(iw))
    else:
        height = largest_dim
        width = iw * (height / float(ih))

    return (width, height)


def find_target_pixels(largest_dim, valid_images):
    smallest = largest_dim * largest_dim

    for path in valid_images:
        img = utils.ImageReader(path)
        iw, ih = get_default_image_size(img, largest_dim)
        pixels = iw * ih
        if pixels < smallest:
            smallest = pixels

    return smallest


def get_image(path, largest_dim, target_pix):
    img = utils.ImageReader(path)

    width, height = get_default_image_size(img, largest_dim)
    n_pix = width * height

    if n_pix > target_pix:
        reduct = (1 + target_pix / float(n_pix)) / 2.0
        height = height * reduct
        width = width * reduct

    return Image(path, width=width, height=height)


# Add all logos present in the directory to a table 4xN table. Each image is
# resized to in width 100px with aspect retained (see get_image()). The last row
# may not be full.
#
# Method could use a ton of generalization, but we're working fast here...
def add_logos(d, directory, conf):
    valid_images = []
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f):
            valid_images.append(f)

    COLUMNS = conf["logo_columns"]
    IMGSIZE = 400 / COLUMNS
    ROWHEIGHT = IMGSIZE + 10
    COLWIDTH = IMGSIZE + 10

    num_p = find_target_pixels(IMGSIZE, valid_images)

    table = []
    row = []
    i = 0
    rows = 0
    for img in valid_images:
        row.append(get_image(img, IMGSIZE, num_p))

        i = i + 1
        if i % COLUMNS == 0:
            table.append(row)
            rows = rows + 1
            row = []

    if i % COLUMNS != 0 and len(row) > 0:
        table.append(row)
        rows = rows + 1

    tstyle = TableStyle(
        [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]
    )

    d.append(
        Table(
            table,
            colWidths=[COLWIDTH] * COLUMNS,
            rowHeights=[ROWHEIGHT] * rows,
            style=tstyle,
        )
    )


def print_header(d, conf):
    ps = ParagraphStyle("title")
    ps.alignment = TA_CENTER

    ps.fontSize = 18
    d.append(Paragraph('<font face="times"><b>%s</b></font>' % conf["name"], ps))
    big_spacer(d)

    ps.fontSize = 14
    d.append(Paragraph('<font face="times">%s</font>' % conf["subname"], ps))

    big_spacer(d)
    big_spacer(d)


def print_footer(d, conf):
    elems = []

    hrule = shapes.Drawing(5.5 * inch, 10)
    hrule.add(shapes.Line(1 * inch, 4, 5.15 * inch, 4, strokColor=black, strokeWidth=1))

    elems.append(hrule)
    big_spacer(elems)

    elems.append(Paragraph("<i>%s</i>" % conf["footer"], BODY_STYLE))

    add_logos(elems, conf["logo_directory"], conf)

    d.append(KeepTogether(elems))


# Create a properly named PDF file and write out the results of a the associated
# candidate questionnare.
def dump_questionnare_to_pdf(questionnare, conf):
    # Extract candidate details from the questionnare
    candidate = get_candidate_details(questionnare, conf)

    # Ensure the directory exists.
    filename = generate_filename(candidate, conf)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    print("Creating %s" % filename)

    # Start the PDF document. Set letter because we are silly Americans.
    doc = SimpleDocTemplate(filename, pagesize=letter)

    # elements will hold all document elements, which must be Flowable.
    # Functions called below primarily append to this list.
    elements = []

    print_header(elements, conf)

    # Setup the main document elements
    print_candidate_details(elements, candidate, conf)

    hrule = shapes.Drawing(5.5 * inch, 10)
    hrule.add(shapes.Line(1 * inch, 4, 5.15 * inch, 4, strokColor=black, strokeWidth=1))
    elements.append(hrule)

    small_spacer(elements)
    print_answers(elements, questionnare, conf)

    big_spacer(elements)
    print_footer(elements, conf)

    def configureDoc(canvas, doc):
        canvas.saveState()

        canvas.setAuthor(conf["pdf_author"])
        canvas.setSubject("%s %s" % (conf["name"], conf["subname"]))
        phrases = []
        for x in conf["pdf_keyphrases"]:
            if x in questionnare.keys():
                phrases.append(questionnare[x])
            else:
                phrases.append(x)
        canvas.setKeywords(", ".join(phrases))
        canvas.setCreator(conf["pdf_creator"])
        canvas.setTitle("%s - %s" % (conf["name"], candidate["Name"]))

        canvas.restoreState()

    # Render the doucment; this also writes to the file specified in the
    # constructor
    doc.build(elements, onFirstPage=configureDoc)


def style_name(field, value):
    return "%s_%s" % (short_hash(field), value)


def print_style(html_conf):
    with tag("head"):
        with tag("style"):
            text("td.header { font-weight: bold; }\n\n")
            text(
                """/* Tooltip container */
.tooltip {
  border-bottom: 1px dotted black; /* If you want dots under the hoverable text */
}

/* Tooltip text */
.tooltip .tooltiptext {
  visibility: hidden;
  width: 240;
  background-color: white;
  color: #fff;
  text-align: center;
  padding: 5px 0;
  border-radius: 6px;

  /* Position the tooltip text - see examples below! */
  position: absolute;
  z-index: 1;
}

/* Show the tooltip text when you mouse over the tooltip container */
.tooltip:hover .tooltiptext {
  visibility: visible;
}\n\n"""
            )
            if CONF_HTML_COLOR in html_conf:
                for k, v in html_conf[CONF_HTML_COLOR].items():
                    for name, nv in v.items():
                        text(
                            "td.%s { background-color: %s; }\n"
                            % (style_name(k, name), nv)
                        )


def print_table_header(html_conf):
    with tag("tr"):
        for col_name in html_conf["cols"]:
            with tag("td", klass="header"):
                text(html_conf[CONF_HTML_TITLES].get(col_name, col_name))


def find_cell_color_class(cell_value, field, lookup):
    if lookup:
        for k, v in lookup.items():
            if re.match("^%s" % k, cell_value, flags=re.IGNORECASE) is not None:
                return style_name(field, k), k

    return None, None


def dump_questionnare_to_row(questionnare, conf):
    html_conf = conf[CONF_HTML_TABLE]

    with tag("tr"):
        for col_name in html_conf["cols"]:
            cell_value = questionnare[col_name]
            color = html_conf.get(CONF_HTML_COLOR, {})

            c, v = find_cell_color_class(
                cell_value, col_name, color.get(col_name, None)
            )
            if c:
                with tag("td", klass="%s" % c):
                    text(v)
            else:
                if color.get(col_name):
                    with tag("td", klass="tooltip"):
                        text("other")
                        with tag("span", klass="tooltiptext"):
                            text(cell_value)
                else:
                    with tag("td"):
                        text(cell_value)


def wrap_html_table(conf, iter_f):
    html_conf = conf[CONF_HTML_TABLE]

    with tag("html"):
        print_style(html_conf)
        with tag("body"):
            with tag("table"):
                print_table_header(html_conf)
                iter_f()


def load_conf(conf_filename, csv_reader):
    conf = json.loads(open(conf_filename).read())

    fields = csv_reader.fieldnames
    for i, x in enumerate(conf["file_structure"]):
        if isinstance(x, numbers.Number):
            print("Replacing %s with %s in file_structure." % (x, fields[x]))
            conf["file_structure"][i] = fields[x]

    for i, x in enumerate(conf["candidate_details"]):
        if isinstance(x, numbers.Number):
            print("Replacing %s with %s in candidate_details." % (x, fields[x]))
            conf["candidate_details"][i] = fields[x]

    overrides = {}
    for k, v in conf["question_overrides"].items():
        if k.isnumeric():
            k = int(k)
            print("Replacing '%s' with '%s' in question_overrides." % (fields[k], v))
            overrides[fields[k]] = v
        else:
            overrides[k] = v
    conf["question_overrides"] = overrides

    # check for an HTML table; load if it exists
    if CONF_HTML_TABLE in conf:
        html_spec = conf[CONF_HTML_TABLE]

        for i, x in enumerate(html_spec["cols"]):
            if isinstance(x, numbers.Number):
                html_spec["cols"][i] = fields[x]

        if CONF_HTML_COLOR in html_spec:
            overrides = {}
            for k, v in html_spec[CONF_HTML_COLOR].items():
                print("%s : %s" % (k, v))
                if k.isnumeric():
                    k = int(k)
                    overrides[fields[k]] = v
                else:
                    overrides[k] = v

            html_spec[CONF_HTML_COLOR] = overrides

        overrides = {}
        if CONF_HTML_TITLES in html_spec:
            for k, v in html_spec[CONF_HTML_TITLES].items():
                print("%s : %s" % (k, v))
                if k.isnumeric():
                    k = int(k)
                    overrides[fields[k]] = v
                else:
                    overrides[k] = v

        html_spec[CONF_HTML_TITLES] = overrides
        print(html_spec)

    return conf


def run(args):
    with open(args.csv_filename) as csvfile:
        # Assumptions about the file:
        #  * Tab delimited
        #  * Proper '\n' delimiters for end-of-line
        #  * The first line in the file contains column key names. These must match
        #    the ALL_CAPS globals at the top of this file.
        reader = csv.DictReader(csvfile, delimiter=",")
        conf = load_conf(args.config_filename, reader)

        conf["logo_directory"] = args.logo_directory.rstrip("/").strip()
        conf["output_directory"] = args.output_directory.rstrip("/").strip()
        print(conf)

        dump_html = CONF_HTML_TABLE in conf

        def loop_iter():
            for row in reader:
                dump_questionnare_to_pdf(row, conf)
                if dump_html:
                    dump_questionnare_to_row(row, conf)

        if dump_html:
            wrap_html_table(conf, loop_iter)
        else:
            loop_iter()

        if dump_html:
            print("Dumping HTML table.")
            with open("test.html", "w") as html_doc:
                html_doc.write(indent(doc.getvalue()))
