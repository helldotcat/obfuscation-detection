import json

from aiohttp import web
from aiohttp.web_fileresponse import FileResponse
from catboost import CatBoostClassifier

from converter import converter

DETECTION_MODEL = CatBoostClassifier()
DETECTION_MODEL.load_model("/app/detection_model.save")


CLASSIFICATION_MODEL = CatBoostClassifier()
CLASSIFICATION_MODEL.load_model("/app/classification_model.save")


def load_feature_columns(path: str):
    with open(path) as f:
        return json.load(f)


FEATURE_COLUMNS = load_feature_columns('/app/feature_columns.json')


async def handle_ru_index(_request):
    return FileResponse('/app/ru/index.html')

async def handle_en_index(_request):
    return FileResponse('/app/en/index.html')


async def handle_obfuscation_check(request):
    request_json = await request.post()
    code = request_json.get('code', '')

    try:
        features_extractor = converter.AstToCsvConverter()
        features_extractor.parse_from_string(code=code)
        features_extractor.convert()
        features_dict = features_extractor.get_features()
    except Exception as e:
        return web.json_response(
            {'processing_error': True}
        )

    feature_vector = []

    nodes_count = sum(features_dict['nodes'].values())

    if nodes_count < 25:
        return web.json_response(
            {'to_small': True}
        )

    nodes_pairs_count = sum(features_dict['node_pairs'].values())

    for feature in FEATURE_COLUMNS:
        if feature == 'v_colors':
            feature_vector.append(
                len(features_dict['nodes'])
            )
            continue

        if feature == 'e_colors':
            feature_vector.append(
                len(features_dict['node_pairs'])
            )
            continue

        key_first, key_second = feature.split(';')

        if key_first == 'nodes':
            feature_vector.append(
                features_dict[key_first].get(key_second, 0) / nodes_count
            )
        elif key_first == 'node_pairs':
            feature_vector.append(
                features_dict[key_first].get(key_second, 0) / nodes_pairs_count
            )
        else:
            feature_vector.append(
                features_dict[key_first].get(key_second, 0)
            )

    detection_result = DETECTION_MODEL.predict(feature_vector)
    detection_proba = DETECTION_MODEL.predict_proba(feature_vector)[1]

    classification_result = CLASSIFICATION_MODEL.predict(feature_vector)[0]

    return web.json_response(
        {
            'detection_result': bool(detection_result),
            'detection_probability': f'{detection_proba * 100:.2f}',
            'obfuscation_class': classification_result,
        }
    )


app = web.Application()
app.add_routes([web.get('/ru', handle_ru_index),
                web.get('/', handle_en_index),
                web.post('/check_obfuscation', handle_obfuscation_check)])


if __name__ == '__main__':
    web.run_app(app, port=5050)
