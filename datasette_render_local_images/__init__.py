from pathlib import Path
from datasette import hookimpl
import base64
import imghdr
import jinja2


def get_size_to_render(plugin_config):
    """Get size to render an image."""
    print(plugin_config)
    height = plugin_config.get("height", -1)
    width = plugin_config.get("width", -1)
    return height, width


def get_local_path(value):
    """Get local path for the value."""
    value = Path(value)
    # Return if exists and a file
    if value.exists() and value.is_file():
        return value
    return ""


@hookimpl
def render_cell(value, datasette):
    """Render local image in any cell.
    """
    if datasette:
        plugin_config = datasette.plugin_config("datasette-render-local-images") or {}
        height, width = get_size_to_render(plugin_config)

    # If the path exists then go ahead
    path = get_local_path(value)
    if not path:
        return None

    image_data = path.read_bytes()

    # Leave out empty cells
    if not image_data:
        return None

    # Is this an image?
    image_type = imghdr.what(None, h=image_data)
    if image_type not in ("png", "jpeg", "gif"):
        return None

    # Render as a HTML Tag
    return jinja2.Markup(
        '<img src="data:image/{};base64,{}" alt="" width="{}" height="{}">'.format(
            image_type, base64.b64encode(image_data).decode("utf8"), width, height
        )
    )
