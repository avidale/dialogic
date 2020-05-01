import attr
import requests


from typing import Dict, List, Optional


@attr.s
class Image:
    id: str = attr.ib()
    size: int = attr.ib()
    createdAt: str = attr.ib()
    origUrl: Optional[str] = attr.ib(default=None)


class YandexImageAPI:
    """
    This class is a wrapper around Yandex image storage API.
    Its official documentation is available online:
    https://yandex.ru/dev/dialogs/alice/doc/resource-upload-docpage/
    """
    def __init__(self, token, skill_id, default_image_id=None, upload_just_in_time=False):
        self.token = token
        self.skill_id = skill_id
        self.default_image_id = default_image_id
        self.upload_just_in_time = upload_just_in_time
        self.url2image: Dict[str, Image] = {}
        self.id2image: Dict[str, Image] = {}

    def update_images(self) -> None:
        """ Retrieve the list of images from the cloud storage and save it to the local index. """
        for image in self.get_images_list():
            if image.origUrl:
                self.url2image[image.origUrl] = image
            self.id2image[image.id] = image

    def add_image(self, url, timeout=5) -> Optional[Image]:
        """ Add image to the local index and Yandex storage by its url."""
        if url in self.url2image:
            return self.url2image[url]
        result = self.upload_image(url, timeout=timeout)
        if result:
            self.url2image[url] = result
            self.id2image[result.id] = result
        return result

    def upload_image(self, url, timeout=5) -> Optional[Image]:
        """
        Try to upload the image by url (without adding it to the local index)
        small images take 1.5-2 seconds to upload
        """
        r = requests.post(
            url='https://dialogs.yandex.net/api/v1/skills/{}/images'.format(self.skill_id),
            headers={'Authorization': 'OAuth {}'.format(self.token)},
            json={'url': url},
            timeout=timeout,
        )
        result = r.json().get('image')
        if result:
            return Image(**result)

    def get_images_list(self) -> List[Image]:
        """ Get all images in the Yandex storage. """
        r = requests.get(
            url='https://dialogs.yandex.net/api/v1/skills/{}/images'.format(self.skill_id),
            headers={'Authorization': 'OAuth {}'.format(self.token)}
        )
        results = r.json().get('images', [])
        return [Image(**item) for item in results]

    def get_image_id_by_url(self, url, try_upload=None, timeout=2) -> Optional[str]:
        """
        Try to get image id from local storage or quickly upload it
        or return the default image.
        """
        if url in self.url2image:
            return self.url2image[url].id
        if try_upload is None:
            try_upload = self.upload_just_in_time
        if try_upload:
            image = self.add_image(url, timeout=timeout)
            if image:
                return image.id
        if self.default_image_id:
            return self.default_image_id

    def get_quota(self):
        """ Get existing an occupied amount of storage for images and sounds in bytes"""
        r = requests.get(
            url='https://dialogs.yandex.net/api/v1/status',
            headers={'Authorization': 'OAuth {}'.format(self.token)}
        )
        return r.json()

    def delete_image(self, image_id):
        """ Delete image from storage by its id and delete it from local index """
        r = requests.delete(
            url='https://dialogs.yandex.net/api/v1/skills/{}/images/{}'.format(self.skill_id, image_id),
            headers={'Authorization': 'OAuth {}'.format(self.token)}
        )
        if r.ok:
            if image_id in self.id2image:
                image = self.id2image[image_id]
                del self.id2image[image_id]
                if image.origUrl in self.url2image and self.url2image[image.origUrl].id == image_id:
                    del self.url2image[image.origUrl]
        return r.json()
