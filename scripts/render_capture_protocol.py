"""Render the submission's operator protocol as exactly one A4 page."""
from pathlib import Path
import re
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission/Part_1_Capture_Routes_and_Input_Tiers'
source = (OUT / 'Capture_Protocol.md').read_text()
fig = plt.figure(figsize=(8.2677, 11.6929), facecolor='white')
width, height = fig.get_size_inches() * 72
margin = 38
font = 10.5
# DejaVu Sans average width is below this conservative wrapping estimate.
columns = int((width - 2 * margin) / (font * .51))
y = height - 35
for paragraph in source.split('\n\n'):
    paragraph = re.sub(r'\*\*(.*?)\*\*', r'\1', paragraph).strip()
    heading = paragraph.startswith('#')
    title = paragraph.startswith('# ')
    paragraph = re.sub(r'^#+\s*', '', paragraph)
    size = 17 if title else (10.5 if heading else font)
    lines = textwrap.wrap(' '.join(paragraph.split()), width=columns if not title else 65,
                          break_long_words=False, break_on_hyphens=False)
    for line in lines:
        fig.text(margin / width, y / height, line, fontsize=size,
                 fontfamily='DejaVu Sans', weight='bold' if heading else 'normal',
                 va='top', color='#17344c' if heading else '#20272c')
        y -= size * 1.22
    y -= 5 if heading else 7
if y < 27:
    raise RuntimeError(f'Protocol overflows page: bottom={y:.1f} pt. Shorten text.')
fig.text(margin / width, 18 / height, 'ASTRA | Part 1 | Stock capture protocol', fontsize=7, color='#596570')
fig.text((width - margin) / width, 18 / height, '1 / 1', fontsize=7, ha='right', color='#596570')
fig.savefig(OUT / 'Capture_Protocol.pdf', metadata={'Title': 'Part 1 — Stray Scanner 1.4 Capture Protocol'})
fig.savefig('/tmp/astra_capture_protocol_preview.png', dpi=130)
plt.close(fig)
print(f'Created one-page protocol; bottom text clearance: {y:.1f} pt')
