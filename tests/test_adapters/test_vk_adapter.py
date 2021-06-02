from dialogic.adapters import VkAdapter
from dialogic.dialog import Response


def test_keyboard_squeeze():
    resp = Response(text='не важно', suggests=[
        'удалить направление', 'Агропромышленный комплекс', 'Вооружение и военная техника',
        'Естественные науки', 'Инженерные науки и технологии', 'Искусство и гуманитарные науки',
        'Компьютерные науки', 'Медицина и здравоохранение', 'Педагогические науки',
        'Социально-экономические науки', 'вакансии', 'мой регион', 'мои направления', 'главное меню'
    ])
    adapter = VkAdapter(suggest_cols='auto')
    result = adapter.make_response(resp)
    keyboard = result['keyboard']['buttons']
    assert len(keyboard) == 10
    assert sum(len(row) for row in keyboard) == len(resp.suggests)
    assert max(len(row) for row in keyboard) <= 5
