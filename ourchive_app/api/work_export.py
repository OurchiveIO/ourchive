from ebooklib import epub
from django.conf import settings
from zipfile import ZipFile
import os
import requests
from django.templatetags.static import static
from .ebook_style import get_epub_style
import io
import shutil


def get_temp_directory(work_uid):
    return f'{settings.TMP_ROOT}/export/{work_uid}/'


def get_media_directory(work_uid):
    return f'{settings.MEDIA_ROOT}/export/{work_uid}/'


def get_zip_dir(work):
    clean_title = "".join([c for c in work.title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    return f"{get_media_directory(work.uid)}{clean_title}.zip"


def get_epub_dir(work):
    clean_title = "".join([c for c in work.title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    return f"{get_media_directory(work.uid)}{clean_title}.epub"


def get_image_from_url(image_url):
    image_file = requests.get(f"{settings.API_PROTOCOL}{settings.ALLOWED_HOSTS[0]}{image_url}")
    image = image_file.content
    filename, file_extension = os.path.splitext(image_url)
    return [image_file, image, filename, file_extension]


def get_zip_temp_dir(work, chapter):
    full_path = f'{get_temp_directory(work.uid)}chapter_{chapter.number}/'
    return os.path.dirname(full_path)


def create_zip(work):
    location = get_zip_dir(work)
    with ZipFile(location, 'w') as work_file:
        # write basic work info; this will result in a very small html file
        temp_dir = get_temp_directory(work.uid)
        os.makedirs(get_temp_directory(work.uid), exist_ok=True)
        with open(f'{temp_dir}/work.html', 'w') as text:
            text.write(f"""<h1>{work.title}</h1> <h2>by {work.user.username}</h2><br/><br/>
               <h3>Summary</h3><p>{work.summary}</p>
                <h3>Notes</h3><p>{work.notes}</p>""")
        work_file.write(f'{temp_dir}/work.html', f'work.html')
        # write each chapter to its own folder
        for chapter in work.chapters.all():
            temp_dir = get_zip_temp_dir(work, chapter)
            os.makedirs(temp_dir, exist_ok=True)
            if chapter.text and chapter.text != "None":
                with open(f'{temp_dir}/chapter_{chapter.id}_{chapter.number}_{chapter.title}.html', 'w') as text:
                    text.write(f"""<h1>{chapter.title}</h1> <h2>by {work.user.username}</h2><br/><br/>
					   <h3>Summary</h3><p>{chapter.summary}</p>
                        <h3>Notes</h3><p>{chapter.notes}</p>
					   <br/><br/><hr><br/></br>
					   {chapter.text}""")
                work_file.write(f'{temp_dir}/chapter_{chapter.id}_{chapter.number}_{chapter.title}.html', f'/chapter_{chapter.number}/{chapter.title}.html')
            if chapter.image_url and chapter.image_url != "None":
                image_info = get_image_from_url(chapter.image_url)
                image_file = image_info[0]
                image = image_info[1]
                filename = image_info[2]
                file_extension = image_info[3]
                image_bytes = io.BytesIO(image)
                with open(f'{temp_dir}/chapter_{chapter.id}_image{file_extension}', 'wb') as image:
                    image.write(image_bytes.read())
                work_file.write(f'{temp_dir}/chapter_{chapter.id}_image{file_extension}', f'/chapter_{chapter.number}/image{file_extension}')
            if chapter.audio_url and chapter.audio_url != "None":
                audio_info = get_image_from_url(chapter.audio_url)
                audio_file = audio_info[0]
                audio = audio_info[1]
                filename = audio_info[2]
                file_extension = audio_info[3]
                audio_bytes = io.BytesIO(audio)
                with open(f'{temp_dir}/chapter_{chapter.id}_audio{file_extension}', 'wb') as audio:
                    audio.write(audio_bytes.read())
                work_file.write(f'{temp_dir}/chapter_{chapter.id}_audio{file_extension}', f'/chapter_{chapter.number}/audio{file_extension}')
            # clean up chapter folder
            shutil.rmtree(temp_dir)
        # clean up parent folder
        shutil.rmtree(get_temp_directory(work.uid))
    return location


def create_epub(work):

    book = epub.EpubBook()

    # set metadata
    book.set_identifier(str(work.id))
    book.set_title(work.title)
    book.set_language('en')
    book.add_metadata('DC', 'description', work.summary)

    book.add_author(work.user.username)

    if work.cover_url is not None and work.cover_url != "" and work.cover_url != "None":
        image_info = get_image_from_url(work.cover_url)
        image_file = image_info[0]
        image = image_info[1]
        filename = image_info[2]
        file_extension = image_info[3]
        image_string = f"work_cover_{str(work.id)}{file_extension}"
        book.set_cover(image_string, image)
        cover_page = epub.EpubHtml(
            title='Cover', file_name='cover_page.xhtml', lang='en')
        content_string = f'<center><img src="{image_string}"/></center>'
        cover_page.content = content_string.encode('utf8')
        book.add_item(cover_page)
        book.toc.append(epub.Link('cover_page.xhtml', 'Cover', ''))
    else:
        cover_page = epub.EpubHtml(
            title=work.title, file_name='cover_page.xhtml', lang='en')
        content_string = f'<center>{work.title}<br/>by {work.user.username}</center>'
        cover_page.content = content_string.encode('utf8')
        book.add_item(cover_page)
        book.toc.append(epub.Link('cover_page.xhtml', 'Cover', ''))

    title_page = epub.EpubHtml(
        title=work.title, file_name='title_page.xhtml', lang='en')
    content_string = f'<center><h1>{work.title}</h1><br/><h2>' + \
            f'{work.user.username}</h2><br/><br/></center>'
    content_string = f'{content_string}<h2>Summary</h2><p>{work.summary}</p>'
    content_string = f'{content_string}<h2>Notes</h2><p>{work.notes}</p>'
    title_page.content = content_string.encode('utf8')
    book.add_item(title_page)
    book.toc.append(epub.Link('title_page.xhtml', 'Title Page', ''))

    book.spine = ['nav', cover_page, title_page]

    for chapter in work.chapters.all():
        new_chapter = epub.EpubHtml(
            title=chapter.title, file_name=chapter.title + '.xhtml', lang='en', content='')
        if chapter.title:
            new_chapter.content = f'{new_chapter.content}<h2>{chapter.title}</h2>'
        if chapter.summary:
            new_chapter.content = f'{new_chapter.content}<h3>Summary</h3><p>{chapter.summary}</p>'
        if chapter.notes:
            new_chapter.content = f'{new_chapter.content}<h3>Notes</h3>{chapter.notes}'
        if new_chapter.content != '':
            new_chapter.content = f'{new_chapter.content}<hr/>'
        if (chapter.image_url is not None and chapter.image_url != "" and chapter.image_url != "None"):
            image_info = get_image_from_url(chapter.image_url)
            image_file = image_info[0]
            image = image_info[1]
            filename = image_info[2]
            file_extension = image_info[3]
            image_string = f"chapter_{str(chapter.id)}{file_extension}"
            image_item = epub.EpubItem(uid=f"img_{chapter.id}",
                                       file_name=image_string,
                                       media_type=f"image/{file_extension.replace('.', '')}",
                                       content=image)
            book.add_item(image_item)
            new_chapter.content = f"{new_chapter.content}<img src='" + image_string + "'/>"
            new_chapter.content += "<br/><br/><br/>"
        if chapter.text and chapter.text != "None":
            new_chapter.content += chapter.text
        if chapter.text or chapter.image_url:
            # don't add anything to the epub if the chapter is functionally empty
            book.add_item(new_chapter)
            book.spine.append(new_chapter)
            toc_link = chapter.summary if chapter.summary else chapter.title
            book.toc.append(epub.Link(chapter.title + '.xhtml',
                                  chapter.title, toc_link))

    # define CSS style
    loaded_css = get_epub_style()
    css_obj = epub.EpubItem(uid="style_book", file_name="style/book.css",
                            media_type="text/css", content=loaded_css)

    book.add_item(epub.EpubNcx())
    #book.add_item(epub.EpubNav())

    # add CSS file
    book.add_item(css_obj)

    # write to the file
    os.makedirs(get_media_directory(work.uid), exist_ok=True)
    location = get_epub_dir(work)
    epub.write_epub(location, book, {})
    return location
