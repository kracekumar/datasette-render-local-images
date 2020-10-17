from datasette.app import Datasette
from datasette_render_local_images import render_cell
import pytest
import httpx
import sqlite_utils


@pytest.fixture(scope="session")
def ds(tmp_path_factory):
    """Create Datasette fixture for testing."""
    db_directory = tmp_path_factory.mktemp("dbs")
    db_path = db_directory / "test.db"
    db = sqlite_utils.Database(db_path)
    db["books"].insert_all(
        [
            {
                "id": 1,
                "name": "Windup Bird Chronicle",
                "author": "Haruki Murakami",
                "author_image": "tests/images/HarukiMurakami.png",
            },
            {
                "id": 2,
                "name": "2666",
                "author": "Roberto Bolano",
                "author_image": "tests/images/Roberto_Bolaño_(ca._1975).jpg",
            },
            {
                "id": 3,
                "name": "The Bluest Eye",
                "author": "Toni Morrison",
                "author_image": "tests/images/Toni_Morrison.jpg",
            },
            {
                "id": 4,
                "name": "Are Prisons Absolute?",
                "author": "Angela Davis",
                "author_image": "tests/images/Angela_Davis_Moscow_1972_cropped.jpg",
            },
            {
                "id": 5,
                "name": "No Exit",
                "author": "Jean Paul Satre",
                "author_image": "tests/images/jps.png",
            },
            {
                "id": 6,
                "name": "Dummy",
                "author": "Kracekumar",
                "author_image": "tests/images/dummy.txt",
            },
            {
                "id": 7,
                "name": "Scalable_Vector_Graphics",
                "author": "W3C",
                "author_image": "tests/images/Scalable_Vector_Graphics",
            },
        ],
        pk="id",
    )
    ds = Datasette(
        [db_path],
        metadata={
            "databases": {"test": {"tables": {"books": {"title": "Some Books"}}}},
            "plugins": {},
        },
    )
    return ds


@pytest.mark.asyncio
async def test_plugin_is_installed():
    app = Datasette([], memory=True).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/plugins.json")
        assert 200 == response.status_code
        installed_plugins = {p["name"] for p in response.json()}
        assert "datasette-render-local-images" in installed_plugins


@pytest.mark.asyncio
async def test_render_cell_with_image_path(ds):
    """Check the local image is rendered as image"""
    result = render_cell("tests/images/HarukiMurakami.png", ds)

    assert result
    assert result.startswith("<img src")
    assert "data:image/png" in result
    assert 'height="-1"' in result
    assert 'width="-1"' in result


@pytest.mark.asyncio
async def test_render_cell_with_image_path_with_custom_height_and_width(ds):
    """Check the local image is rendered as image"""
    ds._metadata["plugins"]["datasette-render-local-images"] = {
        "height": 150,
        "width": 150,
    }
    result = render_cell("tests/images/HarukiMurakami.png", ds)

    assert result
    assert result.startswith("<img src")
    assert "data:image/png" in result
    assert 'height="150"' in result
    assert 'width="150"' in result


@pytest.mark.asyncio
async def test_render_cell_with_missing_image_path(ds):
    """Test for missing file no modification is done"""
    result = render_cell("tests/images/jps.png", ds)

    assert not result


@pytest.mark.asyncio
async def test_table_as_html(ds):
    """Test the local path is rendered as image and missing one is rendered as text"""
    async with httpx.AsyncClient(app=ds.app()) as client:
        response = await client.get("http://localhost/test/books")
        jps_unrendered = (
            '<td class="col-author_image type-str">tests/images/jps.png</td>'
        )

        assert ">Some Books</h1>" in response.text
        assert response.text.count("<img") == 4
        assert jps_unrendered in response.text
