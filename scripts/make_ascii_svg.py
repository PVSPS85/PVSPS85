#!/usr/bin/env python3

import os
from PIL import Image, ImageOps, ImageEnhance


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "assets",
    "cat-source.jpeg"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "ascii-cat.svg"
)


# ---------------------------------------------------------
# ASCII SETTINGS
# ---------------------------------------------------------

# Smaller grid = smaller portrait
COLS = 50
ROWS = 24

# Small terminal text
FONT_SIZE = 6
CHAR_WIDTH = 4.2
LINE_HEIGHT = 6.5

CHARS = " .:-=+*#%@"

TEXT_COLOR = "#c9d1d9"
BACKGROUND = "#0d1117"


def remove_background(image):
    """
    Detect the dark background from the four corners
    and make those pixels transparent-looking in the
    grayscale conversion.
    """

    image = image.convert("RGB")

    width, height = image.size

    corners = [
        image.getpixel((0, 0)),
        image.getpixel((width - 1, 0)),
        image.getpixel((0, height - 1)),
        image.getpixel((width - 1, height - 1)),
    ]

    bg = tuple(
        sum(pixel[i] for pixel in corners) // len(corners)
        for i in range(3)
    )

    pixels = image.load()

    output = Image.new(
        "L",
        image.size,
        255
    )

    out_pixels = output.load()

    for y in range(height):

        for x in range(width):

            r, g, b = pixels[x, y]

            distance = (
                abs(r - bg[0])
                + abs(g - bg[1])
                + abs(b - bg[2])
            )

            if (
                distance < 55
                and r < 90
                and g < 90
                and b < 90
            ):
                value = 255

            else:
                value = (
                    0.299 * r
                    + 0.587 * g
                    + 0.114 * b
                )

            out_pixels[x, y] = int(value)

    return output


def prepare_image():

    image = Image.open(INPUT_FILE)

    # Convert to grayscale and fit into the smaller
    # ASCII grid.
    image = ImageOps.fit(
        image,
        (COLS, ROWS),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5)
    )

    gray = remove_background(image)

    # Improve definition of the cat.
    gray = ImageEnhance.Contrast(gray).enhance(1.8)

    gray = ImageOps.autocontrast(gray)

    return gray


def pixel_to_char(value):

    index = int(
        (value / 255)
        * (len(CHARS) - 1)
    )

    index = max(
        0,
        min(index, len(CHARS) - 1)
    )

    return CHARS[index]


def generate_ascii(image):

    pixels = image.load()

    lines = []

    for y in range(ROWS):

        line = ""

        for x in range(COLS):

            value = pixels[x, y]

            line += pixel_to_char(value)

        lines.append(
            line.rstrip()
        )

    return lines


def escape_xml(text):

    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(lines):

    # Compact SVG dimensions.
    width = 255

    height = 210

    svg = []

    svg.append(
        f'''<svg xmlns="http://www.w3.org/2000/svg"
width="{width}"
height="{height}"
viewBox="0 0 {width} {height}">
'''
    )

    # -----------------------------------------------------
    # Background
    # -----------------------------------------------------

    svg.append(
        f'''
<rect
    x="0"
    y="0"
    width="{width}"
    height="{height}"
    rx="14"
    fill="{BACKGROUND}"
/>
'''
    )

    # -----------------------------------------------------
    # Terminal heading
    # -----------------------------------------------------

    svg.append(
        f'''
<text
    x="15"
    y="22"
    font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    font-size="10"
    font-weight="600"
    fill="{TEXT_COLOR}">
    pranav@github ~ $ cat ./profile.txt
</text>
'''
    )

    # -----------------------------------------------------
    # Animation
    # -----------------------------------------------------

    svg.append(
        '''
<defs>

<style>

.ascii-row {
    opacity: 0;
    animation: typeRow 0.42s ease-out forwards;
}

@keyframes typeRow {

    0% {
        opacity: 0;
        transform: translateX(-8px);
    }

    100% {
        opacity: 1;
        transform: translateX(0);
    }

}

</style>

</defs>
'''
    )

    # -----------------------------------------------------
    # ASCII portrait
    # -----------------------------------------------------

    start_y = 38

    for row, line in enumerate(lines):

        y = (
            start_y
            + row * LINE_HEIGHT
        )

        # Slight stagger creates the typing effect.
        delay = row * 0.045

        svg.append(
            f'''
<text
    class="ascii-row"
    x="15"
    y="{y:.1f}"
    style="animation-delay:{delay:.3f}s"
    font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    font-size="{FONT_SIZE}px"
    font-weight="500"
    xml:space="preserve"
    fill="{TEXT_COLOR}">
    {escape_xml(line)}
</text>
'''
        )

    # -----------------------------------------------------
    # Footer
    # -----------------------------------------------------

    svg.append(
        f'''
<text
    x="15"
    y="{height - 10}"
    font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    font-size="8"
    fill="#8b949e">
    [ ASCII CAT • PVSPS85 ]
</text>
'''
    )

    svg.append("</svg>")

    return "\n".join(svg)


def main():

    if not os.path.exists(INPUT_FILE):

        raise FileNotFoundError(
            f"Cat image not found: {INPUT_FILE}"
        )

    print("Loading cat image...")

    image = prepare_image()

    print("Generating ASCII...")

    lines = generate_ascii(image)

    print("Building compact animated SVG...")

    svg = build_svg(lines)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(svg)

    print(
        f"Generated: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
