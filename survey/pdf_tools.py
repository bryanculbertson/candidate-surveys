#! /usr/bin/python3

import hashlib
import os

import reportlab.graphics.shapes as shapes
from reportlab.lib import utils
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

CANDIDATE_DETAILS = "candidate_details"

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


# Some convience functions for hrule spacing
def spacer(elems: list[Flowable]) -> None:
    elems.append(Spacer(1, 0.1 * inch))


def big_spacer(elems: list[Flowable]) -> None:
    elems.append(Spacer(1, 0.25 * inch))


def small_spacer(elems: list[Flowable]) -> None:
    elems.append(Spacer(1, 0.05 * inch))


def short_hash(s: str) -> str:
    h = hashlib.md5()
    h.update(s.encode())
    return "C" + h.hexdigest()[0:4]


# Generate a pathname with the format:
#    County/City (or County again if county-wide)/Contested Office/Candidate.pdf
# Each path is prefixed with a folder called pdfs/ to keep things clean.
# Note the paths are using unix style delimeters. This should be made
# cross-platform.
def generate_filename(candidate: dict, conf: dict) -> str:
    path = conf["output_directory"]
    for elem in conf["file_structure"]:
        path = "%s/%s" % (path, candidate[elem].replace("/", "-"))
    path = "%s.pdf" % path

    return path


def get_candidate_details(questionnaire: dict, conf: dict) -> dict:
    candidate = {}
    for prop in conf[CANDIDATE_DETAILS]:
        candidate[prop] = questionnaire[prop].strip()

    return candidate


def get_prompt(question: str, conf: dict) -> str:
    if question in conf["question_overrides"]:
        return conf["question_overrides"][question]

    return question


# Print the first section of the document, which details who the candidate is.
def print_candidate_details(d: list[Flowable], candidate: dict, conf: dict) -> None:
    for elem in conf["candidate_details"]:
        d.append(Paragraph("<b>%s</b>: %s" % (get_prompt(elem, conf), candidate[elem])))
        spacer(d)


# Print a single paragraph of a candidate answer.
def print_answer_subpart(
    d: list[Flowable], part: str, print_not_answered: bool = False
) -> None:
    if part == "" and print_not_answered:
        d.append(Paragraph("<i>Not answered.</i>", ANSWER_STYLE))
    else:
        d.append(Paragraph("%s" % part.strip(), ANSWER_STYLE))


# Print candidate answer to a single question.
def print_answer(d: list[Flowable], answer: str) -> None:
    for _, para in enumerate(answer.split("\n")):
        if para != "\n":
            print_answer_subpart(d, para)
            small_spacer(d)


def print_question_subpart(d: list[Flowable], part: str, header: str = "") -> None:
    d.append(Paragraph("<b>%s%s</b>" % (header, part.strip()), BODY_STYLE))


# Print out a bolded copy of a question.
def print_question(d: list[Flowable], question: str, num: int) -> None:
    for i, para in enumerate(question.split("\n")):
        if para != "\n":
            if i == 0:
                print_question_subpart(d, para, header="%s. " % num)
            else:
                print_question_subpart(d, para)
            small_spacer(d)


# Print all questions and answer for a single questionnare.
def print_answers(d: list[Flowable], questionnare: dict, conf: dict) -> None:
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


def get_default_image_size(
    img: utils.ImageReader, largest_dim: float
) -> tuple[float, float]:
    iw, ih = img.getSize()
    width, height = 0.0, 0.0

    if iw >= ih:
        width = largest_dim
        height = ih * (width / float(iw))
    else:
        height = largest_dim
        width = iw * (height / float(ih))

    return (width, height)


def find_target_pixels(largest_dim: float, valid_images: list[str]) -> float:
    smallest = largest_dim * largest_dim

    for path in valid_images:
        img = utils.ImageReader(path)
        iw, ih = get_default_image_size(img, largest_dim)
        pixels = iw * ih
        if pixels < smallest:
            smallest = pixels

    return smallest


def get_image(path: str, largest_dim: float, target_pix: float) -> Image:
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
def add_logos(d: list[Flowable], directory: str, conf: dict) -> None:
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


def print_header(d: list[Flowable], conf: dict) -> None:
    ps = ParagraphStyle("title")
    ps.alignment = TA_CENTER

    ps.fontSize = 18
    d.append(Paragraph('<font face="times"><b>%s</b></font>' % conf["name"], ps))
    big_spacer(d)

    ps.fontSize = 14
    d.append(Paragraph('<font face="times">%s</font>' % conf["subname"], ps))

    big_spacer(d)
    big_spacer(d)


def print_footer(d: list[Flowable], conf: dict) -> None:
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
def dump_questionnare_to_pdf(questionnare: dict, conf: dict) -> None:
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
    elements: list[Flowable] = []

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

    def configureDoc(canvas: Canvas, doc: BaseDocTemplate) -> None:
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


def style_name(field: str, value: str) -> str:
    return "%s_%s" % (short_hash(field), value)
