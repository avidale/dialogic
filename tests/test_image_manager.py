from unittest.mock import patch

import tgalice

from tgalice.utils.content_manager import YandexImageAPI
from tgalice.dialog_connector import DialogConnector


def test_image_api():
    token = '1234'
    skill_id = '5678'
    default_image_id = '9101112'
    manager = YandexImageAPI(token=token, skill_id=skill_id, default_image_id=default_image_id)

    # test updating
    with patch('requests.get') as mock:
        mock.return_value.json = lambda: {
            'images': [
                {'id': 'tree', 'origUrl': 'trees.com/tree.jpg', 'size': 100500, 'createdAt': 'today'},
                {'id': 'snake', 'size': 100500, 'createdAt': 'yesterday'},
            ],
            'total': 2
        }
        manager.update_images()
        assert mock.called
        args = mock.call_args[1]
        assert args['url'] == 'https://dialogs.yandex.net/api/v1/skills/{}/images'.format(skill_id)
        assert args['headers'] == {'Authorization': 'OAuth 1234'}

        assert len(manager.url2image) == 1
        assert len(manager.id2image) == 2

    # test usage without upload
    with patch('requests.post') as mock:
        assert manager.get_image_id_by_url('trees.com/tree.jpg') == 'tree'
        assert manager.get_image_id_by_url('trees.com/pine.jpg') == default_image_id
        assert not mock.called

    # test adding an existing image
    with patch('requests.post') as mock:
        image = manager.add_image(url='trees.com/tree.jpg')
        assert not mock.called
        assert image.id == 'tree'

    # test uploading an image
    with patch('requests.post') as mock:
        oak_url = 'trees.com/oak.jpg'
        mock.return_value.json = lambda: {
            'image': {
                'id': 'oak',
                'origUrl': oak_url,
                'size': 100500,
                'createdAt': 'right_now'
            }
        }
        image = manager.add_image(url=oak_url)
        assert mock.called
        assert mock.call_args[1]['url'] == 'https://dialogs.yandex.net/api/v1/skills/{}/images'.format(skill_id)
        assert image.origUrl == oak_url
        assert image.id == 'oak'

        assert len(manager.id2image) == 3
        assert len(manager.url2image) == 2

    # test uploading an image on the fly
    manager.upload_just_in_time = True
    with patch('requests.post') as mock:
        maple_url = 'trees.com/maple.jpg'
        mock.return_value.ok = True
        mock.return_value.json = lambda: {
            'image': {
                'id': 'maple',
                'origUrl': maple_url,
                'size': 100500,
                'createdAt': 'right_now'
            }
        }
        assert manager.get_image_id_by_url(maple_url) == 'maple'
        assert mock.called

        assert len(manager.id2image) == 4
        assert len(manager.url2image) == 3

    # test removing an image
    with patch('requests.delete') as mock:
        mock.return_value.ok = True
        mock.return_value.json = lambda: {'result': 'ok'}

        manager.delete_image('maple')
        assert mock.called
        assert mock.call_args[1]['url'] == 'https://dialogs.yandex.net/api/v1/skills/{}/images/maple'.format(skill_id)

        assert len(manager.id2image) == 3
        assert len(manager.url2image) == 2

    # test automatic conversion of urls to ids
    connector = DialogConnector(dialog_manager=None, image_manager=manager)
    response = tgalice.dialog.Response('this is an oak', image_url='trees.com/oak.jpg')
    result = connector.standardize_output(
        source=tgalice.SOURCES.ALICE,
        original_message={'version': '1.0'},
        response=response
    )
    assert result['response']['card'] == {
        'type': 'BigImage',
        'image_id': 'oak',
        'description': 'this is an oak',
    }
