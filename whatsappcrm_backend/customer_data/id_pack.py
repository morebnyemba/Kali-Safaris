"""
ID packs: the passengers' ID/passport copies, numbered exactly like the park manifest.

For a tour date (or one booking):
- PDF  — an index (No., name, ID number, nationality, booking, file) followed by
  each passenger's ID copy under the same number, two per A4 page, for the
  printed manifest folder.
- ZIP  — the original ID files named "<No>_<name>_<id number>.<ext>" plus
  index.csv, so the number on the manifest finds the file.

Numbering comes from manifests.collect_manifest_groups (the park manifest's
own source), so passenger 7 on the manifest is passenger 7 here. A booking
that isn't on a manifest yet (unpaid / awaiting details) is numbered 1..n on
its own and marked so.
"""
import csv
import io
import logging
import os
import re
import zipfile
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.utils import timezone

from .manifests import ManifestIncompleteError, collect_manifest_groups  # noqa: F401  (re-raised by views)
from .models import Traveler
from .traveler_validation import ID_REQUIRED_FROM_AGE

logger = logging.getLogger(__name__)

IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff', '.heic')


def _slug(text, fallback):
    text = re.sub(r'[^A-Za-z0-9]+', '-', str(text or '')).strip('-')
    return (text or fallback)[:40]


def _entry(seq, booking, traveler, on_manifest):
    ext = os.path.splitext(traveler.id_document.name)[1].lower() if traveler.id_document else ''
    return {
        'seq': seq, 'booking': booking, 'traveler': traveler, 'on_manifest': on_manifest,
        'file_name': (f"{seq:02d}_{_slug(traveler.name, 'passenger')}_{_slug(traveler.id_number, 'no-id')}{ext}"
                      if traveler.id_document else ''),
        'ext': ext,
    }


def entries_for_date(booking_date):
    """Every confirmed passenger on the date, in manifest order (raises ManifestIncompleteError like the manifest)."""
    groups, _totals = collect_manifest_groups(booking_date)
    entries, seq = [], 0
    for group in groups:
        for traveler in group['travelers']:
            seq += 1
            entries.append(_entry(seq, group['booking'], traveler, True))
    return entries


def entries_for_booking(booking):
    """One booking's passengers, keeping their manifest numbers when the booking is on the manifest."""
    if booking.start_date:
        try:
            on_day = [e for e in entries_for_date(booking.start_date) if e['booking'].pk == booking.pk]
        except ManifestIncompleteError:
            on_day = []
        if on_day:
            return on_day
    travelers = Traveler.objects.filter(booking=booking).order_by('traveler_type', 'name')
    return [_entry(i, booking, t, False) for i, t in enumerate(travelers, start=1)]


def _status(entry):
    t = entry['traveler']
    if t.id_document:
        return 'On file'
    if t.age is not None and t.age < ID_REQUIRED_FROM_AGE and not t.id_number:
        return f'Not required (under {ID_REQUIRED_FROM_AGE})'
    return 'MISSING'


def _read(traveler):
    try:
        with traveler.id_document.open('rb') as fh:
            return fh.read()
    except Exception:
        logger.warning("ID document for traveler %s could not be read", traveler.pk, exc_info=True)
        return None


# --- ZIP ---

def build_zip(entries, title):
    buffer = io.BytesIO()
    index = io.StringIO()
    writer = csv.writer(index)
    writer.writerow(['No', 'Full name', 'ID / passport number', 'Nationality', 'Age', 'Booking reference',
                     'On manifest', 'ID copy', 'File'])
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for e in entries:
            t = e['traveler']
            data = _read(t) if t.id_document else None
            status = _status(e) if data is not None or not t.id_document else 'Unreadable file'
            if data is not None:
                zf.writestr(e['file_name'], data)
            writer.writerow([e['seq'], t.name, t.id_number or '', t.nationality, t.age, e['booking'].booking_reference,
                             'yes' if e['on_manifest'] else 'not yet', status, e['file_name'] if data is not None else ''])
        zf.writestr('index.csv', index.getvalue())
        zf.writestr('README.txt', f"{title}\nGenerated {timezone.localtime():%d %b %Y %H:%M}.\n"
                    "File names start with the passenger's number on the park manifest.\n")
    return buffer.getvalue()


# --- PDF ---

def _image_flowable(data, ext, max_w, max_h):
    """A reportlab Image for an ID photo (EXIF-rotated, downscaled), or for page 1 of a PDF if poppler is installed."""
    from PIL import Image as PILImage, ImageOps
    from reportlab.platypus import Image as RLImage

    try:
        if ext == '.pdf':
            from pdf2image import convert_from_bytes
            img = convert_from_bytes(data, first_page=1, last_page=1, dpi=110)[0]
        else:
            img = ImageOps.exif_transpose(PILImage.open(io.BytesIO(data)))
        img = img.convert('RGB')
        img.thumbnail((1600, 1600))
        out = io.BytesIO()
        img.save(out, 'JPEG', quality=82)
        out.seek(0)
        scale = min(max_w / img.width, max_h / img.height)
        return RLImage(out, width=img.width * scale, height=img.height * scale)
    except Exception:
        logger.info("Could not render ID document (%s) into the PDF", ext, exc_info=True)
        return None


def build_pdf(entries, title, subtitle):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    brand = colors.HexColor('#C8102E')
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=14 * mm,
                            bottomMargin=14 * mm, title=title)
    width = A4[0] - 28 * mm
    story = [
        Paragraph(f"<font color='#C8102E'><b>Kalai Safaris</b></font> · {escape(title)}", styles['Title']),
        Paragraph(escape(subtitle), styles['Normal']),
        Paragraph("Numbers match the park entry manifest. ID files in the ZIP start with the same number.", styles['Italic']),
        Spacer(1, 8),
    ]
    rows = [['No', 'Full name', 'ID / passport no.', 'Nationality', 'Booking', 'ID copy']]
    for e in entries:
        t = e['traveler']
        rows.append([str(e['seq']) + ('' if e['on_manifest'] else '*'), Paragraph(escape(t.name), styles['BodyText']),
                     t.id_number or '—', t.nationality or '—', e['booking'].booking_reference, _status(e)])
    table = Table(rows, colWidths=[12 * mm, 52 * mm, 36 * mm, 28 * mm, 34 * mm, None], repeatRows=1)
    style = [
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8.5), ('FONT', (0, 1), (-1, -1), 'Helvetica', 8.5),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFF4EC')), ('LINEBELOW', (0, 0), (-1, 0), 0.8, brand),
        ('GRID', (0, 1), (-1, -1), 0.25, colors.HexColor('#E5DDD5')), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    for i, e in enumerate(entries, start=1):
        if _status(e) == 'MISSING':
            style.append(('TEXTCOLOR', (5, i), (5, i), brand))
    table.setStyle(TableStyle(style))
    story.append(table)
    if any(not e['on_manifest'] for e in entries):
        story.append(Paragraph("* Not on a park manifest yet (unpaid or awaiting passenger details).", styles['Italic']))

    with_docs = [e for e in entries if e['traveler'].id_document]
    if with_docs:
        story.append(PageBreak())
    max_h = (A4[1] - 28 * mm) / 2 - 22 * mm
    for i, e in enumerate(with_docs):
        t = e['traveler']
        heading = Paragraph(
            f"<b>No. {e['seq']}</b> · {escape(t.name)} · {escape(t.id_number or 'no ID number')} · "
            f"{escape(t.nationality or '')} · booking {escape(e['booking'].booking_reference)}", styles['Heading4'])
        data = _read(t)
        image = _image_flowable(data, e['ext'], width, max_h) if data else None
        body = image or Paragraph(
            f"Could not show this file here. Open <b>{escape(e['file_name'])}</b> from the ZIP.", styles['BodyText'])
        story.append(KeepTogether([heading, Spacer(1, 3), body, Spacer(1, 10)]))
    doc.build(story)
    return buffer.getvalue()


def response(data, filename, content_type):
    resp = HttpResponse(data, content_type=content_type)
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    resp['Cache-Control'] = 'no-store'
    return resp
