# Work Export

Ourchive offers two native file export formats, EPUB and ZIP. 

EPUB exports generate a simple file with cover and title pages, a table of contents, and chapter content. Chapter content shows the image before the chapter text and does not include chapter audio.

ZIP exports generate a ZIP with a `work.html` file containing the work title, author, summary, and notes, and nested directories for each chapter. Chapter directories contain chapter HTML, image, and audio files.

We are open to including any file format, particularly those formats which can be build without third-party, non-Python libraries. Open an issue to request a format, or a PR to add a format.

In addition to native formatting, Ourchive offers creators the ability to specify a preferred format. This preferred format is prioritized in the download options list. Options for preferred format are defined in models.Work.choices. This allows creators who have compiled a specialized format, such as an M4B, to make this file available for download. 

**File types for preferred downloads are not checked. Only trusted users should be permitted to upload files.** File upload permissions are disabled by default. You can enable them in the admin console.