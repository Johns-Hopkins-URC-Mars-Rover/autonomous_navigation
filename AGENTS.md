# AGENTS.md

Instructions for any AI agent working in this repository (Claude Code, Codex, Cursor, Gemini CLI, Copilot, and others). Skills below are plain Markdown on purpose: any agent that can read a file can follow them.

## Skills index

| Skill | Use it when |
| --- | --- |
| [Skill: Creating clear graphs, charts, diagrams and visualizations](#skill-creating-clear-graphs-charts-diagrams-and-visualizations) | You are about to make any chart, plot, pipeline/flow diagram, architecture diagram, timeline, table graphic, SVG, or dashboard. |

---

# Skill: Creating clear graphs, charts, diagrams and visualizations

**Audience for this skill:** an AI agent that writes code or markup to produce visuals but cannot "see" the result the way a designer does. Everything here is therefore stated as concrete rules, numbers, and a verification loop. Do not skip the loop in section 9. Most bad AI visuals are bad because the agent never looked at its own output.

**The one-sentence goal:** a stranger should understand the point of the visual in 5 seconds and be able to find any detail in 30 seconds, without asking anyone.

## 0. Quick checklist (read this even if you read nothing else)

Before you say a visual is finished, every line must be true:

- [ ] I can state the single message of the visual in one sentence, and it is written on the visual as the title.
- [ ] I rendered it to an image and **looked at the image** (not just the code).
- [ ] No text is cut off, overlapping other text, overflowing its box, or touching an edge.
- [ ] Body text is at least 12 px at the size the visual is normally viewed (14 px or more if it will be shrunk to fit a page).
- [ ] Text/background contrast is at least 4.5:1 (dark text on white or very light fills; white text only on dark, saturated fills).
- [ ] Color is never the only way to tell things apart (labels, shapes, patterns, or position also differ).
- [ ] Every axis, arrow, color, abbreviation, and unit is explained on the visual itself.
- [ ] Alignment: things that are the same kind are the same size and aligned on a shared grid.
- [ ] There is a legend or "how to read this" if any symbol is not obvious.
- [ ] The visual is generated from a script or data file that is committed, not hand-edited output.
- [ ] Every fact on it is traceable to a source in the repo, data, or the user's request. Nothing invented.

## 1. When to make a visual at all

A visual earns its place only if it shows something prose or a table shows poorly: **relationships, sequence, flow, comparison, distribution, change over time, location, or hierarchy.**

- If the content is a list of independent facts: use a bullet list or table, not a diagram.
- If you have fewer than 3 data points: write a sentence.
- If the user asked for a visual: make one, but still apply every rule below.
- Never add a visual as decoration. Every shape must carry information.

## 2. Process (follow in order)

1. **Write the message.** One sentence: "The reader should conclude ___." Example: "Three people work in parallel and only meet at the integration gate."
2. **Name the audience and the reading context.** Teammate who knows the project, a newcomer, a reviewer, a slide audience? Printed, on a phone, zoomed in a browser? A newcomer needs more labels and definitions; a slide needs fewer, larger words.
3. **Inventory the content.** List every entity (boxes, series, nodes), every relationship (arrows, joins), and every attribute you want shown. Pull these from the real source files, not memory. When unsure whether to include something, include it, then decide in step 5 how to make it quiet (smaller, grey, grouped), not whether to delete it. Hiding detail is a hierarchy decision, not a deletion decision, unless the user asked for a simplified version.
4. **Pick the visual form** using section 3.
5. **Decide hierarchy.** Choose what is level 1 (title and the main message), level 2 (group labels, box titles), level 3 (body details), level 4 (footnotes, sources). Each level gets one visibly different style (section 5).
6. **Sketch the layout in words and numbers** (grid, columns, rows, widths) before writing markup (section 4).
7. **Build it with a generator script** (section 7), not by hand-typing coordinates one by one.
8. **Render, look, fix, repeat** (section 9). Expect at least 2 or 3 passes.
9. **Document how to regenerate it** next to the file (a docstring or README line with the exact command).

## 3. Choose the right form

| You want to show | Use | Do not use |
| --- | --- | --- |
| Sequence of steps, data flow, pipeline | Left-to-right (or top-to-bottom) flow diagram with arrows; swimlanes if different owners | Pie chart, a bulleted list pretending to be a flow |
| Who does what, in parallel, over phases | Swimlane grid: rows = people/systems, columns = phases | One long chain of boxes |
| System parts and who talks to whom | Box-and-arrow architecture diagram, arrows labelled with what travels | Unlabelled arrows |
| Hierarchy / containment | Nested boxes or a tree | A flat list |
| Change over time | Line chart (continuous) or bar chart (few discrete periods) | Pie chart, 3D |
| Compare categories | Horizontal bar chart, sorted by value | Pie with more than 3 slices, radar chart |
| Part of a whole (2-4 parts) | Single stacked bar or a pie/donut with direct labels | Pie with 5+ slices |
| Relationship between two numbers | Scatter plot (add a trend line only if it is meaningful) | Dual y-axes |
| Distribution | Histogram or box plot | Bar chart of raw counts with no bins |
| Many values across two categories | Heatmap with a labelled color scale and printed numbers | Rainbow color map |
| Precise lookup of many values | A table | Any chart |
| Timeline / schedule | Horizontal timeline with labelled phases (use relative phases if exact dates are unknown) | A table of dates when the shape of the schedule is the point |

If two forms both fit, pick the simpler one.

## 4. Layout rules (the part AIs get wrong most)

### 4.1 Use a grid, always

- Pick a **base unit** (8 px works well) and make every margin, padding, and gap a multiple of it.
- Pick a **column grid** before drawing. Example: lane label column 176 px, then N content columns with a fixed 24 to 28 px gutter. All boxes in a column share the same x and the same width.
- **Align edges.** Left edges of stacked boxes match exactly. Baselines of text in the same row match exactly. Centers match for centered items.
- **Equal things look equal.** Same-kind boxes get the same width, corner radius, border width, and padding. Different heights are fine only when the content differs, and rows should still share top edges.

### 4.2 Spacing numbers that work

| Thing | Value |
| --- | --- |
| Outer page margin | 24 to 48 px |
| Gap between sibling boxes | 24 to 28 px (never less than 16) |
| Padding inside a box | 16 px all sides (12 px minimum) |
| Space between a section title and its content | 8 to 12 px |
| Space between sections inside a box | 10 to 14 px, optionally with a 1 px light rule |
| Line height for body text | 1.3 to 1.4 times the font size (13 px text means about 17.5 px line pitch) |
| Distance from arrow tip to box edge | 2 to 4 px (never overlapping the text) |

Whitespace is a feature. If everything touches, nothing is readable. But also do not leave huge empty boxes: size boxes to content (section 7.2).

### 4.3 Reading order

- Western readers scan **left to right, top to bottom**. Put the start at top-left and the end at bottom-right. Sequence flows in the same direction everywhere. Do not mix flow directions in one diagram.
- Put the title top-left, one line, with a one-line subtitle beneath.
- Put the legend where the eye lands after the title (near the top), not hidden at the bottom.
- Group related things inside a shared container (a lane, a panel) with a light fill and a thin border, and put the group's label at the container's top-left.

### 4.4 Arrows and connectors

- Arrows are **orthogonal** (horizontal and vertical segments) unless a diagonal is the only clean option. Avoid crossing lines. If lines must cross, make one pass visibly "over" by routing around it instead of through it.
- Every arrow answers "what travels along this?" Label it or make it obvious from the endpoints. An unlabelled arrow between two boxes that could mean five things is a bug.
- Style encodes meaning and must be explained in the legend: solid = required, dashed = optional, thick = main path, color = type of data.
- Use one arrowhead style. The arrowhead must be fully visible, not hidden under a box border.
- Do not route a line through a text label. Put labels in a small white box (with a thin border) centered on or beside the line.
- Never use an arrow to mean "see also." Use a plain line or a text reference.

### 4.5 Do not let the visual get unmanageably huge

- If a single diagram needs more than about 7 columns or about 25 boxes, **split it** into an overview plus detail diagrams, or group items into containers.
- If the user wants maximum detail in one picture, make it large but structured: clear headers, repeating card layout, consistent sections. Detail is fine; disorder is not.

## 5. Typography

- **One font family per visual.** Use a system stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif`. Use a monospace stack (`Menlo, Consolas, monospace`) only for code, file names, topic names, and identifiers.
- **Use at most 4 text sizes**, each with a job:

| Level | Size (at 1x) | Weight | Use |
| --- | --- | --- | --- |
| Title | 24 to 30 px | Bold | One per visual |
| Section / group header | 16 to 20 px | Bold | Phase names, panel titles, card titles |
| Body | 12.5 to 14 px | Regular | Details inside boxes |
| Small / caption | 11 to 12 px | Regular, muted color | Footnotes, sources, secondary labels |

- Never go below 11 px. If body text would need to be smaller than 12 px, the visual is overloaded: split it or enlarge the canvas.
- **Hierarchy comes from size, weight, and color together.** Do not use more than 2 weights (regular, bold). Do not use italics except for short subtitles or quotes. Do not use underlines (they look like links). Avoid ALL CAPS beyond 1 to 3 words (tiny chips or tags are fine).
- **Left-align** paragraphs and bullet text. Center only short labels (a box title, a lane name, a single line under an icon).
- **Line length:** keep text lines under about 90 characters. Wrap, do not shrink.
- **Be concise but complete.** Prefer short noun phrases or verb phrases ("Replay one session") over sentences. But do not drop information the user wanted; reflow it to more lines instead.
- Use a real arrow glyph "→" or an SVG arrow, not `->`, in display text. In code or topic names (`map -> odom`) it is fine to keep the literal.
- Use the same term for the same thing everywhere. Do not call it "bundle" in one box and "package" in another unless they are different things.

## 6. Color

### 6.1 Rules

1. **Start from near-neutral.** White or very light grey background (`#ffffff`, `#f8fafc`), dark slate text (`#102a43` for titles, `#243b53` for body, `#486581` for muted text). Never pure black on pure white for large text blocks, and never light grey text on white.
2. **Use color to mean something.** Each color maps to one idea (a person, a category, a status, a phase). Write that mapping in the legend. Do not use color decoratively.
3. **Use few hues.** 3 to 5 distinct hues in one visual. More than 7 is unreadable and hard for color-blind readers.
4. **Pair a saturated stroke with a very light fill of the same hue** for containers (for example stroke `#7a5cc0`, fill `#f4f0ff`). Text inside stays dark neutral, not the hue color, except for a short heading.
5. **Do not rely on color alone.** Add a text label, tag, icon, shape, or line style so that a grayscale printout and a color-blind reader still understand it.
6. **Check contrast.** White text needs a fill at least as dark as Tailwind `*-600` (for example `#2b6cb0`, `#2f855a`, `#c53030`, `#6b46c1`). Dark text on pale `*-50` or `*-100` fills is safe. Grey `#a0aec0` text on white fails; use `#486581` or darker for small text.
7. **Reserve red** for errors, danger, "not allowed," or "stop." Reserve green for success/ok/required evidence. Do not use red and green as the only distinguishing pair.
8. **Charts:** categorical series use a qualitative palette; ordered data (low to high) uses a single-hue light-to-dark ramp; diverging data (below/above a midpoint) uses two hues meeting at a neutral. Never use a rainbow/jet color map.

### 6.2 A safe default palette (color-blind-friendly, good contrast)

| Role | Hex |
| --- | --- |
| Blue | `#2b6cb0` |
| Orange | `#dd6b20` |
| Teal/green | `#2f855a` |
| Purple | `#6b46c1` |
| Amber/brown | `#c27a00` |
| Red (danger only) | `#c53030` |
| Slate (neutral) | `#4a5568` |
| Light fills | the same hue at about 8 to 12 percent tint, for example `#ebf8ff`, `#fffaf0`, `#e6fcf5`, `#faf5ff` |

For a Okabe-Ito set for line/bar charts: `#0072B2 #E69F00 #009E73 #D55E00 #CC79A7 #56B4E9 #F0E442 #000000`.

### 6.3 Theme

If the visual may be viewed in dark mode, give it its own opaque background rectangle (so it never inherits a surprise background) and keep that background light, or deliberately design both. Do not depend on transparent backgrounds.

## 7. Building the visual

### 7.1 Prefer generators over hand-written coordinates

Write a small script (Python standard library is enough for SVG) that holds **content as data** and **drawing as generic functions**. Benefits: you can change a sentence and the layout reflows; the output is reproducible; reviewers can diff the content. The reference implementation in this repo is `2027_build/docs/scripts/generate_pipeline_svg.py` (run `python3 2027_build/docs/scripts/generate_pipeline_svg.py`). Read it as a worked example: content tables at the top, a card layout engine, then assembly.

### 7.2 Size boxes from their content (auto-layout)

SVG does not wrap text or resize boxes. You must do both. The recipe:

```python
import textwrap

CHAR_W = 0.53          # average glyph width as a fraction of font size; conservative
def wrap(text, width_px, size=13):
    chars = max(12, int(width_px / (size * CHAR_W)))
    return textwrap.wrap(text, chars, break_long_words=False) or [""]

# 1. wrap every text item to (box_width - 2*padding)
# 2. height = padding + sum(lines * line_height) + gaps + padding
# 3. rows of boxes use height = max(height of boxes in the row)
# 4. draw rects AFTER you know the final height
```

Keep the estimate conservative (0.53 to 0.56 of the font size per character; bold and capitals are wider). Then verify visually (section 9), because fonts differ between renderers. If text is close to an edge in your render, there is no safety margin; widen the box or wrap earlier.

### 7.3 SVG-specific rules and traps

- Always set `viewBox="0 0 W H"` **and** `width`/`height` equal to W and H. Compute H from content; do not guess.
- Include `<title>` and `<desc>` for accessibility, and `role="img"` with `aria-labelledby`.
- Draw an explicit background `<rect width="W" height="H" fill="#f8fafc"/>` first.
- Order matters: later elements paint on top. Draw containers first, then boxes, then lines, then labels.
- **CSS beats SVG presentation attributes.** If your `<style>` has `text { fill: ... }`, then `<text fill="red">` is ignored. Set per-element color with `style="fill:#xxxxxx"`, or give it a class with higher specificity. (This exact bug has happened here.)
- **Escape text** (`& < >`). Use `xml.sax.saxutils.escape` or equivalent. An unescaped `&` makes the whole file invalid.
- `text-anchor="middle"` centers on x; `y` is the **baseline**, not the top. For a box starting at `y0` with 16 px text, the first baseline is about `y0 + 20`.
- Arrow markers: define once in `<defs>`; use `refX` so the tip lands on the target edge; `orient="auto"`. Make the marker fill match the line color (or define one marker per color).
- Strokes are centered on the edge. A 2 px stroke extends 1 px outside the rect; leave a gap of at least 2 px for arrow tips.
- Do not use external fonts, images, or scripts in a standalone SVG; it must work offline and inside Markdown renderers. Inline everything.
- Validate the XML after generating: `python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" file.svg`.
- Keep file size sane. A diagram should be tens to low hundreds of KB, not megabytes.

### 7.4 Charts with code (matplotlib / plotly / similar)

- One message per chart. Title states the conclusion ("Latency doubles above 50 requests per second"), not just the topic ("Latency vs load").
- **Axes:** label with name and unit ("Latency (ms)"). Start bar charts at zero. Line charts may start above zero only if you say so. Never truncate a bar axis to exaggerate a difference.
- **No dual y-axes.** Use two stacked small charts sharing the x-axis.
- **No 3D, no shadows, no gradients, no pie charts with 5+ slices.**
- **Label directly.** Put series names at the line ends or on the bars instead of a distant legend when there are 5 or fewer series.
- **Sort** categories by value (unless they have a natural order such as time).
- **Gridlines:** light grey (`#e2e8f0`), thin, behind data; remove top and right spines; remove tick marks you do not need.
- **Ticks:** 4 to 7 per axis, human-friendly numbers, thousands separators, consistent decimals.
- **Annotate** the one or two points that matter (peak, threshold, event) with a short text and a thin leader line.
- Size and resolution: save at 2x (`dpi=200`) for raster output, or SVG for vector. Figure width about 8 to 10 inches for a document, fonts 10 to 12 pt at final size.
- Show uncertainty when it exists (error bars, bands, N). State the sample size.
- Always commit the script and the data (or the command that regenerates the data) beside the image.

Matplotlib starter that already applies most rules:

```python
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.figsize": (9, 5), "figure.dpi": 120, "savefig.dpi": 200,
    "font.family": "sans-serif", "font.size": 11,
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e2e8f0", "grid.linewidth": 0.8,
    "axes.axisbelow": True, "axes.labelcolor": "#243b53", "text.color": "#243b53",
    "xtick.color": "#486581", "ytick.color": "#486581",
    "axes.prop_cycle": plt.cycler(color=["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9"]),
})
```

## 8. Content patterns for common technical visuals

### 8.1 Pipeline / workstream diagram (what this repo uses)

Structure it as a **swimlane grid**:

- Rows = owners (people, systems, teams). Columns = phases in order. Phase headers across the top, with a number, a short name, and a one-line subtitle.
- Each cell is a **card** with the same internal sections in the same order. Recommended section set:
  - **IN**: inputs, each tagged with where it comes from (live hardware, recorded file, synthetic, measured by hand).
  - **OUT**: outputs, listing real file names, message types, or artifacts.
  - **DOES**: the main functionality, as ordered steps.
  - **NEEDS**: dependencies, each tagged with what kind (another person's output, a tool, an earlier phase, a gate).
  - **DONE**: the acceptance check, the condition under which the box may be called finished.
  - **NOT**: what the box deliberately does not do.
  - **CODE**: where the code lives.
- Show **cross-owner handoffs** in a separate "who hands what to whom" panel with labelled arrows rather than long lines that cross the grid.
- Show **contracts** (the interface between owners) in a table: name, producer to consumer, minimum fields, when it becomes stable.
- Include a **legend / how to read** panel near the top.
- Finish with the **rules that apply everywhere** (safety, scope, ownership) so nobody has to hunt for them.
- Never state exact dates unless the source gives them. Use relative phases and gates.

### 8.2 Architecture / data-flow diagram

- Boxes are components; arrows are data or control, labelled with the message/file type.
- Group by boundary (process, machine, team) using container boxes.
- Mark external systems differently (dashed border or distinct fill).
- Show the direction of data, and name the protocol or format on the arrow.

### 8.3 Timeline / roadmap

- Time runs left to right. Phases are blocks, milestones are markers with labels, dependencies are arrows.
- When only the order is known, label phases "Phase 1, 2, 3" and say "no dates implied."

### 8.4 Table graphics

If most cells are text, make it a real table: header row with a light fill, 1 px row dividers, left-aligned text, right-aligned numbers, units in the header, no vertical rules unless needed, generous row padding.

### 8.5 Dashboards / multi-chart pages

- Put the single most important number or chart top-left and make it largest.
- Use identical chart styling, axis fonts, and palette across panels.
- Use small multiples (same chart repeated per category, shared axes) instead of one chart with many lines.

## 9. The verification loop (mandatory)

You cannot judge a visual from its source. Render it and look.

1. **Generate** the file.
2. **Validate** it (XML parse for SVG; the script must run clean).
3. **Render to PNG.** Options, in order of preference on a dev machine:
   - `rsvg-convert -w 2000 file.svg -o /tmp/out.png` (librsvg)
   - `inkscape file.svg --export-type=png`
   - Headless browser screenshot (Playwright/Chrome) of the file
   - For matplotlib: `fig.savefig("out.png")` then open it
4. **Look at the image.** If your tooling can view images, view it. Large images: crop into slices (for example with Pillow) of about 1100 px height so small text is legible, and inspect each slice. Do not skim a downscaled thumbnail and call it checked.
5. **Run the inspection list below on every slice.**
6. **Fix** the cause in the generator, regenerate, re-render, re-inspect. Do not patch the output file by hand.
7. Only then report completion, and say what you checked.

Inspection list:

- Text clipped at a box edge or the canvas edge?
- Text overlapping other text, a line, or a border?
- Arrow tips hidden or pointing at nothing? Arrows crossing text?
- Anything running outside the canvas (look at the right and bottom edges especially)?
- Boxes of the same kind misaligned or different widths?
- Large empty areas that suggest a sizing bug?
- Colors as intended (a CSS-versus-attribute override can silently turn colored text black)?
- Every abbreviation or symbol explained?
- Does the first glance match the message from step 1 of the process?

If you cannot render at all, say so plainly in your report and list what remains unverified. Do not claim it looks fine.

## 10. Anti-patterns (never do these)

- Inventing data, file names, numbers, owners, dates, or acceptance criteria to fill a box. Use the repo's docs as the source; if something is unknown, write "to be decided" or omit it and say so.
- Text smaller than 11 px, or text that only fits because it is crammed.
- Walls of unstructured text inside a box. Use labelled sections, short bullets, and rules.
- Rainbow color maps, 3D charts, drop shadows, gradients, clip-art style icons.
- Dual y-axes, truncated bar axes, pie charts with many slices.
- Meaning carried only by color.
- Unlabelled arrows, unlabelled axes, unexplained abbreviations.
- Mixed alignment: some boxes centered, some left, some floating.
- Mixed styles: three different corner radii, four fonts, inconsistent line widths.
- Decorative elements that carry no information.
- Hand-edited generated output (the next regeneration silently deletes it).
- Declaring success without a rendered check.
- Overwriting someone else's in-progress changes to the same file without reading them first. Check `git status` and `git diff` before regenerating shared artifacts.

## 11. Delivery notes for this repository

- Put diagrams beside the docs they explain (for example `2027_build/docs/`) and commit **both** the generator script and the generated output.
- Reference the image from the relevant Markdown with descriptive alt text, and link to the SVG for full-size viewing.
- State the regeneration command in the script docstring and in the doc that embeds the image.
- When the underlying plan changes (owners, phases, contracts), update the generator's content tables first, regenerate, and re-run the verification loop. The diagram and the text docs must not contradict each other.
- Keep wording consistent with the docs under `2027_build/docs/` (for example the names Hedgie, Wobbles, Bedrawn, the "integration gate," and the TF chain `map -> odom -> base_link -> camera_link -> imu_link`).
- Do not make safety or capability claims that the docs do not make (for example, never imply motors are commanded or that a ZED area map is a Nav2 map).

## 12. Worked mini-example (the thinking, not just the output)

**Request:** "Make the pipeline diagram more detailed: inputs, outputs, main functionality, dependencies."

1. *Message:* "Three people build in parallel from day one, hand off through named contracts, and only converge at an integration gate."
2. *Audience:* teammates and newcomers, viewed zoomed in a browser. So: large canvas, full detail, a legend.
3. *Inventory:* read every plan doc; list per person per phase: inputs, outputs, steps, dependencies, acceptance checks, exclusions, code locations; list contracts and the TF ownership rule.
4. *Form:* swimlane grid (people x phases) plus a handoff panel, a contracts table, a TF chain strip, and a rules row.
5. *Hierarchy:* title, phase headers, card titles, section chips (IN/OUT/...), body bullets, small footnotes.
6. *Layout:* fixed lane column, fixed content columns, equal gutters, rows sized by tallest card.
7. *Build:* a generator with content tables and an auto-wrapping card engine.
8. *Verify:* render, slice, inspect; found the right-most column running off the canvas and lane names rendering black due to a CSS override; fixed both in the generator and re-rendered.
9. *Document:* regeneration command in the script docstring and docs.

Follow the same arc for any visual.
