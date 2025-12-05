import flet as ft
from ui import theme
import math

def format_duration(seconds: int) -> str:
    """Convierte segundos en un formato M:SS."""
    mins = math.floor(seconds / 60)
    secs = seconds % 60
    return f"{mins}:{secs:02}"

def SearchResultItem(page: ft.Page, item_data, item_type: str, on_download=None):
    """
    Un componente reutilizable para mostrar un resultado de búsqueda.
    Navega a la vista de detalle correspondiente al hacer clic.
    """
    # Determinar los detalles basados en el tipo de item
    destination_route = ""
    image_src = "https://via.placeholder.com/50" # Fallback general

    if item_type == "artist":
        title = item_data.name
        subtitle = "Artista"
        if item_data.picture_medium:
            image_src = item_data.picture_medium
        destination_route = f"/artist/{item_data.id}"
    elif item_type == "album":
        title = item_data.title
        subtitle = item_data.artist.name if item_data.artist else ""
        if item_data.cover_medium:
            image_src = item_data.cover_medium
        destination_route = f"/album/{item_data.id}"
    elif item_type == "track":
        title = item_data.title
        subtitle = item_data.artist.name if item_data.artist else ""
        if item_data.album and item_data.album.cover_medium:
            image_src = item_data.album.cover_medium
    elif item_type == "playlist":
        title = item_data.title
        subtitle = item_data.user.name if item_data.user else ""
        if item_data.picture_medium:
            image_src = item_data.picture_medium
        destination_route = f"/playlist/{item_data.id}"
    else:
        return ft.Container() # No mostrar nada si el tipo no es válido

    def on_item_click(e):
        if item_type == "track" and on_download:
            p = e.control.page
            p.run_task(on_download, p, item_data)
        elif destination_route:
            print(f"Navegando a: {destination_route}")
            page.go(destination_route)

    return ft.ListTile(
        leading=ft.Image(src=image_src, width=50, height=50, fit=ft.ImageFit.COVER, border_radius=5),
        title=ft.Text(title, weight=ft.FontWeight.BOLD),
        subtitle=ft.Text(subtitle, color=theme.SECONDARY_TEXT),
        on_click=on_item_click,
        data=item_data # Guardar el objeto completo para referencia si es necesario
    )

def TrackListItem(page: ft.Page, track_data, on_play, on_download):
    """
    Componente para una canción en una lista (álbum, playlist, etc.).
    Al hacer clic, se descarga la canción.
    """
    def download_clicked(e):
        p = e.control.page
        p.run_task(on_download, p, track_data)

    return ft.ListTile(
        leading=ft.Text(str(track_data.track_position or '#'), color=theme.SECONDARY_TEXT),
        title=ft.Text(track_data.title_short, weight=ft.FontWeight.W_500),
        subtitle=ft.Text(format_duration(track_data.duration), color=theme.SECONDARY_TEXT),
        on_click=download_clicked
    )

def AlbumCard(page: ft.Page, album_data):
    """
    Componente para mostrar un álbum en la página de un artista.
    """
    cover_url = album_data.cover_medium if album_data.cover_medium else "https://via.placeholder.com/150"
    
    release_year = ""
    if album_data.release_date:
        release_year = album_data.release_date.split('-')[0]

    return ft.Container(
        content=ft.Column([
            ft.Image(
                src=cover_url,
                border_radius=ft.border_radius.all(8),
                width=150,
                height=150
            ),
            ft.Text(album_data.title, size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Text(release_year, size=12, color=theme.SECONDARY_TEXT, text_align=ft.TextAlign.CENTER),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        
        ),
        on_click=lambda _: page.go(f"/album/{album_data.id}"),
        width=150
    )
