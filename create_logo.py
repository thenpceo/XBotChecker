from PIL import Image, ImageDraw, ImageFont
import os

# Create directory if it doesn't exist
os.makedirs('static/images', exist_ok=True)

# Create a new image with a transparent background
width, height = 200, 200
image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Draw an orange circle
circle_color = (255, 157, 66, 255)  # SMOK3 orange
circle_radius = 90
circle_center = (width // 2, height // 2)
draw.ellipse(
    (
        circle_center[0] - circle_radius,
        circle_center[1] - circle_radius,
        circle_center[0] + circle_radius,
        circle_center[1] + circle_radius
    ),
    fill=circle_color
)

# Draw a white X in the center
x_color = (255, 255, 255, 255)  # White
line_width = 15
margin = 40

# Draw the X
draw.line(
    [(margin, margin), (width - margin, height - margin)],
    fill=x_color,
    width=line_width
)
draw.line(
    [(width - margin, margin), (margin, height - margin)],
    fill=x_color,
    width=line_width
)

# Save the image
image.save('static/images/logo.png')

print("Logo created at static/images/logo.png") 