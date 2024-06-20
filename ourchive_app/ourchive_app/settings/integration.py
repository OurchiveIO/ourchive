from ourchive_app.settings.base import *
import sys

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('OURCHIVE_INTEGRATION_DB_NAME', 'ourchive_db_integration'),
        'USER': os.getenv('OURCHIVE_DB_USER', 'ourchive'),
        'PASSWORD': os.getenv('OURCHIVE_DB_PW'),
        'HOST': os.getenv('OURCHIVE_DB_HOST'),
        'PORT': os.getenv('OURCHIVE_DB_PORT', '5432'),
    }
}

CHAPTER_AUDIO_URLS = [
    {
        'audio_url': f'{MEDIA_URL}test_data/chapter_audio/232409__rtb45__uighurtraditional-music-4.wav',
        'audio_description': '',
        'audio_length': 0
    },
    {
        'audio_url': f'{MEDIA_URL}test_data/chapter_audio/261547__titusl108__a-collection-of-folk-1.mp3',
        'audio_description': '',
        'audio_length': 0
    },
    {
        'audio_url': f'{MEDIA_URL}test_data/chapter_audio/721238__gregorquendel__beethoven-the-tempest-2-movement-sonata-no-17-in-d-minor-op-31-no.mp3',
        'audio_description': '',
        'audio_length': 0
    }
]

CHAPTER_VIDEO_URLS = [
    {
        'video_url': f'{MEDIA_URL}test_data/chapter_video/eso1701a.mp4',
        'video_description': '',
        'video_length': 0
    },
    {
        'video_url': f'{MEDIA_URL}test_data/chapter_video/eso1725a.mp4',
        'video_description': '',
        'video_length': 0
    },
    {
        'video_url': f'{MEDIA_URL}test_data/chapter_video/eso2306a.mp4',
        'video_description': '',
        'video_length': 0
    }
]

CHAPTER_IMAGE_URLS = [
    {
        'image_url': f'{MEDIA_URL}test_data/chapter_images/david-clode-9FvTOCfvt_w-unsplash.jpg',
        'image_alt_text': '',
        'image_size': '',
        'image_format': ''
    },
    {
        'image_url': f'{MEDIA_URL}test_data/chapter_images/david-clode-IKFVzqVNGK0-unsplash.jpg',
        'image_alt_text': '',
        'image_size': '',
        'image_format': ''
    },
    {
        'image_url': f'{MEDIA_URL}test_data/chapter_images/david-clode-xNpxB9bfLUE-unsplash.jpg',
        'image_alt_text': '',
        'image_size': '',
        'image_format': ''
    },
    {
        'image_url': f'{MEDIA_URL}test_data/chapter_images/foad-memariaan-OPtPK3kMWEc-unsplash.jpg',
        'image_alt_text': '',
        'image_size': '',
        'image_format': ''
    },
    {
        'image_url': f'{MEDIA_URL}test_data/chapter_images/francesco-ungaro-VRGJDKYUrKo-unsplash.jpg',
        'image_alt_text': '',
        'image_size': '',
        'image_format': ''
    },
    {
        'image_url': f'{MEDIA_URL}test_data/chapter_images/gerald-schombs-GBDkr3k96DE-unsplash.jpg',
        'image_alt_text': '',
        'image_size': '',
        'image_format': ''
    },
    {
        'image_url': f'{MEDIA_URL}test_data/chapter_images/jeremy-bishop-TI_3eaoMyjo-unsplash.jpg',
        'image_alt_text': '',
        'image_size': '',
        'image_format': ''
    },
    {
        'image_url': f'{MEDIA_URL}test_data/chapter_images/ludovic-migneault-hqu_cf0Yp0w-unsplash.jpg',
        'image_alt_text': '',
        'image_size': '',
        'image_format': ''
    },
    {
        'image_url': f'{MEDIA_URL}test_data/chapter_images/olga-ga-_vh546LXLPM-unsplash.jpg',
        'image_alt_text': '',
        'image_size': '',
        'image_format': ''
    },
    {
        'image_url': f'{MEDIA_URL}test_data/chapter_images/zhengtao-tang-V7SKRhXskv8-unsplash.jpg',
        'image_alt_text': '',
        'image_size': '',
        'image_format': ''
    }
]

CHIVE_HEADER_URLS = [
    {
        'header_url': f'{MEDIA_URL}test_data/chive_headers/candi-foltz-l23EsqKgDts-unsplash.jpg',
        'header_alt_text': ''
    },
    {
        'header_url': f'{MEDIA_URL}test_data/chive_headers/donna-ruiz-Pe_SZd-oA_0-unsplash.jpg',
        'header_alt_text': ''
    },
    {
        'header_url': f'{MEDIA_URL}test_data/chive_headers/jan-meeus-7LsuYqkvIUM-unsplash.jpg',
        'header_alt_text': ''
    },
    {
        'header_url': f'{MEDIA_URL}test_data/chive_headers/ray-hennessy-BR2rEWcQQJQ-unsplash.jpg',
        'header_alt_text': ''
    },
    {
        'header_url': f'{MEDIA_URL}test_data/chive_headers/regine-tholen-TBf7nD07dfc-unsplash.jpg',
        'header_alt_text': ''
    },
    {
        'header_url': f'{MEDIA_URL}test_data/chive_headers/vincent-van-zalinge-vUNQaTtZeOo-unsplash.jpg',
        'header_alt_text': ''
    }
]

CHIVE_COVER_URLS = [
    {
        'cover_url': f'{MEDIA_URL}test_data/chive_covers/becca-_r6w0R6SueQ-unsplash.jpg',
        'cover_alt_text': ''
    },
    {
        'cover_url': f'{MEDIA_URL}test_data/chive_covers/daniel-diesenreither-z4yzSsH5EAo-unsplash.jpg',
        'cover_alt_text': ''
    },
    {
        'cover_url': f'{MEDIA_URL}test_data/chive_covers/hans-jurgen-mager-qQWV91TTBrE-unsplash.jpg',
        'cover_alt_text': ''
    },
    {
        'cover_url': f'{MEDIA_URL}test_data/chive_covers/mark-basarab-y421kXlUOQk-unsplash.jpg',
        'cover_alt_text': ''
    },
    {
        'cover_url': f'{MEDIA_URL}test_data/chive_covers/zdenek-machacek-Pt3asvL65Mg-unsplash.jpg',
        'cover_alt_text': ''
    }
]
