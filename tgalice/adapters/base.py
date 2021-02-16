import copy
import logging
from typing import Optional, Dict

from ..dialog.serialized_message import SerializedMessage
from ..dialog import Context, Response


logger = logging.getLogger(__name__)


class BaseAdapter:
    """ A base class for adapters that encode and decode messages into a single format """

    def make_context(self, message, **kwargs) -> Context:
        """ Get a raw `message` in a platform-specific format and encode it into a unified `Context` """
        raise NotImplementedError()

    def make_response(self, response: Response, original_message=None, **kwargs):
        """ Get a unified `Response` object and decode it into the platform-specific response """
        raise NotImplementedError()

    def serialize_context(self, context: Context, data=None, **kwargs) -> Optional[SerializedMessage]:
        if data is None:
            data = context.raw_message
        if context.request_id is not None:
            kwargs['request_id'] = context.request_id
        return SerializedMessage(
            text=context.message_text,
            user_id=context.user_id,
            from_user=True,
            data=data,
            source=context.source,
            **kwargs
        )

    def serialize_response(self, data, context: Context, response: Response, **kwargs) -> Optional[SerializedMessage]:
        data = copy.deepcopy(data)
        if context.request_id is not None:
            kwargs['request_id'] = context.request_id
        if response.label:
            kwargs['label'] = response.label
        return SerializedMessage(
            text=response.text,
            user_id=context.user_id,
            from_user=False,
            data=data,
            source=context.source,
            **kwargs
        )

    def uses_native_state(self, context: Context) -> bool:
        """ Whether dialog state can be extracted directly from a context"""
        return False

    def get_native_state(self, context: Context) -> Optional[Dict]:
        """ Return native dialog state if it is possible"""
        return
